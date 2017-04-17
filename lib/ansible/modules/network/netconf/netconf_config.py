#!/usr/bin/python

# (c) 2016, Leandro Lisboa Penz <lpenz at lpenz.org>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
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
    - This module supports devices with and without the the candidate and
      confirmed-commit capabilities. It always use the safer feature.
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
    required: true


requirements:
  - "python >= 2.6"
  - "ncclient"
'''

EXAMPLES = '''
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

import xml.dom.minidom
try:
    import ncclient.manager
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False


import logging


def netconf_edit_config(m, xml, commit, retkwargs):
    if ":candidate" in m.server_capabilities:
        datastore = 'candidate'
    else:
        datastore = 'running'
    m.lock(target=datastore)
    try:
        if ":candidate" in m.server_capabilities:
            m.discard_changes()
        config_before = m.get_config(source=datastore)
        m.edit_config(target=datastore, config=xml)
        config_after = m.get_config(source=datastore)
        changed = config_before.data_xml != config_after.data_xml
        if changed and commit and ":candidate" in m.server_capabilities:
            if ":confirmed-commit" in m.server_capabilities:
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
            host=dict(type='str', required=True),
            port=dict(type='int', default=830),
            hostkey_verify=dict(type='bool', default=True),
            username=dict(type='str', required=True, no_log=True),
            password=dict(type='str', required=True, no_log=True),
            xml=dict(type='str', required=True),
        )
    )

    if not HAS_NCCLIENT:
        module.fail_json(msg='could not import the python library '
                         'ncclient required by this module')

    try:
        xml.dom.minidom.parseString(module.params['xml'])
    except:
        e = get_exception()
        module.fail_json(
            msg='error parsing XML: ' +
                str(e)
        )
        return

    nckwargs = dict(
        host=module.params['host'],
        port=module.params['port'],
        hostkey_verify=module.params['hostkey_verify'],
        username=module.params['username'],
        password=module.params['password'],
    )
    retkwargs = dict()

    try:
        m = ncclient.manager.connect(**nckwargs)
    except ncclient.transport.errors.AuthenticationError:
        module.fail_json(
            msg='authentication failed while connecting to device'
        )
    except:
        e = get_exception()
        module.fail_json(
            msg='error connecting to the device: ' +
                str(e)
        )
        return
    retkwargs['server_capabilities'] = list(m.server_capabilities)
    try:
        changed = netconf_edit_config(
            m=m,
            xml=module.params['xml'],
            commit=True,
            retkwargs=retkwargs,
        )
    finally:
        m.close_session()
    module.exit_json(changed=changed, **retkwargs)


# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
