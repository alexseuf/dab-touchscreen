# Raspberry Pi Imager distribution

This directory prepares DAB Touchscreen for distribution through Raspberry Pi Imager 2.x.

## Design

- One compressed `.img.xz` per release.
- Raspberry Pi Imager receives the image through an OS-list manifest.
- The image must contain the `rpi-preseed` package before it is published with `"init_format": "rpi-preseed"`.
- Wi-Fi credentials, hostname, user account, SSH, locale and hardware-interface choices are entered in Raspberry Pi Imager and written to `/boot/firmware/rpi-preseed.toml`.
- No Wi-Fi password or other user secret is stored in this repository or on GitHub Pages.

## Publishing

After producing the final uncompressed image and its `.xz` file:

```bash
./imager/generate-os-list.sh \
  path/to/dab-touchscreen.img \
  path/to/dab-touchscreen.img.xz \
  "https://github.com/alexseuf/dab-touchscreen/releases/download/vX.Y.Z/dab-touchscreen-vX.Y.Z.img.xz" \
  vX.Y.Z
```

The script calculates both hashes and byte sizes and writes `imager/os-list.json`.
Do not replace the generated values with hashes of a different image.

## Test

Use Raspberry Pi Imager 2.x:

```bash
rpi-imager --repo https://raw.githubusercontent.com/alexseuf/dab-touchscreen/main/imager/os-list.json
```

Only merge a generated production manifest after the referenced release asset exists.

## Image requirement

Do not advertise `rpi-preseed` for an image that does not actually ship the package. The image-building/provisioning step must install and enable the package first. Until the first distributable image exists, `os-list.json` is intentionally generated rather than committed with fake hashes.
