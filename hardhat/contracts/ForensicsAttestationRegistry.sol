// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract ForensicsAttestationRegistry {

    struct ForensicsAttestation {
        bytes32 txHash;
        uint256 chainId;
        address attestor;
        uint256 timestamp;
        bytes32 reportHash;
        uint16  categoryBitmask;     // bit i set = taxonomy category i (see off-chain enum) was a candidate
        bool    hasConflationFlags;  // true if protocol_conflation_flags was non-empty at attestation time
    }

    // txHash => ForensicsAttestation
    mapping(bytes32 => ForensicsAttestation) public forensicsAttestations;

    // Keep track of all attested tx hashes so we can enumerate them
    bytes32[] public attestedTxHashes;

    event ForensicsAttestationCreated(
        bytes32 indexed txHash,
        uint256 indexed chainId,
        address indexed attestor,
        uint256 timestamp,
        bytes32 reportHash,
        uint16 categoryBitmask,
        bool hasConflationFlags
    );

    function attestForensics(
        bytes32 txHash,
        uint256 chainId,
        bytes32 reportHash,
        uint16 categoryBitmask,
        bool hasConflationFlags
    ) external {
        require(
            forensicsAttestations[txHash].timestamp == 0,
            "Transaction already attested"
        );

        forensicsAttestations[txHash] = ForensicsAttestation({
            txHash: txHash,
            chainId: chainId,
            attestor: msg.sender,
            timestamp: block.timestamp,
            reportHash: reportHash,
            categoryBitmask: categoryBitmask,
            hasConflationFlags: hasConflationFlags
        });

        attestedTxHashes.push(txHash);

        emit ForensicsAttestationCreated(
            txHash,
            chainId,
            msg.sender,
            block.timestamp,
            reportHash,
            categoryBitmask,
            hasConflationFlags
        );
    }

    function getForensicsAttestation(bytes32 txHash)
        external
        view
        returns (ForensicsAttestation memory)
    {
        return forensicsAttestations[txHash];
    }

    function getTotalForensicsAttestations() external view returns (uint256) {
        return attestedTxHashes.length;
    }
}