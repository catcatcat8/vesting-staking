#!/usr/bin/python3

import pytest

@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # выполнять откат цепи после завершения каждого теста, чтобы обеспечить надлежащую изоляцию
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def vestingStaking(VestingStaking, Token, accounts):
    token = Token.deploy({'from': accounts[0]})
    return VestingStaking.deploy(token, {'from': accounts[0]})


@pytest.fixture(scope="module")
def token(Token, accounts):
    return Token.deploy({'from': accounts[0]})


@pytest.fixture(scope="module")
def vestingStakingAndToken(VestingStaking, Token, accounts):
    token = Token.deploy({'from': accounts[0]})
    return [VestingStaking.deploy(token, {'from': accounts[0]}), token]  # for using both contracts in tests