# rpi-preseed policy for DAB Touchscreen

Raspberry Pi Imager 2.x supports `init_format: rpi-preseed`. Imager writes
`/boot/firmware/rpi-preseed.toml`; the image's `rpi-preseed` service applies it once on first boot.

For DAB Touchscreen the intended defaults are:

- target: Raspberry Pi 4, 64-bit
- locale: German (`de_DE.UTF-8`)
- keyboard: German
- timezone: `Europe/Berlin`
- suggested hostname: `dab-touchscreen`
- SSH: enabled when selected by the installer
- Wi-Fi country: DE
- Wi-Fi SSID/password: **never predefined in GitHub**; entered by the operator in Raspberry Pi Imager
- I2C: enabled for DS3231 RTC
- SPI/serial: available to the installer/image as required by the project

The operator-specific Wi-Fi password and account password must remain local to Raspberry Pi Imager and the target media. They must never be placed in `os-list.json`, GitHub Actions logs, release metadata or GitHub Pages.

## Image acceptance check

Before publishing an image as `rpi-preseed` compatible, boot or mount it and verify that the package and its systemd units are present. Then perform one destructive test flash with Imager 2.x and confirm hostname, Wi-Fi, locale and SSH on first boot.

If this check fails, do not publish the manifest with `init_format: rpi-preseed`.
