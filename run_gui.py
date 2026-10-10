"""
Launches the Lektor Web GUI server (port 7860) and provides Nginx links for LAN access.
Automatically opens the browser and serves the player interface.
"""
import socket
import subprocess
import sys
import webbrowser
from pathlib import Path

import uvicorn

from lektor.infrastructure.config import settings

# Ensure UTF-8 support on Windows
if sys.platform == "win32":
    try:
        reconfig = getattr(sys.stdout, "reconfigure", None)
        if callable(reconfig):
            reconfig(encoding="utf-8", errors="replace")
        reconfig_err = getattr(sys.stderr, "reconfigure", None)
        if callable(reconfig_err):
            reconfig_err(encoding="utf-8", errors="replace")
    except Exception:
        pass


def get_network_ips() -> tuple[str, str]:
    """Detects local IP addresses (LAN and Tailscale)."""
    detected_lan: str = "127.0.0.1"
    detected_tailscale: str = ""
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip.startswith("100."):
                detected_tailscale = ip
            elif not ip.startswith("127.") and not ip.startswith("169.254."):
                detected_lan = ip
    except Exception:
        pass
    return detected_lan, detected_tailscale

def ensure_nginx_running() -> bool:
    """Checks if Nginx is running; if not, attempts to start it."""
    nginx_dir = Path(__file__).resolve().parent / "nginx"
    nginx_exe = nginx_dir / "nginx.exe"
    if not nginx_exe.exists():
        return False
    try:
        check = subprocess.run(["tasklist", "/fi", "imagename eq nginx.exe"], capture_output=True, text=True)
        if "nginx.exe" not in check.stdout:
            # Start in background
            subprocess.Popen([str(nginx_exe)], cwd=str(nginx_dir), creationflags=0x00000008 | 0x00000200, close_fds=True)
            return True
        return True
    except Exception:
        return False

def main() -> None:
    host = settings.gui_host
    port = settings.gui_port
    local_url = f"http://{host}:{port}"
    # Ensure Nginx is running for external access
    nginx_active = ensure_nginx_running()
    
    lan_ip, tailscale_ip = get_network_ips()

    try:
        print("\n" + "=" * 75)
        print("  đźŽ§ LEKTOR PRO — WEB GUI PLAYER & CONTROLLER")
        print(f"  đźŹ  Local access (Direct):     {local_url}")
        if nginx_active:
            print(f"  đźš€ Nginx Server (LAN):  http://{lan_ip}  (or http://{lan_ip}:8080)")
            if tailscale_ip:
                print(f"  đź”’ Nginx Server (Tailscale):    http://{tailscale_ip}")
        print("  âŚ¨ď¸Ź  SkrĂłty: Spacja = Play/Pause, StrzaĹ‚ki = Przewijanie 5s, Ctrl+StrzaĹ‚ki = Strony")
        print("=" * 75 + "\n")
    except Exception:
        pass

    if settings.auto_open_browser:
        try:
            webbrowser.open(local_url)
        except Exception:
            pass

    gui_watch_dir = Path(__file__).resolve().parent / "lektor" / "adapters" / "gui"
    # Limit reload_dirs to the GUI directory so generated files do not restart the server.
    uvicorn.run(
        "lektor.infrastructure.gui_app:app",
        host=host,
        port=port,
        log_level="info",
        reload=True,
        reload_dirs=[str(gui_watch_dir)],
    )

if __name__ == "__main__":
    main()

