# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: pipe
    author: Daniel Hokka Zakrisson <daniel@hozac.com>
    version_added: "0.9"
    short_description: read output from a command
    description:
      - Run a command and return the output
    options:
      _terms:
        description: command(s) to run
        required: True
    notes:
      - Like all lookups this runs on the Ansible controller and is unaffected by other keywords, such as become,
        so if you need to different permissions you must change the command or run Ansible as another user.
      - Alternatively you can use a shell/command task that runs against localhost and registers the result.
"""

EXAMPLES = """
- name: raw result of running date command"
  debug: msg="{{ lookup('pipe','date') }}"

- name: Always use quote filter to make sure your variables are safe to use with shell
  debug: msg="{{ lookup('pipe','getent ' + myuser|quote ) }}"
"""

RETURN = """
  _string:
    description:
      - stdout from command
"""

import subprocess

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        ret = []
        for term in terms:
            '''
            http://docs.python.org/2/library/subprocess.html#popen-constructor

            The shell argument (which defaults to False) specifies whether to use the
            shell as the program to execute. If shell is True, it is recommended to pass
            args as a string rather than as a sequence

            https://github.com/ansible/ansible/issues/6550
            '''
            term = str(term)

            p = subprocess.Popen(term, cwd=self._loader.get_basedir(), shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            (stdout, stderr) = p.communicate()
            if p.returncode == 0:
                ret.append(stdout.decode("utf-8").rstrip())
            else:
                raise AnsibleError("lookup_plugin.pipe(%s) returned %d" % (term, p.returncode))
        return ret
