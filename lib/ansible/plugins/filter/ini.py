# (c) 2017, Matt Martz <matt@sivel.net>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import copy
from ansible.module_utils.six.moves import configparser, StringIO


def from_ini(o):
    parser = configparser.RawConfigParser()
    parser.readfp(StringIO(o))
    d = dict(parser._sections)
    for k in d:
        d[k] = dict(d[k])
        d[k].pop('__name__', None)
    d['DEFAULT'] = dict(parser._defaults)
    return d


def to_ini(o):
    data = copy.deepcopy(o)
    defaults = configparser.RawConfigParser(data.pop('DEFAULT', {}))
    parser = configparser.RawConfigParser()
    for section, items in data.items():
        parser.add_section(section)
        for k, v in items.items():
            parser.set(section, k, v)
    out = StringIO()
    defaults.write(out)
    parser.write(out)
    return out.getvalue()


class FilterModule(object):
    def filters(self):
        return {
            'to_ini': to_ini,
            'from_ini': from_ini
        }
