#!/usr/bin/python3
import brownie

def test_correct_reward(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    first_acc = accounts[1]
    first_stake = 60
    first_strategy = 1  # linear

    second_acc = accounts[2]
    second_stake = 40
    second_strategy = 2  # stepped
    
    reward_per_hour = 100
    total_value_locked = first_stake + second_stake

    vestingStaking.initAllocations((first_acc, second_acc), (first_stake, second_stake), (first_strategy, second_strategy))
    vestingStaking.start(reward_per_hour, {"from": accounts[0]})

    balance_of_first_acc_before_reward = vestingStaking.balanceOf(first_acc)
    balance_of_second_acc_before_reward = vestingStaking.balanceOf(second_acc)

    hours_passed = 1
    brownie.chain.sleep(hours_passed * 3600 + 1)  # 1 hour and 1 second (for getting reward)
    vestingStaking.getReward({"from": accounts[1]})
    assert vestingStaking.balanceOf(first_acc) == balance_of_first_acc_before_reward + (first_stake * reward_per_hour * hours_passed // total_value_locked)

    vestingStaking.getReward({"from": accounts[2]})
    assert vestingStaking.balanceOf(second_acc) == balance_of_second_acc_before_reward + (second_stake * reward_per_hour * hours_passed // total_value_locked)

    hours_passed = 2
    brownie.chain.sleep(hours_passed * 3600 + 100)  # 2 hours and 1 second
    balance_of_first_acc_before_reward = vestingStaking.balanceOf(first_acc)
    vestingStaking.getReward({"from": accounts[1]})
    assert vestingStaking.balanceOf(first_acc) == balance_of_first_acc_before_reward + (first_stake * reward_per_hour * hours_passed // total_value_locked)


def test_get_reward_before_one_hour(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    stake = 60
    strategy = 1  # linear

    reward_per_hour = 100

    vestingStaking.initAllocations((accounts[1],), (stake,), (strategy,))
    vestingStaking.start(reward_per_hour, {"from": accounts[0]})
    with brownie.reverts():
        vestingStaking.getReward({"from": accounts[1]})


def test_get_reward_by_non_stakeholder(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    stake = 60
    strategy = 1  # linear

    reward_per_hour = 100

    vestingStaking.initAllocations((accounts[1],), (stake,), (strategy,))
    vestingStaking.start(reward_per_hour, {"from": accounts[0]})
    hours_passed = 1
    brownie.chain.sleep(hours_passed * 3600 + 1)  # 1 hour and 1 second (for getting reward)

    with brownie.reverts():
        vestingStaking.getReward({"from": accounts[2]})  # only account[1] is stakeholder


def test_get_reward_by_whitelisted_stakeholder(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    first_acc_stake = 60
    first_acc_strategy = 1  # linear

    second_acc_stake = 40
    second_acc_strategy = 1

    reward_per_hour = 100

    vestingStaking.initAllocations((accounts[1],), (first_acc_stake,), (first_acc_strategy,))
    vestingStaking.start(reward_per_hour, {"from": accounts[0]})
    vestingStaking.addToWhitelist((accounts[2],))
    vestingStaking.stake(second_acc_stake, second_acc_strategy, {"from": accounts[2]})

    tvl = vestingStaking.totalValueLocked()
    assert tvl == first_acc_stake + second_acc_stake
    
    hours_passed = 1
    brownie.chain.sleep(hours_passed * 3600 + 1)  # 1 hour and 1 second (for getting reward)
    balance_before_reward = vestingStaking.balanceOf(accounts[2])
    vestingStaking.getReward({'from': accounts[2]})

    assert vestingStaking.balanceOf(accounts[2]) == balance_before_reward + (second_acc_stake * reward_per_hour * hours_passed // tvl)


def test_add_aditional_reward(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    stake = 30
    strategy = 1  # linear
    reward_per_hour = 100

    vestingStaking.initAllocations((accounts[1],), (stake,), (strategy,))
    vestingStaking.start(reward_per_hour, {"from": accounts[0]})

    additional_reward = 50
    vestingStaking.addAditionalReward(additional_reward, {"from": accounts[0]})

    assert vestingStaking.rewardPerHour() == reward_per_hour + additional_reward