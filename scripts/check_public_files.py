"""Publication guardrail over tracked/staged files, not a comprehensive secret scanner."""

import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
files = (
    subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True)
    .stdout.decode()
    .split("\0")
)
failures = []
for name in filter(None, files):
    path = root / name
    if (
        name.startswith("private/")
        or path.suffix in {".joblib", ".sqlite", ".pt", ".safetensors"}
        or path.name == ".env"
    ):
        failures.append(f"Forbidden public file: {name}")
    if path.suffix in {".png", ".jpg", ".mp4"}:
        continue
    content = path.read_text(encoding="utf-8", errors="replace")
    # Construct patterns so this guard does not flag its own source.
    patterns = [
        r"gh[pousr]_" + r"[A-Za-z0-9]{30,}",
        r"-----BEGIN " + r"(?:RSA |OPENSSH )?PRIVATE KEY-----",
        r"sk-" + r"[A-Za-z0-9]{35,}",
    ]
    if any(re.search(p, content) for p in patterns):
        failures.append(f"Possible secret: {name}")
    if re.search(r"7656119\d{10}", content):
        failures.append(f"Possible raw SteamID: {name}")
if failures:
    raise SystemExit("\n".join(failures))
print(
    f"Publication guard passed for {len(list(filter(None, files)))} tracked files. Manual content review remains necessary."
)
