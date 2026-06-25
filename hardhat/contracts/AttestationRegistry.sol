// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract AttestationRegistry {

    struct Attestation {
        bytes32 contractHash;
        address auditor;
        uint256 timestamp;
        string riskLevel;
        bytes32 reportHash;
    }

    // contractHash => Attestation
    mapping(bytes32 => Attestation) public attestations;

    // Keep track of all attested hashes so we can enumerate them
    bytes32[] public attestedHashes;

    event AttestationCreated(
        bytes32 indexed contractHash,
        address indexed auditor,
        uint256 timestamp,
        string riskLevel,
        bytes32 reportHash
    );

    function attest(
        bytes32 contractHash,
        string calldata riskLevel,
        bytes32 reportHash
    ) external {
        require(
            attestations[contractHash].timestamp == 0,
            "Contract already attested"
        );

        attestations[contractHash] = Attestation({
            contractHash: contractHash,
            auditor: msg.sender,
            timestamp: block.timestamp,
            riskLevel: riskLevel,
            reportHash: reportHash
        });

        attestedHashes.push(contractHash);

        emit AttestationCreated(
            contractHash,
            msg.sender,
            block.timestamp,
            riskLevel,
            reportHash
        );
    }

    function getAttestation(bytes32 contractHash)
        external
        view
        returns (Attestation memory)
    {
        return attestations[contractHash];
    }

    function getTotalAttestations() external view returns (uint256) {
        return attestedHashes.length;
    }
}