#!/usr/bin/python3
import brownie


def test_sender_balance_decreases(accounts, vestingStaking):
    sender_balance = vestingStaking.balanceOf(accounts[0])
    amount = sender_balance // 4

    vestingStaking.transfer(accounts[1], amount, {'from': accounts[0]})

    assert vestingStaking.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, vestingStaking):
    receiver_balance = vestingStaking.balanceOf(accounts[1])
    amount = vestingStaking.balanceOf(accounts[0]) // 4

    vestingStaking.transfer(accounts[1], amount, {'from': accounts[0]})

    assert vestingStaking.balanceOf(accounts[1]) == receiver_balance + amount


def test_total_supply_not_affected(accounts, vestingStaking):
    total_supply = vestingStaking.totalSupply()
    amount = vestingStaking.balanceOf(accounts[0])

    vestingStaking.transfer(accounts[1], amount, {'from': accounts[0]})

    assert vestingStaking.totalSupply() == total_supply


def test_returns_true(accounts, vestingStaking):
    amount = vestingStaking.balanceOf(accounts[0])
    tx = vestingStaking.transfer(accounts[1], amount, {'from': accounts[0]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, vestingStaking):
    amount = vestingStaking.balanceOf(accounts[0])
    receiver_balance = vestingStaking.balanceOf(accounts[1])

    vestingStaking.transfer(accounts[1], amount, {'from': accounts[0]})

    assert vestingStaking.balanceOf(accounts[0]) == 0
    assert vestingStaking.balanceOf(accounts[1]) == receiver_balance + amount


def test_transfer_zero_vestingStakings(accounts, vestingStaking):
    sender_balance = vestingStaking.balanceOf(accounts[0])
    receiver_balance = vestingStaking.balanceOf(accounts[1])

    vestingStaking.transfer(accounts[1], 0, {'from': accounts[0]})

    assert vestingStaking.balanceOf(accounts[0]) == sender_balance
    assert vestingStaking.balanceOf(accounts[1]) == receiver_balance


def test_transfer_to_self(accounts, vestingStaking):
    sender_balance = vestingStaking.balanceOf(accounts[0])
    amount = sender_balance // 4

    vestingStaking.transfer(accounts[0], amount, {'from': accounts[0]})

    assert vestingStaking.balanceOf(accounts[0]) == sender_balance


def test_insufficient_balance(accounts, vestingStaking):
    balance = vestingStaking.balanceOf(accounts[0])

    with brownie.reverts():
        vestingStaking.transfer(accounts[1], balance + 1, {'from': accounts[0]})


def test_transfer_event_fires(accounts, vestingStaking):
    amount = vestingStaking.balanceOf(accounts[0])
    tx = vestingStaking.transfer(accounts[1], amount, {'from': accounts[0]})

    assert len(tx.events) == 1
    assert tx.events["Transfer"].values() == [accounts[0], accounts[1], amount]