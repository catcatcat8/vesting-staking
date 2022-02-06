#!/usr/bin/python3
import brownie

def test_start(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1
    reward_per_hour = 100
    reward_pool = 1_000_000_000

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    start_time = brownie.chain.time()
    vestingStaking.start(reward_per_hour, reward_pool, {'from': accounts[0]})

    assert vestingStaking.rewardPerHour() == reward_per_hour
    assert vestingStaking.status() == 1   # 0 - not started; 1 - started
    assert vestingStaking.startingTimestamp() in range(start_time, start_time + 2)  # # start time (operations from above will take no more than a second)


def test_stake_before_start(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    with brownie.reverts():
        vestingStaking.stake(60, 1, {"from": accounts[1]})


def test_stake_not_whitelisted(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1
    reward_per_hour = 100
    reward_pool = 1_000_000_000

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})
    vestingStaking.start(reward_per_hour, reward_pool, {'from': accounts[0]})

    with brownie.reverts():
        vestingStaking.stake(60, 1, {"from": accounts[1]})


def test_stake_wrong_strategy(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1
    reward_per_hour = 100
    reward_pool = 1_000_000_000

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})
    vestingStaking.start(reward_per_hour, reward_pool, {'from': accounts[0]})
    vestingStaking.addToWhitelist((accounts[1],), {"from": accounts[0]})

    strategy_num = 100
    with brownie.reverts():
        vestingStaking.stake(60, strategy_num, {"from": accounts[1]})


def test_correct_stake_from_whitelist(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1
    reward_per_hour = 100
    reward_pool = 1_000_000_000

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})
    vestingStaking.start(reward_per_hour, reward_pool, {'from': accounts[0]})
    vestingStaking.addToWhitelist((accounts[1],), {"from": accounts[0]})

    strategy_num = 1
    stake_sum = 60
    time_of_stake = brownie.chain.time()
    vestingStaking.stake(stake_sum, strategy_num, {"from": accounts[1]})

    assert vestingStaking.totalValueLocked() == stake_sum
    assert vestingStaking.isStakeholder(accounts[1]) == True

    assert vestingStaking.stakes(accounts[1])[0] == stake_sum  # tokens staked
    assert vestingStaking.stakes(accounts[1])[1] == 0  # vesting withdrawed
    assert vestingStaking.stakes(accounts[1])[2] in range(time_of_stake, time_of_stake + 2)  # start time (operations from above will take no more than a second)
    assert vestingStaking.stakes(accounts[1])[3] == strategy_num  # vesting strategy number (1 - linear, 2 - stepped)
