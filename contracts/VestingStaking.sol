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

    uint256 public totalValueLocked;

    uint256 public rewardPerHour;

    Status public status;

    enum Status {
        NotStarted,
        Started
    }

    // Linear - linear withdrawing after cliff time
    // Stepped - 50% withdrawing in the 1st half after cliff time, 50% - in the 2nd half
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
        uint256 lastRewardTimestamp;
        uint256 vestingStrategyNumber;
    }

    // The pool from which the admin pays rewards; Always: balanceOf(contractOwner) >= TVL + rewardPool
    uint256 public rewardPool;

    // Stakeholders and stakes
    mapping (address => StakeInfo) public stakes;
    mapping (address => bool) public isStakeholder;

    // Vestings
    uint256 public vestingStrategiesAmount = 0;
    mapping (uint256 => VestingInfo) public vestingStrategies;

    // Whitelist
    mapping (address => bool) public isWhitelisted;


    /**
     * @dev Initializing token for vesting-staking
     */
    constructor(address _tokenAddress) public {
        tokenAddress = _tokenAddress;
        contractOwner = msg.sender;
        status = Status.NotStarted;
    }


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


    function addToWhitelist(address[] memory _accounts) external onlyOwner() {
        require(_accounts.length < 10, "It's allowed to add up to 10 accounts at a time");
        for (uint256 i=0; i<_accounts.length; i++) {
            isWhitelisted[_accounts[i]] = true;
        }
    }


    function deleteFromWhitelist(address _account) external onlyOwner() {
        require(isWhitelisted[_account] == true, "This account is not in the whitelist");
        isWhitelisted[_account] = false;
    }


    function initAllocations(address[] memory _accounts, uint256[] memory _stake, uint256[] memory _strategies) external onlyOwner() {
        require(_accounts.length == _stake.length &&_accounts.length == _strategies.length, "Arrays are not the same size");
        require(_accounts.length < 10, "It's allowed to add up to 10 accounts at a time");
        uint256 startTimestamp = block.timestamp;
        uint256 lastRewardTimestamp = 0;
        uint256 withdrawed = 0;

        for (uint i=0; i<_accounts.length; i++) {
            address account = _accounts[i];
            uint256 stake = _stake[i];
            uint256 strategyNum = _strategies[i];
            require(account != address(0));
            require(Token(tokenAddress).balanceOf(contractOwner) >= stake + totalValueLocked);
            require(stake > 0 && stake < 50_000);
            require(strategyNum != 0 && strategyNum <= vestingStrategiesAmount);

            StakeInfo memory newStake = StakeInfo(
                stake, withdrawed, startTimestamp, lastRewardTimestamp, strategyNum
            );
            stakes[account] = newStake;
            isStakeholder[account] = true;

            totalValueLocked = totalValueLocked.add(stake);
        }
    }


    function start(uint256 _rewardPerHour, uint256 _rewardPool) external onlyOwner() {
        require(Token(tokenAddress).balanceOf(contractOwner) >= _rewardPool + totalValueLocked);
        rewardPerHour = _rewardPerHour;
        status = Status.Started;
        startingTimestamp = block.timestamp;
        rewardPool = _rewardPool;
    }


    function stake(uint256 _stake, uint256 _strategyNum) external {
        require(status == Status.Started, "Vesting-staking hasn't started yet");
        require(isStakeholder[msg.sender] != true, "You are stakeholder already");
        require(isWhitelisted[msg.sender] == true, "You are not in the whitelist, ask admin to add you");
        require(_strategyNum != 0 && _strategyNum <= vestingStrategiesAmount, "Wrong strategy number");
        require(Token(tokenAddress).balanceOf(contractOwner) >= rewardPool + totalValueLocked + _stake, "Contract owner doesn't have that many tokens");

        StakeInfo memory newStake = StakeInfo(
            _stake, 0, block.timestamp, 0, _strategyNum
        );
        stakes[msg.sender] = newStake;
        isStakeholder[msg.sender] = true;

        totalValueLocked = totalValueLocked.add(_stake);
    }


    function getReward() external {
        uint256 tokensReward = calculateCurrentReward(msg.sender);
        require(tokensReward != 0);
        require(rewardPool >= tokensReward, "Not enough tokens in reward pool");
        Token(tokenAddress).transferFrom(contractOwner, msg.sender, tokensReward);
        rewardPool = rewardPool.sub(tokensReward);
        stakes[msg.sender].lastRewardTimestamp = block.timestamp;
    }


    function vestingWithdraw() external {
        uint256 withdraw = calculateVestingSchedule(msg.sender);
        require(withdraw != 0);

        Token(tokenAddress).transferFrom(contractOwner, msg.sender, withdraw);
        stakes[msg.sender].tokensStaked = stakes[msg.sender].tokensStaked.sub(withdraw);
        stakes[msg.sender].vestingWithdrawed = stakes[msg.sender].vestingWithdrawed.add(withdraw);
        totalValueLocked = totalValueLocked.sub(withdraw);
    }


    function calculateCurrentReward(address _account) public view returns (uint256) {
        require(status == Status.Started, "Vesting-staking hasn't started yet");
        require(isStakeholder[msg.sender] == true, "You are not stakeholder");

        uint256 lastRewardTime = 0;

        if (stakes[_account].lastRewardTimestamp == 0) {
            if (stakes[_account].startingTimestamp < startingTimestamp) {
                lastRewardTime = startingTimestamp;
            }
            else {
                lastRewardTime = stakes[_account].startingTimestamp;
            }
        }
        else {
            lastRewardTime = stakes[_account].lastRewardTimestamp;
        }

        require(block.timestamp.sub(lastRewardTime) >= 3600, "At least one hour must pass to receive the reward");
        uint256 hoursAmount = block.timestamp.sub(lastRewardTime).div(1 hours);

        uint256 tokensReward = stakes[_account].tokensStaked.mul(rewardPerHour).mul(hoursAmount).div(totalValueLocked);
        return tokensReward;
    }


    function editAmountPerWallet(address _account, uint256 _amount) external onlyOwner() {
        require(status == Status.NotStarted, "Staking is started already");
        require(isStakeholder[_account] == true, "This account is not a stakeholder");
        require(_amount > 0);
        
        uint256 prevAmount = stakes[_account].tokensStaked;
        require(Token(tokenAddress).balanceOf(contractOwner) >= rewardPool + totalValueLocked + _amount - prevAmount, "Contract owner doesn't have that many tokens");

        stakes[_account].tokensStaked = _amount;

        totalValueLocked = totalValueLocked.sub(prevAmount).add(_amount);
    }


    function calculateVestingSchedule(address _account) public view returns (uint256) {
        require(status == Status.Started, "Vesting-staking hasn't started yet");
        require(isStakeholder[_account] == true, "User is not a stakeholder");

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

    function addAditionalReward(uint256 _extraReward) external onlyOwner() {
        require(Token(tokenAddress).balanceOf(contractOwner) >= rewardPool + totalValueLocked + _extraReward);
        rewardPool = rewardPool.add(_extraReward);
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

    function getLastRewardTimestamp(address _account) public view returns (uint256) {
        return stakes[_account].lastRewardTimestamp;
    }

    function getVestingStrategyNumber(address _account) public view returns (uint256) {
        return stakes[_account].vestingStrategyNumber;
    }

    function getAllUserInfo(address _account) public view returns (uint256, uint256, uint256, uint256, uint256) {
        uint256 stakecount = getStackedTokens(_account);
        uint256 withdraw = getWithdrawedVestingTokens(_account);
        uint256 starttime = getsStartingTimestampOfStacking(_account);
        uint256 lastReward = getLastRewardTimestamp(_account);
        uint256 strategy = getVestingStrategyNumber(_account);
        return (stakecount, withdraw, starttime, lastReward, strategy);
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