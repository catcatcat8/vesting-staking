#!/usr/bin/python3
import re
import brownie

def test_correct_reward(accounts, vestingStakingAndToken):
    vesting_contract = vestingStakingAndToken[0]
    token_contract = vestingStakingAndToken[1]
    token_contract.approve(vesting_contract, token_contract.balanceOf(vesting_contract.contractOwner()))  # approve to vesting contract to spend tokens from owner

    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vesting_contract.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vesting_contract.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    first_acc = accounts[1]
    first_stake = 60
    first_strategy = 1  # linear

    second_acc = accounts[2]
    second_stake = 40
    second_strategy = 2  # stepped
    
    reward_per_hour = 100
    reward_pool = 1_000_000_000
    total_value_locked = first_stake + second_stake

    vesting_contract.initAllocations((first_acc, second_acc), (first_stake, second_stake), (first_strategy, second_strategy))
    vesting_contract.start(reward_per_hour, reward_pool, {"from": accounts[0]})

    balance_of_first_acc_before_reward = token_contract.balanceOf(first_acc)
    balance_of_second_acc_before_reward = token_contract.balanceOf(second_acc)

    hours_passed = 1
    brownie.chain.sleep(hours_passed * 3600)  # 1 hour
    vesting_contract.getReward({"from": accounts[1]})
    assert token_contract.balanceOf(first_acc) == balance_of_first_acc_before_reward + (first_stake * reward_per_hour * hours_passed // total_value_locked)

    vesting_contract.getReward({"from": accounts[2]})
    assert token_contract.balanceOf(second_acc) == balance_of_second_acc_before_reward + (second_stake * reward_per_hour * hours_passed // total_value_locked)

    hours_passed = 2
    brownie.chain.sleep(hours_passed * 3600)  # 2 hours
    balance_of_first_acc_before_reward = token_contract.balanceOf(first_acc)
    vesting_contract.getReward({"from": accounts[1]})
    assert token_contract.balanceOf(first_acc) == balance_of_first_acc_before_reward + (first_stake * reward_per_hour * hours_passed // total_value_locked)


def test_get_reward_before_at_least_one_token_earned(accounts, vestingStakingAndToken):
    vesting_contract = vestingStakingAndToken[0]
    token_contract = vestingStakingAndToken[1]
    token_contract.approve(vesting_contract, token_contract.balanceOf(vesting_contract.contractOwner()))  # approve to vesting contract to spend tokens from owner

    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vesting_contract.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vesting_contract.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    stake = 60
    strategy = 1  # linear

    reward_per_hour = 100
    reward_pool = 1_000_000_000

    vesting_contract.initAllocations((accounts[1],), (stake,), (strategy,))
    vesting_contract.start(reward_per_hour, reward_pool, {"from": accounts[0]})
    with brownie.reverts():
        vesting_contract.getReward({"from": accounts[1]})


def test_get_reward_by_non_stakeholder(accounts, vestingStakingAndToken):
    vesting_contract = vestingStakingAndToken[0]
    token_contract = vestingStakingAndToken[1]
    token_contract.approve(vesting_contract, token_contract.balanceOf(vesting_contract.contractOwner()))  # approve to vesting contract to spend tokens from owner

    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vesting_contract.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vesting_contract.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    stake = 60
    strategy = 1  # linear

    reward_per_hour = 100
    reward_pool = 1_000_000_000

    vesting_contract.initAllocations((accounts[1],), (stake,), (strategy,))
    vesting_contract.start(reward_per_hour, reward_pool, {"from": accounts[0]})
    hours_passed = 1
    brownie.chain.sleep(hours_passed * 3600 + 1)  # 1 hour and 1 second (for getting reward)

    with brownie.reverts():
        vesting_contract.getReward({"from": accounts[2]})  # only account[1] is stakeholder


def test_get_reward_by_whitelisted_stakeholder(accounts, vestingStakingAndToken):
    vesting_contract = vestingStakingAndToken[0]
    token_contract = vestingStakingAndToken[1]
    token_contract.approve(vesting_contract, token_contract.balanceOf(vesting_contract.contractOwner()))  # approve to vesting contract to spend tokens from owner

    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vesting_contract.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vesting_contract.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    first_acc_stake = 60
    first_acc_strategy = 1  # linear

    second_acc_stake = 40
    second_acc_strategy = 1

    reward_per_hour = 100
    reward_pool = 1_000_000_000

    vesting_contract.initAllocations((accounts[1],), (first_acc_stake,), (first_acc_strategy,))
    vesting_contract.start(reward_per_hour, reward_pool, {"from": accounts[0]})
    vesting_contract.addToWhitelist((accounts[2],))
    vesting_contract.stake(second_acc_stake, second_acc_strategy, {"from": accounts[2]})

    tvl = vesting_contract.totalValueLocked()
    assert tvl == first_acc_stake + second_acc_stake
    
    hours_passed = 1
    brownie.chain.sleep(hours_passed * 3600)  # 1 hour
    balance_before_reward = token_contract.balanceOf(accounts[2])
    vesting_contract.getReward({'from': accounts[2]})

    assert token_contract.balanceOf(accounts[2]) == balance_before_reward + (second_acc_stake * reward_per_hour * hours_passed // tvl)


def test_add_aditional_reward(accounts, vestingStakingAndToken):
    vesting_contract = vestingStakingAndToken[0]
    token_contract = vestingStakingAndToken[1]
    token_contract.approve(vesting_contract, token_contract.balanceOf(vesting_contract.contractOwner()))  # approve to vesting contract to spend tokens from owner

    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vesting_contract.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vesting_contract.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    stake = 30
    strategy = 1  # linear
    reward_per_hour = 100
    reward_pool = 1_000_000_000

    vesting_contract.initAllocations((accounts[1],), (stake,), (strategy,))
    vesting_contract.start(reward_per_hour, reward_pool, {"from": accounts[0]})

    additional_reward = 5_000_000
    vesting_contract.addAditionalReward(additional_reward, {"from": accounts[0]})

    assert vesting_contract.rewardPool() == reward_pool + additional_reward
