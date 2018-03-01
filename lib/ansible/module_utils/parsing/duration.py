# Copyright (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import datetime
import itertools
import re

DURATION_RE = re.compile(
    r'(?P<sign>[-+]?)(?P<value>[0-9]*(?:\.[0-9]*)?)(?P<unit>[a-z]{1,2})'
)

SECOND = 1
MILLISECOND = SECOND / 1000
MICROSECOND = MILLISECOND / 1000
NANOSECOND = MICROSECOND / 1000
MINUTE = SECOND * 60
HOUR = MINUTE * 60

UNIT_MAP = {
    "ns": NANOSECOND,
    "us": MICROSECOND,
    "ms": MILLISECOND,
    "s": SECOND,
    "m": MINUTE,
    "h": HOUR,
}


class timedelta(datetime.timedelta):
    """Compat class that provides total_seconds for python<2.7"""

    def total_seconds(self):
        """Total seconds in the duration."""
        return ((self.days * 86400 + self.seconds) * 10**6 +
                self.microseconds) / 10**6


def timedelta_to_dict(delta):
    """Accepts a ``datetime.timedelta``, returns a dictionary of units

    :param delta: timedelta
    :type delta: datetime.timedelta
    :return: returns a dictionary of units
    :rtype: dict
    """

    delta = abs(delta)
    return {
        'year': delta.days // 365,
        'day': delta.days % 365,
        'hour': delta.seconds // 3600,
        'minute': (delta.seconds // 60),
        'second': delta.seconds % 60,
        'microsecond': delta.microseconds
    }


def human_time_delta(dt, units=('year', 'day', 'hour', 'minute', 'second'),
                     past_tense='{0} ago', future_tense='in {0}'):
    """Accept a datetime or timedelta, return a human readable delta string

    :param dt: datetime or timedelta
    :param units: list of possible units to be used in resultant string
    :params past_tense: string with ``{0}`` format for output of positive delta
    :params future_tense: string with ``{0}`` format for output of negtive delta
    :type delta: datetime.datetime or datetime.timedelta
    :type units: list
    :type past_tense: str
    :type future_tense: str
    :return: Human readable string representation of a time delta
    :rtype: str
    """

    delta = dt
    if isinstance(dt, datetime.timedelta):
        delta = dt
    else:
        delta = datetime.datetime.now() - dt

    if delta < datetime.timedelta(0):
        tense = future_tense
    else:
        tense = past_tense

    d = timedelta_to_dict(delta)
    hlist = []
    for unit in units:
        if d[unit] == 0:
            continue  # skip 0's
        s = '' if d[unit] == 1 else 's'  # handle plurals
        hlist.append('%s %s%s' % (d[unit], unit, s))
    human_delta = ', '.join(hlist)
    return tense.format(human_delta)


def duration(s):
    """Type function for use in an ``argument_spec`` to parse a duration.

    This function accepts a int/float value as seconds, or a duration value
    as described by ``parse_duration``.

    :param s: duration string
    :type s: str, float, or int
    :return: returns timedelta of parsed duration
    :rtype: datetime.timedelta

    >>> duration(300)
    timedelta(0, 300)
    >>> duration(300.0)
    timedelta(0, 300)
    >>> duration('300.0')
    timedelta(0, 300)
    >>> duration('5m')
    timedelta(0, 300)

    """

    try:
        return timedelta(seconds=float(s))
    except ValueError:
        return parse_duration(s)


def parse_duration(s):
    """parses a duration string. A duration string is a possibly signed
    sequence of decimal numbers, each with optional fraction and a unit
    suffix, such as "300ms", "-1.5h" or "2h45m". Valid time units are
    "ns", "us", "ms", "s", "m", "h".

    Python does not support nanoseconds. The parser will accept and
    handle it, but any value less than 1 microsecond will be lost
    when returning a timedelta object.

    :param s: duration string
    :type s: str
    :return: returns timedelta of parsed duration
    :rtype: datetime.timedelta

    >>> parse_duration("1h15m30.918273645s")
    timedelta(0, 4530, 918274)
    >>> parse_duration("10h")
    timedelta(0, 36000)
    >>> parse_duration("1h10m10s")
    timedelta(0, 4210)
    >>> parse_duration("4h30m")
    timedelta(0, 16200)
    >>> parse_duration("1h30m")
    timedelta(0, 5400)
    >>> parse_duration("1000ns")
    timedelta(0, 0, 1)
    >>> parse_duration("1m30s")
    timedelta(0, 90)
    >>> parse_duration("-1m")
    timedelta(-1, 86340)
    >>> parse_duration("9007199254.740993ms")
    timedelta(104, 21599, 254741)
    >>> parse_duration("9007199254740993ns")
    timedelta(104, 21599, 254741)
    >>> parse_duration("7199254.740993ms") == parse_duration("7199254740993ns")
    True

    """
    matches = list(DURATION_RE.finditer(s))
    if not all(itertools.chain.from_iterable([m.groups()[1:] for m in matches])):
        raise ValueError("%r is not a valid duration" % s)

    run = []
    for match in matches:
        if match.group('sign') not in ('', '-', '+'):
            raise ValueError('%r is not a valid number sign' % match.group('sign'))
        sign = -1 if match.group('sign') == '-' else 1
        try:
            unit = UNIT_MAP[match.group('unit')]
            run.append(
                sign * float(match.group('value')) * unit
            )
        except KeyError:
            raise ValueError("%r is not a valid unit" % match.group('unit'))

    return timedelta(seconds=sum(run))
