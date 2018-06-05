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


from ansible.plugins.lookup import LookupBase

try:
    from __main__ import display
    import subprocess
    from ansible.errors import AnsibleError
    from ansible.module_utils._text import to_text
    import epdb
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def run_command(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read()
    return to_text(result)


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        display.vvv("got your argument "+str(terms))
        
        command = None
        # if no argument passed, show whole process table
        if len(terms)is 0:
            command = "ps aux"
        # if get an argument, search it in the process table
        elif len(terms) is 1:
            command = "ps aux|grep " + str(terms[0])
        # other condition, raise exception
        else:
            raise AnsibleError("Argument Fault: 1 string argument expect, {0} got.".format(len(terms))) 

        display.vvv(command)
        # run command and get result
        result = run_command(command)
        display.vvv(result)
        return [result]
