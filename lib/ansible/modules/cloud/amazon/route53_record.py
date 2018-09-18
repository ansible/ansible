#!/usr/bin/python

# Copyright: (c) Ansible Project
# Copyright: (c) 2018, Shuang Wang <ooocamel@icloud.com>

# This code refactors the module route53.py of Ansible in order to support boto3.
# Name this module [route53_record] for the consistency with other route53_xxx modules.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: route53_record
version_added: "2.8"
short_description: Manages DNS records in Amazons Route53 service
description: Creates,deletes,updates,reads DNS records in Amazons Route53 service
author: Shuang Wang (@ptux)

requirements:
  - botocore
  - boto3
  - python >= 2.7

options:
  state:
    description:
      - Specifies the state of the resource record. As of Ansible 2.4, the I(command) option has been changed
        to I(state) as default and the choices 'present' and 'absent' have been added, but I(command) still works as well.
    required: true
    aliases: [ 'command' ]
    choices: [ 'present', 'absent', 'get', 'create', 'delete' ]
  zone:
    description:
      - The DNS zone to modify
    required: true
  hosted_zone_id:
    description:
      - The Hosted Zone ID of the DNS zone to modify
  record:
    description:
      - The full DNS record to create or delete
    required: true
  ttl:
    description:
      - The TTL(seconds) to give the new record
    type: int
    default: 3600
  type:
    description:
      - The type of DNS record to create
    required: true
    choices: [ 'A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'CAA', 'NS', 'SOA' ]
  alias:
    description:
      - Indicates if this is an alias record.
    type: bool
    default: 'no'
  alias_hosted_zone_id:
    description:
      - The hosted zone identifier.
  alias_evaluate_target_health:
    description:
      - Whether or not to evaluate an alias target health. Useful for aliases to Elastic Load Balancers.
    type: bool
    default: no
  value:
    description:
      - The new value when creating a DNS record.  YAML lists or multiple comma-spaced values are allowed for non-alias records.
      - When deleting a record all values for the record must be specified or Route53 will not delete it.
  overwrite:
    description:
      - Whether an existing record should be overwritten on create if values do not match
    type: bool
  retry_interval:
    description:
      - In the case that route53 is still servicing a prior request, this module will wait and try again after this many seconds. If you have many
        domain names, the default of 500 seconds may be too long.
    default: 500
  private_zone:
    description:
      - If set to C(yes), the private zone matching the requested name within the domain will be used if there are both public and private zones.
        The default is to use the public zone.
    type: bool
    default: 'no'
  identifier:
    description:
      - Have to be specified for Weighted, latency-based and failover resource record sets only. An identifier
        that differentiates among multiple resource record sets that have the
        same combination of DNS name and type.
  weight:
    description:
      - Weighted resource record sets only. Among resource record sets that
        have the same combination of DNS name and type, a value that
        determines what portion of traffic for the current resource record set
        is routed to the associated location.
  region:
    description:
      - Latency-based resource record sets only Among resource record sets
        that have the same combination of DNS name and type, a value that
        determines which region this should be associated with for the
        latency-based routing
  health_check:
    description:
      - Health check to associate with this record
  failover:
    description:
      - Failover resource record sets only. Whether this is the primary or
        secondary resource record set. Allowed values are PRIMARY and SECONDARY
    choices: [PRIMARY, SECONDARY]
  vpc_id:
    description:
      - "When used in conjunction with private_zone: true, this will only modify records in the private hosted zone attached to this VPC."
      - This allows you to have multiple private hosted zones, all with the same name, attached to different VPCs.
  wait:
    description:
      - Wait until the changes have been replicated to all Amazon Route 53 DNS servers.
    type: bool
    default: 'no'
  wait_timeout:
    description:
      - How long to wait for the changes to be replicated, in seconds.
    default: 300

extends_documentation_fragment:
  - aws
  - ec2
'''

RETURN = '''
nameservers:
  description: nameservers associated with the zone
  returned: when state is 'get'
  type: list
  sample:
  - ns-1036.awsdns-00.org.
  - ns-516.awsdns-00.net.
  - ns-1504.awsdns-00.co.uk.
  - ns-1.awsdns-00.com.
set:
  description: info specific to the resource record
  returned: when state is 'get'
  type: complex
  contains:
    alias:
      description: whether this is an alias
      returned: always
      type: bool
      sample: false
    failover:
      description: ""
      returned: always
      type: NoneType
      sample: null
    health_check:
      description: health_check associated with this record
      returned: always
      type: NoneType
      sample: null
    identifier:
      description: ""
      returned: always
      type: NoneType
      sample: null
    record:
      description: domain name for the record set
      returned: always
      type: string
      sample: new.foo.com.
    region:
      description: ""
      returned: always
      type:
      sample:
    ttl:
      description: resource record cache TTL
      returned: always
      type: string
      sample: '3600'
    type:
      description: record set type
      returned: always
      type: string
      sample: A
    value:
      description: value
      returned: always
      type: string
      sample: 52.43.18.27
    values:
      description: values
      returned: always
      type: list
      sample:
      - 52.43.18.27
    weight:
      description: weight of the record
      returned: always
      type: string
      sample: '3'
    zone:
      description: zone this record set belongs to
      returned: always
      type: string
      sample: foo.bar.com.
'''

EXAMPLES = '''
# Add new.foo.com as an A record with 3 IPs and wait until the changes have been replicated
- route53_record:
      state: present
      zone: foo.com
      record: new.foo.com
      type: A
      ttl: 7200
      value: 1.1.1.1,2.2.2.2,3.3.3.3
      wait: yes

# Update new.foo.com as an A record with a list of 3 IPs and wait until the changes have been replicated
- route53_record:
      state: present
      zone: foo.com
      record: new.foo.com
      type: A
      ttl: 7200
      value:
        - 1.1.1.1
        - 2.2.2.2
        - 3.3.3.3
      wait: yes

# Retrieve the details for new.foo.com
- route53_record:
      state: get
      zone: foo.com
      record: new.foo.com
      type: A
  register: rec

# Delete new.foo.com A record using the results from the get command
- route53_record:
      state: absent
      zone: foo.com
      record: "{{ rec.set.record }}"
      ttl: "{{ rec.set.ttl }}"
      type: "{{ rec.set.type }}"
      value: "{{ rec.set.value }}"

# Add an AAAA record.  Note that because there are colons in the value
# that the IPv6 address must be quoted. Also shows using the old form command=create.
- route53_record:
      command: create
      zone: foo.com
      record: localhost.foo.com
      type: AAAA
      ttl: 7200
      value: "::1"

# Add a SRV record with multiple fields for a service on port 22222
# For more information on SRV records see:
# https://en.wikipedia.org/wiki/SRV_record
- route53_record:
      state: present
      zone: foo.com
      record: "_example-service._tcp.foo.com"
      type: SRV
      value: "0 0 22222 host1.foo.com,0 0 22222 host2.foo.com"

# Add a TXT record. Note that TXT and SPF records must be surrounded
# by quotes when sent to Route 53:
- route53_record:
      state: present
      zone: foo.com
      record: localhost.foo.com
      type: TXT
      ttl: 7200
      value: '"bar"'

# Add an alias record that points to an Amazon ELB:
- route53_record:
      state: present
      zone: foo.com
      record: elb.foo.com
      type: A
      value: "{{ elb_dns_name }}"
      alias: True
      alias_hosted_zone_id: "{{ elb_zone_id }}"

# Retrieve the details for elb.foo.com
- route53_record:
      state: get
      zone: foo.com
      record: elb.foo.com
      type: A
  register: rec

# Delete an alias record using the results from the get command
- route53_record:
      state: absent
      zone: foo.com
      record: "{{ rec.set.record }}"
      ttl: "{{ rec.set.ttl }}"
      type: "{{ rec.set.type }}"
      value: "{{ rec.set.value }}"
      alias: True
      alias_hosted_zone_id: "{{ rec.set.alias_hosted_zone_id }}"

# Add an alias record that points to an Amazon ELB and evaluates it health:
- route53_record:
    state: present
    zone: foo.com
    record: elb.foo.com
    type: A
    value: "{{ elb_dns_name }}"
    alias: True
    alias_hosted_zone_id: "{{ elb_zone_id }}"
    alias_evaluate_target_health: True

# Add an AAAA record with Hosted Zone ID.
- route53_record:
      state: present
      zone: foo.com
      hosted_zone_id: Z2AABBCCDDEEFF
      record: localhost.foo.com
      type: AAAA
      ttl: 7200
      value: "::1"

# Use a routing policy to distribute traffic:
- route53_record:
      state: present
      zone: foo.com
      record: www.foo.com
      type: CNAME
      value: host1.foo.com
      ttl: 30
      # Routing policy
      identifier: "host1@www"
      weight: 100
      health_check: "d994b780-3150-49fd-9205-356abdd42e75"

# Add a CAA record (RFC 6844):
- route53_record:
      state: present
      zone: example.com
      record: example.com
      type: CAA
      value:
        - 0 issue "ca.example.net"
        - 0 issuewild ";"
        - 0 iodef "mailto:security@example.com"

'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils._text import to_native
from ansible.module_utils.ec2 import (
    AWSRetry,
    boto3_conn,
    boto_exception,
    ec2_argument_spec,
    get_aws_connection_info,
    snake_dict_to_camel_dict,
    camel_dict_to_snake_dict
)


class AWSRoute53Record(object):
    def __init__(self, module=None, results=None):
        self._module = module
        self._results = results
        self._connection = self._module.client('ec2')
        self._check_mode = self._module.check_mode
        self.warnings = []

    def _read_zone(self):
        pass

    def _create_record(self):
        pass

    def _read_record(self):
        pass

    def _update_record(self):
        pass

    def _delete_record(self):
        pass

    def ensure_present(self):
        pass

    def ensure_absent(self):
        pass

    def process(self):
        pass


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(aliases=['command'], choices=['present', 'absent', 'get', 'create', 'delete'], required=True),
        zone=dict(required=True),
        hosted_zone_id=dict(required=False, default=None),
        record=dict(required=True),
        ttl=dict(required=False, type='int', default=3600),
        type=dict(choices=['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'CAA', 'NS', 'SOA'], required=True),
        alias=dict(required=False, type='bool'),
        alias_hosted_zone_id=dict(required=False),
        alias_evaluate_target_health=dict(required=False, type='bool', default=False),
        value=dict(required=False, type='list'),
        overwrite=dict(required=False, type='bool'),
        retry_interval=dict(required=False, default=500),
        private_zone=dict(required=False, type='bool', default=False),
        identifier=dict(required=False, default=None),
        weight=dict(required=False, type='int'),
        health_check=dict(required=False),
        failover=dict(required=False, choices=['PRIMARY', 'SECONDARY']),
        vpc_id=dict(required=False),
        wait=dict(required=False, type='bool', default=False),
        wait_timeout=dict(required=False, type='int', default=300),
    ))

    # state=present, absent, create, delete THEN value is required
    required_if = [('state', 'present', ['value']), ('state', 'create', ['value'])]
    required_if.extend([('state', 'absent', ['value']), ('state', 'delete', ['value'])])

    # If alias is True then you must specify alias_hosted_zone as well
    required_together = [['alias', 'alias_hosted_zone_id']]

    # failover, region, and weight are mutually exclusive
    mutually_exclusive = [('failover', 'region', 'weight')]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    results = dict(changed=False)

    record_controller = AWSRoute53Record(module=module, results=results)
    record_controller.process()

    module.exit_json(**results)


if __name__ == '__main__':
    main()
