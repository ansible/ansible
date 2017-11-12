#!/usr/bin/python
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


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: iot_thing
short_description: Manage AWS IOT things
description:
    - This module allows the user to manage IOT things.  It includes support for creating and deleting things as well as
      setting attributes and thing types.  It also allows principals to be attached and detached.
version_added: "2.5"
requirements: [ boto3 ]
author:
    - 'Andrew Kowpak (@akowpak-miovision)'
options:
  name:
    description:
      - The name of the IOT thing.
    required: true
  state:
    description:
      - If the IOT thing should be added or removed.
    default: present
    choices: [ 'present', 'absent' ]
  type:
    description:
      - An IOT thing type to associate with this IOT thing.
      - This parameter is mutually exclusive with I(remove_type).
  remove_type:
    description:
      - If the IOT type association should be removed from this IOT thing.
      - This parameter is mutually exclusive with I(type).
    type: bool
  attached_principals:
    description:
      - List of certificate or credential ARNs that should be attached to this IOT thing.
  detached_principals:
    description:
      - List of certificate or credential ARNs that should not be attached to this IOT thing.
  attributes:
    description:
      - A dictionary of attributes that should be set on this IOT thing.
  absent_attributes:
    description:
      - A list of attribute names that should not exist on this IOT thing.
  expected_version:
    description:
      - The version of the IOT thing that is expected to exist.  If a different version exists, then an attempt to
        update or delete the IOT thing will fail.
extends_documentation_fragment:
    - aws
    - ec2
'''


EXAMPLES = '''
- name: create IOT thing
  iot_thing:
    name: mything
    state: present

- name: delete IOT thing
  iot_thing:
    name: mything
    state: absent

- name: set type of IOT thing
  iot_thing:
    name: mything
    type: mytype

- name: set the type associated with an IOT thing
  iot_thing:
    name: mything
    remove_type: True

- name: disassociate an IOT thing from a type
  iot_thing:
    name: mything
    type:
      state: absent

- name: attach a certificate to an IOT thing
  iot_thing:
    name: mything
    attached_principals:
      - "arn:aws:iot:us-east-1:account-id:cert/uuid"

- name: detach a certificate from an IOT thing
  iot_thing:
    name: mything
    detached_principals:
      - "arn:aws:iot:us-east-1:account-id:cert/uuid"

- name: add attributes to an IOT thing
  iot_thing:
    name: mything
    attributes:
      key1: value1
      key2: value2

- name: remove attributes from an IOT thing
  iot_thing:
    name: mything
    absent_attributes:
      - key3
'''


RETURN = '''
default_client_id:
    description: The ID of the default client for this IOT thing.
    returned: on success when I(state=present)
    type: string
    sample: mythingid
version:
    description: The current version of the thing record in the IOT registry.
    returned: on success when I(state=present)
    type: int
    sample: 123
attribute:
    description: The attributes currently set on the IOT thing.
    returned: on success when I(state=present)
    type: dict
    sample: {"attribute1": "value1", "attribute2", "value2"}
principals:
    description: List of certificate or credential ARNs currently attached to this IOT thing.
    returned: on success when I(state=present)
    type: list
    sample: ["arn:aws:iot:us-east-1:account-id:cert/uuid-1", "arn:aws:iot:us-east-1:account-id:cert/uuid-2"]
thing_arn:
    description: The ARN of this IOT thing.
    returned: on success when the IOT thing is initially created.
    type: string
    sample: "arn:aws:iot:us-east-1:account-id:cert/mything"
thing_name:
    description: The name of this IOT thing.
    returned: on success when I(state=present)
    type: string
    sample: mything
thing_type_name:
    description: The name of this IOT thing.
    returned: on success when I(state=present) and there is an IOT type associated with this IOT thing.
    type: string
    sample: mytype
'''


from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn, camel_dict_to_snake_dict


try:
    from botocore.exceptions import ClientError, ValidationError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def main():
    argument_spec = dict(
        name=dict(required=True, type='str'),
        state=dict(default='present', choices=['present', 'absent']),
        type=dict(type='str'),
        remove_type=dict(type='bool'),
        attached_principals=dict(type='list', default=[]),
        detached_principals=dict(type='list', default=[]),
        attributes=dict(type='dict', default=dict()),
        absent_attributes=dict(type='list', default=[]),
        expected_version=dict(type='int')
    )

    mutually_exclusive = [['type', 'remove_type']]

    aws_module = AnsibleAWSModule(argument_spec=argument_spec,
                                  supports_check_mode=True,
                                  mutually_exclusive=mutually_exclusive)

    state = aws_module.params.get('state')
    thing_name = aws_module.params.get('name')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(aws_module, boto3=True)
    if not region:
        aws_module.fail_json(msg='region must be specified')

    try:
        client = boto3_conn(aws_module,
                            conn_type='client',
                            resource='iot',
                            region=region,
                            endpoint=ec2_url,
                            **aws_connect_kwargs)
    except (ClientError, ValidationError) as e:
        aws_module.fail_json_aws(e, msg='Trying to connect to AWS')

    thing = describe_thing(aws_module, client, thing_name)

    result = dict(changed=False)
    if thing is None and state == 'present':
        result = create_thing(aws_module, thing_name, client)
    elif thing is not None:
        if state == 'present':
            result = update_thing(aws_module, thing, client)
        else:
            result = delete_thing(aws_module, client, thing)

    aws_module.exit_json(**result)


def describe_thing(aws_module, client, thing_name):
    thing = None
    try:
        thing = client.describe_thing(thingName=thing_name)
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            aws_module.fail_json_aws(e, msg='Describing thing')

    return thing


def create_thing(aws_module, thing_name, client):
    thing_type = aws_module.params.get('type')
    attributes = aws_module.params.get('attributes')
    principals = aws_module.params.get('attached_principals')

    create_args = dict(
        thingName=thing_name,
        attributePayload=create_attribute_payload(attributes)
    )

    if thing_type is not None:
        create_args['thingTypeName'] = thing_type

    if not aws_module.check_mode:
        try:
            thing = client.create_thing(**create_args)
        except ClientError as e:
            aws_module.fail_json_aws(e, msg='Creating thing')

        for principal in principals:
            attach_principal(aws_module, client, thing_name, principal)

        return describe_and_format_changed_thing(
            aws_module, client, thing_name, principals, dict(thing_arn=thing.get('thingArn')))
    else:
        create_args['attributes'] = create_args['attributePayload']['attributes']
        del create_args['attributePayload']
        create_args['version'] = 1
        return format_thing(True, create_args, principals)


def update_thing(aws_module, thing, client):
    thing_name = thing.get('thingName')
    expected_version = parse_expected_version(aws_module, thing)

    thing_changed = change_thing(aws_module, client, thing, thing_name, expected_version)
    principals_changed, final_principals = change_principals(aws_module, client, thing_name)

    if thing_changed:
        if not aws_module.check_mode:
            return describe_and_format_changed_thing(aws_module, client, thing_name, final_principals, dict())
        else:
            # thing will be updated by change_thing when running in check mode
            return format_thing(True, thing, final_principals)
    elif principals_changed:
        return format_thing(True, thing, final_principals)
    else:
        return format_thing(False, thing, final_principals)


def change_thing(aws_module, client, thing, thing_name, expected_version):
    update_args = dict()

    set_type_delta(aws_module, thing, update_args)
    set_attribute_delta(aws_module, thing, update_args)

    if not update_args:
        return False

    update_args['thingName'] = thing_name

    if expected_version is not None:
        update_args['expectedVersion'] = expected_version

    if not aws_module.check_mode:
        change_thing_in_cloud(aws_module, client, update_args)
    else:
        change_thing_in_check_mode(aws_module, thing, update_args)

    return True


def set_type_delta(aws_module, thing, update_args):
    thing_type = aws_module.params.get('type')
    remove_type = aws_module.params.get('remove_type')
    current_type = thing.get('thingTypeName')

    if thing_type is not None:
        if current_type is None or current_type != thing_type:
            update_args['thingTypeName'] = thing_type
    elif remove_type:
        if current_type is not None:
            update_args['removeThingType'] = True


def set_attribute_delta(aws_module, thing, update_args):
    present_attributes = aws_module.params.get('attributes')
    absent_attributes = get_absent_attributes(aws_module)
    current_attributes = thing.get('attributes')
    attributes = dict()
    for name, value in present_attributes.items():
        if value != current_attributes.get(name):
            attributes[name] = value

    for name, value in absent_attributes.items():
        if name in current_attributes:
            attributes[name] = value

    if attributes:
        update_args['attributePayload'] = create_attribute_payload(attributes)


def change_thing_in_cloud(aws_module, client, update_args):
    try:
        client.update_thing(**update_args)
    except ClientError as e:
        aws_module.fail_json_aws(e, msg='Updating thing')


def change_thing_in_check_mode(aws_module, thing, update_args):
    expected_version = update_args.get('expectedVersion')
    version = thing.get('version')
    if expected_version is not None and expected_version != thing['version']:
        aws_module.fail_json(msg='Expected thing version %s but actual version is %s' % (expected_version, version))

    thing_type = update_args.get('thingTypeName')
    if thing_type is not None:
        thing['thingTypeName'] = thing_type

    remove_type = update_args.get('removeThingType')
    if remove_type is not None:
        del thing['thingTypeName']

    attribute_payload = update_args.get('attributePayload')
    if attribute_payload:
        for name, value in attribute_payload['attributes'].items():
            if value:
                thing['attributes'][name] = value
            else:
                del thing['attributes'][name]

    thing['version'] = thing['version'] + 1


def change_principals(aws_module, client, thing_name):
    attached_principals = aws_module.params.get('attached_principals')
    detached_principals = aws_module.params.get('detached_principals')
    current_principals = set(list_principals(aws_module, client, thing_name))
    principals_to_attach = set(attached_principals) - current_principals
    principals_to_detach = current_principals & set(detached_principals)
    final_principals = list((current_principals - principals_to_detach) | principals_to_attach)

    if not aws_module.check_mode:
        for principal in principals_to_detach:
            detach_principal(aws_module, client, thing_name, principal)

        for principal in principals_to_attach:
            attach_principal(aws_module, client, thing_name, principal)

    changed = bool(principals_to_attach) or bool(principals_to_detach)

    return changed, final_principals


def delete_thing(aws_module, client, thing):
    if not aws_module.check_mode:
        thing_name = thing.get('thingName')
        expected_version = parse_expected_version(aws_module, thing)
        principals = list_principals(aws_module, client, thing_name)

        for principal in principals:
            detach_principal(aws_module, client, thing_name, principal)

        delete_args = dict(thingName=thing_name)
        if expected_version is not None:
            delete_args['expectedVersion'] = expected_version

        try:
            client.delete_thing(**delete_args)
        except ClientError as e:
            aws_module.fail_json_aws(e, msg='Deleting thing')

    return dict(changed=True)


def get_absent_attributes(aws_module):
    attribute_names = aws_module.params.get('absent_attributes')

    absent_attributes = dict()

    for name in attribute_names:
        absent_attributes[name] = ''

    return absent_attributes


def create_attribute_payload(attributes):
    return dict(
        attributes=attributes,
        merge=True
    )


def list_principals(aws_module, client, thing_name):
    try:
        principals = client.list_thing_principals(thingName=thing_name)
    except ClientError as e:
        aws_module.fail_json_aws(e, msg='Listing thing principals')
    return principals.get('principals')


def attach_principal(aws_module, client, thing_name, principal):
    try:
        client.attach_thing_principal(thingName=thing_name,
                                      principal=principal)
    except ClientError as e:
        aws_module.fail_json_aws(e, msg='Attaching principal')


def detach_principal(aws_module, client, thing_name, principal):
    try:
        client.detach_thing_principal(thingName=thing_name,
                                      principal=principal)
    except ClientError as e:
        aws_module.fail_json_aws(e, msg='Detaching principal')


def parse_expected_version(aws_module, thing):
    expected_version = aws_module.params.get('expected_version')
    version = thing.get('version')
    if expected_version is not None and version != expected_version:
        aws_module.fail_json(msg='Expected thing version %s but actual version is %s' % (expected_version, version))
    return expected_version


def describe_and_format_changed_thing(aws_module, client, thing_name, principals, additional_details):
    try:
        thing = client.describe_thing(thingName=thing_name)
    except ClientError as e:
        aws_module.fail_json_aws(e, msg='Describing thing')

    thing.update(additional_details)

    return format_thing(True, thing, principals)


def format_thing(changed, thing, principals):
    del thing['ResponseMetadata']
    thing['principals'] = principals
    thing['changed'] = changed
    return camel_dict_to_snake_dict(thing)


if __name__ == '__main__':
    main()
