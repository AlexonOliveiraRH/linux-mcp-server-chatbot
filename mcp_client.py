import subprocess
import json

class LinuxMCPClient:
    def __init__(self, host: str | None = None):
        self.host = host

    def run(self, tool: str, args: dict | None = None) -> str:
        payload = {
            "tool": tool,
            "args": args or {}
        }

        cmd = ["linux-mcp-server"]
        if self.host:
            cmd += ["--host", self.host]

        proc = subprocess.run(
            cmd,
            input=json.dumps(payload),
            text=True,
            capture_output=True
        )

        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)

        return proc.stdout

