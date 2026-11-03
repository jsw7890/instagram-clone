const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const backend = path.join(root, "backend");
const frontend = path.join(root, "frontend");

function log(message) {
  console.log(`\n==> ${message}`);
}

function fail(message) {
  console.error(message);
  process.exit(1);
}

function run(command, args, cwd, useShell = false) {
  const result = spawnSync(command, args, {
    cwd,
    stdio: "inherit",
    shell: useShell,
    env: process.env,
  });
  if (result.error) {
    fail(`${command} 실행 실패: ${result.error.message}`);
  }
  if (result.status !== 0) {
    fail(`${command} ${args.join(" ")} 가 종료 코드 ${result.status} 로 실패했습니다.`);
  }
}

function commandExists(command, args = ["--version"]) {
  const result = spawnSync(command, args, {
    stdio: "ignore",
    shell: process.platform === "win32" && command === "npm",
  });
  return !result.error && result.status === 0;
}

function findPython() {
  if (commandExists("py", ["-3", "--version"])) {
    return { command: "py", prefix: ["-3"] };
  }
  if (commandExists("python", ["--version"])) {
    return { command: "python", prefix: [] };
  }
  if (commandExists("python3", ["--version"])) {
    return { command: "python3", prefix: [] };
  }
  fail(
    "Python 3이 없습니다. https://www.python.org/downloads/ 에서 설치하고 PATH에 추가한 뒤 다시 실행하세요.",
  );
}

function venvPython() {
  return process.platform === "win32"
    ? path.join(backend, ".venv", "Scripts", "python.exe")
    : path.join(backend, ".venv", "bin", "python");
}

function ensureEnvFile(dir) {
  const dest = path.join(dir, ".env");
  const src = path.join(dir, ".env.example");
  if (!fs.existsSync(dest) && fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
    console.log(`created ${path.relative(root, dest)}`);
  }
}

function setup() {
  if (!commandExists("npm", ["-v"])) {
    fail("Node.js(npm)가 없습니다. https://nodejs.org/ 에서 LTS를 설치하세요.");
  }

  log("환경 파일 준비");
  ensureEnvFile(backend);
  ensureEnvFile(frontend);

  const python = findPython();
  const venv = venvPython();

  log("백엔드 패키지 설치");
  if (!fs.existsSync(venv)) {
    console.log("가상환경 생성 중...");
    run(python.command, [...python.prefix, "-m", "venv", ".venv"], backend);
  }
  const backendOk = spawnSync(venv, ["-c", "import fastapi, uvicorn, sqlalchemy"], { stdio: "ignore" });
  if (backendOk.status !== 0) {
    run(venv, ["-m", "pip", "install", "-r", "requirements.txt"], backend);
  } else {
    console.log("백엔드 패키지가 이미 설치되어 있습니다.");
  }

  log("SQLite 스키마 마이그레이션");
  run(venv, ["migrate.py"], backend);

  log("프론트엔드 패키지 설치");
  const vitePkg = path.join(frontend, "node_modules", "vite", "package.json");
  if (!fs.existsSync(vitePkg)) {
    run("npm", ["install"], frontend, true);
  } else {
    console.log("프론트엔드 패키지가 이미 설치되어 있습니다.");
  }
}

module.exports = { setup, root, backend, frontend, venvPython };

if (require.main === module) {
  setup();
  console.log("\n패키지 설치 완료");
}
