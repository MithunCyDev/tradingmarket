import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(import.meta.dirname, "..");
const python =
  process.platform === "win32"
    ? path.join(repoRoot, "apps", "api", ".venv", "Scripts", "python.exe")
    : path.join(repoRoot, "apps", "api", ".venv", "bin", "python");

if (!existsSync(python)) {
  console.error("Missing apps/api/.venv. Create it and install apps/api/requirements.txt.");
  process.exit(1);
}

const child = spawn(
  python,
  [
    "-m",
    "uvicorn",
    "app.main:app",
    "--app-dir",
    path.join(repoRoot, "apps", "api"),
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
  ],
  { cwd: path.join(repoRoot, "apps", "api"), stdio: "inherit" },
);

child.on("exit", (code) => {
  process.exit(code ?? 1);
});
