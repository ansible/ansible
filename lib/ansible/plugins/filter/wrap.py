# (c) 2017, Gerben Geijteman <gerben@hyperized.net>
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

# Inspired by:
#   - https://stackoverflow.com/a/29573589
#   - https://stackoverflow.com/a/39998511

# Example usage:
#
# mylist:
#   - hello
#   - world
# mylist | wrap_list('"') | join(', ')
#
# results in:
#
# "hello", "world"

from __future__ import (absolute_import, division, print_function)

from functools import partial

__metaclass__ = type


def wrap(value, wrapper='"'):
    """
    Wraps given wrapper quote around value
    :param value:
    :param wrapper:
    :return:
    """
    return wrapper + value + wrapper


def wrap_list(list, wrapper='"'):
    """
    Wraps given wrapper quote around list values
    :param list:
    :param wrapper:
    :return:
    """
    return [wrapper + item + wrapper for item in list]


class FilterModule(object):
    """
    FilterModule class
    """

    def filters(self):
        """
        Returns filters
        :return:
        """
        return {'wrap': wrap,
                'wrap_list': wrap_list, }
