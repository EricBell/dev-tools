# URL Monitor

Simple Bash/Python tool for monitoring reachability of a host over time and analyzing the log for outages.

## Use

Start logging one ping every 5 seconds:

```bash
./tools/url_monitor/ping_to_file.sh 8.8.8.8 /tmp/ping.log
```

Use a custom interval in seconds:

```bash
./tools/url_monitor/ping_to_file.sh example.com logs/example-ping.log 10
```

Stop logging with `Ctrl+C`.

Analyze the log:

```bash
./tools/url_monitor/analyze_ping_log.py /tmp/ping.log
```

Specify the expected interval if the log is too short to infer it:

```bash
./tools/url_monitor/analyze_ping_log.py /tmp/ping.log --expected-interval 10
```

## What it does

- `ping_to_file.sh` repeatedly runs `ping -c 1 <target>` and appends exactly one timestamped line per attempt.
- `analyze_ping_log.py` reads that log and reports:
  - log period and record counts
  - timeout-based disconnections
  - recording gaps where the logger may have stopped, slept, or paused

## Log format

```text
YYYY-MM-DD HH:MM:SS PING <target> time=<N>ms
YYYY-MM-DD HH:MM:SS PING <target> time=timeout
```

## Setup / dependencies

- Bash
- system `ping` command
- Python 3.10+ for analysis
- No third-party Python packages

## Notes

- Despite the name, this monitors ping reachability for a host/IP, not HTTP status for a full URL path.
- Large logs stay on disk; analysis prints a concise summary/table.
- The analyzer ignores lines that do not match the documented format.
