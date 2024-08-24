# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import time

from datetime import datetime as Dtime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _human_offset(offset):
    return offset / 60 / 60 * -1


def _get_offset(tz):

    offset = None
    if tz.lower() == 'local':
        offset = time.altzone if time.daylight else time.timezone
    elif tz.lower() == 'utc':
        offset = 0
    else:
        offset = Dtime.now(timezone.utc).astimezone(_resolve_timezone(tz))

    return offset


def _resolve_timezone(tz, fallback='local'):

    if tz is None:
        tz = fallback

    if tz.lower() == 'local':
        tz = Dtime.now(timezone.utc).astimezone().tzname()
    elif tz.lower() == 'utc':
        tz = timezone.utc

    try:
        return ZoneInfo(tz)
    except ZoneInfoNotFoundEror as e:
        raise AnsibleFilterError("Invalid timezone supplied '{tz'}") from e


def to_datetime(string, format="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strptime(string, format)


def from_datetime(timestruct, timeformat="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(timestruct, timeformat)


def strftime(string_format, second=None, utc=None):
    ''' generate a date/time string using https://docs.python.org/3/library/time.html#time.strftime for format '''
    if utc:
        timefn = time.gmtime
    else:
        timefn = time.localtime
    if second is not None:
        try:
            second = float(second)
        except Exception:
            raise AnsibleFilterError('Invalid value for epoch value (%s)' % second)
    return time.strftime(string_format, timefn(second))


def convert_to_tz(to_convert, initial=None, resulting=None):

    initial = _resolve_timezone(initial, 'utc')
    resulting = _resolve_timezone(resulting, 'local')
    


def to_utc(to_convert, timezone=None):

    timezone = _resolve_timezone(timezone, 'local')
    return convert_to_tz(to_convert, initial=timezone, resulting=timezone.utc)


def to_local_tz(to_convert, timezone=None):

    timezone = _resolve_timezone(timezone, 'utc')


class FilterModule(object):
    ''' Ansible datetime jinja2 filters '''

    def filters(self):
        return {

            # convert string to datetime
            'to_datetime': to_datetime,

            # Get formated string from 'now'
            'strftime': strftime,
        }
