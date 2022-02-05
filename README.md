# Vesting-Stacking

## Description

Rewards are distributed depending on users share in TVL. Users getting reward depending on time they hold their share, that means that reward accumulates with predefined speed (for example 100 tokens per day). Users can get their reward at any time (it will not be restaked to increase user share). The difference from usual staking is that user can linearly claim their tokens depending on vesting strategy. If user withdraws, his share recalculates and therefore he will be getting less reward.  

## On contract initialization:

- Defining owner of the contract and token which will be used for staking/vesting

## Before vesting started (before calling function start()):

- Defining the whitelist of users which can interact with SC.
- Defining initial allocations which will be immediately stacked and start to vest after calling start()
- Defining initial reward for stacking
- Defining different vesting strategies

## After vesting started (after calling function start()):

- Users from whitelist can now interact with SC and start to stake.
- Any user that participate in stacking/vesting can start to claim or get rewards.

## Admin functionality:

- Edit whitelisted wallet addresses
    - Edit amounts per wallet before start()
- Creating different vesting strategies
- Add additional reward amount

## Necessary view functions:

- Calculate dynamic APY (annual percent yield), should be the same for all users
- Report TVL (total value locked)
- Report all info per user
- How much to claim is left per vesting
- Full amount of tokens

## Build

### Installing ganache-cli (skip this step if already installed)

Make sure you have Node.js (>= v8) installed.

Using npm:

```Bash
npm install -g ganache-cli
```

### Installing brownie (skip this step if already installed)

Make sure you have python3 (>= 3.6) installed.

Using pipx:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install eth-brownie
```

## Compilation

To compile the smart contract:

```bash
brownie compile
```

## Deploy

To deploy the smart contract to the local Ganache test network

```bash
brownie run deploy.py
```

## Tests

To run the smart contract tests:

```bash
brownie test
```
