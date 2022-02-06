#!/usr/bin/python3
import brownie

""" VestingStaking.sol tests """

def test_add_to_whitelist(accounts, vestingStaking):
    vestingStaking.addToWhitelist((accounts[1], accounts[2]))

    assert vestingStaking.isWhitelisted(accounts[1]) == True
    assert vestingStaking.isWhitelisted(accounts[2]) == True
    assert vestingStaking.isWhitelisted(accounts[3]) == False


def test_delete_from_whitelist(accounts, vestingStaking):
    vestingStaking.addToWhitelist((accounts[1], accounts[2]))
    vestingStaking.deleteFromWhitelist(accounts[1])

    assert vestingStaking.isWhitelisted(accounts[1]) == False


def test_delete_not_whitelisted_from_whitelist(accounts, vestingStaking):
    vestingStaking.addToWhitelist((accounts[1], accounts[2]))

    with brownie.reverts():
        vestingStaking.deleteFromWhitelist(accounts[3])
