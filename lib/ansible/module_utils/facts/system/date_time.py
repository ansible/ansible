# Data and time related facts collection for ansible.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import time

from ansible.module_utils.facts.collector import BaseFactCollector


class DateTimeFactCollector(BaseFactCollector):
    name = 'date_time'
    _fact_ids = set()

    def collect(self, module=None, collected_facts=None):
        facts_dict = {}
        date_time_facts = {}

        now = datetime.datetime.now()
        date_time_facts['year'] = now.strftime('%Y')
        date_time_facts['month'] = now.strftime('%m')
        date_time_facts['weekday'] = now.strftime('%A')
        date_time_facts['weekday_number'] = now.strftime('%w')
        date_time_facts['weeknumber'] = now.strftime('%W')
        date_time_facts['day'] = now.strftime('%d')
        date_time_facts['hour'] = now.strftime('%H')
        date_time_facts['minute'] = now.strftime('%M')
        date_time_facts['second'] = now.strftime('%S')
        date_time_facts['epoch'] = now.strftime('%s')
        if date_time_facts['epoch'] == '' or date_time_facts['epoch'][0] == '%':
            # NOTE: in this case, the epoch wont match the rest of the date_time facts? ie, it's a few milliseconds later..? -akl
            date_time_facts['epoch'] = str(int(time.time()))
        date_time_facts['date'] = now.strftime('%Y-%m-%d')
        date_time_facts['time'] = now.strftime('%H:%M:%S')
        date_time_facts['iso8601_micro'] = now.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        date_time_facts['iso8601'] = now.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        date_time_facts['iso8601_basic'] = now.strftime("%Y%m%dT%H%M%S%f")
        date_time_facts['iso8601_basic_short'] = now.strftime("%Y%m%dT%H%M%S")
        date_time_facts['tz'] = time.strftime("%Z")
        date_time_facts['tz_offset'] = time.strftime("%z")

        facts_dict['date_time'] = date_time_facts
        return facts_dict
