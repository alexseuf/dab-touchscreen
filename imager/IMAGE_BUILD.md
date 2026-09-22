# Build a distributable DAB Touchscreen Raspberry Pi image

This is the production path for creating the image referenced by Raspberry Pi Imager.

## Base image

Use Raspberry Pi OS 64-bit compatible with Raspberry Pi 4. The image builder must install the DAB Touchscreen application from this repository and must install `rpi-preseed` before the image is published with `init_format: rpi-preseed`.

## Required image preparation

Run these operations in the image/chroot during the build:

```bash
apt-get update
apt-get install -y rpi-preseed
```

Then install DAB Touchscreen using the existing project installation path. Keep credentials out of the image.

Before shutdown/image capture:

```bash
rm -f /boot/firmware/rpi-preseed.toml
rm -f /etc/NetworkManager/system-connections/*.nmconnection || true
rm -f /etc/ssh/ssh_host_* || true
rm -rf /var/lib/systemd/random-seed
journalctl --rotate || true
journalctl --vacuum-time=1s || true
apt-get clean
```

Do not copy a developer's home-network Wi-Fi profile, MQTT password, SSH private key, shell history or other local secret into the release image.

## Validation before release

The image is releasable only if all of the following pass:

1. Raspberry Pi 4 boots from a freshly flashed SD card or USB SSD.
2. Raspberry Pi Imager 2.x accepts the custom repository manifest.
3. Imager offers OS customisation for the DAB Touchscreen image.
4. A test SSID/password entered in Imager is applied on first boot.
5. Hostname is applied.
6. German locale, keyboard and Europe/Berlin timezone are correct when selected.
7. SSH follows the option selected in Imager.
8. DAB Touchscreen starts automatically in kiosk mode.
9. Display and touch orientation are correct.
10. The local MQTT broker/application services are healthy.
11. No test Wi-Fi credentials or other secrets remain in the resulting image.

## Release sequence

```bash
xz -T0 -9 -k dab-touchscreen-vX.Y.Z.img
./imager/generate-os-list.sh \
  dab-touchscreen-vX.Y.Z.img \
  dab-touchscreen-vX.Y.Z.img.xz \
  "https://github.com/alexseuf/dab-touchscreen/releases/download/vX.Y.Z/dab-touchscreen-vX.Y.Z.img.xz" \
  vX.Y.Z
```

Upload the `.img.xz` to the matching GitHub Release, commit the generated `imager/os-list.json`, and only then publish/update the installer page.
