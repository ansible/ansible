# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = """
    lookup: datetime
    author: Will Thames (@willthames)
    version_added: "2.10"
    short_description: Creates a date time object, similar to C(ansible_date_time) fact
    description:
      - Creates a date time object at the time of execution. The fact is identical in
        structure to the `ansible_date_time` fact returned from the setup module or
        gathering facts, but can be used at the end of a playbook to calculate how
        long something took.
"""

EXAMPLES = """
- name: some tasks that set up the operation

- name: gather the time at the start of an operation
  set_fact:
    start_time: "{{ lookup('datetime') }}"

- name: do some really long operations

- name: gather the time at the start of an operation
  set_fact:
    end_time: "{{ lookup('datetime') }}"

- name: output duration in seconds
  debug:
    msg: "The really long operations took {{ end_time.epoch - start_time.epoch }}"
"""

RETURN = """
  year:
    description: year (YYYY)
  month:
    description: zero padded month (mm)
  weekday:
    description: name of the day of the week
  weekday_number:
    description: number of the day of the week
  weeknumber:
    description: number of the week in the year
  day:
    description: zero padded day of month (dd)
  hour:
    description: zero padded hour (HH)
  minute:
    description: zero padded minutes (MM)
  second:
    description: zero padded seconds (SS)
  epoch:
    description: seconds since 1st January 1970
  date:
    description: date in YYYY/dd/mm format
  time:
    description: time in HH:MM:SS format
  iso8601:
    description: ISO8601 timestamp
  iso8601_micro:
    description: ISO8601 timestamp with microsecond resolution
  iso8601_basic:
    description: ISO8601 timestamp without punctuation with microsecond resolution
  iso8601_basic_short:
    description: ISO8601 timestamp without punctuation
  tz:
    description: time zone name
  tz_offset:
    description: time zone offset
"""

from ansible.module_utils.facts.system.date_time import DateTimeFactCollector
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, **kwargs):
        collector = DateTimeFactCollector()
        result = collector.collect()
        return [result['date_time']]
