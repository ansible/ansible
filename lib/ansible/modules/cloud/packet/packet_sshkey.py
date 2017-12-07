#!/usr/bin/python
# Copyright 2016 Tomas Karasek <tom.to.the.k@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: packet_sshkey
short_description: Create/delete an SSH key in Packet host.
description:
     - Create/delete an SSH key in Packet host.
     - API is documented at U(https://www.packet.net/help/api/#page:ssh-keys,header:ssh-keys-ssh-keys-post).
version_added: "2.3"
author: "Tomas Karasek (@t0mk) <tom.to.the.k@gmail.com>"
options:
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
  auth_token:
    description:
     - Packet api token. You can also supply it in env var C(PACKET_API_TOKEN).
  label:
     description:
     - Label for the key. If you keep it empty, it will be read from key string.
  id:
    description:
     - UUID of the key which you want to remove.
  fingerprint:
    description:
     - Fingerprint of the key which you want to remove.
  key:
    description:
     - Public Key string ({type} {base64 encoded key} {description}).
  key_file:
    description:
     - File with the public key.

requirements:
  - "python >= 2.6"
  - packet-python

'''

EXAMPLES = '''
# All the examples assume that you have your Packet API token in env var PACKET_API_TOKEN.
# You can also pass the api token in module param auth_token.

- name: create sshkey from string
  hosts: localhost
  tasks:
    packet_sshkey:
      key: "{{ lookup('file', 'my_packet_sshkey.pub') }}"

- name: create sshkey from file
  hosts: localhost
  tasks:
    packet_sshkey:
      label: key from file
      key_file: ~/ff.pub

- name: remove sshkey by id
  hosts: localhost
  tasks:
    packet_sshkey:
      state: absent
      id: eef49903-7a09-4ca1-af67-4087c29ab5b6
'''

RETURN = '''
changed:
    description: True if a sshkey was created or removed.
    type: bool
    sample: True
    returned: always
sshkeys:
    description: Information about sshkeys that were createe/removed.
    type: list
    sample: [
        {
            "fingerprint": "5c:93:74:7c:ed:07:17:62:28:75:79:23:d6:08:93:46",
            "id": "41d61bd8-3342-428b-a09c-e67bdd18a9b7",
            "key": "ssh-dss AAAAB3NzaC1kc3MAAACBAIfNT5S0ncP4BBJBYNhNPxFF9lqVhfPeu6SM1LoCocxqDc1AT3zFRi8hjIf6TLZ2AA4FYbcAWxLMhiBxZRVldT9GdBXile78kAK5z3bKTwq152DCqpxwwbaTIggLFhsU8wrfBsPWnDuAxZ0h7mmrCjoLIE3CNLDA/NmV3iB8xMThAAAAFQCStcesSgR1adPORzBxTr7hug92LwAAAIBOProm3Gk+HWedLyE8IfofLaOeRnbBRHAOL4z0SexKkVOnQ/LGN/uDIIPGGBDYTvXgKZT+jbHeulRJ2jKgfSpGKN4JxFQ8uzVH492jEiiUJtT72Ss1dCV4PmyERVIw+f54itihV3z/t25dWgowhb0int8iC/OY3cGodlmYb3wdcQAAAIBuLbB45djZXzUkOTzzcRDIRfhaxo5WipbtEM2B1fuBt2gyrvksPpH/LK6xTjdIIb0CxPu4OCxwJG0aOz5kJoRnOWIXQGhH7VowrJhsqhIc8gN9ErbO5ea8b1L76MNcAotmBDeTUiPw01IJ8MdDxfmcsCslJKgoRKSmQpCwXQtN2g== tomk@hp2",
            "label": "mynewkey33"
        }
    ]
    returned: always
'''  # NOQA

import os
import uuid

from ansible.module_utils.basic import AnsibleModule

HAS_PACKET_SDK = True
try:
    import packet
except ImportError:
    HAS_PACKET_SDK = False


PACKET_API_TOKEN_ENV_VAR = "PACKET_API_TOKEN"


def serialize_sshkey(sshkey):
    sshkey_data = {}
    copy_keys = ['id', 'key', 'label', 'fingerprint']
    for name in copy_keys:
        sshkey_data[name] = getattr(sshkey, name)
    return sshkey_data


def is_valid_uuid(myuuid):
    try:
        val = uuid.UUID(myuuid, version=4)
    except ValueError:
        return False
    return str(val) == myuuid


def load_key_string(key_str):
    ret_dict = {}
    key_str = key_str.strip()
    ret_dict['key'] = key_str
    cut_key = key_str.split()
    if len(cut_key) in [2, 3]:
        if len(cut_key) == 3:
            ret_dict['label'] = cut_key[2]
    else:
        raise Exception("Public key %s is in wrong format" % key_str)
    return ret_dict


def get_sshkey_selector(module):
    key_id = module.params.get('id')
    if key_id:
        if not is_valid_uuid(key_id):
            raise Exception("sshkey ID %s is not valid UUID" % key_id)
    selecting_fields = ['label', 'fingerprint', 'id', 'key']
    select_dict = {}
    for f in selecting_fields:
        if module.params.get(f) is not None:
            select_dict[f] = module.params.get(f)

    if module.params.get('key_file'):
        with open(module.params.get('key_file')) as _file:
            loaded_key = load_key_string(_file.read())
        select_dict['key'] = loaded_key['key']
        if module.params.get('label') is None:
            if loaded_key.get('label'):
                select_dict['label'] = loaded_key['label']

    def selector(k):
        if 'key' in select_dict:
            # if key string is specified, compare only the key strings
            return k.key == select_dict['key']
        else:
            # if key string not specified, all the fields must match
            return all([select_dict[f] == getattr(k, f) for f in select_dict])
    return selector


def act_on_sshkeys(target_state, module, packet_conn):
    selector = get_sshkey_selector(module)
    existing_sshkeys = packet_conn.list_ssh_keys()
    matching_sshkeys = filter(selector, existing_sshkeys)
    changed = False
    if target_state == 'present':
        if matching_sshkeys == []:
            # there is no key matching the fields from module call
            # => create the key, label and
            newkey = {}
            if module.params.get('key_file'):
                with open(module.params.get('key_file')) as f:
                    newkey = load_key_string(f.read())
            if module.params.get('key'):
                newkey = load_key_string(module.params.get('key'))
            if module.params.get('label'):
                newkey['label'] = module.params.get('label')
            for param in ('label', 'key'):
                if param not in newkey:
                    _msg = ("If you want to ensure a key is present, you must "
                            "supply both a label and a key string, either in "
                            "module params, or in a key file. %s is missing"
                            % param)
                    raise Exception(_msg)
            matching_sshkeys = []
            new_key_response = packet_conn.create_ssh_key(
                newkey['label'], newkey['key'])
            changed = True

            matching_sshkeys.append(new_key_response)
    else:
        # state is 'absent' => delete mathcing keys
        for k in matching_sshkeys:
            try:
                k.delete()
                changed = True
            except Exception as e:
                _msg = ("while trying to remove sshkey %s, id %s %s, "
                        "got error: %s" %
                        (k.label, k.id, target_state, e))
                raise Exception(_msg)

    return {
        'changed': changed,
        'sshkeys': [serialize_sshkey(k) for k in matching_sshkeys]
    }


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            auth_token=dict(default=os.environ.get(PACKET_API_TOKEN_ENV_VAR),
                            no_log=True),
            label=dict(type='str', aliases=['name'], default=None),
            id=dict(type='str', default=None),
            fingerprint=dict(type='str', default=None),
            key=dict(type='str', default=None, no_log=True),
            key_file=dict(type='path', default=None),
        ),
        mutually_exclusive=[
            ('label', 'id'),
            ('label', 'fingerprint'),
            ('id', 'fingerprint'),
            ('key', 'fingerprint'),
            ('key', 'id'),
            ('key_file', 'key'),
        ]
    )

    if not HAS_PACKET_SDK:
        module.fail_json(msg='packet required for this module')

    if not module.params.get('auth_token'):
        _fail_msg = ("if Packet API token is not in environment variable %s, "
                     "the auth_token parameter is required" %
                     PACKET_API_TOKEN_ENV_VAR)
        module.fail_json(msg=_fail_msg)

    auth_token = module.params.get('auth_token')

    packet_conn = packet.Manager(auth_token=auth_token)

    state = module.params.get('state')

    if state in ['present', 'absent']:
        try:
            module.exit_json(**act_on_sshkeys(state, module, packet_conn))
        except Exception as e:
            module.fail_json(msg='failed to set sshkey state: %s' % str(e))
    else:
        module.fail_json(msg='%s is not a valid state for this module' % state)


if __name__ == '__main__':
    main()
