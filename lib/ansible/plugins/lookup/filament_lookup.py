from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
   lookup: filament
    author: zhikang zhang <zhikzhan@redhat.com>
    version_added: "2.6"
    short_description: show process table
    description:
        - This lookup returns process table on the Ansible controller's operation system.
    options:
      _terms:
        description: the process you want to find
        required: None
"""

EXAMPLES = """
  result: "{{lookup('filament_lookup')}}"
  tasks:
  - debug:
    msg: "result is {{result}}"
"""

RETURN = """
content of process table
"""

import subprocess
import epdb

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text
from ansible.module_utils import six

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def run_command(terms):
    command = "ps aux"
    if terms is not None:
        command = "%s|grep %s" % (command, str(terms[0]))
    display.vvv(command)

    try:
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result = p.stdout.read()
    except OSError as os_err:
        six.raise_from(AnsibleError("Failed to fetch processes."), os_err)
    except ISError as io_err:
        six.raise_from(AnsibleError("Failed to read subprocess output."), io_err)
    return to_text(result)


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        display.vvv("got your argument " + str(terms))
        # validate and process arguments
        if len(terms) >= 2:
            raise AnsibleError("Argument Fault: 1 argument expected, %d got." % (len(terms)))
        if len(terms) == 0:
            terms = None
        # run command and get result
        result = run_command(terms)
        display.vvv(result)
        return [result]
