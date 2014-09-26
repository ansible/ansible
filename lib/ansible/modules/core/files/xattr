#!/usr/bin/python
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

DOCUMENTATION = '''
---
module: xattr
version_added: "1.3"
short_description: set/retrieve extended attributes
description:
     - Manages filesystem user defined extended attributes, requires that they are enabled
       on the target filesystem and that the setfattr/getfattr utilities are present.
options:
  name:
    required: true
    default: None
    aliases: ['path']
    description:
      - The full path of the file/object to get the facts of
  key:
    required: false
    default: None
    description:
      - The name of a specific Extended attribute key to set/retrieve
  value:
    required: false
    default: None
    description:
      - The value to set the named name/key to, it automatically sets the C(state) to 'set'
  state:
    required: false
    default: get
    choices: [ 'read', 'present', 'all', 'keys', 'absent' ]
    description:
      - defines which state you want to do.
        C(read) retrieves the current value for a C(key) (default)
        C(present) sets C(name) to C(value), default if value is set
        C(all) dumps all data
        C(keys) retrieves all keys
        C(absent) deletes the key
  follow:
    required: false
    default: yes
    choices: [ 'yes', 'no' ]
    description:
      - if yes, dereferences symlinks and sets/gets attributes on symlink target,
        otherwise acts on symlink itself.

author: Brian Coca
'''

EXAMPLES = '''
# Obtain the extended attributes  of /etc/foo.conf
- xattr: name=/etc/foo.conf

# Sets the key 'foo' to value 'bar'
- xattr: path=/etc/foo.conf key=user.foo value=bar

# Removes the key 'foo'
- xattr: name=/etc/foo.conf key=user.foo state=absent
'''

import operator

def get_xattr_keys(module,path,follow):
    cmd = [ module.get_bin_path('getfattr', True) ]
    # prevents warning and not sure why it's not default
    cmd.append('--absolute-names')
    if not follow:
        cmd.append('-h')
    cmd.append(path)

    return _run_xattr(module,cmd)

def get_xattr(module,path,key,follow):

    cmd = [ module.get_bin_path('getfattr', True) ]
    # prevents warning and not sure why it's not default
    cmd.append('--absolute-names')
    if not follow:
        cmd.append('-h')
    if key is None:
        cmd.append('-d')
    else:
        cmd.append('-n %s' % key)
    cmd.append(path)

    return _run_xattr(module,cmd,False)

def set_xattr(module,path,key,value,follow):

    cmd = [ module.get_bin_path('setfattr', True) ]
    if not follow:
        cmd.append('-h')
    cmd.append('-n %s' % key)
    cmd.append('-v %s' % value)
    cmd.append(path)

    return _run_xattr(module,cmd)

def rm_xattr(module,path,key,follow):

    cmd = [ module.get_bin_path('setfattr', True) ]
    if not follow:
        cmd.append('-h')
    cmd.append('-x %s' % key)
    cmd.append(path)

    return _run_xattr(module,cmd,False)

def _run_xattr(module,cmd,check_rc=True):

    try:
        (rc, out, err) = module.run_command(' '.join(cmd), check_rc=check_rc)
    except Exception, e:
        module.fail_json(msg="%s!" % e.strerror)

    #result = {'raw': out}
    result = {}
    for line in out.splitlines():
        if re.match("^#", line) or line == "":
            pass
        elif re.search('=', line):
            (key, val) = line.split("=")
            result[key] = val.strip('"')
        else:
            result[line] = ''
    return result

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True, aliases=['path']),
            key = dict(required=False, default=None),
            value = dict(required=False, default=None),
            state = dict(required=False, default='read', choices=[ 'read', 'present', 'all', 'keys', 'absent' ], type='str'),
            follow = dict(required=False, type='bool', default=True),
        ),
        supports_check_mode=True,
    )
    path = module.params.get('name')
    key = module.params.get('key')
    value = module.params.get('value')
    state = module.params.get('state')
    follow = module.params.get('follow')

    if not os.path.exists(path):
        module.fail_json(msg="path not found or not accessible!")


    changed=False
    msg = ""
    res = {}

    if key is None and state in ['present','absent']:
        module.fail_json(msg="%s needs a key parameter" % state)

    # All xattr must begin in user namespace
    if key is not None and not re.match('^user\.',key):
        key = 'user.%s' % key


    if (state == 'present' or value is not None):
        current=get_xattr(module,path,key,follow)
        if current is None or not key in current or value != current[key]:
            if not module.check_mode:
                res = set_xattr(module,path,key,value,follow)
            changed=True
        res=current
        msg="%s set to %s" % (key, value)
    elif state == 'absent':
        current=get_xattr(module,path,key,follow)
        if current is not None and key in current:
            if not module.check_mode:
                res = rm_xattr(module,path,key,follow)
            changed=True
        res=current
        msg="%s removed" % (key)
    elif state == 'keys':
        res=get_xattr_keys(module,path,follow)
        msg="returning all keys"
    elif state == 'all':
        res=get_xattr(module,path,None,follow)
        msg="dumping all"
    else:
        res=get_xattr(module,path,key,follow)
        msg="returning %s" % key

    module.exit_json(changed=changed, msg=msg, xattr=res)

# import module snippets
from ansible.module_utils.basic import *

main()
