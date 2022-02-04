#!/usr/bin/python3
import brownie

def test_correct_create_linear_and_stepped_strategies(accounts, vestingStaking):
    cliff_time_in_days = 30
    vesting_time = 30
    linear = 0
    stepped = 1

    assert vestingStaking.vestingStrategiesAmount() == 0

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time, linear, {'from': accounts[0]})
    assert vestingStaking.vestingStrategiesAmount() == 1

    vestingStaking.createWestingStrategy(cliff_time_in_days, vesting_time, stepped, {'from': accounts[0]})
    assert vestingStaking.vestingStrategiesAmount() == 2

    seconds_in_day = 86400
    assert vestingStaking.vestingStrategies(1) == (cliff_time_in_days * seconds_in_day, vesting_time * seconds_in_day, linear)
    assert vestingStaking.vestingStrategies(2) == (cliff_time_in_days * seconds_in_day, vesting_time * seconds_in_day, stepped)


def test_create_wrong_strategy(accounts, vestingStaking):
    strategy_type = 2  # not linear, not stepped

    with brownie.reverts():
        vestingStaking.createWestingStrategy(30, 30, strategy_type, {'from': accounts[0]})


def test_zero_cliff_time(accounts, vestingStaking):
    cliff_time = 0

    with brownie.reverts():
        vestingStaking.createWestingStrategy(cliff_time, 30, 0, {'from': accounts[0]})
    

def test_zero_vesting_time(accounts, vestingStaking):
    vesting_time = 0

    with brownie.reverts():
        vestingStaking.createWestingStrategy(30, vesting_time, 0, {'from': accounts[0]})
