#!/usr/bin/python
# -*- mode: python -*-
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
author:
    - "Ansible Core Team (@ansible)"
module: include_role
short_description: Load and execute a role
description:
     - "Loads and executes a role as a task, this frees roles from the `role:` directive and allows them to be treated more as tasks."
version_added: "2.2"
options:
  name:
    description:
      - The name of the role to be executed.
    required: True
  tasks_from:
    description:
      - "File to load from a Role's tasks/ directory."
    required: False
    default: 'main'
  vars_from:
    description:
      - "File to load from a Role's vars/ directory."
    required: False
    default: 'main'
  defaults_from:
    description:
      - "File to load from a Role's defaults/ directory."
    required: False
    default: 'main'
notes:
    - THIS IS EARLY PREVIEW, THINGS MAY CHANGE
    - Only basic roles have been tested for now, some things might not work as expected.
    - Handlers are made available to the whole play.
    - Currently role variables are not pushed up to the play.
    - simple dependencies seem to work fine.
    - Role search paths work (implicit vars/ templates/ files/ etc)
    - loops don't work.
    - "Things not tested (yet): plugin overrides, nesting includes, used as handler, other stuff I did not think of when I wrote this."
'''

EXAMPLES = """
- include_role: name=myrole

- name: Run tasks/other.yml instead of 'main'
  include_role:
    role: myrole
    tasks_from: other

- name: Pass variables to role
  include_role:
    name: myrole
  vars:
    rolevar1: 'value from task'

"""

RETURN = """
# this module does not return anything except tasks to execute
"""
