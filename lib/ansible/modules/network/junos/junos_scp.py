#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: junos_scp
version_added: "2.5"
author: "Christian Giese (@GIC-de)"
short_description: Transfer files from or to remote devices running Junos
description:
  - This module transfers files via SCP from or to remote devices
    running Junos.
extends_documentation_fragment: junos
options:
  src:
    description:
      - The C(src) argument takes a single path, or a list of paths to be
        transferred. The argument C(recursive) must be C(true) to transfer
        directories.
    required: true
  dest:
    description:
      - The C(dest) argument specifies the path in which to receive the files.
    default: '.'
  recursive:
    description:
      - The C(recursive) argument enables recursive transfer of files and
        directories.
    type: bool
    default: 'no'
  remote_src:
    description:
      - The C(remote_src) argument enables the download of files (I(scp get)) from
        the remote device. The default behavior is to upload files (I(scp put))
        to the remote device.
    type: bool
    default: 'no'
requirements:
  - junos-eznc
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - Tested against vMX JUNOS version 17.3R1.10.
  - Works with C(local) connections only.
"""

EXAMPLES = """
# the required set of connection arguments have been purposely left off
# the examples for brevity
- name: upload local file to home directory on remote device
  junos_scp:
    src: test.tgz

- name: upload local file to tmp directory on remote device
  junos_scp:
    src: test.tgz
    dest: /tmp/

- name: download file from remote device
  junos_scp:
    src: test.tgz
    remote_src: true
"""

RETURN = """
changed:
  description: always true
  returned: always
  type: bool
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.junos.junos import junos_argument_spec, get_param
from ansible.module_utils._text import to_native

try:
    from jnpr.junos import Device
    from jnpr.junos.utils.scp import SCP
    from jnpr.junos.exception import ConnectError
    HAS_PYEZ = True
except ImportError:
    HAS_PYEZ = False


def connect(module):
    host = get_param(module, 'host')

    kwargs = {
        'port': get_param(module, 'port') or 830,
        'user': get_param(module, 'username')
    }

    if get_param(module, 'password'):
        kwargs['passwd'] = get_param(module, 'password')

    if get_param(module, 'ssh_keyfile'):
        kwargs['ssh_private_key_file'] = get_param(module, 'ssh_keyfile')

    kwargs['gather_facts'] = False

    try:
        device = Device(host, **kwargs)
        device.open()
        device.timeout = get_param(module, 'timeout') or 10
    except ConnectError as exc:
        module.fail_json('unable to connect to %s: %s' % (host, to_native(exc)))

    return device


def transfer_files(module, device):
    dest = module.params['dest']
    recursive = module.params['recursive']

    with SCP(device) as scp:
        for src in module.params['src']:
            if module.params['remote_src']:
                scp.get(src.strip(), local_path=dest, recursive=recursive)
            else:
                scp.put(src.strip(), remote_path=dest, recursive=recursive)


def main():
    """ Main entry point for Ansible module execution
    """
    argument_spec = dict(
        src=dict(type='list', required=True),
        dest=dict(type='path', required=False, default="."),
        recursive=dict(type='bool', default=False),
        remote_src=dict(type='bool', default=False),
        transport=dict(default='netconf', choices=['netconf'])
    )

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if module.params['provider'] is None:
        module.params['provider'] = {}

    if not HAS_PYEZ:
        module.fail_json(
            msg='junos-eznc is required but does not appear to be installed. '
                'It can be installed using `pip install junos-eznc`'
        )

    result = dict(changed=True)

    if not module.check_mode:
        # open pyez connection and transfer files via SCP
        try:
            device = connect(module)
            transfer_files(module, device)
        except Exception as ex:
            module.fail_json(
                msg=to_native(ex)
            )
        finally:
            try:
                # close pyez connection and ignore exceptions
                device.close()
            except Exception:
                pass

    module.exit_json(**result)


if __name__ == '__main__':
    main()
