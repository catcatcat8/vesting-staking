// SPDX-License-Identifier: MIT

pragma solidity >0.6.0;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

import "./Token.sol";

contract VestingStaking is Ownable{
    using SafeMath for uint256;

    address public contractOwner;
    address public tokenAddress;

    uint256 public startingTimestamp;

    // Total staked tokens
    uint256 public totalValueLocked;

    uint256 public rewardPerHour;

    Status public status;

    enum Status {
        NotStarted,
        Started
    }

    // Linear - linear withdrawing after cliff time
    // Stepped - 50% withdrawing in the 1st half of vesting time, 50% - in the 2nd half
    enum VestingStrategies {
        Linear,
        Stepped
    }

    struct VestingInfo {
        uint256 cliffTime;
        uint256 vestingTime;
        VestingStrategies vestingStrategy;
    }

    struct StakeInfo {
        uint256 tokensStaked;
        uint256 vestingWithdrawed;
        uint256 startingTimestamp;
        uint256 vestingStrategyNumber;
        uint256 rewardPerTokenPaid;
        uint256 reward;
    }

    // Synthetix-staking
    uint256 public rewardPerTokenStored;
    uint256 public lastUpdateTime;

    // The pool from which the admin pays rewards 
    // Always: balanceOf(contractOwner) >= TVL + rewardPool
    uint256 public rewardPool;

    // Stakeholders and stakes
    mapping (address => StakeInfo) public stakes;
    mapping (address => bool) public isStakeholder;

    // Vestings
    uint256 public vestingStrategiesAmount = 0;
    mapping (uint256 => VestingInfo) public vestingStrategies;

    // Whitelisted accounts can stake tokens after calling start() by the owner
    mapping (address => bool) public isWhitelisted;

    //-------------------------------------------------------------------------
    // STATE MODIFYING FUNCTIONS
    //-------------------------------------------------------------------------

    // Initializing token for vesting-staking
    constructor(address _tokenAddress) public {
        tokenAddress = _tokenAddress;
        contractOwner = msg.sender;
        status = Status.NotStarted;
    }

    // Creating linear or stepped (50% tokens in each half of vesting time) westing strategy by the contract owner
    function createWestingStrategy(uint256 _cliffTimeInDays, uint256 _vestingTimeInDays, VestingStrategies _vestingStrategy) external onlyOwner() {
        require(_cliffTimeInDays >= 1);
        require(_vestingTimeInDays > 1);
        require(_vestingStrategy == VestingStrategies.Linear || _vestingStrategy == VestingStrategies.Stepped);
        vestingStrategiesAmount += 1;
        VestingInfo memory newVestingStrat = VestingInfo(
            _cliffTimeInDays * 1 days, _vestingTimeInDays * 1 days, _vestingStrategy
        );
        vestingStrategies[vestingStrategiesAmount] = newVestingStrat; 
    }

    // Adding accounts to the whitelist
    function addToWhitelist(address[] memory _accounts) external onlyOwner() {
        require(_accounts.length < 10, "It's allowed to add up to 10 accounts at a time");
        for (uint256 i=0; i<_accounts.length; i++) {
            isWhitelisted[_accounts[i]] = true;
        }
    }

    // Deleting account from the whitelist
    function deleteFromWhitelist(address _account) external onlyOwner() {
        require(isWhitelisted[_account], "This account is not in the whitelist");
        isWhitelisted[_account] = false;
    }

    // Defining initial allocations which will be immediately stacked and start to vest after calling start()
    function initAllocations(address[] memory _accounts, uint256[] memory _stake, uint256[] memory _strategies) external onlyOwner() {
        require(_accounts.length == _stake.length &&_accounts.length == _strategies.length, "Arrays are not the same size");
        require(_accounts.length < 10, "It's allowed to add up to 10 accounts at a time");
        uint256 startTimestamp = block.timestamp;

        for (uint i=0; i<_accounts.length; i++) {
            address account = _accounts[i];
            uint256 stake = _stake[i];
            uint256 strategyNum = _strategies[i];
            require(account != address(0));
            require(Token(tokenAddress).balanceOf(contractOwner) >= stake + totalValueLocked);
            require(stake > 0 && stake < 50_000);
            require(strategyNum != 0 && strategyNum <= vestingStrategiesAmount);

            StakeInfo memory newStake = StakeInfo(
                stake, 0, startTimestamp, strategyNum, 0, 0
            );
            stakes[account] = newStake;
            isStakeholder[account] = true;

            totalValueLocked = totalValueLocked.add(stake);
        }
    }

    // Start of vesting-staking and initializing rewards by the contract owner
    function start(uint256 _rewardPerHour, uint256 _rewardPool) external onlyOwner() {
        require(Token(tokenAddress).balanceOf(contractOwner) >= _rewardPool + totalValueLocked);
        rewardPerHour = _rewardPerHour;
        status = Status.Started;
        startingTimestamp = block.timestamp;
        lastUpdateTime = startingTimestamp;
        rewardPool = _rewardPool;
    }

    // Staking and choosing vesting strategy by whitelisted account
    function stake(uint256 _stake, uint256 _strategyNum) external updateReward {
        require(status == Status.Started, "Vesting-staking hasn't started yet");
        require(!isStakeholder[msg.sender], "You are stakeholder already");
        require(isWhitelisted[msg.sender], "You are not in the whitelist, ask admin to add you");
        require(_strategyNum != 0 && _strategyNum <= vestingStrategiesAmount, "Wrong strategy number");
        require(Token(tokenAddress).balanceOf(contractOwner) >= rewardPool + totalValueLocked + _stake, "Contract owner doesn't have that many tokens");

        stakes[msg.sender].tokensStaked = _stake;
        stakes[msg.sender].vestingWithdrawed = 0;
        stakes[msg.sender].startingTimestamp = block.timestamp;
        stakes[msg.sender].vestingStrategyNumber = _strategyNum;

        isStakeholder[msg.sender] = true;

        totalValueLocked = totalValueLocked.add(_stake);
    }

    // Getting stake reward to the balance of ERC20 token according to account's stake share to TVL
    function getReward() external updateReward {
        uint256 tokensReward = stakes[msg.sender].reward;
        require(tokensReward != 0);
        require(rewardPool >= tokensReward, "Not enough tokens in reward pool");

        Token(tokenAddress).transferFrom(contractOwner, msg.sender, tokensReward);
        rewardPool = rewardPool.sub(tokensReward);
        stakes[msg.sender].reward = 0;
    }

    // Withdraw staked tokens according to the vesting strategy. Decreases your share in TVL.
    function vestingWithdraw() external updateReward {
        uint256 withdraw = calculateVestingSchedule(msg.sender);
        require(withdraw != 0);

        Token(tokenAddress).transferFrom(contractOwner, msg.sender, withdraw);
        stakes[msg.sender].tokensStaked = stakes[msg.sender].tokensStaked.sub(withdraw);
        stakes[msg.sender].vestingWithdrawed = stakes[msg.sender].vestingWithdrawed.add(withdraw);
        totalValueLocked = totalValueLocked.sub(withdraw);
    }

    // Admin function for editing the amount of staked token for account before start() is called
    function editAmountPerWallet(address _account, uint256 _amount) external onlyOwner() {
        require(status == Status.NotStarted, "Staking is started already");
        require(isStakeholder[_account], "This account is not a stakeholder");
        require(_amount > 0);
        
        uint256 prevAmount = stakes[_account].tokensStaked;
        require(Token(tokenAddress).balanceOf(contractOwner) >= rewardPool + totalValueLocked + _amount - prevAmount, "Contract owner doesn't have that many tokens");

        stakes[_account].tokensStaked = _amount;

        totalValueLocked = totalValueLocked.sub(prevAmount).add(_amount);
    }

    // Replenishment of the reward pool by the contract owner
    function addAditionalReward(uint256 _extraReward) external onlyOwner() {
        require(Token(tokenAddress).balanceOf(contractOwner) >= rewardPool + totalValueLocked + _extraReward);
        rewardPool = rewardPool.add(_extraReward);
    }

    //-------------------------------------------------------------------------
    // MODIFIERS
    //-------------------------------------------------------------------------

    // Called when someone stakes, withdraws or receives tokens (synthetix-staking algorithm)
    modifier updateReward() {
        rewardPerTokenStored = _rewardPerToken();
        lastUpdateTime = block.timestamp;
        stakes[msg.sender].reward = _earned();
        stakes[msg.sender].rewardPerTokenPaid = rewardPerTokenStored;
        _;
    }

    //-------------------------------------------------------------------------
    // INTERNAL FUNCTIONS
    //-------------------------------------------------------------------------

    // Calculates not paid current reward per staked token
    function _rewardPerToken() internal returns (uint256) {
        if (totalValueLocked == 0) {
            return 0;
        }
        return rewardPerTokenStored + (
            rewardPerHour * (block.timestamp - lastUpdateTime) * 1e18 / totalValueLocked / 1 hours
        );
    }

    // Calculates reward for stakeholder
    function _earned() internal returns (uint256) {
        return (stakes[msg.sender].tokensStaked * (_rewardPerToken() - stakes[msg.sender].rewardPerTokenPaid) / 1e18) + stakes[msg.sender].reward;
    }

    //-------------------------------------------------------------------------
    // VIEW FUNCTIONS
    //-------------------------------------------------------------------------

    // Calculates the amount of vesting schedule tokens for withdrawing
    function calculateVestingSchedule(address _account) public view returns (uint256) {
        require(status == Status.Started, "Vesting-staking hasn't started yet");
        require(isStakeholder[_account], "User is not a stakeholder");

        VestingInfo memory accountStrategy = vestingStrategies[stakes[_account].vestingStrategyNumber];

        uint256 startVesting = stakes[_account].startingTimestamp;
        if (startVesting < startingTimestamp) {
            startVesting = startingTimestamp;
        }

        // Vesting time is over, account can withdraw 100% tokens
        if (block.timestamp > startVesting + accountStrategy.cliffTime + accountStrategy.vestingTime) {
            return stakes[_account].tokensStaked;
        }
        // Withdraw according to the strategy
        else {
            if (block.timestamp > startVesting + accountStrategy.cliffTime) {  // it is possible to withdraw some tokens
                uint256 withdraw = 0;
                if (accountStrategy.vestingStrategy == VestingStrategies.Linear) {
                    withdraw = (block.timestamp - startVesting - accountStrategy.cliffTime) *
                        (stakes[msg.sender].tokensStaked + stakes[msg.sender].vestingWithdrawed) / accountStrategy.vestingTime;
                    withdraw = withdraw - stakes[msg.sender].vestingWithdrawed;
                }
                else {  // 50% in 1st half, 50% in 2nd half

                    if ((block.timestamp - startVesting - accountStrategy.cliffTime) < accountStrategy.vestingTime.div(2)) {  // 1st half
                        withdraw = (stakes[msg.sender].tokensStaked + stakes[msg.sender].vestingWithdrawed).div(2) - stakes[msg.sender].vestingWithdrawed;
                    }
                    else {
                        withdraw = stakes[msg.sender].tokensStaked;
                    }
                }

                return withdraw;
            }
            return 0;
        }
    }

    function getTVLAmount() public view returns (uint256) {
        return totalValueLocked;
    }

    function getAPYStaked() public view returns (uint256) {
        return (rewardPerHour * 24 * 365 * 100) / totalValueLocked;
    }

    function getAPYNotStaked(uint256 _stake) public view returns (uint256) {
        return (rewardPerHour * 24 * 365 * 100) / (totalValueLocked + _stake);
    }

    function getTotalSupply() public view returns (uint256) {
        return Token(tokenAddress).totalSupply();
    }

    function getStackedTokens(address _account) public view returns (uint256) {
        return stakes[_account].tokensStaked;
    }

    function getWithdrawedVestingTokens(address _account) public view returns (uint256) {
        return stakes[_account].vestingWithdrawed;
    }

    function getsStartingTimestampOfStacking(address _account) public view returns (uint256) {
        return stakes[_account].startingTimestamp;
    }

    function getVestingStrategyNumber(address _account) public view returns (uint256) {
        return stakes[_account].vestingStrategyNumber;
    }

    function getAllUserInfo(address _account) public view returns (uint256, uint256, uint256, uint256) {
        uint256 stakecount = getStackedTokens(_account);
        uint256 withdraw = getWithdrawedVestingTokens(_account);
        uint256 starttime = getsStartingTimestampOfStacking(_account);
        uint256 strategy = getVestingStrategyNumber(_account);
        return (stakecount, withdraw, starttime, strategy);
    }

    function getStrategyCliffTime(uint256 _strategyNumber) public view returns (uint256) {
        return vestingStrategies[_strategyNumber].cliffTime;
    }

    function getStrategyVestingTime(uint256 _strategyNumber) public view returns (uint256) {
        return vestingStrategies[_strategyNumber].vestingTime;
    }

    function getStrategyType(uint256 _strategyNumber) public view returns (VestingStrategies) {
        return vestingStrategies[_strategyNumber].vestingStrategy;
    }
}