# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import logging
import warnings


log_color_to_level = {
    'blue': 5,  # less than debug : COLOR_VERBOSE
    'dark gray': logging.DEBUG,  # 10 : COLOR_DEBUG
    'cyan': logging.INFO-3,  # 17 : COLOR_SKIP
    'green': logging.INFO,  # 20 : COLOR_OK
    'yellow': logging.INFO+3,  # 23 : COLOR_CHANGED
    'white': logging.INFO+6,  # 26 : COLOR_HIGHLIGHT
    'purple': logging.WARNING,  # 30 : COLOR_DEPRECATE
    'bright purple': logging.WARNING,  # 30 : COLOR_WARN
    'red': logging.ERROR,  # 40 : COLOR_ERROR
    'bright red': logging.FATAL  # 50 : COLOR_UNREACHABLE
}


class LogStyle:
    '''LogStyle is designed to behave like a simple string color in ordered
    to keep code that was using C.COLOR_* backwards compatible.

    The class enables the logging facility to receive more detailed information
    about the message being logged, not only color.

    Current implementation includes `value` attribute which is the mapped
    python logging level for that color (style).

    This allows sorting and filtering messages based on their levels.
    '''

    def __init__(self, color):
        self.color = color
        self.value = 0  # undefined log level
        try:
            self.value = log_color_to_level[color]
        except Exception as e:
            warnigns.warn("Unknown style '%s' mapped to log level 0 (unset)")

    def __str__(self):
        return self.color

    def __repr__(self):
        return self.color

    # http://portingguide.readthedocs.io/en/latest/comparisons.html
    def __eq__(self, other):
        return self.value == getattr(other, 'value', 0)

    def __ne__(self, other):
        return self.value == getattr(other, 'value', 0)

    def __lt__(self, other):
        return self.value < getattr(other, 'value', 0)

    def __le__(self, other):
        return self.value <= getattr(other, 'value', 0)

    def __gt__(self, other):
        return self.value > getattr(other, 'value', 0)

    def __ge__(self, other):
        return self.value >= getattr(other, 'value', 0)
