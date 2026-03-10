#!/bin/bash
source config.env

mapfile -t drives < <(lsblk -dpno NAME,TYPE | awk '$2=="disk"{print $1}')

running=0

for d in "${drives[@]}"; do

if lsblk -no MOUNTPOINT "$d" | grep -q .; then
continue
fi

sudo ./burnin.sh "$d" &

((running++))

if [ "$running" -ge "$PARALLEL_JOBS" ]; then
wait -n
((running--))
fi

done

wait
