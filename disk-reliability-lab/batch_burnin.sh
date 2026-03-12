#!/bin/bash
set -euo pipefail

# ANSI color codes for warnings
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Safety checks
echo -e "${YELLOW}=================================================${NC}"
echo -e "${YELLOW}   BATCH BURN-IN TEST - SAFETY CHECKS${NC}"
echo -e "${YELLOW}=================================================${NC}"

# 1. Check if config.env exists
if [ ! -f "config.env" ]; then
    echo -e "${RED}ERROR: config.env not found!${NC}"
    echo "Please create config.env with PARALLEL_JOBS setting."
    exit 1
fi

source config.env

# 2. Check PARALLEL_JOBS is set and valid
if [ -z "${PARALLEL_JOBS:-}" ]; then
    echo -e "${RED}ERROR: PARALLEL_JOBS not set in config.env${NC}"
    echo "Set PARALLEL_JOBS=1 for sequential testing."
    exit 1
fi

if ! [[ "$PARALLEL_JOBS" =~ ^[0-9]+$ ]] || [ "$PARALLEL_JOBS" -lt 1 ]; then
    echo -e "${RED}ERROR: PARALLEL_JOBS must be a positive integer${NC}"
    exit 1
fi

# 3. Check if burnin.sh exists and is executable
if [ ! -f "burnin.sh" ]; then
    echo -e "${RED}ERROR: burnin.sh not found!${NC}"
    exit 1
fi

if [ ! -x "burnin.sh" ]; then
    echo -e "${RED}ERROR: burnin.sh is not executable! Run: chmod +x burnin.sh${NC}"
    exit 1
fi

# 4. Check if already running
LOCKFILE="/tmp/batch_burnin.lock"
if [ -f "$LOCKFILE" ]; then
    LOCK_PID=$(cat "$LOCKFILE" 2>/dev/null || echo "")
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        echo -e "${RED}ERROR: Another batch burn-in is already running (PID: $LOCK_PID)${NC}"
        echo "If this is stale, remove: $LOCKFILE"
        exit 1
    else
        echo -e "${YELLOW}Removing stale lock file...${NC}"
        rm -f "$LOCKFILE"
    fi
fi

# Create lock file
echo $$ > "$LOCKFILE"
trap "rm -f $LOCKFILE" EXIT

# 5. Find target drives
echo ""
echo "Scanning for unmounted disk drives..."
mapfile -t drives < <(lsblk -dpno NAME,TYPE | awk '$2=="disk"{print $1}')

if [ ${#drives[@]} -eq 0 ]; then
    echo -e "${RED}ERROR: No disk drives found!${NC}"
    exit 1
fi

# 6. Filter out mounted drives and show what will be affected
targets=()
echo ""
echo "Disks that will be tested:"
for d in "${drives[@]}"; do
    if lsblk -no MOUNTPOINT "$d" | grep -q .; then
        echo "  SKIP (mounted): $d"
    else
        echo -e "  ${GREEN}TEST:${NC} $d"
        targets+=("$d")
    fi
done

if [ ${#targets[@]} -eq 0 ]; then
    echo -e "${RED}ERROR: No unmounted disks found to test!${NC}"
    echo "All disks are mounted - nothing to do."
    exit 1
fi

# 7. Show configuration
echo ""
echo "Configuration:"
echo "  Parallel jobs: $PARALLEL_JOBS"
echo "  Disks to test: ${#targets[@]}"
echo "  Target disks:"
for d in "${targets[@]}"; do
    model=$(lsblk -d -no MODEL "$d" 2>/dev/null || echo "Unknown")
    size=$(lsblk -d -no SIZE "$d" 2>/dev/null || echo "Unknown")
    serial=$(lsblk -d -no SERIAL "$d" 2>/dev/null || echo "Unknown")
    echo "    - $d ($model, $size, S/N: $serial)"
done

# 8. Final confirmation with countdown
echo ""
echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
echo -e "${RED}  WARNING: THIS WILL DESTROY ALL DATA ON TARGET DISKS!${NC}"
echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "The badblocks burn-in test writes to every sector of each disk."
echo "All existing data on the target disks will be permanently lost."
echo ""

# 9. Require explicit confirmation
read -p "Type 'DESTROY' to confirm and continue: " confirm
if [ "$confirm" != "DESTROY" ]; then
    echo -e "${YELLOW}Cancelled - no disks were modified.${NC}"
    exit 0
fi

# 10. Countdown before starting
echo ""
echo "Starting in..."
for i in 5 4 3 2 1; do
    echo -e "${YELLOW}$i...${NC}"
    sleep 1
done
echo -e "${GREEN}GO!${NC}"
echo ""

# 11. Run burn-in tests
running=0
start_time=$(date +%s)

for d in "${targets[@]}"; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting burn-in on $d"

    sudo ./burnin.sh "$d" &
    ((running++))

    if [ "$running" -ge "$PARALLEL_JOBS" ]; then
        wait -n
        ((running--))
    fi
done

# Wait for all to complete
echo ""
echo "All tests started. Waiting for completion..."
wait

end_time=$(date +%s)
duration=$((end_time - start_time))
hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  BATCH BURN-IN COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo "Total time: ${hours}h ${minutes}m ${seconds}s"
echo ""
echo "Check burn-in logs for results."
echo -e "${RED}Note: All data on tested disks has been destroyed.${NC}"
