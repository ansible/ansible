from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: filament_lookup
    author: Ansible core team
    version_added: "2.7"
    short_description: reuturn output of process table.
    description:
      - If recieved no arguments, return the whole process table. If recieved arguments, search the process tale with the argument as a process name.
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

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def run_command(terms):
    command = "ps aux"
    # if no argument passed, show whole process table
    if len(terms) == 0:
        pass
    # if get an argument, search it in the process table
    elif len(terms) == 1:
        command = "%s|grep %s" % (command, str(terms[0]))
    # other condition, raise exception
    else:
        raise AnsibleError("Argument Fault: 1 string argument expect, {0} got.".format(len(terms)))
    display.vvv(command)

    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read()
    return to_text(result)


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        display.vvv("got your argument " + str(terms))
        # run command and get result
        result = run_command(terms)
        display.vvv(result)
        return [result]
