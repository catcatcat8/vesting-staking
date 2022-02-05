// SPDX-License-Identifier: MIT

pragma solidity >0.6.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract Token is ERC20 {
    constructor() public ERC20("Token", "VST") {
        _mint(msg.sender, 1_000_000_000_000_000);
    }
}