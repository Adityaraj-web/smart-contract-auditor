// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * VulnerableVault — intentionally insecure contract for Slither testing.
 * Three deliberately introduced vulnerabilities:
 *   1. Reentrancy in withdraw()
 *   2. Unchecked return value in emergencyWithdraw()
 *   3. Integer underflow in unchecked block in calculateFee()
 */
contract VulnerableVault {
    mapping(address => uint256) public balances;
    address public owner;
    uint256 public totalDeposited;

    constructor() {
        owner = msg.sender;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
        totalDeposited += msg.value;
    }

    // VULNERABILITY 1: Reentrancy
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        // External call BEFORE state update — reentrancy window open here
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        // State update happens too late
        balances[msg.sender] -= amount;
        totalDeposited -= amount;
    }

    // VULNERABILITY 2: Unchecked return value
    function emergencyWithdraw(address payable recipient) external {
        require(msg.sender == owner, "Not owner");
        // send() returns a bool indicating success or failure — ignored here
        recipient.send(address(this).balance);
    }

    // VULNERABILITY 3: Integer underflow in unchecked block
    function calculateFee(uint256 amount, uint256 fee) external pure returns (uint256) {
        unchecked {
            // If fee > amount, this silently wraps to a huge number
            return amount - fee;
        }
    }
}