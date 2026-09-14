#!/usr/bin/env python3
"""Autonomous stage orchestrator for first boot and later resumes.

This is deliberately conservative: a stage only advances when its check command
returns success. Blockers leave the last known-good stage intact.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

STATE = Path('/var/lib/dab-touchscreen/commissioning-state.json')
LOG = Path('/var/log/dab-touchscreen/commissioning.log')
MAX_STAGE = 9
REPORT_INTERVAL = 30 * 60


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')


def ensure_dirs() -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {
        'mode': 'automatic', 'current_stage': 0, 'last_completed_stage': -1,
        'completed': [], 'failed': [], 'retry_count': 0,
        'status': 'starting', 'last_action': 'first boot', 'updated_at': now(),
    }


def save_state(state: dict) -> None:
    state['updated_at'] = now()
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2) + '\n')
    os.chmod(tmp, 0o600)
    tmp.replace(STATE)


def report(event: str, state: dict, detail: str = '') -> None:
    msg = (
        f"DAB Touchscreen | {event} | Phase {state['current_stage']}/{MAX_STAGE} | "
        f"Status: {state['status']} | {detail}"
    )
    logging.info(msg)
    # OpenClaw integration point: use the already configured primary channel.
    # The concrete CLI/API is installation-specific and shall be wired during SSD provisioning.
    helper = Path('/usr/local/bin/dab-openclaw-report')
    if helper.exists() and os.access(helper, os.X_OK):
        subprocess.run([str(helper), msg], check=False, timeout=30)

    # Optional local MQTT mirror; failures must never stop commissioning.
    if subprocess.run(['sh', '-c', 'command -v mosquitto_pub >/dev/null'], check=False).returncode == 0:
        subprocess.run([
            'mosquitto_pub', '-h', '127.0.0.1', '-t', 'dab-touchscreen/status/commissioning',
            '-m', msg, '-r'
        ], check=False, timeout=10)


def run_stage_check(stage: int) -> tuple[bool, str]:
    cmd = ['/usr/bin/python3', 'scripts/commissioning_check.py', '--stage', str(stage)]
    p = subprocess.run(cmd, cwd='/opt/dab-touchscreen', text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    return p.returncode == 0, p.stdout[-4000:]


def main() -> int:
    ensure_dirs()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.FileHandler(LOG), logging.StreamHandler()])
    state = load_state()
    state['status'] = 'running'
    save_state(state)
    report('Start/Fortsetzung', state, 'Autonome Inbetriebnahme gestartet.')
    last_periodic_report = time.monotonic()

    while state['current_stage'] <= MAX_STAGE:
        stage = state['current_stage']
        state['last_action'] = f'Phase {stage} prüfen/umsetzen'
        state['status'] = 'running'
        save_state(state)
        report('Phasenstart', state, state['last_action'])

        # OpenClaw implementation hook. The provisioning step should replace/wire this
        # wrapper so OpenClaw can implement the phase before the acceptance check runs.
        phase_helper = Path('/usr/local/bin/dab-openclaw-stage')
        if phase_helper.exists() and os.access(phase_helper, os.X_OK):
            p = subprocess.run([str(phase_helper), str(stage)], check=False, timeout=7200)
            if p.returncode != 0:
                state['retry_count'] += 1
                save_state(state)
                report('Umsetzungsfehler', state, f'OpenClaw-Phase gab Code {p.returncode} zurück.')

        ok, output = run_stage_check(stage)
        if ok:
            if stage not in state['completed']:
                state['completed'].append(stage)
            state['last_completed_stage'] = stage
            state['retry_count'] = 0
            state['status'] = 'completed_stage'
            save_state(state)
            report('Phase abgeschlossen', state, f'Phase {stage} erfolgreich geprüft.')
            state['current_stage'] = stage + 1
            save_state(state)
            continue

        state['retry_count'] += 1
        state['failed'].append({'stage': stage, 'at': now(), 'output': output[-1500:]})
        save_state(state)
        report('Prüfung fehlgeschlagen', state, output[-800:])

        if state['retry_count'] >= 5:
            state['status'] = 'blocked'
            state['last_action'] = 'Warte auf Lösung eines Blockers'
            save_state(state)
            report('BLOCKER', state, 'Nach 5 Versuchen gestoppt. Vorherige stabile Phase bleibt aktiv.')
            return 2

        delay = min(10 * (2 ** (state['retry_count'] - 1)), 300)
        report('Wiederholungsversuch', state, f'Neuer Versuch in {delay} s.')
        time.sleep(delay)

        if time.monotonic() - last_periodic_report >= REPORT_INTERVAL:
            report('Fortschritt', state, f'Aktuell: {state["last_action"]}; Benutzereingriff: nein')
            last_periodic_report = time.monotonic()

    state['status'] = 'finished'
    state['last_action'] = 'Produktionsbetrieb'
    save_state(state)
    report('Projekt abgeschlossen', state, 'Alle Inbetriebnahmephasen erfolgreich abgeschlossen.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
