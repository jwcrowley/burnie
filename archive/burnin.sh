#!/bin/bash
set -euo pipefail
source config.env

DRIVE=$1

SERIAL=$(smartctl -i $DRIVE | grep "Serial Number" | awk '{print $3}' || echo unknown)
MODEL=$(smartctl -i $DRIVE | grep "Device Model" | cut -d: -f2 | xargs || echo unknown)
SIZE=$(blockdev --getsize64 $DRIVE)

ARTDIR="$ARTIFACT_DIR/$SERIAL"
mkdir -p "$ARTDIR"

echo "Starting burn-in for $DRIVE"

smartctl -x -j $DRIVE > "$ARTDIR/smart_before.json" || true

fio --name=seqwrite --filename=$DRIVE --rw=write --bs=1M --iodepth=32 --direct=1 --size=100% --ioengine=libaio --output="$ARTDIR/fio_seq.json" --output-format=json

fio --name=randburn --filename=$DRIVE --rw=randrw --rwmixread=70 --bs=1M --iodepth=32 --numjobs=4 --runtime=4h --time_based --direct=1 --ioengine=libaio --write_lat_log="$ARTDIR/latency"

smartctl -x -j $DRIVE > "$ARTDIR/smart_after.json" || true

echo "Burn-in finished for $SERIAL"
