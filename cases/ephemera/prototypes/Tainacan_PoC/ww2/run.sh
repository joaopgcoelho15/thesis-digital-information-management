#!/bin/sh
# Uses the frozen public source snapshot. Never changes the production WordPress.
set -eu
TASK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CONTAINER=ephemera-tainacan-poc-wordpress-1
python3 "$TASK_DIR/prepare.py"
docker exec "$CONTAINER" mkdir -p /tmp/ephemera-ww2/media /tmp/ephemera-ww2/reports
for name in import.php verify.php manifest.json; do
  docker cp "$TASK_DIR/$name" "$CONTAINER:/tmp/ephemera-ww2/$name"
done
docker cp "$TASK_DIR/media/." "$CONTAINER:/tmp/ephemera-ww2/media/"
docker cp "$TASK_DIR/reports/before.json" "$CONTAINER:/tmp/ephemera-ww2/reports/before.json"
docker exec "$CONTAINER" php /tmp/ephemera-ww2/import.php
docker exec "$CONTAINER" php /tmp/ephemera-ww2/verify.php
