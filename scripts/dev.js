const { spawn } = require("child_process");
const net = require("net");
const { setup, backend, frontend, venvPython } = require("./setup");

const BACKEND_PORT = 8000;
const FRONTEND_PORT = 5173;
const FRONTEND_URL = `http://localhost:${FRONTEND_PORT}`;
const children = [];
let shuttingDown = false;

function isPortOpen(port) {
  return new Promise((resolve) => {
    const socket = net.connect({ host: "127.0.0.1", port });
    socket.setTimeout(400);
    socket.on("connect", () => {
      socket.destroy();
      resolve(true);
    });
    socket.on("timeout", () => {
      socket.destroy();
      resolve(false);
    });
    socket.on("error", () => resolve(false));
  });
}

async function waitForPort(port, label, timeoutMs = 90000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (await isPortOpen(port)) return;
    await new Promise((r) => setTimeout(r, 400));
  }
  throw new Error(`${label}(port ${port})가 시간 안에 시작되지 않았습니다.`);
}

function spawnLogged(command, args, cwd, useShell = process.platform === "win32") {
  const child = spawn(command, args, {
    cwd,
    stdio: "inherit",
    shell: useShell,
    env: process.env,
  });
  children.push(child);
  child.on("exit", (code) => {
    if (!shuttingDown && code && code !== 0) {
      console.error(`${command} exited with code ${code}`);
    }
  });
  return child;
}

function openBrowser(url) {
  if (process.platform === "win32") {
    spawn("cmd", ["/c", "start", "", url], { stdio: "ignore", detached: true });
    return;
  }
  const opener = process.platform === "darwin" ? "open" : "xdg-open";
  spawn(opener, [url], { stdio: "ignore", detached: true });
}

function shutdown() {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const child of children) {
    if (!child.pid) continue;
    if (process.platform === "win32") {
      spawn("taskkill", ["/pid", String(child.pid), "/t", "/f"], { stdio: "ignore" });
    } else {
      child.kill("SIGTERM");
    }
  }
}

process.on("SIGINT", () => {
  shutdown();
  process.exit(0);
});
process.on("SIGTERM", shutdown);

async function main() {
  setup();

  console.log("\n==> 서버 실행");
  if (await isPortOpen(BACKEND_PORT)) {
    console.log("백엔드가 이미 8000 포트에서 실행 중입니다.");
  } else {
    spawnLogged(
      venvPython(),
      ["-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", String(BACKEND_PORT)],
      backend,
      false,
    );
  }

  if (await isPortOpen(FRONTEND_PORT)) {
    console.log("프론트엔드가 이미 5173 포트에서 실행 중입니다.");
  } else {
    spawnLogged("npx", ["vite", "--host", "127.0.0.1", "--port", String(FRONTEND_PORT)], frontend, true);
  }

  console.log("\n==> 서버 준비 대기");
  await waitForPort(BACKEND_PORT, "백엔드");
  await waitForPort(FRONTEND_PORT, "프론트엔드");

  console.log("\n==> 브라우저 열기");
  openBrowser(FRONTEND_URL);
  console.log(`앱:     ${FRONTEND_URL}`);
  console.log("API:    http://localhost:8000/docs");
  console.log("계정:   demo / demo1234");
  console.log("종료:   Ctrl+C\n");
}

main().catch((err) => {
  console.error(err.message || err);
  shutdown();
  process.exit(1);
});
