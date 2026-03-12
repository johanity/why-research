"""Diamond renderer for why CLI output."""

from __future__ import annotations

import sys
import time
import random
from typing import List

from .engine import Finding, DepthResult


# Timing constants
CHAR_DELAY = 0.012
DOT_DELAY = 0.04
BANG_DELAY = 0.13
LINE_PAUSE_MIN = 0.15
LINE_PAUSE_MAX = 0.45
DEPTH_PAUSE = 0.6
STAT_CHAR_DELAY = 0.03
STAT_SEGMENT_PAUSE = 0.15


def render_topic(topic: str) -> None:
    """Render the opening."""
    print()
    _slow(f"why {topic}", delay=0.05)
    print()
    time.sleep(0.6)


def render_finding(finding: Finding, index: int, total_in_depth: int, depth: int) -> None:
    """Render a single finding as it arrives."""
    mid = total_in_depth // 2

    # Diamond dot count
    if index <= mid:
        dots = index + 1
    else:
        dots = max(1, total_in_depth - index)

    padding = " " * (8 - dots)
    dot_str = "·" * dots

    # Pause between findings
    time.sleep(random.uniform(LINE_PAUSE_MIN, LINE_PAUSE_MAX))

    # Dots appear
    sys.stdout.write(f"     {padding}")
    for d in dot_str:
        sys.stdout.write(d)
        sys.stdout.flush()
        time.sleep(DOT_DELAY)

    sys.stdout.write("  ")
    sys.stdout.flush()
    time.sleep(0.08)

    # Title types out
    for ch in finding.title:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(CHAR_DELAY)

    # Bang indicators
    if finding.bangs:
        # Pad to align bangs
        title_len = len(finding.title)
        pad = max(2, 32 - title_len - dots)
        sys.stdout.write(" " * pad)
        sys.stdout.flush()
        time.sleep(0.15)

        for b in finding.bangs:
            sys.stdout.write(b)
            sys.stdout.flush()
            time.sleep(BANG_DELAY)

    print()


def render_depth_start(depth: int) -> None:
    """Render the opening dot of a new depth level."""
    indent = " " * depth
    pad = " " * (8 - 1)
    time.sleep(DEPTH_PAUSE if depth > 0 else 0.3)
    print(f"     {indent}{pad}·")


def render_depth_end(depth: int, result: DepthResult, cumulative: dict) -> None:
    """Render the closing dot and stats for a depth level."""
    indent = " " * depth
    pad = " " * (8 - 1)
    time.sleep(0.2)
    print(f"     {indent}{pad}·")


def render_stats(
    total_found: int,
    total_useful: int,
    total_surprise: int,
    brain_level: int,
) -> None:
    """Render the score line."""
    print()
    time.sleep(0.5)

    sys.stdout.write("     ")
    segments = [
        str(total_found),
        "·",
        f"{total_useful}✦",
        "·",
        f"{total_surprise}!",
        "·",
        f"+{brain_level}🧠",
    ]

    for segment in segments:
        for ch in segment:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(STAT_CHAR_DELAY)
        time.sleep(STAT_SEGMENT_PAUSE)

    print()


def render_file(filename: str) -> None:
    """Render the output file path."""
    time.sleep(0.4)
    print()
    _slow(f"     {filename}", delay=0.03)


def render_threads(n_threads: int) -> None:
    """Render remaining threads."""
    time.sleep(0.5)
    print()
    _slow(f"     {n_threads} threads left to pull ↓", delay=0.03)
    print()


def _slow(text: str, delay: float = 0.02) -> None:
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()
