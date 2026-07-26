const hre = require("hardhat");

async function main() {
  console.log("Deploying ForensicsAttestationRegistry to Sepolia...");

  const ForensicsAttestationRegistry = await hre.ethers.getContractFactory(
    "ForensicsAttestationRegistry"
  );
  const registry = await ForensicsAttestationRegistry.deploy();

  await registry.waitForDeployment();

  const address = await registry.getAddress();

  console.log("ForensicsAttestationRegistry deployed to:", address);
  console.log(
    "Add this to your .env file: FORENSICS_CONTRACT_ADDRESS=" + address
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});