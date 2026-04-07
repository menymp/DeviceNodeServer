#!/bin/sh
set -eu

: "${REACTOR_WAIT_IMAGES:=}"
: "${REACTOR_WAIT_TIMEOUT:=120}"
: "${REACTOR_WAIT_INTERVAL:=3}"

if [ -z "$REACTOR_WAIT_IMAGES" ]; then
  echo "No images to wait for"
  exit 0
fi

deadline=$(( $(date +%s) + REACTOR_WAIT_TIMEOUT ))

# Normalize an image string into host(optional), repo, tag
# Accepts forms:
#   repo:tag
#   host:port/repo:tag
normalize() {
  img="$1"
  # default host empty
  host=""
  repo_tag="$img"

  # if contains '/', and left part contains ':' (host:port) or a dot, treat left as host
  if echo "$img" | grep -q '/'; then
    left="${img%%/*}"
    if echo "$left" | grep -Eq '[:.]'; then
      host="$left"
      repo_tag="${img#*/}"
    fi
  fi

  repo="${repo_tag%:*}"
  tag="${repo_tag#*:}"
  printf "%s|%s|%s" "$host" "$repo" "$tag"
}

check_manifest() {
  host_override="$1"   # if non-empty, try this host first
  repo="$2"
  tag="$3"

  # hosts to try: explicit override, container DNS, localhost, host.docker.internal
  hosts=""
  if [ -n "$host_override" ]; then
    hosts="$host_override registry localhost host.docker.internal"
  else
    hosts="registry localhost host.docker.internal"
  fi

  for h in $hosts; do
    # if host already contains port, do not append :5000
    if echo "$h" | grep -q ':'; then
      url="http://$h/v2/$repo/manifests/$tag"
    else
      url="http://$h:5000/v2/$repo/manifests/$tag"
    fi
    if curl -s -f -H "Accept: application/vnd.oci.image.manifest.v1+json,application/vnd.docker.distribution.manifest.v2+json" "$url" >/dev/null 2>&1; then
      echo "manifest found at $url"
      return 0
    fi
  done
  return 1
}

for raw in $(echo "$REACTOR_WAIT_IMAGES" | tr ',' ' '); do
  echo "Processing wait target: $raw"
  normalized=$(normalize "$raw")
  hostpart=$(printf "%s" "$normalized" | cut -d'|' -f1)
  repo=$(printf "%s" "$normalized" | cut -d'|' -f2)
  tag=$(printf "%s" "$normalized" | cut -d'|' -f3)

  echo "Waiting for image $repo:$tag (host hint: ${hostpart:-<none>})"

  while true; do
    if check_manifest "$hostpart" "$repo" "$tag"; then
      echo "Image $repo:$tag available (manifest)"
      break
    fi

    # fallback: try docker pull if socket is mounted
    if command -v docker >/dev/null 2>&1 && [ -S /var/run/docker.sock ]; then
      # if raw already contains host, use it; otherwise try localhost:5000
      if docker pull "$raw" >/dev/null 2>&1 || docker pull "localhost:5000/$repo:$tag" >/dev/null 2>&1; then
        echo "Image $repo:$tag available (docker pull)"
        break
      fi
    fi

    if [ "$(date +%s)" -ge "$deadline" ]; then
      echo "Timeout waiting for $raw after ${REACTOR_WAIT_TIMEOUT}s" >&2
      exit 1
    fi
    sleep "$REACTOR_WAIT_INTERVAL"
  done
done

echo "All images available"
exit 0

