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
author: "Allen Sanabria (@linuxdynasty)"
module: include_vars
short_description: Load variables from files, dynamically within a task.
description:
     - Loads variables from a YAML/JSON files dynamically from within a file or
       from a directory recursively during task runtime. If loading a directory, the files are sorted alphabetically before being loaded.
options:
  file:
    version_added: "2.2"
    description:
       - The file name from which variables should be loaded.
       - If the path is relative, it will look for the file in vars/ subdirectory of a role or relative to playbook.
  dir:
    version_added: "2.2"
    description:
      - The directory name from which the variables should be loaded.
      - If the path is relative, it will look for the file in vars/ subdirectory of a role or relative to playbook.
    default: null
  name:
    version_added: "2.2"
    description:
        - The name of a variable into which assign the included vars, if omitted (null) they will be made top level vars.
    default: null
  depth:
    version_added: "2.2"
    description:
      - By default, this module will recursively go through each sub directory and load up the variables. By explicitly setting the depth, this module will only go as deep as the depth.
    default: 0
  files_matching:
    version_added: "2.2"
    description:
      - Limit the variables that are loaded within any directory to this regular expression.
    default: null
  ignore_files:
    version_added: "2.2"
    description:
      - List of file names to ignore. The defaults can not be overridden, but can be extended.
    default: null
  free-form:
    description:
        - This module allows you to specify the 'file' option directly w/o any other options.
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

# Include all yml files in vars/all and all nested directories
- include_vars:
    dir: 'vars/all'

# Include all yml files in vars/all and all nested directories and save the output in test.
- include_vars:
    dir: 'vars/all'
    name: test

# Include all yml files in vars/services
- include_vars:
    dir: 'vars/services'
    depth: 1

# Include only bastion.yml files
- include_vars:
    dir: 'vars'
    files_matching: 'bastion.yml'

# Include only all yml files exception bastion.yml
- include_vars:
    dir: 'vars'
    ignore_files: 'bastion.yml'
"""
