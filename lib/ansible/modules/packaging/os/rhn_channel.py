#!/usr/bin/python

# (c) Vincent Van de Kussen
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
module: rhn_channel
short_description: Adds or removes Red Hat software channels
description:
    - Adds or removes Red Hat software channels
version_added: "1.1"
author: Vincent Van der Kussen
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
- rhn_channel: name=rhel-x86_64-server-v2vwin-6 sysname=server01 url=https://rhn.redhat.com/rpc/api user=rhnuser password=guessme
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
            password = dict(required=True, aliases=['pwd']),
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
main()

