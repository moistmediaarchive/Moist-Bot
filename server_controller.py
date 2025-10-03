import sys
import os
import subprocess
import signal
import re

# Pull paths from environment (set in .env and loaded by main.py)
SERVER_BASE_PATH = os.environ.get("SERVER_BASE")
PID_FILE = os.environ.get("PID_FILE")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def list_available_tracks():
    if not os.path.exists(SERVER_BASE_PATH):
        eprint(f"⚠️ Server base path not found: {SERVER_BASE_PATH}")
        return
    tracks = [name for name in os.listdir(SERVER_BASE_PATH)
              if os.path.isdir(os.path.join(SERVER_BASE_PATH))]
    if tracks:
        eprint("\n📂 Available tracks:")
        for t in tracks:
            eprint(f"  - {t}")
    else:
        eprint("⚠️ No track folders found.")

def stop_current_server():
    if not os.path.exists(PID_FILE):
        print("No running server found.")
        return
    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"✅ Stopped server with PID {pid}.")
    except ProcessLookupError:
        print("⚠️ No process found with that PID.")
    except Exception as e:
        eprint(f"Error stopping server: {e}")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

def start_server(track_name):
    track_path = os.path.join(SERVER_BASE_PATH, track_name)
    server_exe = os.path.join(track_path, "AssettoServer")
    if not os.path.exists(server_exe):
        eprint(f"❌ No AssettoServer found for track: {track_name}")
        list_available_tracks()
        sys.exit(1)

    stop_current_server()
    eprint(f"Starting server for {track_name}...")

    proc = subprocess.Popen(
        [server_exe],
        cwd=track_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True
    )

    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))

    join_url = None
    for line in proc.stdout:
        print(line.strip())
        match = re.search(r"https?://acstuff\.ru[^\s]+", line)
        if match:
            join_url = match.group(0)
            print(f"JOIN_URL: {join_url}")
            break

    if join_url:
        print(f"\n>>> JOIN LINK FOUND <<<\n{join_url}\n")
    else:
        eprint("⚠️ No join link detected yet.")

    eprint(f"Server started for {track_name} (PID {proc.pid})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        eprint("Usage: python3 server_controller.py <track_name|stop>")
        list_available_tracks()
        sys.exit(1)
    arg = sys.argv[1].strip().lower()
    if arg == "stop":
        stop_current_server()
        sys.exit(0)
    track = sys.argv[1].strip()
    start_server(track)
