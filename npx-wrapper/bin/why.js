#!/usr/bin/env node

const { execSync, spawn } = require("child_process");
const { existsSync } = require("fs");

// Check if why-cli is installed via pip
try {
  execSync("why --help", { stdio: "ignore" });
} catch {
  console.log("Installing why-cli...");
  try {
    execSync("pip install why-cli", { stdio: "inherit" });
  } catch {
    execSync("pip3 install why-cli", { stdio: "inherit" });
  }
}

// Forward all args to the Python CLI
const args = process.argv.slice(2);
const child = spawn("why", args, { stdio: "inherit" });
child.on("exit", (code) => process.exit(code));
