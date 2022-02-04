#!/usr/bin/python3

from brownie import VestingStaking, accounts


def main():
    return VestingStaking.deploy({'from': accounts[0]})