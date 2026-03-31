#!/bin/sh
set -eu

: "${REACTOR_WAIT_IMAGES:=}"
: "${REACTOR_WAIT_TIMEOUT:=120}"   # seconds
: "${REACTOR_WAIT_INTERVAL:=3}"    # seconds

if [ -z "$REACTOR_WAIT_IMAGES" ]; then
  echo "No images to wait for"
  exit 0
fi

start=$(date +%s)
for img in $(echo "$REACTOR_WAIT_IMAGES" | tr ',' ' '); do
  echo "Waiting for image $img"
  while true; do
    if docker pull "$img" >/dev/null 2>&1; then
      echo "Image $img available"
      break
    fi
    now=$(date +%s)
    elapsed=$((now - start))
    if [ "$elapsed" -ge "$REACTOR_WAIT_TIMEOUT" ]; then
      echo "Timeout waiting for $img after ${REACTOR_WAIT_TIMEOUT}s" >&2
      exit 1
    fi
    sleep "$REACTOR_WAIT_INTERVAL"
  done
done

echo "All images available"
exit 0
