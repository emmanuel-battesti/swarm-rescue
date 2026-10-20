#!/usr/bin/env bash
# Usage: ./docker/run_in_docker_ubuntu22_py311.sh [command]
# Default command: python -m pytest -q (uses python3.11 in the image)
# Build only (useful for debug / CI), from repo root:
#   BUILD_ONLY=1 ./docker/run_in_docker_ubuntu22_py311.sh
# Run a quick check (prints Python version and OK):
#   ./docker/run_in_docker_ubuntu22_py311.sh 'bash -lc "python3 -V; echo OK"'
# Run a specific test file:
#   ./docker/run_in_docker_ubuntu22_py311.sh 'bash -lc "python -m pytest tests/test_shader_config.py -q"'
#   ./docker/run_in_docker_ubuntu22_py311.sh 'bash -lc "python -m pytest tests/test_sensor_consistency.py -q"'
#   ./docker/run_in_docker_ubuntu22_py311.sh "python examples/example_semantic_sensor.py"
set -euo pipefail

SUFFIX_VERSION="ubuntu22_py311"

IMAGE_NAME=swarm-rescue:${SUFFIX_VERSION}
DOCKERFILE_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$DOCKERFILE_DIR/.." && pwd)"

DOCKERFILE="$DOCKERFILE_DIR/Dockerfile.${SUFFIX_VERSION}"

if [ ! -s "$DOCKERFILE" ]; then
  echo "ERROR: Dockerfile not found or empty: $DOCKERFILE"
  echo "Please ensure the Dockerfile exists and is not empty."
  exit 1
fi

# Build image if missing
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  echo "Building Docker image ${IMAGE_NAME} from $DOCKERFILE..."
  docker build -f "$DOCKERFILE" -t "$IMAGE_NAME" "$ROOT_DIR"
  echo "Build finished."
else
  echo "Docker image $IMAGE_NAME already exists -> skipping build"
fi

# If BUILD_ONLY env set, exit after build
if [ "${BUILD_ONLY:-0}" != "0" ]; then
  echo "BUILD_ONLY=1 -> exiting after build"
  exit 0
fi

# Default command
DEFAULT_CMD='python -m pytest -q'
CMD=${1:-$DEFAULT_CMD}

# Run container mounting project
# Place the pip cache on the host under docker/tmp/.docker_pip_cache_${SUFFIX_VERSION}
# and mount the whole docker/tmp into the container so other XDG caches (matplotlib, mesa_shader_cache, ...) appear there
DOCKER_TMP_DIR="$DOCKERFILE_DIR/tmp"
PIP_CACHE="$DOCKER_TMP_DIR/.docker_pip_cache_${SUFFIX_VERSION}"
# ensure parent tmp directory exists
mkdir -p "$DOCKER_TMP_DIR"
mkdir -p "$PIP_CACHE"

# Map host UID:GID to container process to avoid permission issues on bind mounts
HOST_UID=${HOST_UID:-$(id -u 2>/dev/null || echo 1000)}
HOST_GID=${HOST_GID:-$(id -g 2>/dev/null || echo 1000)}

# Ensure pip cache dir is writable by that uid:gid
if command -v chown >/dev/null 2>&1; then
  chown "${HOST_UID}:${HOST_GID}" "$PIP_CACHE" || true
fi

# Prepare inner script
# Put the inner script inside docker/tmp so it is preserved on the host
TMP_SCRIPT_PATH="$DOCKER_TMP_DIR/.docker_inner_${SUFFIX_VERSION}.sh"
# Create the inner script header. We will append the exact user command safely.
# Use a placeholder __SUFFIX_VERSION__ that we will replace on the host (bake-in)
cat > "$TMP_SCRIPT_PATH" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
# Baked-in suffix placeholder will be replaced on the host by sed
SUFFIX_V="__SUFFIX_VERSION__"
echo "[inner script] SUFFIX_V=${SUFFIX_V}"
# Use python3.11 and venv
python3.11 -m venv docker/tmp/.venv_${SUFFIX_V}
# shellcheck disable=SC1091
source docker/tmp/.venv_${SUFFIX_V}/bin/activate
if [ "${SKIP_INSTALL:-0}" = "0" ]; then
  python -m pip install --upgrade pip setuptools wheel
  pip install -e ".[dev]" || true
else
  echo "SKIP_INSTALL=1 -> skipping pip install"
fi

# Start Xvfb when needed
XVFB_PID=""
if [ -z "${DISPLAY:-}" ] || [ "${FORCE_XVFB:-0}" = "1" ]; then
  if command -v Xvfb >/dev/null 2>&1; then
    echo "No DISPLAY detected or FORCE_XVFB=1 -> starting Xvfb on :99"
    Xvfb :99 -screen 0 1280x720x24 >/tmp/.xvfb.log 2>&1 &
    XVFB_PID=$!
    export DISPLAY=:99
    sleep 0.2
  else
    echo "Warning: Xvfb not found in image; tests requiring a display may fail"
  fi
fi

# Ensure we cleanup Xvfb after the user command runs
cleanup() {
  if [ -n "${XVFB_PID:-}" ]; then
    echo "Stopping Xvfb (pid=${XVFB_PID})"
    kill "${XVFB_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT
SCRIPT

# Append the user command safely (avoid sed/escaping issues)
printf '%s\n' "$CMD" >> "$TMP_SCRIPT_PATH"

# Replace the placeholder with the concrete suffix value on the host (bake-in)
sed -i "s/__SUFFIX_VERSION__/${SUFFIX_VERSION}/g" "$TMP_SCRIPT_PATH"

# Make the inner script executable and owned by the host UID:GID
chmod +x "$TMP_SCRIPT_PATH"
if command -v chown >/dev/null 2>&1; then
  chown "${HOST_UID}:${HOST_GID}" "$TMP_SCRIPT_PATH" || true
fi

# GPU and X11 detection: build docker run extra options when available
GPU_OPTS=()
# Enable GPU by setting USE_GPU=1; default is auto-detect (USE_GPU=auto)
if [ "${USE_GPU:-auto}" != "0" ]; then
  if [ -e /dev/nvidia0 ] || command -v nvidia-smi >/dev/null 2>&1; then
    echo "GPU: NVIDIA detected on host, enabling --gpus all"
    GPU_OPTS=(--gpus all)
    # bind common nvidia device nodes if present (best-effort)
    for dev in /dev/nvidiactl /dev/nvidia-uvm /dev/nvidia0; do
      if [ -e "$dev" ]; then
        GPU_OPTS+=(--device="$dev")
      fi
    done
  elif [ -d /dev/dri ]; then
    echo "GPU: /dev/dri present on host, mounting for integrated GPU support"
    # mount whole /dev/dri (readonly) for integrated GPUs (Intel, AMD)
    GPU_OPTS+=(--mount type=bind,source=/dev/dri,target=/dev/dri,readonly)
  else
    echo "No GPU devices detected on host (or USE_GPU=0). Continuing without GPU support."
  fi
fi

DOCKER_X11_OPTS=()
if [ -n "${DISPLAY:-}" ] && [ -S /tmp/.X11-unix/X0 ]; then
  # Only mount X11 socket if it exists on host; avoid forcing if not needed
  DOCKER_X11_OPTS=(-e "DISPLAY=${DISPLAY}" --mount type=bind,source=/tmp/.X11-unix,target=/tmp/.X11-unix)
fi

# Run container with optional GPU/X11 options

docker run --rm -it --entrypoint "" \
  ${GPU_OPTS[@]+"${GPU_OPTS[@]}"} \
  ${DOCKER_X11_OPTS[@]+"${DOCKER_X11_OPTS[@]}"} \
  -u "${HOST_UID}:${HOST_GID}" \
  -e HOME=/project \
  -e XDG_CACHE_HOME=/project/docker/tmp \
  -e PIP_CACHE_DIR=/project/docker/tmp/.docker_pip_cache_${SUFFIX_VERSION} \
  -v "$ROOT_DIR":/project:rw \
  -v "$DOCKER_TMP_DIR":/project/docker/tmp:rw \
  -w /project \
  "$IMAGE_NAME" /bin/bash /project/docker/tmp/.docker_inner_${SUFFIX_VERSION}.sh

echo "Container finished."
