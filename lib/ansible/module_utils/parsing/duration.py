# Copyright (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import datetime
import itertools
import re

DURATION_RE = re.compile(
    '(?P<sign>[-+]?)(?P<value>[0-9]*(?:\.[0-9]*)?)(?P<unit>[a-z]{1,2})'
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
    "s":  SECOND,
    "m":  MINUTE,
    "h":  HOUR,
}


def duration(s):
    """Type function for use in an ``argument_spec`` to parse a duration.

    This function accepts a int/float value as seconds, or a duration value
    as described by ``parse_duration``.

    :param s: duration string
    :type s: str, float, or int
    :return: returns timedelta of parsed duration
    :rtype: datetime.timedelta

    >>> duration(300)
    datetime.timedelta(0, 300)
    >>> duration(300.0)
    datetime.timedelta(0, 300)
    >>> duration('300.0')
    datetime.timedelta(0, 300)
    >>> duration('5m')
    datetime.timedelta(0, 300)

    """

    try:
        return datetime.timedelta(seconds=float(s))
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
    datetime.timedelta(0, 4530, 918274)
    >>> parse_duration("10h")
    datetime.timedelta(0, 36000)
    >>> parse_duration("1h10m10s")
    datetime.timedelta(0, 4210)
    >>> parse_duration("4h30m")
    datetime.timedelta(0, 16200)
    >>> parse_duration("1h30m")
    datetime.timedelta(0, 5400)
    >>> parse_duration("1000ns")
    datetime.timedelta(0, 0, 1)
    >>> parse_duration("1m30s")
    datetime.timedelta(0, 90)
    >>> parse_duration("-1m")
    datetime.timedelta(-1, 86340)
    >>> parse_duration("9007199254.740993ms")
    datetime.timedelta(104, 21599, 254741)
    >>> parse_duration("9007199254740993ns")
    datetime.timedelta(104, 21599, 254741)
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

    return datetime.timedelta(seconds=sum(run))
