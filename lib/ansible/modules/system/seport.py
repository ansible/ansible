#!/usr/bin/python

# (c) 2014, Dan Keder <dan.keder@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: seport
short_description: Manages SELinux network port type definitions
description:
     - Manages SELinux network port type definitions.
version_added: "2.0"
options:
  ports:
    description:
      - Ports or port ranges, separated by a comma
    required: true
    default: null
  proto:
    description:
      - Protocol for the specified port.
    required: true
    default: null
    choices: [ 'tcp', 'udp' ]
  setype:
    description:
      - SELinux type for the specified port.
    required: true
    default: null
  state:
    description:
      - Desired boolean value.
    required: true
    default: present
    choices: [ 'present', 'absent' ]
  reload:
    description:
      - Reload SELinux policy after commit.
    required: false
    default: yes
notes:
   - The changes are persistent across reboots
   - Not tested on any debian based system
requirements: [ 'libselinux-python', 'policycoreutils-python' ]
author: Dan Keder
'''

EXAMPLES = '''
# Allow Apache to listen on tcp port 8888
- seport:
    ports: 8888
    proto: tcp
    setype: http_port_t
    state: present

# Allow sshd to listen on tcp port 8991
- seport:
    ports: 8991
    proto: tcp
    setype: ssh_port_t
    state: present

# Allow memcached to listen on tcp ports 10000-10100 and 10112
- seport:
    ports: 10000-10100,10112
    proto: tcp
    setype: memcache_port_t
    state: present
'''

import traceback

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

from ansible.module_utils.basic import AnsibleModule, HAVE_SELINUX
from ansible.module_utils._text import to_native


def semanage_port_get_ports(seport, setype, proto):
    """ Get the list of ports that have the specified type definition.

    :param seport: Instance of seobject.portRecords

    :type setype: str
    :param setype: SELinux type.

    :type proto: str
    :param proto: Protocol ('tcp' or 'udp')

    :rtype: list
    :return: List of ports that have the specified SELinux type.
    """
    records = seport.get_all_by_type()
    if (setype, proto) in records:
        return records[(setype, proto)]
    else:
        return []


def semanage_port_get_type(seport, port, proto):
    """ Get the SELinux type of the specified port.

    :param seport: Instance of seobject.portRecords

    :type port: str
    :param port: Port or port range (example: "8080", "8080-9090")

    :type proto: str
    :param proto: Protocol ('tcp' or 'udp')

    :rtype: tuple
    :return: Tuple containing the SELinux type and MLS/MCS level, or None if not found.
    """
    ports = port.split('-', 1)
    if len(ports) == 1:
        ports.extend(ports)
    key = (int(ports[0]), int(ports[1]), proto)

    records = seport.get_all()
    if key in records:
        return records[key]
    else:
        return None


def semanage_port_add(module, ports, proto, setype, do_reload, serange='s0', sestore=''):
    """ Add SELinux port type definition to the policy.

    :type module: AnsibleModule
    :param module: Ansible module

    :type ports: list
    :param ports: List of ports and port ranges to add (e.g. ["8080", "8080-9090"])

    :type proto: str
    :param proto: Protocol ('tcp' or 'udp')

    :type setype: str
    :param setype: SELinux type

    :type do_reload: bool
    :param do_reload: Whether to reload SELinux policy after commit

    :type serange: str
    :param serange: SELinux MLS/MCS range (defaults to 's0')

    :type sestore: str
    :param sestore: SELinux store

    :rtype: bool
    :return: True if the policy was changed, otherwise False
    """
    try:
        seport = seobject.portRecords(sestore)
        seport.set_reload(do_reload)
        change = False
        ports_by_type = semanage_port_get_ports(seport, setype, proto)
        for port in ports:
            if port not in ports_by_type:
                change = True
                port_type = semanage_port_get_type(seport, port, proto)
                if port_type is None and not module.check_mode:
                    seport.add(port, proto, serange, setype)
                elif port_type is not None and not module.check_mode:
                    seport.modify(port, proto, serange, setype)

    except (ValueError, IOError, KeyError, OSError, RuntimeError) as e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, to_native(e)), exception=traceback.format_exc())

    return change


def semanage_port_del(module, ports, proto, setype, do_reload, sestore=''):
    """ Delete SELinux port type definition from the policy.

    :type module: AnsibleModule
    :param module: Ansible module

    :type ports: list
    :param ports: List of ports and port ranges to delete (e.g. ["8080", "8080-9090"])

    :type proto: str
    :param proto: Protocol ('tcp' or 'udp')

    :type setype: str
    :param setype: SELinux type.

    :type do_reload: bool
    :param do_reload: Whether to reload SELinux policy after commit

    :type sestore: str
    :param sestore: SELinux store

    :rtype: bool
    :return: True if the policy was changed, otherwise False
    """
    try:
        seport = seobject.portRecords(sestore)
        seport.set_reload(do_reload)
        change = False
        ports_by_type = semanage_port_get_ports(seport, setype, proto)
        for port in ports:
            if port in ports_by_type:
                change = True
                if not module.check_mode:
                    seport.delete(port, proto)

    except (ValueError, IOError, KeyError, OSError, RuntimeError) as e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, to_native(e)), exception=traceback.format_exc())

    return change


def main():
    module = AnsibleModule(
        argument_spec={
            'ports': {
                'required': True,
                },
            'proto': {
                'required': True,
                'choices': ['tcp', 'udp'],
                },
            'setype': {
                'required': True,
                },
            'state': {
                'required': True,
                'choices': ['present', 'absent'],
                },
            'reload': {
                'required': False,
                'type': 'bool',
                'default': 'yes',
                },
        },
        supports_check_mode=True
    )
    if not HAVE_SELINUX:
        module.fail_json(msg="This module requires libselinux-python")

    if not HAVE_SEOBJECT:
        module.fail_json(msg="This module requires policycoreutils-python")

    if not selinux.is_selinux_enabled():
        module.fail_json(msg="SELinux is disabled on this host.")

    ports = [x.strip() for x in str(module.params['ports']).split(',')]
    proto = module.params['proto']
    setype = module.params['setype']
    state = module.params['state']
    do_reload = module.params['reload']

    result = {
        'ports': ports,
        'proto': proto,
        'setype': setype,
        'state': state,
    }

    if state == 'present':
        result['changed'] = semanage_port_add(module, ports, proto, setype, do_reload)
    elif state == 'absent':
        result['changed'] = semanage_port_del(module, ports, proto, setype, do_reload)
    else:
        module.fail_json(msg='Invalid value of argument "state": {0}'.format(state))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
