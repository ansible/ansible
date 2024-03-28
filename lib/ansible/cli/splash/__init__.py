import fcntl
import os
import pkgutil
import random
import re

from importlib.resources import contents
from itertools import groupby
from struct import pack, unpack
from termios import TIOCGWINSZ


class _SplashInfo:
    splash_rc_re = re.compile(r'(?P<name>\w+)_(?P<cols>\d+)x(?P<rows>\d+).txt')

    def __init__(self, splash_name: str):
        m = self.splash_rc_re.match(splash_name)
        if not m:
            raise ValueError(f'invalid splash name {splash_name}')

        self.cols: int = int(m.group('cols'))
        self.rows: int = int(m.group('rows'))
        self.basename: str = m.group('name')
        self.filename = splash_name

    @property
    def area(self) -> int:
        return self.cols * self.rows

    def fits(self, cols, rows):
        return self.cols <= cols and self.rows <= rows

    def __repr__(self):
        return f"_SplashInfo('{self.filename}')"

    @classmethod
    def is_valid_splash_name(self, splash_name):
        return bool(_SplashInfo.splash_rc_re.match(splash_name))


def dump_splash(color=True):
    try:
        if not os.isatty(1):
            return
        tty_rows, tty_cols = unpack('HHHH', fcntl.ioctl(1, TIOCGWINSZ, pack('HHHH', 0, 0, 0, 0)))[0:2]
    except Exception:
        return

    if os.environ.get('ANSIBLE_NO_SPLASH', None):
        return

    # adjust for typical version output length
    tty_rows -= 12

    all_splashes = [_SplashInfo(s) for s in sorted(contents(__package__)) if _SplashInfo.is_valid_splash_name(s)]

    available_splashes = []
    # get the largest version of each basename that fits the window
    available_splashes = [max(splashes, key=lambda s: s.area) for _, splashes in groupby((s for s in all_splashes if s.fits(tty_cols, tty_rows)), lambda x: x.basename)]

    if not available_splashes:
        return

    try:
        b_data = pkgutil.get_data(__package__, f'{random.choice(available_splashes).filename}')
    except Exception:
        # TODO: warn
        return

    if not b_data:
        return
    data = b_data.decode("utf8")
    if not color:
        data = _filter_ansi(data)
    print(f'\n{data}\n')


_ansi_re = None  # ANSI escape sequence re lazy compiled on first use


def _filter_ansi(raw):
    global _ansi_re
    if not _ansi_re:  # lazily compile the RE
        _ansi_re = re.compile(r'\033\[([0-9;]*)m')

    return re.sub(_ansi_re, '', raw)
