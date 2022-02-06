#!/usr/bin/python3
import brownie

def test_correct_init_allocations(accounts, vestingStaking):
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
    
    start_time = brownie.chain.time()

    assert vestingStaking.totalValueLocked() == 0

    vestingStaking.initAllocations((first_acc, second_acc), (first_stake, second_stake), (first_strategy, second_strategy))

    assert vestingStaking.stakes(first_acc)[0] == first_stake  # tokens staked
    assert vestingStaking.stakes(first_acc)[1] == 0  # vesting withdrawed
    assert vestingStaking.stakes(first_acc)[2] in range(start_time, start_time + 2)  # start time (operations from above will take no more than a second)
    assert vestingStaking.stakes(first_acc)[3] == 1  # vesting strategy number (1 - linear, 2 - stepped)

    assert vestingStaking.stakes(second_acc)[0] == second_stake
    assert vestingStaking.stakes(second_acc)[1] == 0
    assert vestingStaking.stakes(second_acc)[2] in range(start_time, start_time + 2)
    assert vestingStaking.stakes(second_acc)[3] == 2

    assert vestingStaking.totalValueLocked() == first_stake + second_stake


def test_wrong_stake_array_size(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    with brownie.reverts():
        vestingStaking.initAllocations((accounts[1], accounts[2]), (60,), (1, 2))  # two accounts, but 1 stake

    with brownie.reverts():
        vestingStaking.initAllocations((accounts[1], accounts[2]), (60, 40, 20), (1, 2))  # two accounts, but 3 stakes


def test_stake_more_than_limit(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    stake_limit = 49999

    with brownie.reverts():
        vestingStaking.initAllocations((accounts[1], accounts[2]), (60, stake_limit + 1), (1, 2))  # stake 50000 tokens for 2nd account


def test_wrong_strategy_for_init_allocations(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    vesting_strategies = 2

    with brownie.reverts():
        vestingStaking.initAllocations((accounts[1], accounts[2]), (60, 20), (vesting_strategies + 1, 2))  # 3rd vesting strat for 1st acc


def test_edit_amount_per_wallet(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time_in_days = 30
    linear = 0
    stepped = 1

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, linear, {'from': accounts[0]})
    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time_in_days, stepped, {'from': accounts[0]})

    stake = 30
    strategy = 1  # linear

    vestingStaking.initAllocations((accounts[1],), (stake,), (strategy,))

    new_stake = 60
    vestingStaking.editAmountPerWallet(accounts[1], new_stake)
    new_stake_in_contract = vestingStaking.stakes(accounts[1])[0]

    assert new_stake_in_contract == new_stake
