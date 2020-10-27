import pkgutil
import re


def dump_splash(splash_name='chaosbomb_80x40', color=True):
    try:
        b_data = pkgutil.get_data(__package__, f'{splash_name}.txt')
    except Exception:
        # TODO: warn
        return

    # TODO: are we a TTY?
    # TODO: select the right size based on TTY caps
    # TODO: do we support color
    # TODO: filter escape codes if not color

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
        _ansi_re = re.compile('\033\[([0-9;]*)m')

    return re.sub(_ansi_re, '', raw)
