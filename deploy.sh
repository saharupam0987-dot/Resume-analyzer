#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Automated EC2 setup for Student-Teacher Evaluation System
# Usage: sudo bash deploy.sh
# Supports: Amazon Linux 2023, Ubuntu 22.04
# =============================================================================
set -euo pipefail

# ---- Colors ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ---- Must be root ----
if [[ $EUID -ne 0 ]]; then
    err "This script must be run as root (sudo bash deploy.sh)"
fi

# ---- Detect OS ----
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID="${ID:-unknown}"
else
    err "Cannot detect OS — /etc/os-release not found"
fi

log "Detected OS: $OS_ID ($PRETTY_NAME)"

# ---- App directory (script location) ----
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
log "App directory: $APP_DIR"

if [[ ! -f "$APP_DIR/app.py" ]]; then
    err "app.py not found in $APP_DIR — run this script from the project root"
fi

if [[ ! -f "$APP_DIR/.env" ]]; then
    err ".env file not found — copy .env.example to .env and set your API keys"
fi

# ---- 1. Create 2GB swap (if not already present) ----
if swapon --show | grep -q '/swapfile'; then
    log "Swap already active — skipping"
else
    log "Creating 2GB swap file..."
    dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    # Persist across reboots
    if ! grep -q '/swapfile' /etc/fstab; then
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi
    # Set swappiness
    sysctl vm.swappiness=60
    if ! grep -q 'vm.swappiness' /etc/sysctl.conf; then
        echo 'vm.swappiness=60' >> /etc/sysctl.conf
    fi
    log "Swap enabled (2GB, swappiness=60)"
fi

# ---- 2. Install Docker ----
if command -v docker &>/dev/null; then
    log "Docker already installed: $(docker --version)"
else
    log "Installing Docker..."
    case "$OS_ID" in
        amzn)
            yum update -y
            yum install -y docker
            systemctl start docker
            systemctl enable docker
            ;;
        ubuntu)
            apt-get update -y
            apt-get install -y ca-certificates curl gnupg
            install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
                gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            chmod a+r /etc/apt/keyrings/docker.gpg
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
              https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
              tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt-get update -y
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        *)
            err "Unsupported OS: $OS_ID — install Docker manually and re-run"
            ;;
    esac
    log "Docker installed: $(docker --version)"
fi

# ---- 3. Install Docker Compose (plugin or standalone) ----
if docker compose version &>/dev/null; then
    log "Docker Compose already available: $(docker compose version)"
else
    log "Installing Docker Compose plugin..."
    case "$OS_ID" in
        amzn)
            COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | \
                grep '"tag_name"' | cut -d'"' -f4)
            mkdir -p /usr/local/lib/docker/cli-plugins
            curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" \
                -o /usr/local/lib/docker/cli-plugins/docker-compose
            chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
            ;;
        ubuntu)
            # Already installed via docker-compose-plugin above
            apt-get install -y docker-compose-plugin 2>/dev/null || true
            ;;
    esac
    log "Docker Compose ready: $(docker compose version)"
fi

# ---- 4. Add ec2-user / ubuntu to docker group ----
for u in ec2-user ubuntu; do
    if id "$u" &>/dev/null; then
        usermod -aG docker "$u"
        log "Added $u to docker group"
    fi
done

# ---- 5. Build and start ----
log "Building Docker image (this will take a few minutes on t2.micro)..."
cd "$APP_DIR"
docker compose build --no-cache

log "Starting container..."
docker compose up -d

# ---- 6. Verify ----
log "Waiting for app to start..."
sleep 10

if curl -sf http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    log "Health check passed!"
else
    warn "Health check did not pass yet — the app may still be loading."
    warn "Check logs: docker compose logs -f"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} Deployment complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "  Access the app at: http://<YOUR_ELASTIC_IP>:8501"
echo ""
echo "  Useful commands:"
echo "    docker compose logs -f      # view logs"
echo "    docker compose restart      # restart app"
echo "    docker compose down          # stop app"
echo "    docker compose up -d --build # rebuild & restart"
echo ""
