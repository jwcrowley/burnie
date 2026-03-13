#!/bin/bash

# Usage: sudo ./burnin.sh /dev/sdX

set -euo pipefail

DRIVE=$1
NAME=$(basename "$DRIVE")
DATE=$(date +%F_%H-%M)
LOG="burnin_${NAME}_${DATE}.log"

exec > >(tee -a "$LOG") 2>&1

echo "Burn-in started at $(date)"
echo "Target: $DRIVE"
echo ""

# -------------------------------
# Safety Checks
# -------------------------------

if [[ $EUID -ne 0 ]]; then
    echo "Run as root."
    exit 1
fi

if [[ -z "${DRIVE:-}" || ! -b "$DRIVE" ]]; then
    echo "Usage: $0 /dev/sdX"
    exit 1
fi

command -v fio >/dev/null || { echo "fio not installed"; exit 1; }
command -v smartctl >/dev/null || { echo "smartmontools not installed"; exit 1; }

if lsblk -no MOUNTPOINT "$DRIVE" | grep -q .; then
    echo "ERROR: A partition on this drive is mounted."
    lsblk "$DRIVE"
    exit 1
fi

ROOTDISK=$(lsblk -no pkname "$(findmnt -n -o SOURCE /)")
if [[ "/dev/$ROOTDISK" == "$DRIVE" ]]; then
    echo "Refusing to run on system disk."
    exit 1
fi

echo ""
echo "Device Info:"
lsblk -d -o NAME,SIZE,MODEL,SERIAL "$DRIVE"
echo ""

CONFIRM=$(basename "$DRIVE")
read -p "Type $CONFIRM to confirm destructive burn-in: " INPUT

if [[ "$INPUT" != "$CONFIRM" ]]; then
    echo "Verification failed."
    exit 1
fi

# -------------------------------
# SMART Baseline
# -------------------------------

echo ""
echo "SMART BEFORE TEST"
smartctl -a "$DRIVE"

# -------------------------------
# Phase 1 — Full Sequential Write
# -------------------------------

echo ""
echo "PHASE 1: Sequential full-disk write (surface initialization)"

fio \
--name=seqwrite \
--filename="$DRIVE" \
--rw=write \
--bs=1M \
--direct=1 \
--ioengine=libaio \
--iodepth=32 \
--size=100% \
--verify=crc32c \
--do_verify=1 \
--verify_fatal=1 \
--group_reporting

# -------------------------------
# Phase 2 — Sequential Read Verify
# -------------------------------

echo ""
echo "PHASE 2: Sequential read verification"

fio \
--name=seqread \
--filename="$DRIVE" \
--rw=read \
--bs=1M \
--direct=1 \
--ioengine=libaio \
--iodepth=32 \
--size=100% \
--group_reporting

# -------------------------------
# Phase 3 — Random Stress Burn
# -------------------------------

echo ""
echo "PHASE 3: 24h Random workload burn-in"

fio \
--name=randburn \
--filename="$DRIVE" \
--rw=randrw \
--rwmixread=70 \
--bs=1M \
--direct=1 \
--ioengine=libaio \
--iodepth=32 \
--numjobs=4 \
--size=100% \
--runtime=24h \
--time_based \
--verify=crc32c \
--verify_fatal=1 \
--randrepeat=0 \
--status-interval=60 \
--group_reporting

# -------------------------------
# SMART After Test
# -------------------------------

echo ""
echo "SMART AFTER TEST"
smartctl -a "$DRIVE"

echo ""
echo "Burn-in completed at $(date)"
echo "Log saved to $LOG"
