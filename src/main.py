"""DAB touchscreen application entry point with staged commissioning support."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "commissioning.yaml"


def load_commissioning_config(path: Path = CONFIG_PATH) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def apply_stage_defaults(config: dict, stage: int) -> dict:
    """Return a copy of config with only functions permitted for the stage enabled."""
    cfg = dict(config)
    features = dict(cfg.get("features", {}))

    stage_features = {
        0: set(),
        1: {"gui", "demo_data", "ethernet_read", "wifi_scan"},
        2: {"gui", "mqtt_broker", "mqtt_client", "demo_data", "ethernet_read", "wifi_scan"},
        3: {"gui", "mqtt_broker", "mqtt_client", "real_mqtt_mapping", "ethernet_read", "wifi_scan"},
        4: {"gui", "mqtt_broker", "mqtt_client", "real_mqtt_mapping", "history", "ethernet_read", "wifi_scan"},
        5: {"gui", "mqtt_broker", "mqtt_client", "real_mqtt_mapping", "history", "ethernet_read", "ethernet_write", "wifi_scan"},
        6: {"gui", "mqtt_broker", "mqtt_client", "real_mqtt_mapping", "history", "ethernet_read", "ethernet_write", "wifi_scan", "wifi_write"},
        7: {"gui", "mqtt_broker", "mqtt_client", "real_mqtt_mapping", "history", "ethernet_read", "ethernet_write", "wifi_scan", "wifi_write", "mqtt_explorer"},
        8: {"gui", "mqtt_broker", "mqtt_client", "real_mqtt_mapping", "history", "ethernet_read", "ethernet_write", "wifi_scan", "wifi_write", "mqtt_explorer", "autostart"},
        9: set(features.keys()),
    }

    allowed = stage_features.get(stage, stage_features[0])
    for name in features:
        features[name] = name in allowed

    cfg["features"] = features
    cfg["stage"] = stage
    cfg.setdefault("safety", {})["allow_network_changes"] = stage >= 5
    cfg["safety"]["allow_credential_changes"] = stage >= 6
    return cfg


def print_startup_summary(config: dict) -> None:
    print(f"DAB Touchscreen commissioning stage: {config.get('stage')}")
    print("Enabled features:")
    for name, enabled in config.get("features", {}).items():
        print(f"  {'[x]' if enabled else '[ ]'} {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="DAB touchscreen HMI")
    parser.add_argument("--stage", type=int, choices=range(0, 10), help="commissioning stage 0..9")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    config = load_commissioning_config(args.config)
    stage = args.stage if args.stage is not None else int(config.get("stage", 1))
    config = apply_stage_defaults(config, stage)
    print_startup_summary(config)

    if args.check_only:
        return 0

    # OpenClaw implementation hook:
    # Instantiate only the services whose feature flags are enabled.
    # The GUI must also hide/disable controls belonging to later stages.
    # This entry point intentionally remains runnable before the full GUI exists.
    print("Application scaffold ready. Implement stage-specific services incrementally.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
