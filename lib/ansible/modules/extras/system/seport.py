#!/usr/bin/python

# (c) 2014, Dan Keder <dan.keder@gmail.com>
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
module: seport
short_description: Manages SELinux network port type definitions
description:
     - Manages SELinux network port type definitions.
version_added: "1.7.1"
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
- seport: ports=8888 proto=tcp setype=http_port_t state=present
# Allow sshd to listen on tcp port 8991
- seport: ports=8991 proto=tcp setype=ssh_port_t state=present
# Allow memcached to listen on tcp ports 10000-10100 and 10112
- seport: ports=10000-10100,10112 proto=tcp setype=memcache_port_t state=present
'''

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


def semanage_port_exists(seport, port, proto):
    """ Get the SELinux port type definition from policy. Return None if it does
    not exist.

    :param seport: Instance of seobject.portRecords

    :type port: str
    :param port: Port or port range (example: "8080", "8080-9090")

    :type proto: str
    :param proto: Protocol ('tcp' or 'udp')

    :rtype: bool
    :return: True if the SELinux port type definition exists, False otherwise
    """
    ports = port.split('-', 1)
    if len(ports) == 1:
        ports.extend(ports)
    ports = map(int, ports)
    record = (ports[0], ports[1], proto)
    return record in seport.get_all()


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
        for port in ports:
            exists = semanage_port_exists(seport, port, proto)
            if not exists and not module.check_mode:
                seport.add(port, proto, serange, setype)
            change = change or not exists

    except ValueError, e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, str(e)))
    except IOError, e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, str(e)))
    except KeyError, e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, str(e)))
    except OSError, e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, str(e)))
    except RuntimeError, e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, str(e)))

    return change


def semanage_port_del(module, ports, proto, do_reload, sestore=''):
    """ Delete SELinux port type definition from the policy.

    :type module: AnsibleModule
    :param module: Ansible module

    :type ports: list
    :param ports: List of ports and port ranges to delete (e.g. ["8080", "8080-9090"])

    :type proto: str
    :param proto: Protocol ('tcp' or 'udp')

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
        for port in ports:
            exists = semanage_port_exists(seport, port, proto)
            if not exists and not module.check_mode:
                seport.delete(port, proto)
            change = change or not exists

    except ValueError, e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, str(e)))
    except IOError,e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, str(e)))
    except KeyError, e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, str(e)))
    except OSError, e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, str(e)))
    except RuntimeError, e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, str(e)))

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

    ports = [x.strip() for x in module.params['ports'].split(',')]
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
        result['changed'] = semanage_port_del(module, ports, proto, do_reload)
    else:
        module.fail_json(msg='Invalid value of argument "state": {0}'.format(state))

    module.exit_json(**result)


from ansible.module_utils.basic import *
main()
