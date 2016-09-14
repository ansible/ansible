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
  static:
    description:
      - Gives Ansible a hint if this is a 'static' include or not. If static it implies that it won't need templating nor loops nor conditionals and will show included tasks in the --list options.
    required: False
    default: None
  private:
    description:
      - If True the variables from defaults/ and vars/ in a role will not be made available to the rest of the play.
    default: None
notes:
    - THIS IS EARLY PREVIEW, THINGS MAY CHANGE
    - Handlers are made available to the whole play.
    - simple dependencies seem to work fine.
    - "Things not tested (yet): plugin overrides, nesting includes, used as handler, other stuff I did not think of when I wrote this."
'''

EXAMPLES = """
- include_role: name=myrole

- name: Run tasks/other.yml instead of 'main'
  include_role:
    name: myrole
    tasks_from: other

- name: Pass variables to role
  include_role:
    name: myrole
  vars:
    rolevar1: 'value from task'

- name: Use role in loop
  include_role:
    name: myrole
  with_items:
    - '{{roleinput1}}"
    - '{{roleinput2}}"
  loop_control:
    loop_var: roleinputvar

- name: conditional role
  include_role:
    name: myrole
  when: not idontwanttorun
"""

RETURN = """
# this module does not return anything except tasks to execute
"""
