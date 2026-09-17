#!/usr/bin/env bash
set -Eeuo pipefail

MODE=${1:-boot}
RTC=/dev/rtc0

case "$MODE" in
  boot)
    # The DS3231 driver should expose rtc0. If hardware is absent, leave the
    # system usable and let network time synchronization handle the clock.
    if [[ -e "$RTC" ]]; then
      hwclock --rtc="$RTC" --hctosys --utc || true
      logger -t dab-rtc "Systemzeit aus DS3231 RTC übernommen"
    else
      logger -t dab-rtc "Keine RTC gefunden; System läuft ohne Hardware-Uhr weiter"
    fi
    ;;
  shutdown)
    # Save the current system time only when a real RTC is present. By shutdown
    # NTP normally had the opportunity to correct the system clock.
    if [[ -e "$RTC" ]]; then
      hwclock --rtc="$RTC" --systohc --utc || true
      logger -t dab-rtc "Systemzeit in DS3231 RTC gespeichert"
    fi
    ;;
  *)
    echo "Usage: $0 {boot|shutdown}" >&2
    exit 2
    ;;
esac
