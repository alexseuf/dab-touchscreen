#!/usr/bin/env python3
"""Basic staged commissioning diagnostics for dab-touchscreen."""

from __future__ import annotations

import argparse
import shutil
import socket
import subprocess
from pathlib import Path


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def service_active(name: str) -> bool:
    if not command_exists("systemctl"):
        return False
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def tcp_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def yesno(value: bool) -> str:
    return "OK" if value else "FEHLER"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=int, choices=range(0, 10), required=True)
    args = parser.parse_args()

    checks: list[tuple[str, bool]] = []
    checks.append(("Python >= 3", True))
    checks.append(("NetworkManager/nmcli vorhanden", command_exists("nmcli")))
    checks.append(("systemd vorhanden", command_exists("systemctl")))

    if args.stage >= 1:
        checks.append(("Display-Session vorhanden", bool(Path("/dev/fb0").exists() or Path("/dev/dri").exists())))

    if args.stage >= 2:
        checks.append(("Mosquitto installiert", command_exists("mosquitto")))
        checks.append(("Mosquitto aktiv", service_active("mosquitto")))
        checks.append(("MQTT Port 1883 erreichbar", tcp_open("127.0.0.1", 1883)))

    if args.stage >= 4:
        state_parent = Path("/var/lib/dab-touchscreen")
        checks.append(("Laufzeitdaten-Verzeichnis vorhanden", state_parent.exists()))

    if args.stage >= 8:
        checks.append(("DAB HMI systemd service aktiv", service_active("dab-touchscreen.service")))

    print(f"Inbetriebnahmeprüfung Stufe {args.stage}\n")
    failed = 0
    for description, ok in checks:
        print(f"[{yesno(ok):6}] {description}")
        if not ok:
            failed += 1

    print(f"\nErgebnis: {len(checks) - failed}/{len(checks)} Prüfungen erfolgreich")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
