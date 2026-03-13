#!/bin/bash
set -e
source config.env

init() {
sqlite3 "$DB" < schema.sql
}

add_disk() {
serial=$1
model=$2
size=$3

sqlite3 "$DB" <<EOF
INSERT OR IGNORE INTO disks
(serial,model,size_bytes,first_seen,status,reliability_score)
VALUES
('$serial','$model','$size',datetime('now'),'new',100);
EOF
}

case "$1" in
init)
init
;;
*)
echo "Usage: diskdb.sh init"
;;
esac
