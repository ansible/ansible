#!/usr/bin/python

# Copyright: (c) Vincent Van de Kussen
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: rhn_channel
short_description: Adds or removes Red Hat software channels
description:
    - Adds or removes Red Hat software channels.
version_added: "1.1"
author:
- Vincent Van der Kussen (@vincentvdk)
notes:
    - This module fetches the system id from RHN.
    - This module doesn't support I(check_mode).
options:
    name:
        description:
            - Name of the software channel.
        required: true
    sysname:
        description:
            - Name of the system as it is known in RHN/Satellite.
        required: true
    state:
        description:
            - Whether the channel should be present or not, taking action if the state is different from what is stated.
        default: present
    url:
        description:
            - The full URL to the RHN/Satellite API.
        required: true
    user:
        description:
            - RHN/Satellite login.
        required: true
    password:
        description:
            - RHN/Satellite password.
        required: true
'''

EXAMPLES = '''
- rhn_channel:
    name: rhel-x86_64-server-v2vwin-6
    sysname: server01
    url: https://rhn.redhat.com/rpc/api
    user: rhnuser
    password: guessme
  delegate_to: localhost
'''

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import xmlrpc_client


def get_systemid(client, session, sysname):
    systems = client.system.listUserSystems(session)
    for system in systems:
        if system.get('name') == sysname:
            idres = system.get('id')
            idd = int(idres)
            return idd


def subscribe_channels(channelname, client, session, sysname, sys_id):
    channels = base_channels(client, session, sys_id)
    channels.append(channelname)
    return client.system.setChildChannels(session, sys_id, channels)


def unsubscribe_channels(channelname, client, session, sysname, sys_id):
    channels = base_channels(client, session, sys_id)
    channels.remove(channelname)
    return client.system.setChildChannels(session, sys_id, channels)


def base_channels(client, session, sys_id):
    basechan = client.channel.software.listSystemChannels(session, sys_id)
    try:
        chans = [item['label'] for item in basechan]
    except KeyError:
        chans = [item['channel_label'] for item in basechan]
    return chans


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            name=dict(type='str', required=True),
            sysname=dict(type='str', required=True),
            url=dict(type='str', required=True),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True, aliases=['pwd'], no_log=True),
        )
    )

    state = module.params['state']
    channelname = module.params['name']
    systname = module.params['sysname']
    saturl = module.params['url']
    user = module.params['user']
    password = module.params['password']

    # initialize connection
    client = xmlrpc_client.ServerProxy(saturl)
    try:
        session = client.auth.login(user, password)
    except Exception as e:
        module.fail_json(msg="Unable to establish session with Sattelite server: %s " % to_text(e))

    if not session:
        module.fail_json(msg="Failed to establish session with Sattelite server.")

    # get systemid
    try:
        sys_id = get_systemid(client, session, systname)
    except Exception as e:
        module.fail_json(msg="Unable to get system id: %s " % to_text(e))

    if not sys_id:
        module.fail_json(msg="Failed to get system id.")

    # get channels for system
    try:
        chans = base_channels(client, session, sys_id)
    except Exception as e:
        module.fail_json(msg="Unable to get channel information: %s " % to_text(e))

    try:
        if state == 'present':
            if channelname in chans:
                module.exit_json(changed=False, msg="Channel %s already exists" % channelname)
            else:
                subscribe_channels(channelname, client, session, systname, sys_id)
                module.exit_json(changed=True, msg="Channel %s added" % channelname)

        if state == 'absent':
            if channelname not in chans:
                module.exit_json(changed=False, msg="Not subscribed to channel %s." % channelname)
            else:
                unsubscribe_channels(channelname, client, session, systname, sys_id)
                module.exit_json(changed=True, msg="Channel %s removed" % channelname)
    except Exception as e:
        module.fail_json('Unable to %s channel (%s): %s' % ('add' if state == 'present' else 'remove', channelname, to_text(e)))
    finally:
        client.auth.logout(session)


if __name__ == '__main__':
    main()
