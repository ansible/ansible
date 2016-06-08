#!/usr/bin/python

# (c) 2016, Dag Wieers <dag@wieers.com>
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

DOCUMENTATION = '''
---
module: sefcontext
short_description: Manages SELinux file context mapping definitions
description:
     - Manages SELinux file context mapping definitions
     - Similar to the C(semanage fcontext) command
version_added: "2.2"
options:
  target:
    description:
      - Target path (expression).
    required: true
    default: null
    aliases: ['path']
  ftype:
    description:
      - File type.
    required: false
    default: a
  setype:
    description:
      - SELinux type for the specified target.
    required: true
    default: null
  seuser:
    description:
      - SELinux user for the specified target.
    required: false
    default: null
  selevel:
    description:
      - SELinux range for the specified target.
    required: false
    default: null
    aliases: ['serange']
  state:
    description:
      - Desired boolean value.
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  reload:
    description:
      - Reload SELinux policy after commit.
    required: false
    default: yes
notes:
   - The changes are persistent across reboots
requirements: [ 'libselinux-python', 'policycoreutils-python' ]
author: Dag Wieers
'''

EXAMPLES = '''
# Allow apache to modify files in /srv/git_repos
- sefcontext: target='/srv/git_repos(/.*)?' setype=httpd_git_rw_content_t state=present
'''

RETURN = '''
# Default return values
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception

try:
    import selinux
    HAVE_SELINUX=True
except ImportError:
    HAVE_SELINUX=False

try:
    import seobject
    HAVE_SEOBJECT=True
except ImportError:
    HAVE_SEOBJECT=False

### Make backward compatible
option_to_file_type_str = {
    'a': 'all files',
    'b': 'block device',
    'c': 'character device',
    'd': 'directory',
    'f': 'regular file',
    'l': 'symbolic link',
    's': 'socket file',
    'p': 'named pipe',
}

def semanage_fcontext_exists(sefcontext, target, ftype):
    ''' Get the SELinux file context mapping definition from policy. Return None if it does not exist. '''
    record = (target, ftype)
    records = sefcontext.get_all()
    try:
        return records[record]
    except KeyError:
        return None

def semanage_fcontext_modify(module, result, target, ftype, setype, do_reload, serange, seuser, sestore=''):
    ''' Add or modify SELinux file context mapping definition to the policy. '''

    changed = False
    prepared_diff = ''

    try:
        sefcontext = seobject.fcontextRecords(sestore)
        sefcontext.set_reload(do_reload)
        exists = semanage_fcontext_exists(sefcontext, target, ftype)
        if exists:
            # Modify existing entry
            orig_seuser, orig_serole, orig_setype, orig_serange = exists

            if seuser is None:
                seuser = orig_seuser
            if serange is None:
                serange = orig_serange

            if setype != orig_setype or seuser != orig_seuser or serange != orig_serange:
                if not module.check_mode:
                    sefcontext.modify(target, setype, ftype, serange, seuser)
                changed = True

                if module._diff:
                    prepared_diff += '# Change to semanage file context mappings\n'
                    prepared_diff += '-%s      %s      %s:%s:%s:%s\n' % (target, ftype, orig_seuser, orig_serole, orig_setype, orig_serange)
                    prepared_diff += '+%s      %s      %s:%s:%s:%s\n' % (target, ftype, seuser, orig_serole, setype, serange)
        else:
            # Add missing entry
            if seuser is None:
                seuser = 'system_u'
            if serange is None:
                serange = 's0'

            if not module.check_mode:
                sefcontext.add(target, setype, ftype, serange, seuser)
            changed = True

            if module._diff:
                prepared_diff += '# Addition to semanage file context mappings\n'
                prepared_diff += '+%s      %s      %s:%s:%s:%s\n' % (target, ftype, seuser, 'object_r', setype, serange)

    except Exception:
        e = get_exception()
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, str(e)))

    if module._diff and prepared_diff:
        result['diff'] = dict(prepared=prepared_diff)

    module.exit_json(changed=changed, seuser=seuser, serange=serange, **result)

def semanage_fcontext_delete(module, result, target, ftype, do_reload, sestore=''):
    ''' Delete SELinux file context mapping definition from the policy. '''

    changed = False
    prepared_diff = ''

    try:
        sefcontext = seobject.fcontextRecords(sestore)
        sefcontext.set_reload(do_reload)
        exists = semanage_fcontext_exists(sefcontext, target, ftype)
        if exists:
            # Remove existing entry
            orig_seuser, orig_serole, orig_setype, orig_serange = exists

            if not module.check_mode:
                sefcontext.delete(target, ftype)
            changed = True

            if module._diff:
                prepared_diff += '# Deletion to semanage file context mappings\n'
                prepared_diff += '-%s      %s      %s:%s:%s:%s\n' % (target, ftype, exists[0], exists[1], exists[2], exists[3])

    except Exception:
        e = get_exception()
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, str(e)))

    if module._diff and prepared_diff:
        result['diff'] = dict(prepared=prepared_diff)

    module.exit_json(changed=changed, **result)


def main():
    module = AnsibleModule(
        argument_spec = dict(
                target  = dict(required=True, aliases=['path']),
                ftype   = dict(required=False, choices=option_to_file_type_str.keys(), default='a'),
                setype  = dict(required=True),
                seuser  = dict(required=False, default=None),
                selevel = dict(required=False, default=None, aliases=['serange']),
                state   = dict(required=False, choices=['present', 'absent'], default='present'),
                reload  = dict(required=False, type='bool', default='yes'),
            ),
        supports_check_mode = True,
    )
    if not HAVE_SELINUX:
        module.fail_json(msg="This module requires libselinux-python")

    if not HAVE_SEOBJECT:
        module.fail_json(msg="This module requires policycoreutils-python")

    if not selinux.is_selinux_enabled():
        module.fail_json(msg="SELinux is disabled on this host.")

    target = module.params['target']
    ftype = module.params['ftype']
    setype = module.params['setype']
    seuser = module.params['seuser']
    serange = module.params['selevel']
    state = module.params['state']
    do_reload = module.params['reload']

    result = dict(target=target, ftype=ftype, setype=setype, state=state)

    # Convert file types to (internally used) strings
    ftype = option_to_file_type_str[ftype]

    if state == 'present':
        semanage_fcontext_modify(module, result, target, ftype, setype, do_reload, serange, seuser)
    elif state == 'absent':
        semanage_fcontext_delete(module, result, target, ftype, do_reload)
    else:
        module.fail_json(msg='Invalid value of argument "state": {0}'.format(state))


if __name__ == '__main__':
    main()