#!/usr/bin/python

# Copyright: (c) 2018, Theo Ouzhinski <touzhinski@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
    module: virt_secret
    short_description: Manages libvirt secrets
    description:
        - Manages libvirt secrets.
    version_added: "2.8"
    author: Theo Ouzhinski (@theo-o)
    options:
        uuid:
            description:
                - The UUID of the secret being managed.
                - This module requires this parameter to be compliant with RFC4122.
                - Either this or I(secret) must be used to identify the secret in question.
        secret:
            description:
                - A Base64-encoded secret value.
                - Either this or I(uuid) must be used to identify the secret in question.
        usage_type:
            description:
                - Describes the category of what the secret is used for.
                - Currently, libvirt only supports volume, ceph, iscsi, and tls.
                - Required when I(state: present).
            choices:
                - volume
                - ceph
                - iscsi
                - tls
        usage_element:
            description:
                - The libvirt XML file contains an element that describes a particular attribute of the secret.
                - For I(volume) secrets, this element is the path of the volume this secret is associated with.
                - For I(ceph), I(iscsi), and I(tls) secrets, this element is the usage name for the secret and must be unique.
                - Required when I(usage) is defined.
        description:
            description:
                - "A human-readable description of the secret's purpose"
                - Not required
        ephemeral:
            description:
                - Whether the secret should only be kept in memory.
                - Required when I(state: present)
            type: bool
        private:
            description:
                - Whether the secret should not be revealed to a caller of libvirt.
                - If secret is private, it cannot be removed with an absent state.
                - Required when I(state: present)
            type: bool
        state:
            description:
                - Specify what state you want the secret to be in.
            required: true
            choices:
                - present
                - absent
    notes:
        - Check mode is supported for this module.
        - The libvirt docs can be found L(here, https://libvirt.org/formatsecret.html)
    requirements:
        - libvirt
'''

EXAMPLES = '''
- name: Define a Ceph secret without a value
  virt_secret:
    uuid: 50f71783-f894-4acc-8054-4e8f270c4f4b
    usage_type: ceph
    usage_element: client.libvirt secret
    private: no
    ephemeral: no
    state: present

- name: Define a Ceph secret with a value and random UUID
  virt_secret:
    secret: AQBHCbtT6APDHhAA5W00cBchwkQjh3dkKsyPjw==
    usage_type: ceph
    usage_element: another client.libvirt secret
    private: no
    ephemeral: no
    state: present

- name: Define a volume secret
  virt_secret:
    uuid: 4094057f-2bcb-46f3-81c0-2d0b8fdefa58
    secret: b3BlbiBzZXNhbWU=
    description: A volume secret
    usage_type: volume
    usage_element: /var/lib/libvirt/images/secret.img
    private: no
    ephemeral: no
    state: present

- name: Define an iscsi secret
  virt_secret:
    uuid: 4a5ab3d5-a24f-4c59-b397-f767351f33e9
    secret: bXlzZWNyZXQ=
    description: An iscsi secret
    usage_type: iscsi
    usage_element: libvirtiscsi
    private: no
    ephemeral: no

- name: Define a TLS secret
  virt_secret:
    uuid: 2c870ada-0068-4293-96b1-5004a26c89f2
    secret: bGV0bWVpbg==
    description: A TLS secret
    usage_type: tls
    usage_element: TLS_example
    private: no
    ephemeral: no

- name: Remove a secret with given UUID
  virt_secret:
    uuid: 50f71783-f894-4acc-8054-4e8f270c4f4b
    state: absent

- name: Remove a secret with given value
  virt_secret:
    secret: AQBHCbtT6APDHhAA5W00cBchwkQjh3dkKsyPjw==
    state: absent
'''

RETURN = '''
uuid:
    description: UUID of changed secret else an empty string
    returned: always
    type: string
    sample: 50f71783-f894-4acc-8054-4e8f270c4f4b

stderr:
    description: When failed, returns standard error message
    returned: when failed
    type: string
    sample: failed to get secret a
'''

STATE_CHOICES = ['present', 'absent']
USAGE_CHOICES = ['volume', 'ceph', 'iscsi', 'tls']

TYPE_TO_ELEMENT = dict(volume='volume',
                       ceph='name',
                       iscsi='target',
                       tls='name')


from xml.etree import ElementTree as ET
from os import remove
from uuid import UUID
from tempfile import mkstemp
from base64 import b64encode, b64decode

from ansible.module_utils.basic import AnsibleModule


def _list_secrets(module, bin_path):
    command = "{0} -q secret-list".format(bin_path)

    rc, stdout, stderr = module.run_command(command)
    secret_list = []
    for line in stdout.splitlines():
        rc, value, stderr = _get_secret_value(module, bin_path, line.strip().split("  ")[0])
        if rc != 0:
            value = ""
        secret_list.append(dict(
            uuid=line.strip().split("  ")[0],
            usage=line.strip().split("  ")[1].strip(),
            value=value.strip()))

    return secret_list


def _check_usage(module, bin_path, usage_type, usage_element):
    global result
    all_secrets = _list_secrets(module, bin_path)
    for sct_slug in all_secrets:
        if sct_slug['usage'] == "{0} {1}".format(usage_type, usage_element):
            module.fail_json(msg="A secret already exists with given usage_type and usage_element.", **result)


def _get_secret_value(module, bin_path, uuid):
    return module.run_command("{0} -q secret-get-value {1}".format(bin_path, uuid))


def _get_secret(module, bin_path, uuid, secret):
    all_secrets = _list_secrets(module, bin_path)

    for sct in all_secrets:
        if uuid and uuid == sct['uuid']:
            return sct
        if secret and secret == sct['value']:
            return sct

    return None


def define_secret(module, bin_path, uuid, secret, usage_type, usage_element, description, ephemeral, private):
    global result

    root = ET.Element('secret')
    if ephemeral:
        root.set('ephemeral', 'yes')
    else:
        root.set('ephemeral', 'no')

    if private:
        root.set('private', 'yes')
    else:
        root.set('private', 'no')

    if uuid:
        uuid_element = ET.SubElement(root, 'uuid')
        uuid_element.text = uuid

    if description:
        description_element = ET.SubElement(root, 'description')
        description_element.text = description

    usage_elmnt = ET.SubElement(root, 'usage')
    usage_elmnt.set('type', usage_type)
    usage_sbelmnt = ET.SubElement(usage_elmnt, TYPE_TO_ELEMENT[usage_type])
    usage_sbelmnt.text = usage_element

    if not module.check_mode:
        tree = ET.ElementTree(element=root)
        f, path = mkstemp()

        try:
            tree.write(path)
        except Exception as err:
            remove(path)
            raise Exception(err)

        rc, stdout, stderr = module.run_command("{0} secret-define {1}".format(bin_path, path))
        remove(path)
        if rc != 0:
            module.fail_json(msg="Defining secret failed.", stderr=stderr, **result)
        uuid = stdout.split(" ")[1]
        result['uuid'] = uuid
    else:
        result['changed'] = True

    if secret:
        _set_value(module, bin_path, uuid, secret)


def modify_secret(module, bin_path, uuid, secret, usage_type, usage_element, description, ephemeral, private):
    global result
    sct = _get_secret(module, bin_path, uuid, secret)
    if sct is None:
        return None

    rc, stdout, stderr = module.run_command("{0} secret-dumpxml {1}".format(bin_path, sct['uuid']))
    if rc != 0:
        module.fail_json(msg="Error getting secret XML.", stderr=stderr, **result)
    xml = stdout.strip()

    root = ET.fromstring(xml)

    needs_change = False

    if uuid and uuid != sct['uuid']:
        needs_change = True

    is_ephemeral = root.attrib['ephemeral']
    if (ephemeral and is_ephemeral == 'no') or (not ephemeral and is_ephemeral == 'yes'):
        needs_change = True

    is_private = root.attrib['private']
    if (private and is_private == 'no') or (not private and is_private == 'yes'):
        needs_change = True

    usage_elmnt = root.find('usage')
    if usage_type and usage_elmnt.attrib['type'] != usage_type:
        needs_change = True

    sub = usage_elmnt.find(TYPE_TO_ELEMENT[usage_type])
    if usage_element and sub.text != usage_element:
        needs_change = True

    if description and root.find('description') and root.find('description').text != description:
        needs_change = True

    if needs_change:
        rc, stdout, stderr = module.run_command("{0} secret-undefine {1}".format(bin_path, sct['uuid']))
        _check_usage(module, bin_path, usage_type, usage_element)
        return define_secret(module, bin_path, uuid, secret, usage_type, usage_element, description, ephemeral, private)
    else:
        return sct['uuid']


def _set_value(module, bin_path, uuid, secret_value):
    global result
    if not module.check_mode:
        rc, stdout, stderr = module.run_command("{0} secret-set-value {1} {2}".format(bin_path, uuid, secret_value))
    result['changed'] = True


def remove_secret(module, bin_path, uuid, secret):
    global result

    sct = _get_secret(module, bin_path, uuid, secret)
    if sct is None:
        return None

    if not module.check_mode:
        rc, stdout, stderr = module.run_command("{0} secret-undefine {1}".format(bin_path, sct["uuid"]))
        if rc != 0:
            module.fail_json(msg="Could not undefine secret.", stderr=stderr, **result)
        result['changed'] = True
        return sct["uuid"]
    else:
        result['changed'] = True
        return None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            uuid=dict(),
            secret=dict(),
            usage_type=dict(choices=USAGE_CHOICES),
            usage_element=dict(),
            description=dict(),
            ephemeral=dict(type='bool'),
            private=dict(type='bool'),
            state=dict(choices=STATE_CHOICES, required=True)),
        supports_check_mode=True)

    binary_path = module.get_bin_path('virsh', required=True)

    uuid = module.params.get('uuid', None)
    secret = module.params.get('secret', None)
    usage_type = module.params.get('usage_type', None)
    usage_element = module.params.get('usage_element', None)
    description = module.params.get('description', None)
    ephemeral = module.params.get('ephemeral', None)
    private = module.params.get('private', None)
    state = module.params.get('state', None)

    global result
    result = dict(
        changed=False,
        uuid='')

    if uuid is None and secret is None:
        module.fail_json(msg="Either a UUID or a secret must be defined.", **result)

    if secret:
        try:
            b64encode(b64decode(secret)) == secret
        except Exception:
            module.fail_json(msg="Secret must be Base64-encoded.", **result)

    if uuid:
        try:
            UUID(uuid)
        except Exception:
            module.fail_json(msg="uuid not compliant with RFC 4122.", **result)

    if state == 'present':
        sct = _get_secret(module, binary_path, uuid, secret)

        if usage_type is None:
            module.fail_json(msg="usage_type must be defined.", **result)
        if usage_type and usage_element is None:
            module.fail_json(msg="usage_element must be defined with usage_type.", **result)

        if sct:
            uuid = modify_secret(module, binary_path, uuid, secret, usage_type, usage_element, description, ephemeral, private)
            if uuid:
                result['uuid'] = uuid
        else:
            _check_usage(module, binary_path, usage_type, usage_element)
            uuid = define_secret(module, binary_path, uuid, secret, usage_type, usage_element, description, ephemeral, private)
            if uuid:
                result['uuid'] = uuid
    elif state == 'absent':
        uuid = remove_secret(module, binary_path, uuid, secret)
        if uuid:
            result['uuid'] = uuid

    module.exit_json(**result)


if __name__ == '__main__':
    main()
