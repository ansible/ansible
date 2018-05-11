#!/usr/bin/python

# (c) 2016, Leandro Lisboa Penz <lpenz at lpenz.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: netconf_config
author: "Leandro Lisboa Penz (@lpenz)"
short_description: netconf device configuration
description:
    - Netconf is a network management protocol developed and standardized by
      the IETF. It is documented in RFC 6241.

    - This module allows the user to send a configuration XML file to a netconf
      device, and detects if there was a configuration change.
notes:
    - This module supports devices with and without the candidate and
      confirmed-commit capabilities. It always use the safer feature.
    - This module supports the use of connection=netconf
version_added: "2.2"
options:
  host:
    description:
     - the hostname or ip address of the netconf device
    required: true
  port:
    description:
     - the netconf port
    default: 830
    required: false
  hostkey_verify:
    description:
     - if true, the ssh host key of the device must match a ssh key present on the host
     - if false, the ssh host key of the device is not checked
    default: true
    required: false
  look_for_keys:
    description:
     - if true, enables looking in the usual locations for ssh keys (e.g. ~/.ssh/id_*)
     - if false, disables looking for ssh keys
    default: true
    required: false
    version_added: "2.4"
  allow_agent:
    description:
     - if true, enables querying SSH agent (if found) for keys
     - if false, disables querying the SSH agent for ssh keys
    default: true
    required: false
    version_added: "2.4"
  datastore:
    description:
     - auto, uses candidate and fallback to running
     - candidate, edit <candidate/> datastore and then commit
     - running, edit <running/> datastore directly
    default: auto
    required: false
    version_added: "2.4"
  save:
    description:
      - The C(save) argument instructs the module to save the running-
        config to the startup-config if changed.
    required: false
    default: false
    version_added: "2.4"
  username:
    description:
     - the username to authenticate with
    required: true
  password:
    description:
     - password of the user to authenticate with
    required: true
  xml:
    description:
     - the XML content to send to the device
    required: false
  src:
    description:
      - Specifies the source path to the xml file that contains the configuration
        or configuration template to load.  The path to the source file can
        either be the full path on the Ansible control host or a relative
        path from the playbook or role root directory.  This argument is mutually
        exclusive with I(xml).
    required: false
    version_added: "2.4"


requirements:
  - "python >= 2.6"
  - "ncclient"
'''

EXAMPLES = '''
- name: use lookup filter to provide xml configuration
  netconf_config:
    xml: "{{ lookup('file', './config.xml') }}"
    host: 10.0.0.1
    username: admin
    password: admin

- name: set ntp server in the device
  netconf_config:
    host: 10.0.0.1
    username: admin
    password: admin
    xml: |
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <system xmlns="urn:ietf:params:xml:ns:yang:ietf-system">
                <ntp>
                    <enabled>true</enabled>
                    <server>
                        <name>ntp1</name>
                        <udp><address>127.0.0.1</address></udp>
                    </server>
                </ntp>
            </system>
        </config>

- name: wipe ntp configuration
  netconf_config:
    host: 10.0.0.1
    username: admin
    password: admin
    xml: |
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <system xmlns="urn:ietf:params:xml:ns:yang:ietf-system">
                <ntp>
                    <enabled>false</enabled>
                    <server operation="remove">
                        <name>ntp1</name>
                    </server>
                </ntp>
            </system>
        </config>

'''

RETURN = '''
server_capabilities:
    description: list of capabilities of the server
    returned: success
    type: list
    sample: ['urn:ietf:params:netconf:base:1.1','urn:ietf:params:netconf:capability:confirmed-commit:1.0','urn:ietf:params:netconf:capability:candidate:1.0']

'''

import traceback
import xml.dom.minidom

from xml.etree.ElementTree import fromstring, tostring

try:
    import ncclient.manager
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.connection import Connection, ConnectionError


def netconf_edit_config(m, xml, commit, retkwargs, datastore, capabilities, local_connection):
    m.lock(target=datastore)
    try:
        if datastore == "candidate":
            m.discard_changes()

        config_before = m.get_config(source=datastore)
        m.edit_config(target=datastore, config=xml)
        config_after = m.get_config(source=datastore)

        if local_connection:
            changed = config_before.data_xml != config_after.data_xml
        else:
            changed = config_before != config_after

        if changed and commit and datastore == "candidate":
            if ":confirmed-commit" in capabilities:
                m.commit(confirmed=True)
                m.commit()
            else:
                m.commit()

        return changed
    finally:
        m.unlock(target=datastore)


# ------------------------------------------------------------------- #
# Main


def main():

    module = AnsibleModule(
        argument_spec=dict(
            xml=dict(type='str', required=False),
            src=dict(type='path', required=False),

            datastore=dict(choices=['auto', 'candidate', 'running'], default='auto'),
            save=dict(type='bool', default=False),

            # connection arguments
            host=dict(type='str'),
            port=dict(type='int', default=830),

            username=dict(type='str', no_log=True),
            password=dict(type='str', no_log=True),

            hostkey_verify=dict(type='bool', default=True),
            look_for_keys=dict(type='bool', default=True),

            allow_agent=dict(type='bool', default=True),
        ),
        mutually_exclusive=[('xml', 'src')]
    )

    if not module._socket_path and not HAS_NCCLIENT:
        module.fail_json(msg='could not import the python library '
                         'ncclient required by this module')

    if (module.params['src']):
        config_xml = str(module.params['src'])
    elif module.params['xml']:
        config_xml = str(module.params['xml'])
    else:
        module.fail_json(msg='Option src or xml must be provided')

    local_connection = module._socket_path is None

    if not local_connection:
        m = Connection(module._socket_path)
        capabilities = module.from_json(m.get_capabilities())
        server_capabilities = capabilities.get('server_capabilities')

    else:
        nckwargs = dict(
            host=module.params['host'],
            port=module.params['port'],
            hostkey_verify=module.params['hostkey_verify'],
            allow_agent=module.params['allow_agent'],
            look_for_keys=module.params['look_for_keys'],
            username=module.params['username'],
            password=module.params['password'],
        )

        try:
            m = ncclient.manager.connect(**nckwargs)
            server_capabilities = list(m.server_capabilities)
        except ncclient.transport.errors.AuthenticationError:
            module.fail_json(
                msg='authentication failed while connecting to device'
            )
        except Exception as e:
            module.fail_json(msg='error connecting to the device: %s' % to_native(e), exception=traceback.format_exc())

        try:
            xml.dom.minidom.parseString(config_xml)
        except Exception as e:
            module.fail_json(msg='error parsing XML: %s' % to_native(e), exception=traceback.format_exc())

    retkwargs = dict()
    retkwargs['server_capabilities'] = server_capabilities

    server_capabilities = '\n'.join(server_capabilities)

    if module.params['datastore'] == 'candidate':
        if ':candidate' in server_capabilities:
            datastore = 'candidate'
        else:
            if local_connection:
                m.close_session()
            module.fail_json(
                msg=':candidate is not supported by this netconf server'
            )
    elif module.params['datastore'] == 'running':
        if ':writable-running' in server_capabilities:
            datastore = 'running'
        else:
            if local_connection:
                m.close_session()
            module.fail_json(
                msg=':writable-running is not supported by this netconf server'
            )
    elif module.params['datastore'] == 'auto':
        if ':candidate' in server_capabilities:
            datastore = 'candidate'
        elif ':writable-running' in server_capabilities:
            datastore = 'running'
        else:
            if local_connection:
                m.close_session()
            module.fail_json(
                msg='neither :candidate nor :writable-running are supported by this netconf server'
            )
    else:
        if local_connection:
            m.close_session()
        module.fail_json(
            msg=module.params['datastore'] + ' datastore is not supported by this ansible module'
        )

    if module.params['save']:
        if ':startup' not in server_capabilities:
            module.fail_json(
                msg='cannot copy <running/> to <startup/>, while :startup is not supported'
            )

    try:
        changed = netconf_edit_config(
            m=m,
            xml=config_xml,
            commit=True,
            retkwargs=retkwargs,
            datastore=datastore,
            capabilities=server_capabilities,
            local_connection=local_connection
        )
        if changed and module.params['save']:
            m.copy_config(source="running", target="startup")
    except Exception as e:
        module.fail_json(msg='error editing configuration: %s' % to_native(e), exception=traceback.format_exc())
    finally:
        if local_connection:
            m.close_session()

    module.exit_json(changed=changed, **retkwargs)


if __name__ == '__main__':
    main()
