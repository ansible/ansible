#
# (c) 2016, Sumit Kumar <sumit4@netapp.com>
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


class ModuleDocFragment(object):

    DOCUMENTATION = """
options:
  strict:
    description:
        - If true make invalid entries a fatal error, otherwise skip and continue
        - Since it is possible to use facts in the expressions they might not always be available
          and we ignore those errors by default.
    type: boolean
    default: False
  compose:
    description: create vars from jinja2 expressions
    type: dictionary
    default: {}
  groups:
    description: add hosts to group based on Jinja2 conditionals
    type: dictionary
    default: {}
  keyed_groups:
    description: add hosts to group based on the values of a variable
    type: list
    default: []
"""
