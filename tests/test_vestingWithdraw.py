#!/usr/bin/python3
import brownie

def test_correct_linear_strategy_vesting_withdraw(accounts, vestingStaking):
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

    balance_of_first_acc_before_vesting_withdraw = vestingStaking.balanceOf(accounts[1])
    locked_tokens_before_withdraw = vestingStaking.stakes(accounts[1])[0]

    # Trying to withdraw 1/30 after 1st day after cliff
    days_passed = 31
    brownie.chain.sleep(days_passed * 24 * 3600 + 1)  # 31 days and 1 second (for getting 1/30 of stake)
    vestingStaking.vestingWithdraw({"from": accounts[1]})
    withdrawed_tokens = (days_passed - cliff_time_in_days) * stake // vesting_time_in_days

    assert vestingStaking.balanceOf(accounts[1]) == balance_of_first_acc_before_vesting_withdraw + withdrawed_tokens
    assert vestingStaking.stakes(accounts[1])[0] == locked_tokens_before_withdraw - withdrawed_tokens  # stake
    assert vestingStaking.stakes(accounts[1])[1] == withdrawed_tokens  # withdraw
    
    # Trying to withdraw again in the same day
    with brownie.reverts():
        vestingStaking.vestingWithdraw({"from": accounts[1]})

    three_days_more_passed = 3
    brownie.chain.sleep(three_days_more_passed * 24 * 3600 + 1)  # 3 days and 1 second (for getting 4/30 of initial stake = 3 tokens (1 withdrawed already))
    vestingStaking.vestingWithdraw({"from": accounts[1]})
    new_withdraw = (days_passed + three_days_more_passed - cliff_time_in_days) * stake // vesting_time_in_days - withdrawed_tokens  # 4-1 tokens

    assert vestingStaking.balanceOf(accounts[1]) == balance_of_first_acc_before_vesting_withdraw + withdrawed_tokens + new_withdraw
    assert vestingStaking.stakes(accounts[1])[0] == locked_tokens_before_withdraw - withdrawed_tokens - new_withdraw  # stake
    assert vestingStaking.stakes(accounts[1])[1] == withdrawed_tokens + new_withdraw  # withdraw


def test_correct_stepped_strategy_vesting_withdraw(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1
    percent_in_first_half_of_vesting_time = 50

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    stake = 30
    strategy = 2  # stepped
    reward_per_hour = 100

    vestingStaking.initAllocations((accounts[1],), (stake,), (strategy,))
    vestingStaking.start(reward_per_hour, {"from": accounts[0]})

    balance_of_first_acc_before_vesting_withdraw = vestingStaking.balanceOf(accounts[1])
    locked_tokens_before_withdraw = vestingStaking.stakes(accounts[1])[0]

    # Trying to withdraw 1/2 in 1st half
    days_passed = 35
    brownie.chain.sleep(days_passed * 24 * 3600 + 1)  # 35 days and 1 second (for getting 50% of stake)
    vestingStaking.vestingWithdraw({"from": accounts[1]})
    withdrawed_tokens = stake * percent_in_first_half_of_vesting_time // 100  # get 50% (15 tokens)

    assert vestingStaking.balanceOf(accounts[1]) == balance_of_first_acc_before_vesting_withdraw + withdrawed_tokens
    assert vestingStaking.stakes(accounts[1])[0] == locked_tokens_before_withdraw - withdrawed_tokens  # stake
    assert vestingStaking.stakes(accounts[1])[1] == withdrawed_tokens  # withdraw

    # Trying to withdraw again 50% in the same day
    with brownie.reverts():
        vestingStaking.vestingWithdraw({"from": accounts[1]})

    # In second half of vesting time account can withdraw left 50% of tokens
    twenty_days_more_passed = 20
    brownie.chain.sleep(twenty_days_more_passed * 24 * 3600 + 1)  # 20 days and 1 second (for getting left 1/2 of stake)
    vestingStaking.vestingWithdraw({"from": accounts[1]})
    new_withdraw = stake * percent_in_first_half_of_vesting_time // 100  # get 50% (again 15 tokens)

    assert vestingStaking.balanceOf(accounts[1]) == balance_of_first_acc_before_vesting_withdraw + withdrawed_tokens + new_withdraw
    assert vestingStaking.stakes(accounts[1])[0] == locked_tokens_before_withdraw - withdrawed_tokens - new_withdraw  # stake
    assert vestingStaking.stakes(accounts[1])[1] == withdrawed_tokens + new_withdraw  # withdraw


def test_vesting_withdraw_correct_tvl(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1
    percent_in_first_half_of_vesting_time = 50

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    stake = 30
    strategy = 2  # stepped
    reward_per_hour = 100

    vestingStaking.initAllocations((accounts[1],), (stake,), (strategy,))
    vestingStaking.start(reward_per_hour, {"from": accounts[0]})

    tvl_before_withdraw = vestingStaking.totalValueLocked()

    # Trying to withdraw 1/2 in 1st half
    days_passed = 35
    brownie.chain.sleep(days_passed * 24 * 3600 + 1)  # 35 days and 1 second (for getting 50% of stake)
    vestingStaking.vestingWithdraw({"from": accounts[1]})
    withdrawed_tokens = stake * percent_in_first_half_of_vesting_time // 100  # get 50% (15 tokens)

    assert vestingStaking.totalValueLocked() == tvl_before_withdraw - withdrawed_tokens


def test_vesting_withdraw_before_clifftime(accounts, vestingStaking):
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

    # Trying to withdraw before cliff time
    with brownie.reverts():
        vestingStaking.vestingWithdraw({"from": accounts[1]})
