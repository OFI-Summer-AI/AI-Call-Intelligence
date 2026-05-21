"""Start the AI Call Intelligence server."""
import os
import socket
import sys
import uvicorn


def _kill_port(port: int) -> None:
    """Kill any process already bound to *port* so startup never fails with EADDRINUSE."""
    import subprocess, platform
    try:
        if platform.system() == "Windows":
            # netstat -ano lists PID in the last column
            out = subprocess.check_output(
                ["netstat", "-ano"], text=True, stderr=subprocess.DEVNULL
            )
            for line in out.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = int(parts[-1])
                    if pid and pid != os.getpid():
                        subprocess.call(["taskkill", "/F", "/PID", str(pid)],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"[run.py] Killed PID {pid} that was holding port {port}")
        else:
            out = subprocess.check_output(
                ["lsof", "-ti", f"tcp:{port}"], text=True, stderr=subprocess.DEVNULL
            )
            for pid_str in out.split():
                pid = int(pid_str.strip())
                if pid and pid != os.getpid():
                    subprocess.call(["kill", "-9", str(pid)],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"[run.py] Killed PID {pid} that was holding port {port}")
    except Exception as exc:
        print(f"[run.py] Could not auto-clear port {port}: {exc}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    _kill_port(port)          # free the port before uvicorn tries to bind
    uvicorn.run("app.realtime_server:app", host="0.0.0.0", port=port, reload=False)
