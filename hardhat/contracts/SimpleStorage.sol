// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract SimpleStorage {
    uint256 private value;
    address public owner;

    event ValueChanged(address indexed changedBy, uint256 newValue);

    constructor() {
        owner = msg.sender;
    }

    function setValue(uint256 _value) external {
        value = _value;
        emit ValueChanged(msg.sender, _value);
    }

    function getValue() external view returns (uint256) {
        return value;
    }
}