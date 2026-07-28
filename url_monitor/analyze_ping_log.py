#!/usr/bin/env python3
"""
Analyze ping_to_file.sh output and report internet disconnections.

Expected log line format from ping_to_file.sh:
    YYYY-MM-DD HH:MM:SS PING <url> time=<N>ms
    YYYY-MM-DD HH:MM:SS PING <url> time=timeout

Usage:
    python3 analyze_ping_log.py /path/to/ping.log
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median
from typing import Iterable

LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+PING\s+.*?\s+time=(?P<time>timeout|[0-9.]+\s*ms?)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PingRecord:
    timestamp: datetime
    ok: bool
    latency_ms: float | None
    line_number: int


@dataclass(frozen=True)
class Outage:
    start: datetime
    end: datetime | None
    failed_pings: int
    ongoing: bool = False

    @property
    def duration(self) -> timedelta:
        end = self.end if self.end is not None else self.start
        return end - self.start


@dataclass(frozen=True)
class Gap:
    start: datetime
    end: datetime
    duration: timedelta


def parse_log(path: str) -> tuple[list[PingRecord], int]:
    records: list[PingRecord] = []
    ignored = 0

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line_number, line in enumerate(f, start=1):
            match = LINE_RE.match(line.strip())
            if not match:
                ignored += 1
                continue

            timestamp = datetime.strptime(match.group("ts"), "%Y-%m-%d %H:%M:%S")
            value = match.group("time").lower().replace(" ", "")
            if value == "timeout":
                records.append(PingRecord(timestamp, False, None, line_number))
            else:
                records.append(PingRecord(timestamp, True, float(value.removesuffix("ms")), line_number))

    records.sort(key=lambda r: r.timestamp)
    return records, ignored


def infer_interval(records: list[PingRecord], fallback_seconds: float) -> float:
    deltas = [
        (b.timestamp - a.timestamp).total_seconds()
        for a, b in zip(records, records[1:])
        if (b.timestamp - a.timestamp).total_seconds() > 0
    ]
    if not deltas:
        return fallback_seconds

    # Ignore very large gaps when estimating the normal ping interval.
    likely_normal = sorted(deltas)[: max(1, int(len(deltas) * 0.75))]
    return float(median(likely_normal))


def find_outages(records: list[PingRecord]) -> list[Outage]:
    outages: list[Outage] = []
    in_outage = False
    start: datetime | None = None
    failed = 0

    for record in records:
        if not record.ok:
            if not in_outage:
                in_outage = True
                start = record.timestamp
                failed = 0
            failed += 1
        elif in_outage:
            outages.append(Outage(start=start, end=record.timestamp, failed_pings=failed))  # type: ignore[arg-type]
            in_outage = False
            start = None
            failed = 0

    if in_outage:
        outages.append(Outage(start=start, end=records[-1].timestamp, failed_pings=failed, ongoing=True))  # type: ignore[arg-type]

    return outages


def find_recording_gaps(records: list[PingRecord], expected_interval: float, gap_multiple: float) -> list[Gap]:
    threshold = expected_interval * gap_multiple
    gaps: list[Gap] = []
    for a, b in zip(records, records[1:]):
        delta = (b.timestamp - a.timestamp).total_seconds()
        if delta > threshold:
            gaps.append(Gap(a.timestamp, b.timestamp, timedelta(seconds=delta)))
    return gaps


def fmt_duration(delta: timedelta) -> str:
    seconds = int(round(delta.total_seconds()))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def print_table(rows: Iterable[tuple[str, ...]], headers: tuple[str, ...]) -> None:
    rows = list(rows)
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def line(values: tuple[str, ...]) -> str:
        return "  ".join(value.ljust(widths[i]) for i, value in enumerate(values))

    print(line(headers))
    print(line(tuple("-" * width for width in widths)))
    for row in rows:
        print(line(row))


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze ping_to_file.sh logs for disconnections.")
    parser.add_argument("logfile", help="Output file written by ping_to_file.sh")
    parser.add_argument(
        "--expected-interval",
        type=float,
        default=None,
        help="Expected seconds between ping attempts. Defaults to inferred interval, or 5 seconds if it cannot be inferred.",
    )
    parser.add_argument(
        "--gap-multiple",
        type=float,
        default=2.5,
        help="Report missing-record gaps longer than expected_interval * this value. Default: 2.5",
    )
    args = parser.parse_args()

    records, ignored = parse_log(args.logfile)
    if not records:
        print("No timestamped ping_to_file.sh records found.")
        print("Expected lines like: YYYY-MM-DD HH:MM:SS PING example.com time=23.4ms")
        if ignored:
            print(f"Ignored {ignored} unrecognized line(s).")
        return 1

    expected = args.expected_interval if args.expected_interval is not None else infer_interval(records, 5.0)
    outages = find_outages(records)
    gaps = find_recording_gaps(records, expected, args.gap_multiple)

    ok_count = sum(1 for r in records if r.ok)
    fail_count = len(records) - ok_count
    first = records[0].timestamp
    last = records[-1].timestamp

    print(f"Log period: {first} to {last} ({fmt_duration(last - first)})")
    print(f"Records: {len(records)} total, {ok_count} successful, {fail_count} timeout")
    print(f"Expected interval: {expected:.1f}s")
    if ignored:
        print(f"Ignored unrecognized lines: {ignored}")
    print()

    if outages:
        print(f"Disconnections found: {len(outages)}")
        print_table(
            (
                (
                    str(i),
                    outage.start.strftime("%Y-%m-%d %H:%M:%S"),
                    "still disconnected at end of log" if outage.ongoing else outage.end.strftime("%Y-%m-%d %H:%M:%S"),  # type: ignore[union-attr]
                    fmt_duration(outage.duration),
                    str(outage.failed_pings),
                )
                for i, outage in enumerate(outages, start=1)
            ),
            ("#", "Start", "Recovered", "Duration", "Failed pings"),
        )
    else:
        print("No disconnections found (no timeout entries).")

    if gaps:
        print()
        print("Recording gaps found (ping script may have stopped, machine slept, or logging paused):")
        print_table(
            (
                (
                    str(i),
                    gap.start.strftime("%Y-%m-%d %H:%M:%S"),
                    gap.end.strftime("%Y-%m-%d %H:%M:%S"),
                    fmt_duration(gap.duration),
                )
                for i, gap in enumerate(gaps, start=1)
            ),
            ("#", "Last record before gap", "Next record after gap", "Gap length"),
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
