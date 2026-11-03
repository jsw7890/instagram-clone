const { spawnSync } = require("child_process");
const path = require("path");

const backend = path.join(__dirname, "..", "backend");
const python =
  process.platform === "win32"
    ? path.join(backend, ".venv", "Scripts", "python.exe")
    : path.join(backend, ".venv", "bin", "python");

const result = spawnSync(python, ["migrate.py"], {
  cwd: backend,
  stdio: "inherit",
  env: process.env,
});

if (result.status !== 0) {
  process.exit(result.status ?? 1);
}
