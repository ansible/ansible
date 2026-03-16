#!/usr/bin/env python
from __future__ import annotations

import argparse
import signal
import subprocess
import sys


def signal_type(v: str) -> signal.Signals:
    if v.isdecimal():
        return signal.Signals(int(v))
    if not v.startswith('SIG'):
        v = f'SIG{v}'
    return getattr(signal.Signals, v)


parser = argparse.ArgumentParser()
parser.add_argument('duration', type=int)
parser.add_argument('--signal', '-s', default=signal.SIGTERM, type=signal_type)
parser.add_argument('command', nargs='+')
args = parser.parse_args()

p: subprocess.Popen | None = None
try:
    p = subprocess.Popen(args.command)
    p.wait(timeout=args.duration)
    sys.exit(p.returncode)
except subprocess.TimeoutExpired:
    if p and p.poll() is None:
        p.send_signal(args.signal)
        p.wait()
    sys.exit(124)
