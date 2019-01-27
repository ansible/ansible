# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: waapm
    version_added: "2.4"
    short_description: get secrets from WALLIX Bastion
    requirements:
      - WALLIX Application-to-Application (waapm) installed
    description:
      - Get a password or a ssh key from WALLIX Password Manager.
        A WAAPM seal operation should have been made on the system before.
"""

EXAMPLES = """
  - name: passing options to the lookup
    debug: msg={{ lookup('waapm', account='root@local@linux', bastion=bastion_alias)}}
"""

RETURN = """
  password:
    description:
      - The actual value stored
"""

import os
import subprocess
from subprocess import PIPE
from subprocess import Popen

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.parsing.splitter import parse_kv
from ansible.module_utils._text import to_text
from ansible.utils.display import Display

display = Display()

WAAPM_CMD = os.getenv('WAAPM_CMD', 'waapm')


class WAAPM:

    def __init__(self, account=None, **kwargs):

        self.account = account
        self.params = []
        for key, value in kwargs.items():
            if len(key) > 1:
                self.params.append("--%s" % key.lower())
            else:
                self.params.append("-%s" % key)
            if value:
                self.params.append("%s" % value)

    def get(self):

        result = []

        try:
            params = [WAAPM_CMD, 'checkout']
            params.extend(self.params)
            params.append(self.account)
            display.debug(' '.join(params))

            secret, error = Popen(params, stdout=PIPE, stderr=PIPE, stdin=PIPE).communicate()

            if error:
                raise AnsibleError("waapm => %s " % (error))

            if secret and secret.endswith(b'\n'):
                secret = secret[:-1]

            result.append(secret)

        except subprocess.CalledProcessError as e:
            raise AnsibleError(e.output)
        except OSError as e:
            raise AnsibleError("waapm => %s (%d) " % (e.strerror, e.errno))

        return result


class LookupModule(LookupBase):

    """
    USAGE:

    """

    def run(self, terms, variables=None, **kwargs):

        if isinstance(terms, list):
            return_values = []
            for term in terms:
                waapm = WAAPM(account=term, **kwargs)
                return_values.append(waapm.get())
            return return_values
        else:
            waapm = WAAPM(account=terms, **kwargs)
            return waapm.get()

