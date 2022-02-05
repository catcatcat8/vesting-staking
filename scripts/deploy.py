#!/usr/bin/python3

from brownie import VestingStaking, Token, accounts


def main():
    token = Token.deploy({'from': accounts[0]})
    return VestingStaking.deploy(token, {'from': accounts[0]})