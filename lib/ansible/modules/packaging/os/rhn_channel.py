#!/usr/bin/python

# (c) Vincent Van de Kussen
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: rhn_channel
short_description: Adds or removes Red Hat software channels
description:
    - Adds or removes Red Hat software channels
version_added: "1.1"
author: "Vincent Van der Kussen (@vincentvdk)"
notes:
    - this module fetches the system id from RHN.
requirements:
    - none
options:
    name:
        description:
            - name of the software channel
        required: true
        default: null
    sysname:
        description:
            - name of the system as it is known in RHN/Satellite
        required: true
        default: null
    state:
        description:
            - whether the channel should be present or not
        required: false
        default: present
    url:
        description:
            - The full url to the RHN/Satellite api
        required: true
    user:
        description:
            - RHN/Satellite user
        required: true
    password:
        description:
            - "the user's password"
        required: true
'''

EXAMPLES = '''
- rhn_channel:
    name: rhel-x86_64-server-v2vwin-6
    sysname: server01
    url: https://rhn.redhat.com/rpc/api
    user: rhnuser
    password: guessme
'''

import xmlrpclib
from operator import itemgetter
import re


# ------------------------------------------------------- #

def get_systemid(client, session, sysname):
    systems = client.system.listUserSystems(session)
    for system in systems:
        if system.get('name') == sysname:
            idres = system.get('id')
            idd = int(idres)
            return idd

# ------------------------------------------------------- #

# unused:
#
#def get_localsystemid():
#    f = open("/etc/sysconfig/rhn/systemid", "r")
#    content = f.read()
#    loc_id = re.search(r'\b(ID-)(\d{10})' ,content)
#    return loc_id.group(2)

# ------------------------------------------------------- #

def subscribe_channels(channelname, client, session, sysname, sys_id):
    channels = base_channels(client, session, sys_id)
    channels.append(channelname)
    return client.system.setChildChannels(session, sys_id, channels)

# ------------------------------------------------------- #

def unsubscribe_channels(channelname, client, session, sysname, sys_id):
    channels = base_channels(client, session, sys_id)
    channels.remove(channelname)
    return client.system.setChildChannels(session, sys_id, channels)

# ------------------------------------------------------- #

def base_channels(client, session, sys_id):
    basechan = client.channel.software.listSystemChannels(session, sys_id)
    try:
        chans = [item['label'] for item in basechan]
    except KeyError:
        chans = [item['channel_label'] for item in basechan]
    return chans

# ------------------------------------------------------- #


def main():

    module = AnsibleModule(
        argument_spec = dict(
            state = dict(default='present', choices=['present', 'absent']),
            name = dict(required=True),
            sysname = dict(required=True),
            url = dict(required=True),
            user = dict(required=True),
            password = dict(required=True, aliases=['pwd'], no_log=True),
        )
        #        supports_check_mode=True
    )

    state = module.params['state']
    channelname = module.params['name']
    systname = module.params['sysname']
    saturl = module.params['url']
    user = module.params['user']
    password = module.params['password']

    #initialize connection
    client = xmlrpclib.Server(saturl, verbose=0)
    session = client.auth.login(user, password)

    # get systemid
    sys_id = get_systemid(client, session, systname)

    # get channels for system
    chans = base_channels(client, session, sys_id)


    if state == 'present':
        if channelname in chans:
            module.exit_json(changed=False, msg="Channel %s already exists" % channelname)
        else:
            subscribe_channels(channelname, client, session, systname, sys_id)
            module.exit_json(changed=True, msg="Channel %s added" % channelname)

    if state == 'absent':
        if not channelname in chans:
            module.exit_json(changed=False, msg="Not subscribed to channel %s." % channelname)
        else:
            unsubscribe_channels(channelname, client, session, systname, sys_id)
            module.exit_json(changed=True, msg="Channel %s removed" % channelname)

    client.auth.logout(session)


# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
