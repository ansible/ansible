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
author: "Benno Joy (@bennojoy)"
module: include_vars
short_description: Load variables from files, dynamically within a task.
description:
     - Loads variables from a YAML/JSON file dynamically during task runtime.  It can work with conditionals, or use host specific variables to determine the path name to load from.
options:
  file:
    version_added: "2.2"
    description:
       - The file name from which variables should be loaded.
       - If the path is relative, it will look for the file in vars/ subdirectory of a role or relative to playbook.
  name:
    version_added: "2.2"
    description:
        - The name of a variable into which assign the included vars, if omitted (null) they will be made top level vars.
    default: null
  free-form:
    description:
        - This module allows you to specify the 'file' option directly w/o any other options.
notes:
    - The file is always required either as the explicit option or using the free-form.
version_added: "1.4"
'''

EXAMPLES = """
# Include vars of stuff.yml into the 'stuff' variable (2.2).
- include_vars:
    file: stuff.yml
    name: stuff

# Conditionally decide to load in variables into 'plans' when x is 0, otherwise do not. (2.2)
- include_vars: file=contingency_plan.yml name=plans
  when: x == 0

# Load a variable file based on the OS type, or a default if not found.
- include_vars: "{{ item }}"
  with_first_found:
   - "{{ ansible_distribution }}.yml"
   - "{{ ansible_os_family }}.yml"
   - "default.yml"

# bare include (free-form)
- include_vars: myvars.yml

"""
