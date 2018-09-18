# (c) 2016, Andrew Zenk <azenk@umn.edu>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: lastpass
    author:
      -  Andrew Zenk <azenk@umn.edu>
    version_added: "2.3"
    requirements:
      - lpass (command line utility)
      - must have already logged into lastpass
    short_description: fetch data from lastpass
    description:
      - use the lpass command line utility to fetch specific fields from lastpass
    options:
      _terms:
        description: key from which you want to retrieve the field
        required: True
      field:
        description: field to return from lastpass
        default: 'password'
"""

EXAMPLES = """
- name: get 'custom_field' from lastpass entry 'entry-name'
  debug:
    msg: "{{ lookup('lastpass', 'entry-name', field='custom_field') }}"
"""

RETURN = """
  _raw:
    description: secrets stored
"""

from subprocess import Popen, PIPE

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LPassException(AnsibleError):
    pass


class LPass(object):

    def __init__(self, path='lpass'):
        self._cli_path = path

    @property
    def cli_path(self):
        return self._cli_path

    @property
    def logged_in(self):
        out, err = self._run(self._build_args("logout"), stdin="n\n", expected_rc=1)
        return err.startswith("Are you sure you would like to log out?")

    def _run(self, args, stdin=None, expected_rc=0):
        p = Popen([self.cli_path] + args, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        out, err = p.communicate(stdin)
        rc = p.wait()
        if rc != expected_rc:
            raise LPassException(err)
        return out, err

    def _build_args(self, command, args=None):
        if args is None:
            args = []
        args = [command] + args
        args += ["--color=never"]
        return args

    def get_field(self, key, field):
        if field in ['username', 'password', 'url', 'notes', 'id', 'name']:
            out, err = self._run(self._build_args("show", ["--{0}".format(field), key]))
        else:
            out, err = self._run(self._build_args("show", ["--field={0}".format(field), key]))
        return out.strip()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        lp = LPass()

        if not lp.logged_in:
            raise AnsibleError("Not logged into lastpass: please run 'lpass login' first")

        field = kwargs.get('field', 'password')
        values = []
        for term in terms:
            values.append(lp.get_field(term, field))
        return values
