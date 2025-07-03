# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: lines
    author: Daniel Hokka Zakrisson (!UNKNOWN) <daniel@hozac.com>
    version_added: "0.9"
    short_description: read lines from command
    description:
      - Run one or more commands and split the output into lines, returning them as a list
    options:
      _terms:
        description: command(s) to run
        required: True
    notes:
      - The given commands are passed to a shell for execution, therefore all variables that are part of the commands and
        come from a remote/untrusted source MUST be sanitized using the P(ansible.builtin.quote#filter) filter to avoid
        shell injection vulnerabilities. See the example section.
      - Like all lookups, this runs on the Ansible controller and is unaffected by other keywords such as 'become'.
        If you need to use different permissions, you must change the command or run Ansible as another user.
      - Alternatively, you can use a shell/command task that runs against localhost and registers the result.
      - The directory of the play is used as the current working directory.
"""

EXAMPLES = """
- name: We could read the file directly, but this shows output from command
  ansible.builtin.debug: msg="{{ item }} is an output line from running cat on /etc/motd"
  with_lines: cat /etc/motd

- name: Always use quote filter to make sure your variables are safe to use with shell
  ansible.builtin.debug: msg="{{ item }} is an output line from running given command"
  with_lines: "cat {{ file_name | quote }}"

- name: More useful example of looping over a command result
  ansible.builtin.shell: "/usr/bin/frobnicate {{ item }}"
  with_lines:
    - "/usr/bin/frobnications_per_host --param {{ inventory_hostname }}"
"""

RETURN = """
  _list:
    description:
      - lines of stdout from command
    type: list
    elements: str
"""

import subprocess
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.common.text.converters import to_text


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = []
        for term in terms:
            p = subprocess.Popen(term, cwd=self._loader.get_basedir(), shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            (stdout, stderr) = p.communicate()
            if p.returncode == 0:
                ret.extend([to_text(l) for l in stdout.splitlines()])
            else:
                raise AnsibleError("lookup_plugin.lines(%s) returned %d" % (term, p.returncode))
        return ret
