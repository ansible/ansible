# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
    name: pipe
    author: Daniel Hokka Zakrisson (!UNKNOWN) <daniel@hozac.com>
    version_added: "0.9"
    short_description: read output from a command
    description:
      - Run a command and return the output.
    options:
      _terms:
        description: command(s) to run.
        required: True
    notes:
      - The given command is passed to a shell for execution, therefore all variables that are part of the command and
        come from a remote/untrusted source MUST be sanitized using the P(ansible.builtin.quote#filter) filter to avoid
        shell injection vulnerabilities. See the example section.
      - Like all lookups this runs on the Ansible controller and is unaffected by other keywords, such as become,
        so if you need to different permissions you must change the command or run Ansible as another user.
      - Alternatively you can use a shell/command task that runs against localhost and registers the result.
      - The directory of the play is used as the current working directory.
"""

EXAMPLES = r"""
- name: raw result of running date command
  ansible.builtin.debug:
    msg: "{{ lookup('ansible.builtin.pipe', 'date') }}"

- name: Always use quote filter to make sure your variables are safe to use with shell
  ansible.builtin.debug:
    msg: "{{ lookup('ansible.builtin.pipe', 'getent passwd ' + myuser | quote ) }}"
"""

RETURN = r"""
  _string:
    description:
      - stdout from command
    type: list
    elements: str
"""

import subprocess

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = []
        for term in terms:
            # https://docs.python.org/3/library/subprocess.html#popen-constructor
            #
            # The shell argument (which defaults to False) specifies whether to use the
            # shell as the program to execute. If shell is True, it is recommended to pass
            # args as a string rather than as a sequence
            #
            # https://github.com/ansible/ansible/issues/6550
            term = str(term)

            p = subprocess.Popen(term, cwd=self._templar.basedir, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            (stdout, stderr) = p.communicate()
            if p.returncode == 0:
                ret.append(stdout.decode("utf-8").rstrip())
            else:
                raise AnsibleError("lookup_plugin.pipe(%s) returned %d" % (term, p.returncode))
        return ret
