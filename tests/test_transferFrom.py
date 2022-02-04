#!/usr/bin/python3
import brownie


def test_sender_balance_decreases(accounts, vestingStaking):
    sender_balance = vestingStaking.balanceOf(accounts[0])
    amount = sender_balance // 4

    vestingStaking.approve(accounts[1], amount, {'from': accounts[0]})
    vestingStaking.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert vestingStaking.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, vestingStaking):
    receiver_balance = vestingStaking.balanceOf(accounts[2])
    amount = vestingStaking.balanceOf(accounts[0]) // 4

    vestingStaking.approve(accounts[1], amount, {'from': accounts[0]})
    vestingStaking.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert vestingStaking.balanceOf(accounts[2]) == receiver_balance + amount


def test_caller_balance_not_affected(accounts, vestingStaking):
    caller_balance = vestingStaking.balanceOf(accounts[1])
    amount = vestingStaking.balanceOf(accounts[0])

    vestingStaking.approve(accounts[1], amount, {'from': accounts[0]})
    vestingStaking.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert vestingStaking.balanceOf(accounts[1]) == caller_balance


def test_caller_approval_affected(accounts, vestingStaking):
    approval_amount = vestingStaking.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    vestingStaking.approve(accounts[1], approval_amount, {'from': accounts[0]})
    vestingStaking.transferFrom(accounts[0], accounts[2], transfer_amount, {'from': accounts[1]})

    assert vestingStaking.allowance(accounts[0], accounts[1]) == approval_amount - transfer_amount


def test_receiver_approval_not_affected(accounts, vestingStaking):
    approval_amount = vestingStaking.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    vestingStaking.approve(accounts[1], approval_amount, {'from': accounts[0]})
    vestingStaking.approve(accounts[2], approval_amount, {'from': accounts[0]})
    vestingStaking.transferFrom(accounts[0], accounts[2], transfer_amount, {'from': accounts[1]})

    assert vestingStaking.allowance(accounts[0], accounts[2]) == approval_amount


def test_total_supply_not_affected(accounts, vestingStaking):
    total_supply = vestingStaking.totalSupply()
    amount = vestingStaking.balanceOf(accounts[0])

    vestingStaking.approve(accounts[1], amount, {'from': accounts[0]})
    vestingStaking.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert vestingStaking.totalSupply() == total_supply


def test_returns_true(accounts, vestingStaking):
    amount = vestingStaking.balanceOf(accounts[0])
    vestingStaking.approve(accounts[1], amount, {'from': accounts[0]})
    tx = vestingStaking.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, vestingStaking):
    amount = vestingStaking.balanceOf(accounts[0])
    receiver_balance = vestingStaking.balanceOf(accounts[2])

    vestingStaking.approve(accounts[1], amount, {'from': accounts[0]})
    vestingStaking.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert vestingStaking.balanceOf(accounts[0]) == 0
    assert vestingStaking.balanceOf(accounts[2]) == receiver_balance + amount


def test_transfer_zero_vestingStakings(accounts, vestingStaking):
    sender_balance = vestingStaking.balanceOf(accounts[0])
    receiver_balance = vestingStaking.balanceOf(accounts[2])

    vestingStaking.approve(accounts[1], sender_balance, {'from': accounts[0]})
    vestingStaking.transferFrom(accounts[0], accounts[2], 0, {'from': accounts[1]})

    assert vestingStaking.balanceOf(accounts[0]) == sender_balance
    assert vestingStaking.balanceOf(accounts[2]) == receiver_balance


def test_transfer_zero_vestingStakings_without_approval(accounts, vestingStaking):
    sender_balance = vestingStaking.balanceOf(accounts[0])
    receiver_balance = vestingStaking.balanceOf(accounts[2])

    vestingStaking.transferFrom(accounts[0], accounts[2], 0, {'from': accounts[1]})

    assert vestingStaking.balanceOf(accounts[0]) == sender_balance
    assert vestingStaking.balanceOf(accounts[2]) == receiver_balance


def test_insufficient_balance(accounts, vestingStaking):
    balance = vestingStaking.balanceOf(accounts[0])

    vestingStaking.approve(accounts[1], balance + 1, {'from': accounts[0]})
    with brownie.reverts():
        vestingStaking.transferFrom(accounts[0], accounts[2], balance + 1, {'from': accounts[1]})


def test_insufficient_approval(accounts, vestingStaking):
    balance = vestingStaking.balanceOf(accounts[0])

    vestingStaking.approve(accounts[1], balance - 1, {'from': accounts[0]})
    with brownie.reverts():
        vestingStaking.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_no_approval(accounts, vestingStaking):
    balance = vestingStaking.balanceOf(accounts[0])

    with brownie.reverts():
        vestingStaking.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_revoked_approval(accounts, vestingStaking):
    balance = vestingStaking.balanceOf(accounts[0])

    vestingStaking.approve(accounts[1], balance, {'from': accounts[0]})
    vestingStaking.approve(accounts[1], 0, {'from': accounts[0]})

    with brownie.reverts():
        vestingStaking.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_transfer_to_self(accounts, vestingStaking):
    sender_balance = vestingStaking.balanceOf(accounts[0])
    amount = sender_balance // 4

    vestingStaking.approve(accounts[0], sender_balance, {'from': accounts[0]})
    vestingStaking.transferFrom(accounts[0], accounts[0], amount, {'from': accounts[0]})

    assert vestingStaking.balanceOf(accounts[0]) == sender_balance
    assert vestingStaking.allowance(accounts[0], accounts[0]) == sender_balance - amount


def test_transfer_to_self_no_approval(accounts, vestingStaking):
    amount = vestingStaking.balanceOf(accounts[0])

    with brownie.reverts():
        vestingStaking.transferFrom(accounts[0], accounts[0], amount, {'from': accounts[0]})


def test_transfer_event_fires(accounts, vestingStaking):
    amount = vestingStaking.balanceOf(accounts[0])

    vestingStaking.approve(accounts[1], amount, {'from': accounts[0]})
    tx = vestingStaking.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert len(tx.events) == 2
    assert tx.events["Transfer"].values() == [accounts[0], accounts[2], amount]