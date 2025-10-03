import sys
import os
import subprocess
import signal
import re
from dotenv import load_dotenv

load_dotenv()

def eprint(*args, **kwargs):
    """Helper to print to stderr (so Discord can capture errors)."""
    print(*args, file=sys.stderr, **kwargs)


SERVER_BASE_PATH = os.getenv("SERVER_BASE")
if not SERVER_BASE_PATH:
    eprint("❌ SERVER_BASE is not set in .env")
    sys.exit(1)

PID_FILE = os.getenv("PID_FILE", os.path.join(SERVER_BASE_PATH, "current_server.pid"))

def list_available_tracks():
    """List all folders under SERVER_BASE_PATH that look like tracks."""
    if not os.path.exists(SERVER_BASE_PATH):
        eprint(f"⚠️ Server base path not found: {SERVER_BASE_PATH}")
        return

    tracks = [
        name for name in os.listdir(SERVER_BASE_PATH)
        if os.path.isdir(os.path.join(SERVER_BASE_PATH, name))
    ]

    if tracks:
        eprint("\n📂 Available tracks:")
        for t in tracks:
            eprint(f"  - {t}")
    else:
        eprint("⚠️ No track folders found in the server directory.")

def stop_current_server():
    """Stop the currently running server using the PID file."""
    if not os.path.exists(PID_FILE):
        print("No running server found.")
        return

    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())

    try:
        os.kill(pid, signal.SIGTERM)
        print(f"✅ Stopped server with PID {pid}.")
    except ProcessLookupError:
        print("⚠️ No process found with that PID (it might have already stopped).")
    except Exception as e:
        eprint(f"Error stopping server: {e}")

    # Remove the PID file if it exists
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

def start_server(track_name):
    """Start the server for the specified track."""
    track_path = os.path.join(SERVER_BASE_PATH, track_name)
    server_exe = os.path.join(track_path, "AssettoServer")

    if not os.path.exists(server_exe):
        eprint(f"❌ No AssettoServer found for track: {track_name}")
        list_available_tracks()
        sys.exit(1)

    # Stop any running server first
    stop_current_server()

    eprint(f"Starting server for {track_name}...")

    try:
        proc = subprocess.Popen(
            [server_exe],
            cwd=track_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    except Exception as e:
        eprint(f"❌ Failed to start server for {track_name}: {e}")
        sys.exit(1)

    # Store the PID
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))

    # Look for https://acstuff.ru/ join link
    join_url = None

    for raw_line in proc.stdout:
        line = raw_line.decode(errors="ignore").strip()
        print(line)  # Keep normal output visible in logs

        match = re.search(r"(https://acstuff\.ru/s/q:race/online/join\?[^ \n\r]+)", line)
        if match:
            join_url = match.group(1)
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
        eprint("\nHere are the available tracks:")
        list_available_tracks()
        sys.exit(1)

    arg = sys.argv[1].strip().lower()

    if arg == "stop":
        stop_current_server()
        sys.exit(0)

    # Otherwise, start a track
    track = sys.argv[1].strip()
    start_server(track)
