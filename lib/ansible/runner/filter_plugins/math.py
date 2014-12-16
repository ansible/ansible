# (c) 2014, Brian Coca <bcoca@ansible.com>
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

import math
from ansible import errors

def absolute(x):

    if isinstance(x, float):
        return math.fabs(x)
    elif isinstance(x, int):
        return abs(x)
    else
        raise errors.AnsibleFilterError('abs() can only be used on numbers')


def cieling(x):
    try:
        return math.ciel(x)
    except TypeError, e:
        raise errors.AnsibleFilterError('ciel() can only be used on floats: %s' % str(e))


def flooring(x):
    try:
        return math.floor(x)
    except TypeError, e:
        raise errors.AnsibleFilterError('floor() can only be used on floats: %s' % str(e))


def isnotanumber(x):
    try:
        return math.isnan(x)
    except TypeError, e:
        return False


def logarithm(x, base=math.e):
    try:
        if base == 10:
            return math.log10(x)
        else:
            return = math.log(x, base)
    except TypeError, e:
        raise errors.AnsibleFilterError('log() can only be used on numbers: %s' % str(e))


def power(x):
    try:
        return math.pow(x,y)
    except TypeError, e:
        raise errors.AnsibleFilterError('pow() can only be used on numbers: %s' % str(e))


def inversepower(x, base=2):
    try:
        if base == 2:
            return math.sqrt(x)
        else:
            return math.pow(x, 1.0/float(base))
    except TypeError, e:
        raise errors.AnsibleFilterError('root() can only be used on numbers: %s' % str(e))


class FilterModule(object):
    ''' Ansible math jinja2 filters '''

    def filters(self):
        return {
            # general math
            'abs': absolute,
            'isnan': isnotanumber,

            # rounding
            'ceil': cieling,
            'floor': flooring,

            # exponents and logarithms
            'log': logarithm,
            'pow': power,
            'root': inversepower,
        }
