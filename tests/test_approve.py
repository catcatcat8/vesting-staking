#!/usr/bin/python3

import pytest


@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(vestingStaking, accounts, idx):
    assert vestingStaking.allowance(accounts[0], accounts[idx]) == 0


def test_approve(vestingStaking, accounts):
    vestingStaking.approve(accounts[1], 10**19, {'from': accounts[0]})

    assert vestingStaking.allowance(accounts[0], accounts[1]) == 10**19


def test_modify_approve(vestingStaking, accounts):
    vestingStaking.approve(accounts[1], 10**19, {'from': accounts[0]})
    vestingStaking.approve(accounts[1], 12345678, {'from': accounts[0]})

    assert vestingStaking.allowance(accounts[0], accounts[1]) == 12345678


def test_revoke_approve(vestingStaking, accounts):
    vestingStaking.approve(accounts[1], 10**19, {'from': accounts[0]})
    vestingStaking.approve(accounts[1], 0, {'from': accounts[0]})

    assert vestingStaking.allowance(accounts[0], accounts[1]) == 0


def test_approve_self(vestingStaking, accounts):
    vestingStaking.approve(accounts[0], 10**19, {'from': accounts[0]})

    assert vestingStaking.allowance(accounts[0], accounts[0]) == 10**19


def test_only_affects_target(vestingStaking, accounts):
    vestingStaking.approve(accounts[1], 10**19, {'from': accounts[0]})

    assert vestingStaking.allowance(accounts[1], accounts[0]) == 0


def test_returns_true(vestingStaking, accounts):
    tx = vestingStaking.approve(accounts[1], 10**19, {'from': accounts[0]})

    assert tx.return_value is True


def test_approval_event_fires(accounts, vestingStaking):
    tx = vestingStaking.approve(accounts[1], 10**19, {'from': accounts[0]})

    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [accounts[0], accounts[1], 10**19]