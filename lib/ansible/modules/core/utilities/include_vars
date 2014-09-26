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
author: Benno Joy
module: include_vars
short_description: Load variables from files, dynamically within a task.
description:
     - Loads variables from a YAML file dynamically during task runtime.  It can work with conditionals, or use host specific variables to determine the path name to load from.
options:
  free-form:
    description:
       - The file name from which variables should be loaded, if called from a role it will look for 
         the file in vars/ subdirectory of the role, otherwise the path would be relative to playbook. An absolute path can also be provided.
    required: true
version_added: "1.4"
'''

EXAMPLES = """
# Conditionally decide to load in variables when x is 0, otherwise do not.
- include_vars: contingency_plan.yml
  when: x == 0

# Load a variable file based on the OS type, or a default if not found.
- include_vars: "{{ item }}"
  with_first_found:
   - "{{ ansible_distribution }}.yml"
   - "{{ ansible_os_family }}.yml"
   - "default.yml"

"""
