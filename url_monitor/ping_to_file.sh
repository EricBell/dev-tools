#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: ping_to_file.sh <host-or-ip> <output_file> [interval_seconds]

Ping a host repeatedly and append one timestamped line per attempt.

Examples:
  ./ping_to_file.sh 8.8.8.8 /tmp/ping.log
  ./ping_to_file.sh example.com logs/example-ping.log 10

Output format:
  YYYY-MM-DD HH:MM:SS PING <host-or-ip> time=<N>ms
  YYYY-MM-DD HH:MM:SS PING <host-or-ip> time=timeout
USAGE
}

if [[ "$#" -lt 2 || "$#" -gt 3 ]]; then
    usage >&2
    exit 1
fi

TARGET=$1
OUTPUT_FILE=$2
INTERVAL=${3:-5}

if ! [[ "$INTERVAL" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    echo "Error: interval_seconds must be numeric." >&2
    usage >&2
    exit 1
fi

output_dir=$(dirname "$OUTPUT_FILE")
if [[ "$output_dir" != "." ]]; then
    mkdir -p "$output_dir"
fi

# Infinite loop to ping the target every INTERVAL seconds.
# Write exactly one line per ping in the documented format.
while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    ping_output=$(ping -c 1 "$TARGET" 2>&1 || true)

    time_regex='time=([0-9.]+)[[:space:]]*ms'
    if [[ $ping_output =~ $time_regex ]]; then
        time_ms="${BASH_REMATCH[1]}ms"
    else
        time_ms="timeout"
    fi

    printf '%s PING %s time=%s\n' "$timestamp" "$TARGET" "$time_ms" | tee -a "$OUTPUT_FILE"
    sleep "$INTERVAL"
done
