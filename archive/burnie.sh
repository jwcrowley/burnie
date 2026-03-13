#!/bin/bash

# Usage: sudo ./burnin.sh /dev/sdX
DRIVE=$1

# 1. Basic Safety & Root Check
if [[ $EUID -ne 0 ]]; then
   echo "Error: This script must be run as root."
   exit 1
fi

if [[ -z "$DRIVE" || ! -b "$DRIVE" ]]; then
    echo "Usage: $0 /dev/sdX"
    echo "Example: $0 /dev/sde"
    exit 1
fi

# 2. Check if the drive is currently mounted
if mount | grep -q "^$DRIVE"; then
    echo "ERROR: $DRIVE is currently MOUNTED."
    echo "Testing a mounted drive with writes WILL destroy your filesystem."
    echo "Unmount it first or target a file path instead."
    exit 1
fi

# 3. THE DOUBLE-LOCK VERIFICATION
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo "WARNING: YOU ARE ABOUT TO PERFORM A DESTRUCTIVE BURN-IN."
echo "TARGET DEVICE: $DRIVE"
echo "ALL DATA ON $DRIVE WILL BE PERMANENTLY OVERWRITTEN."
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo ""

# Extract just the name (e.g., sde) from the path (/dev/sde)
CONFIRM_NAME=$(basename "$DRIVE")

read -p "To confirm, please type the device name again (e.g. $CONFIRM_NAME): " USER_INPUT

if [[ "$USER_INPUT" != "$CONFIRM_NAME" ]]; then
    echo "Verification failed. Exiting to protect your data."
    exit 1
fi

echo "Identity verified. Starting 24-hour burn-in on $DRIVE..."

# 4. The Improved FIO Command
fio --name=burn_$(basename "$DRIVE") \
  --filename="$DRIVE" \
  --rw=randrw \
  --rwmixread=70 \
  --bs=8M \
  --direct=1 \
  --ioengine=libaio \
  --iodepth=16 \
  --numjobs=4 \
  --runtime=24h \
  --time_based \
  --group_reporting \
  --verify=md5 \
  --do_verify=1 \
  --verify_fatal=1 \
  --randrepeat=0 \
  --status-interval=60

