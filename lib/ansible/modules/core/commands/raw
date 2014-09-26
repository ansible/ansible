# this is a virtual module that is entirely implemented server side

DOCUMENTATION = '''
---
module: raw
version_added: historical
short_description: Executes a low-down and dirty SSH command
options:
  free_form:
    description:
      - the raw module takes a free form command to run
    required: true
  executable:
    description:
      - change the shell used to execute the command. Should be an absolute path to the executable.
    required: false
    version_added: "1.0"
description: 
     - Executes a low-down and dirty SSH command, not going through the module
       subsystem. This is useful and should only be done in two cases. The
       first case is installing C(python-simplejson) on older (Python 2.4 and
       before) hosts that need it as a dependency to run modules, since nearly
       all core modules require it. Another is speaking to any devices such as
       routers that do not have any Python installed. In any other case, using
       the M(shell) or M(command) module is much more appropriate. Arguments
       given to M(raw) are run directly through the configured remote shell.
       Standard output, error output and return code are returned when
       available. There is no change handler support for this module.
     - This module does not require python on the remote system, much like
       the M(script) module.
notes:
   -  If you want to execute a command securely and predictably, it may be
      better to use the M(command) module instead. Best practices when writing
      playbooks will follow the trend of using M(command) unless M(shell) is
      explicitly required. When running ad-hoc commands, use your best
      judgement.
author: Michael DeHaan
'''

EXAMPLES = '''
# Bootstrap a legacy python 2.4 host
- raw: yum -y install python-simplejson
'''
