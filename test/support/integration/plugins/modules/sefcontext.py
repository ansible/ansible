#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: sefcontext
short_description: Manages SELinux file context mapping definitions
description:
- Manages SELinux file context mapping definitions.
- Similar to the C(semanage fcontext) command.
version_added: '2.2'
options:
  target:
    description:
    - Target path (expression).
    type: str
    required: yes
    aliases: [ path ]
  ftype:
    description:
    - The file type that should have SELinux contexts applied.
    - "The following file type options are available:"
    - C(a) for all files,
    - C(b) for block devices,
    - C(c) for character devices,
    - C(d) for directories,
    - C(f) for regular files,
    - C(l) for symbolic links,
    - C(p) for named pipes,
    - C(s) for socket files.
    type: str
    choices: [ a, b, c, d, f, l, p, s ]
    default: a
  setype:
    description:
    - SELinux type for the specified target.
    type: str
    required: yes
  seuser:
    description:
    - SELinux user for the specified target.
    type: str
  selevel:
    description:
    - SELinux range for the specified target.
    type: str
    aliases: [ serange ]
  state:
    description:
    - Whether the SELinux file context must be C(absent) or C(present).
    type: str
    choices: [ absent, present ]
    default: present
  reload:
    description:
    - Reload SELinux policy after commit.
    - Note that this does not apply SELinux file contexts to existing files.
    type: bool
    default: yes
  ignore_selinux_state:
    description:
    - Useful for scenarios (chrooted environment) that you can't get the real SELinux state.
    type: bool
    default: no
    version_added: '2.8'
notes:
- The changes are persistent across reboots.
- The M(sefcontext) module does not modify existing files to the new
  SELinux context(s), so it is advisable to first create the SELinux
  file contexts before creating files, or run C(restorecon) manually
  for the existing files that require the new SELinux file contexts.
- Not applying SELinux fcontexts to existing files is a deliberate
  decision as it would be unclear what reported changes would entail
  to, and there's no guarantee that applying SELinux fcontext does
  not pick up other unrelated prior changes.
requirements:
- libselinux-python
- policycoreutils-python
author:
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Allow apache to modify files in /srv/git_repos
  sefcontext:
    target: '/srv/git_repos(/.*)?'
    setype: httpd_git_rw_content_t
    state: present

- name: Apply new SELinux file context to filesystem
  command: restorecon -irv /srv/git_repos
'''

RETURN = r'''
# Default return values
'''

import os
import subprocess
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.common.respawn import has_respawned, probe_interpreters_for_module, respawn_module
from ansible.module_utils._text import to_native

SELINUX_IMP_ERR = None
try:
    import selinux
    HAVE_SELINUX = True
except ImportError:
    SELINUX_IMP_ERR = traceback.format_exc()
    HAVE_SELINUX = False

SEOBJECT_IMP_ERR = None
try:
    import seobject
    HAVE_SEOBJECT = True
except ImportError:
    SEOBJECT_IMP_ERR = traceback.format_exc()
    HAVE_SEOBJECT = False

# Add missing entries (backward compatible)
if HAVE_SEOBJECT:
    seobject.file_types.update(
        a=seobject.SEMANAGE_FCONTEXT_ALL,
        b=seobject.SEMANAGE_FCONTEXT_BLOCK,
        c=seobject.SEMANAGE_FCONTEXT_CHAR,
        d=seobject.SEMANAGE_FCONTEXT_DIR,
        f=seobject.SEMANAGE_FCONTEXT_REG,
        l=seobject.SEMANAGE_FCONTEXT_LINK,
        p=seobject.SEMANAGE_FCONTEXT_PIPE,
        s=seobject.SEMANAGE_FCONTEXT_SOCK,
    )

# Make backward compatible
option_to_file_type_str = dict(
    a='all files',
    b='block device',
    c='character device',
    d='directory',
    f='regular file',
    l='symbolic link',
    p='named pipe',
    s='socket',
)


def get_runtime_status(ignore_selinux_state=False):
    return True if ignore_selinux_state is True else selinux.is_selinux_enabled()


def semanage_fcontext_exists(sefcontext, target, ftype):
    ''' Get the SELinux file context mapping definition from policy. Return None if it does not exist. '''

    # Beware that records comprise of a string representation of the file_type
    record = (target, option_to_file_type_str[ftype])
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

    except Exception as e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, to_native(e)))

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

    except Exception as e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, to_native(e)))

    if module._diff and prepared_diff:
        result['diff'] = dict(prepared=prepared_diff)

    module.exit_json(changed=changed, **result)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ignore_selinux_state=dict(type='bool', default=False),
            target=dict(type='str', required=True, aliases=['path']),
            ftype=dict(type='str', default='a', choices=option_to_file_type_str.keys()),
            setype=dict(type='str', required=True),
            seuser=dict(type='str'),
            selevel=dict(type='str', aliases=['serange']),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            reload=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
    )

    if not HAVE_SELINUX or not HAVE_SEOBJECT and not has_respawned():
        system_interpreters = [
            '/usr/libexec/platform-python',
            '/usr/bin/python3',
            '/usr/bin/python2',
        ]
        # policycoreutils-python depends on libselinux-python
        interpreter = probe_interpreters_for_module(system_interpreters, 'seobject')
        if interpreter:
            respawn_module(interpreter)

    if not HAVE_SELINUX or not HAVE_SEOBJECT:
        module.fail_json(msg=missing_required_lib("policycoreutils-python(3)"), exception=SELINUX_IMP_ERR)

    ignore_selinux_state = module.params['ignore_selinux_state']

    if not get_runtime_status(ignore_selinux_state):
        module.fail_json(msg="SELinux is disabled on this host.")

    target = module.params['target']
    ftype = module.params['ftype']
    setype = module.params['setype']
    seuser = module.params['seuser']
    serange = module.params['selevel']
    state = module.params['state']
    do_reload = module.params['reload']

    result = dict(target=target, ftype=ftype, setype=setype, state=state)

    if state == 'present':
        semanage_fcontext_modify(module, result, target, ftype, setype, do_reload, serange, seuser)
    elif state == 'absent':
        semanage_fcontext_delete(module, result, target, ftype, do_reload)
    else:
        module.fail_json(msg='Invalid value of argument "state": {0}'.format(state))


if __name__ == '__main__':
    main()
