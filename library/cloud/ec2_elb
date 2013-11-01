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

DOCUMENTATION = """
---
module: ec2_elb
short_description: De-registers or registers instances from EC2 ELB(s)
description:
  - This module de-registers or registers an AWS EC2 instance from the ELB(s)
    that it belongs to.
  - Returns fact "ec2_elbs" which is a list of elbs attached to the instance
    if state=absent is passed as an argument.
  - Will be marked changed when called only if there are ELBs found to operate on.
version_added: "1.2"
requirements: [ "boto" ]
author: John Jarvis
options:
  state:
    description:
      - register or deregister the instance
    required: true

  instance_id:
    description:
      - EC2 Instance ID
    required: true

  ec2_elbs:
    description:
      - List of ELB names, required for registration. The ec2_elbs fact should be used if there was a previous de-register.
    required: false
    default: None
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY environment variable is used. 
    required: false
    default: None
    aliases: ['ec2_secret_key', 'secret_key' ]
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY environment variable is used.
    required: false
    default: None
    aliases: ['ec2_access_key', 'access_key' ]
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    aliases: ['aws_region', 'ec2_region']
  enable_availability_zone:
    description:
      - Whether to enable the availability zone of the instance on the target ELB if the availability zone has not already
        been enabled. If set to no, the task will fail if the availability zone is not enabled on the ELB.
    required: false
    default: yes
    choices: [ "yes", "no" ]
  wait:
    description:
      - Wait for instance registration or deregistration to complete successfully before returning.  
    required: false
    default: yes
    choices: [ "yes", "no" ] 

"""

EXAMPLES = """
# basic pre_task and post_task example
pre_tasks:
  - name: Gathering ec2 facts
    ec2_facts:
  - name: Instance De-register
    local_action: ec2_elb
    args:
      instance_id: "{{ ansible_ec2_instance_id }}"
      state: 'absent'
roles:
  - myrole
post_tasks:
  - name: Instance Register
    local_action: ec2_elb
    args:
      instance_id: "{{ ansible_ec2_instance_id }}"
      ec2_elbs: "{{ item }}"
      state: 'present'
    with_items: ec2_elbs
"""

import time
import sys
import os

AWS_REGIONS = ['ap-northeast-1',
               'ap-southeast-1',
               'ap-southeast-2',
               'eu-west-1',
               'sa-east-1',
               'us-east-1',
               'us-west-1',
               'us-west-2']

try:
    import boto
    import boto.ec2
    import boto.ec2.elb
    from boto.regioninfo import RegionInfo
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

class ElbManager:
    """Handles EC2 instance ELB registration and de-registration"""

    def __init__(self, module, instance_id=None, ec2_elbs=None,
                 aws_access_key=None, aws_secret_key=None, region=None):
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.module = module
        self.instance_id = instance_id
        self.region = region
        self.lbs = self._get_instance_lbs(ec2_elbs)
        self.changed = False

    def deregister(self, wait):
        """De-register the instance from all ELBs and wait for the ELB
        to report it out-of-service"""

        for lb in self.lbs:
            initial_state = lb.get_instance_health([self.instance_id])[0]
            lb.deregister_instances([self.instance_id])
            if wait:
                self._await_elb_instance_state(lb, 'OutOfService', initial_state)
            else:
                # We cannot assume no change was made if we don't wait
                # to find out
                self.changed = True

    def register(self, wait, enable_availability_zone):
        """Register the instance for all ELBs and wait for the ELB
        to report the instance in-service"""
        for lb in self.lbs:
            initial_state = lb.get_instance_health([self.instance_id])[0]
            if enable_availability_zone:
                self._enable_availailability_zone(lb)
            lb.register_instances([self.instance_id])
            if wait:
                self._await_elb_instance_state(lb, 'InService', initial_state)
            else:
                # We cannot assume no change was made if we don't wait
                # to find out
                self.changed = True

    def exists(self, lbtest):
        """ Verify that the named ELB actually exists """
        
        found = False
        for lb in self.lbs:
            if lb.name == lbtest:
                found=True
                break
        return found

    def _enable_availailability_zone(self, lb):
        """Enable the current instance's availability zone in the provided lb.
        Returns True if the zone was enabled or False if no change was made.
        lb: load balancer"""
        instance = self._get_instance()
        if instance.placement in lb.availability_zones:
            return False

        lb.enable_zones(zones=instance.placement)

        # If successful, the new zone will have been added to
        # lb.availability_zones
        return instance.placement in lb.availability_zones

    def _await_elb_instance_state(self, lb, awaited_state, initial_state):
        """Wait for an ELB to change state
        lb: load balancer
        awaited_state : state to poll for (string)"""
        while True:
            instance_state = lb.get_instance_health([self.instance_id])[0]
            if instance_state.state == awaited_state:
                # Check the current state agains the initial state, and only set
                # changed if they are different.
                if instance_state.state != initial_state.state:
                    self.changed = True
                break
            elif (awaited_state == 'InService'
                  and instance_state.reason_code == "Instance"):
                # If the reason_code for the instance being out of service is
                # "Instance" this indicates a failure state, e.g. the instance
                # has failed a health check or the ELB does not have the
                # instance's availabilty zone enabled. The exact reason why is
                # described in InstantState.description.
                msg = ("The instance %s could not be put in service on %s."
                       " Reason: %s")
                self.module.fail_json(msg=msg % (self.instance_id,
                                                 lb,
                                                 instance_state.description))
            else:
                time.sleep(1)

    def _get_instance_lbs(self, ec2_elbs=None):
        """Returns a list of ELBs attached to self.instance_id
        ec2_elbs: an optional list of elb names that will be used
                  for elb lookup instead of returning what elbs
                  are attached to self.instance_id"""

        try:
            endpoint="elasticloadbalancing.%s.amazonaws.com" % self.region
            connect_region = RegionInfo(name=self.region, endpoint=endpoint)
            elb = boto.ec2.elb.ELBConnection(self.aws_access_key, self.aws_secret_key, region=connect_region)
        except boto.exception.NoAuthHandlerFound, e:
            self.module.fail_json(msg=str(e))

        elbs = elb.get_all_load_balancers()

        if ec2_elbs:
            lbs = sorted(lb for lb in elbs if lb.name in ec2_elbs)
        else:
            lbs = []
            for lb in elbs:
                for info in lb.instances:
                    if self.instance_id == info.id:
                        lbs.append(lb)
        return lbs

    def _get_instance(self):
        """Returns a boto.ec2.InstanceObject for self.instance_id"""
        try:
            endpoint = "ec2.%s.amazonaws.com" % self.region
            connect_region = RegionInfo(name=self.region, endpoint=endpoint)
            ec2_conn = boto.ec2.EC2Connection(self.aws_access_key, self.aws_secret_key, region=connect_region)
        except boto.exception.NoAuthHandlerFound, e:
            self.module.fail_json(msg=str(e))
        return ec2_conn.get_only_instances(instance_ids=[self.instance_id])[0]


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state={'required': True,
                    'choices': ['present', 'absent']},
            instance_id={'required': True},
            ec2_elbs={'default': None, 'required': False, 'type':'list'},
            aws_secret_key={'default': None, 'aliases': ['ec2_secret_key', 'secret_key'], 'no_log': True},
            aws_access_key={'default': None, 'aliases': ['ec2_access_key', 'access_key']},
            region={'default': None, 'required': False, 'aliases':['aws_region', 'ec2_region'], 'choices':AWS_REGIONS},
            enable_availability_zone={'default': True, 'required': False, 'choices': BOOLEANS, 'type': 'bool'},
            wait={'required': False, 'choices': BOOLEANS, 'default': True, 'type': 'bool'}
        )
    )

    # def get_ec2_creds(module):
    #   return ec2_url, ec2_access_key, ec2_secret_key, region
    ec2_url, aws_access_key, aws_secret_key, region = get_ec2_creds(module)

    ec2_elbs = module.params['ec2_elbs']
    region = module.params['region']
    wait = module.params['wait']
    enable_availability_zone = module.params['enable_availability_zone']

    if module.params['state'] == 'present' and 'ec2_elbs' not in module.params:
        module.fail_json(msg="ELBs are required for registration")

    instance_id = module.params['instance_id']
    elb_man = ElbManager(module, instance_id, ec2_elbs, aws_access_key,
                         aws_secret_key, region=region)

    if ec2_elbs is not None:
        for elb in ec2_elbs:
            if not elb_man.exists(elb):
                msg="ELB %s does not exist" % elb
                module.fail_json(msg=msg)

    if module.params['state'] == 'present':
        elb_man.register(wait, enable_availability_zone)
    elif module.params['state'] == 'absent':
        elb_man.deregister(wait)

    ansible_facts = {'ec2_elbs': [lb.name for lb in elb_man.lbs]}
    ec2_facts_result = dict(changed=elb_man.changed, ansible_facts=ansible_facts)

    module.exit_json(**ec2_facts_result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
