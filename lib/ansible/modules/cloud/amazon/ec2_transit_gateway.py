#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: ec2_transit_gateway
short_description: Create and delete AWS Transit Gateways.
description:
  - Creates AWS Transit Gateways
  - Deletes AWS Transit Gateways
  - Updates tags on existing transit gateways
version_added: "2.8"
requirements: [ 'botocore', 'boto3' ]
options:
  asn:
    description:
      - A private Autonomous System Number (ASN) for the Amazon side of a BGP session.
        The range is 64512 to 65534 for 16-bit ASNs and 4200000000 to 4294967294 for 32-bit ASNs.
  auto_associate:
    description:
      - Enable or disable automatic association with the default association route table.
    default: yes
    type: bool
  auto_attach:
    description:
      - Enable or disable automatic acceptance of attachment requests.
    default: no
    type: bool
  auto_propagate:
    description:
      - Enable or disable automatic propagation of routes to the default propagation route table.
    default: yes
    type: bool
  description:
     description:
       - The description of the transit gateway.
     type: str
  dns_support:
    description:
      - Whether to enable AWS DNS support.
    default: yes
    type: bool
  purge_tags:
    description:
      - Whether to purge existing tags not included with tags argument.
    default: yes
    type: bool
  state:
    description:
      - present to ensure resource is created.
      - absent to remove resource.
    default: present
    choices: [ "present", "absent"]
  tags:
    description:
      - A dictionary of resource tags
  transit_gateway_id:
    description:
      - The ID of the transit gateway.
    type: str
  vpn_ecmp_support:
    description:
      - Enable or disable Equal Cost Multipath Protocol support.
    default: yes
    type: bool
  wait:
    description:
      - Whether to wait for status
    default: yes
  wait_timeout:
    description:
      - number of seconds to wait for status
    default: 300

author: "Bob Boldin (@BobBoldin)"
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
- name: Create a new transit gateway using defaults
  ec2_transit_gateway:
    state: present
    region: us-east-1
    description: personal-testing
  register: created_tgw

- name: Create a new transit gateway with options
  ec2_transit_gateway:
    asn: 64514
    auto_associate: no
    auto_propagate: no
    dns_support: True
    description: "nonprod transit gateway"
    purge_tags: False
    state: present
    region: us-east-1
    tags:
      Name: nonprod transit gateway
      status: testing

- name: Remove a transit gateway by description
  ec2_transit_gateway:
    state: absent
    region: us-east-1
    description: personal-testing

- name: Remove a transit gateway by id
  ec2_transit_gateway:
    state: absent
    region: ap-southeast-2
    transit_gateway_id: tgw-3a9aa123
  register: deleted_tgw
'''

RETURN = '''
transit_gateway:
  description: The attributes of the transit gateway.
  type: complex
  returned: I(state=present)
  contains:
    creation_time:
      description: The creation time of the transit gateway.
      returned: always
      type: str
      sample: "2019-03-06T17:13:51+00:00"
    description:
      description: The description of the transit gateway.
      returned: always
      type: str
      sample: my test tgw
    options:
      description: The options attributes of the transit gateway
      returned: always
      type: complex
      contains:
        amazon_side_asn:
          description:
            - A private Autonomous System Number (ASN) for the Amazon side of a BGP session.
              The range is 64512 to 65534 for 16-bit ASNs and 4200000000 to 4294967294 for 32-bit ASNs.
          returned: always
          type: str
          sample: 64512
        auto_accept_shared_attachements:
          description: Indicates whether attachment requests are automatically accepted.
          returned: always
          type: str
          sample: disable
        default_route_table_association:
          description:
           - Indicates  whether resource attachments are automatically
              associated with the default association route table.
          returned: always
          type: str
          sample: enable
        association_default_route_table_id:
          description: The ID of the default association route table.
          returned: Iwhen exists
          type: str
          sample: tgw-rtb-abc123444
        default_route_table_propagation:
          description:
           - Indicates  whether  resource  attachments   automatically
             propagate routes to the default propagation route table.
          returned: always
          type: str
          sample: disable
        propagation_default_route_table_id:
          description: The ID of the default propagation route table.
          returned: when exists
          type: str
          sample: tgw-rtb-def456777
        vpn_ecmp_support:
          description: Indicates  whether  Equal Cost Multipath Protocol support is enabled.
          returned: always
          type: str
          sample: enable
        dns_support:
          description: Indicates whether DNS support is enabled.
          returned: always
          type: str
          sample: enable
    owner_id:
      description: The account that owns the transit gateway.
      returned: always
      type: str
      sample: '123456789012'
    state:
      description: The state of the transit gateway.
      returned: always
      type: str
      sample: pending
    tags:
      description: A dictionary of resource tags
      returned: always
      type: dict
      sample:
        tags:
          Name: nonprod_tgw
    transit_gateway_arn:
      description: The ID of the transit_gateway.
      returned: always
      type: str
      sample: tgw-3a9aa123
    transit_gateway_id:
      description: The ID of the transit_gateway.
      returned: always
      type: str
      sample: tgw-3a9aa123
'''

try:
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:
    pass
    # handled by imported AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from time import sleep, time
from ansible.module_utils._text import to_text
from ansible.module_utils.ec2 import (
    ansible_dict_to_boto3_tag_list,
    ansible_dict_to_boto3_filter_list,
    AWSRetry,
    boto3_tag_list_to_ansible_dict,
    camel_dict_to_snake_dict,
    compare_aws_tags
)


class AnsibleEc2Tgw(object):

    def __init__(self, module, results):
        self._module = module
        self._results = results
        self._connection = self._module.client('ec2')
        self._check_mode = self._module.check_mode

        if not hasattr(self._connection, 'describe_transit_gateways'):
            self._module.fail_json(msg='transit gateway module requires boto3 >= 1.9.52')

    def process(self):
        """ Process the request based on state parameter .
          state = present will search for an existing tgw based and return the object data.
            if no object is found it will be created

          state = absent will attempt to remove the tgw however will fail if it still has
            attachments or associations
          """
        description = self._module.params.get('description')
        state = self._module.params.get('state', 'present')
        tgw_id = self._module.params.get('transit_gateway_id')

        if state == 'present':
            self.ensure_tgw_present(tgw_id, description)
        elif state == 'absent':
            self.ensure_tgw_absent(tgw_id, description)

    def wait_for_status(self, wait_timeout, tgw_id, status, skip_deleted=True):
        """
        Wait for the Transit Gateway to reach  the specified status
        :param wait_timeout: Number of seconds to wait, until this timeout is reached.
        :param tgw_id: The Amazon nat id.
        :param status: The status to wait for.
                examples. status=available, status=deleted
        :param skip_deleted: ignore deleted transit gateways
        :return dict: transit gateway object
        """
        polling_increment_secs = 5
        wait_timeout = time() + wait_timeout
        status_achieved = False
        transit_gateway = dict()

        while wait_timeout > time():
            try:
                transit_gateway = self.get_matching_tgw(tgw_id=tgw_id, skip_deleted=skip_deleted)

                if transit_gateway:
                    if self._check_mode:
                        transit_gateway['state'] = status

                    if transit_gateway.get('state') == status:
                        status_achieved = True
                        break

                    elif transit_gateway.get('state') == 'failed':
                        break

                else:
                    sleep(polling_increment_secs)

            except ClientError as e:
                self._module.fail_json_aws(e)

        if not status_achieved:
            self._module.fail_json(
                msg="Wait time out reached, while waiting for results")

        return transit_gateway

    @AWSRetry.exponential_backoff()
    def get_matching_tgw(self, tgw_id, description=None, skip_deleted=True):
        """ search for  an existing tgw by either tgw_id or description
        :param tgw_id:  The AWS id of the transit gateway
        :param description:  The description of the transit gateway.
        :param skip_deleted: ignore deleted transit gateways
        :return dict: transit gateway object
        """
        filters = []
        if tgw_id:
            filters = ansible_dict_to_boto3_filter_list({'transit-gateway-id': tgw_id})

        try:
            response = self._connection.describe_transit_gateways(Filters=filters)
        except (ClientError, BotoCoreError) as e:
            self._module.fail_json_aws(e)

        tgw = None
        tgws = []

        if len(response.get('TransitGateways', [])) == 1 and tgw_id:
            if (response['TransitGateways'][0]['State'] != 'deleted') or not skip_deleted:
                tgws.extend(response['TransitGateways'])

        for gateway in response.get('TransitGateways', []):
            if description == gateway['Description'] and gateway['State'] != 'deleted':
                tgws.append(gateway)

        if len(tgws) > 1:
            self._module.fail_json(
                msg='EC2 returned more than one transit Gateway for description {0}, aborting'.format(description))
        elif tgws:
            tgw = camel_dict_to_snake_dict(tgws[0], ignore_list=['Tags'])
            tgw['tags'] = boto3_tag_list_to_ansible_dict(tgws[0]['Tags'])

        return tgw

    @staticmethod
    def enable_option_flag(flag):
        disabled = "disable"
        enabled = "enable"
        if flag:
            return enabled
        return disabled

    def create_tgw(self, description):
        """
        Create a transit gateway and optionally wait for status to become available.

        :param description: The description of the transit gateway.
        :return dict: transit gateway object
        """
        options = dict()
        wait = self._module.params.get('wait')
        wait_timeout = self._module.params.get('wait_timeout')

        if self._module.params.get('asn'):
            options['AmazonSideAsn'] = self._module.params.get('asn')

        options['AutoAcceptSharedAttachments'] = self.enable_option_flag(self._module.params.get('auto_accept'))
        options['DefaultRouteTableAssociation'] = self.enable_option_flag(self._module.params.get('auto_associate'))
        options['DefaultRouteTablePropagation'] = self.enable_option_flag(self._module.params.get('auto_propagate'))
        options['VpnEcmpSupport'] = self.enable_option_flag(self._module.params.get('vpn_ecmp_support'))
        options['DnsSupport'] = self.enable_option_flag(self._module.params.get('dns_support'))

        try:
            response = self._connection.create_transit_gateway(Description=description, Options=options)
        except (ClientError, BotoCoreError) as e:
            self._module.fail_json_aws(e)

        tgw_id = response['TransitGateway']['TransitGatewayId']

        if wait:
            result = self.wait_for_status(wait_timeout=wait_timeout, tgw_id=tgw_id, status="available")
        else:
            result = self.get_matching_tgw(tgw_id=tgw_id)

        self._results['msg'] = (' Transit gateway {0} created'.format(result['transit_gateway_id']))

        return result

    def delete_tgw(self, tgw_id):
        """
        De;lete the transit gateway and optionally wait for status to become deleted

        :param tgw_id: The id of the transit gateway
        :return dict: transit gateway object
        """
        wait = self._module.params.get('wait')
        wait_timeout = self._module.params.get('wait_timeout')

        try:
            response = self._connection.delete_transit_gateway(TransitGatewayId=tgw_id)
        except (ClientError, BotoCoreError) as e:
            self._module.fail_json_aws(e)

        if wait:
            result = self.wait_for_status(wait_timeout=wait_timeout, tgw_id=tgw_id, status="deleted", skip_deleted=False)
        else:
            result = self.get_matching_tgw(tgw_id=tgw_id, skip_deleted=False)

        self._results['msg'] = (' Transit gateway {0} deleted'.format(tgw_id))

        return result

    def ensure_tags(self, tgw_id, tags, purge_tags):
        """
        Ensures tags are applied to the transit gateway.  Optionally will remove any
        existing tags not in the tags argument if purge_tags is set to true

        :param tgw_id:  The AWS id of the transit gateway
        :param tags:  list of tags to  apply to the  transit gateway.
        :param purge_tags:  when true existing tags not in tags parms are removed
        :return:  true if tags were updated
        """
        tags_changed = False
        filters = ansible_dict_to_boto3_filter_list({'resource-id': tgw_id})
        try:
            cur_tags = self._connection.describe_tags(Filters=filters)
        except (ClientError, BotoCoreError) as e:
            self._module.fail_json_aws(e, msg="Couldn't describe tags")

        to_update, to_delete = compare_aws_tags(boto3_tag_list_to_ansible_dict(cur_tags.get('Tags')), tags, purge_tags)

        if to_update:
            try:
                if not self._check_mode:
                    AWSRetry.exponential_backoff()(self._connection.create_tags)(
                        Resources=[tgw_id],
                        Tags=ansible_dict_to_boto3_tag_list(to_update)
                    )
                self._results['changed'] = True
                tags_changed = True
            except (ClientError, BotoCoreError) as e:
                self._module.fail_json_aws(e, msg="Couldn't create tags {0} for resource {1}".format(
                    ansible_dict_to_boto3_tag_list(to_update), tgw_id))

        if to_delete:
            try:
                if not self._check_mode:
                    tags_list = []
                    for key in to_delete:
                        tags_list.append({'Key': key})

                    AWSRetry.exponential_backoff()(self._connection.delete_tags)(
                        Resources=[tgw_id],
                        Tags=tags_list
                    )
                self._results['changed'] = True
                tags_changed = True
            except (ClientError, BotoCoreError) as e:
                self._module.fail_json_aws(e, msg="Couldn't delete tags {0} for resource {1}".format(
                    ansible_dict_to_boto3_tag_list(to_delete), tgw_id))

        return tags_changed

    def ensure_tgw_present(self, tgw_id=None, description=None):
        """
        Will create a tgw if no match to the tgw_id or description are found
        Will update the tgw tags if matching one found but tags are not synced

        :param tgw_id:  The AWS id of the transit gateway
        :param description:  The description of the transit gateway.
        :return dict: transit gateway object
        """
        tgw = self.get_matching_tgw(tgw_id, description)

        if tgw is None:
            if self._check_mode:
                self._results['changed'] = True
                self._results['transit_gateway_id'] = None
                return self._results

            try:
                if not description:
                    self._module.fail_json(msg="Failed to create Transit Gateway: description argument required")
                tgw = self.create_tgw(description)
                self._results['changed'] = True
            except (BotoCoreError, ClientError) as e:
                self._module.fail_json_aws(e, msg='Unable to create Transit Gateway')

        if self._module.params.get('tags') != tgw.get('tags'):
            stringed_tags_dict = dict((to_text(k), to_text(v)) for k, v in self._module.params.get('tags').items())
            if self.ensure_tags(tgw['transit_gateway_id'], stringed_tags_dict, self._module.params.get('purge_tags')):
                self._results['changed'] = True

        self._results['transit_gateway'] = self.get_matching_tgw(tgw_id=tgw['transit_gateway_id'])

        return self._results

    def ensure_tgw_absent(self, tgw_id=None, description=None):
        """
        Will delete the tgw if a single tgw is found not yet in deleted status

        :param tgw_id:  The AWS id of the transit gateway
        :param description:  The description of the transit gateway.
        :return doct: transit gateway object
        """
        self._results['transit_gateway_id'] = None
        tgw = self.get_matching_tgw(tgw_id, description)

        if tgw is not None:
            if self._check_mode:
                self._results['changed'] = True
                return self._results

            try:
                tgw = self.delete_tgw(tgw_id=tgw['transit_gateway_id'])
                self._results['changed'] = True
                self._results['transit_gateway'] = self.get_matching_tgw(tgw_id=tgw['transit_gateway_id'],
                                                                         skip_deleted=False)
            except (BotoCoreError, ClientError) as e:
                self._module.fail_json_aws(e, msg='Unable to delete Transit Gateway')

        return self._results


def setup_module_object():
    """
    merge argument spec and create Ansible module object
    :return: Ansible module object
    """

    argument_spec = dict(
        asn=dict(type='int'),
        auto_associate=dict(type='bool', default='yes'),
        auto_attach=dict(type='bool', default='no'),
        auto_propagate=dict(type='bool', default='yes'),
        description=dict(type='str'),
        dns_support=dict(type='bool', default='yes'),
        purge_tags=dict(type='bool', default='yes'),
        state=dict(default='present', choices=['present', 'absent']),
        tags=dict(default=dict(), type='dict'),
        transit_gateway_id=dict(type='str'),
        vpn_ecmp_support=dict(type='bool', default='yes'),
        wait=dict(type='bool', default='yes'),
        wait_timeout=dict(type='int', default=300)
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_one_of=[('description', 'transit_gateway_id')],
        supports_check_mode=True,
    )

    return module


def main():

    module = setup_module_object()

    results = dict(
        changed=False
    )

    tgw_manager = AnsibleEc2Tgw(module=module, results=results)
    tgw_manager.process()

    module.exit_json(**results)


if __name__ == '__main__':
    main()
