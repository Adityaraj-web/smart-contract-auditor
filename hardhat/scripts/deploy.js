const hre = require("hardhat");

async function main() {
  console.log("Deploying AttestationRegistry to Sepolia...");

  const AttestationRegistry = await hre.ethers.getContractFactory(
    "AttestationRegistry"
  );
  const registry = await AttestationRegistry.deploy();

  await registry.waitForDeployment();

  const address = await registry.getAddress();

  console.log("AttestationRegistry deployed to:", address);
  console.log(
    "Add this to your .env file: CONTRACT_ADDRESS=" + address
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});