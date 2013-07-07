# (c) 2012, Jeroen Hoekx <jeroen@hoekx.be>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import base64
import json
import os.path
import yaml
import types
from ansible import errors

def to_nice_yaml(*a, **kw):
    '''Make verbose, human readable yaml'''
    return yaml.safe_dump(*a, indent=4, allow_unicode=True, default_flow_style=False, **kw)

def to_nice_json(*a, **kw):
    '''Make verbose, human readable JSON'''
    return json.dumps(*a, indent=4, sort_keys=True, **kw)

def failed(*a, **kw):
    item = a[0] 
    if type(item) != dict:
        raise errors.AnsibleError("|failed expects a dictionary")
    rc = item.get('rc',0)
    failed = item.get('failed',False)
    if rc != 0 or failed:
        return True
    else:
        return False

def success(*a, **kw):
    return not failed(*a, **kw)

def skipped(*a, **kw):
    item = a[0]
    if type(item) != dict:
        raise errors.AnsibleError("|skipped expects a dictionary")
    skipped = item.get('skipped', False)
    return skipped

def mandatory(a):
    ''' Make a variable mandatory '''
    if not a:
        raise errors.AnsibleError('Mandatory variable not defined.')
    return a

def bool(a):
    ''' return a bool for the arg '''
    if a is None or type(a) == bool:
        return a
    if type(a) in types.StringTypes:
        a = a.lower()
    if a in ['yes', 'on', '1', 'true', 1]:
        return True
    else:
        return False

class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            # base 64
            'b64decode': base64.b64decode,
            'b64encode': base64.b64encode,

            # json
            'to_json': json.dumps,
            'to_nice_json': to_nice_json,
            'from_json': json.loads,

            # yaml
            'to_yaml': yaml.safe_dump,
            'to_nice_yaml': to_nice_yaml,
            'from_yaml': yaml.safe_load,

            # path
            'basename': os.path.basename,
            'dirname': os.path.dirname,

            # failure testing
            'failed'  : failed,
            'success' : success,

            # skip testing
            'skipped' : skipped,

            # variable existence
            'mandatory': mandatory,

            # value as boolean
            'bool': bool,
        }
    
