#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "Usage: $0 <uncompressed.img> <compressed.img.xz> <download-url> <version>" >&2
  exit 2
fi

IMG="$1"
XZ="$2"
URL="$3"
VERSION="$4"
OUT="$(dirname "$0")/os-list.json"

for f in "$IMG" "$XZ"; do
  test -f "$f" || { echo "Missing file: $f" >&2; exit 1; }
done

extract_size=$(stat -c '%s' "$IMG")
download_size=$(stat -c '%s' "$XZ")
extract_sha=$(sha256sum "$IMG" | awk '{print $1}')
download_sha=$(sha256sum "$XZ" | awk '{print $1}')
release_date=$(date -u +%F)

python3 - "$OUT" "$URL" "$VERSION" "$release_date" "$extract_size" "$extract_sha" "$download_size" "$download_sha" <<'PY'
import json, sys
out,url,version,date,esize,esha,dsize,dsha=sys.argv[1:]
data={"os_list":[{
  "name":"DAB Touchscreen",
  "description":"Raspberry-Pi-4 Touch-HMI für 3-Phasen-PFC und DAB",
  "url":url,
  "icon":"https://raw.githubusercontent.com/alexseuf/dab-touchscreen/main/docs/images/01_overview.svg",
  "website":"https://github.com/alexseuf/dab-touchscreen",
  "release_date":date,
  "extract_size":int(esize),
  "extract_sha256":esha,
  "image_download_size":int(dsize),
  "image_download_sha256":dsha,
  "devices":["pi4"],
  "init_format":"rpi-preseed",
  "architecture":"armv8",
  "capabilities":["i2c","spi","serial","passwordless_sudo"]
}]}
with open(out,"w",encoding="utf-8") as f:
    json.dump(data,f,indent=2,ensure_ascii=False)
    f.write("\n")
print(out)
PY

echo "Generated $OUT for $VERSION"
echo "Uncompressed SHA256: $extract_sha"
echo "Compressed SHA256:   $download_sha"
