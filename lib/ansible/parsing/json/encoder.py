# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import datetime
import json

from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from ansible.vars.hostvars import HostVars, HostVarsVars


class AnsibleJSONEncoder(json.JSONEncoder):
    '''
    Simple encoder class to deal with JSON encoding of internal types
    '''
    def default(self, o):
        if isinstance(o, (HostVars, HostVarsVars)):
            return dict(o)
        elif isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        elif isinstance(o, AnsibleVaultEncryptedUnicode):
            return o.data
        else:
            return super(AnsibleJSONEncoder, self).default(o)
