#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


DOCUMENTATION = """
---
module: ec2_elb
short_description: De-registers or registers instances from EC2 ELBs
description:
  - This module de-registers or registers an AWS EC2 instance from the ELBs
    that it belongs to.
  - Returns fact "ec2_elbs" which is a list of elbs attached to the instance
    if state=absent is passed as an argument.
  - Will be marked changed when called only if there are ELBs found to operate on.
version_added: "1.2"
author: "John Jarvis (@jarv)"
options:
  state:
    description:
      - register or deregister the instance
    required: true
    choices: ['present', 'absent']
  instance_id:
    description:
      - EC2 Instance ID
    required: true
  ec2_elbs:
    description:
      - List of ELB names, required for registration. The ec2_elbs fact should be used if there was a previous de-register.
  enable_availability_zone:
    description:
      - Whether to enable the availability zone of the instance on the target ELB if the availability zone has not already
        been enabled. If set to no, the task will fail if the availability zone is not enabled on the ELB.
    type: bool
    default: 'yes'
  wait:
    description:
      - Wait for instance registration or deregistration to complete successfully before returning.
    type: bool
    default: 'yes'
  validate_certs:
    description:
      - When set to "no", SSL certificates will not be validated for boto versions >= 2.6.0.
    type: bool
    default: 'yes'
    version_added: "1.5"
  wait_timeout:
    description:
      - Number of seconds to wait for an instance to change state. If 0 then this module may return an error if a transient error occurs.
        If non-zero then any transient errors are ignored until the timeout is reached. Ignored when wait=no.
    default: 0
    version_added: "1.6"
extends_documentation_fragment:
    - aws
    - ec2
"""

EXAMPLES = """
# basic pre_task and post_task example
pre_tasks:
  - name: Gathering ec2 facts
    action: ec2_facts
  - name: Instance De-register
    local_action:
      module: ec2_elb
      instance_id: "{{ ansible_ec2_instance_id }}"
      state: absent
roles:
  - myrole
post_tasks:
  - name: Instance Register
    local_action:
      module: ec2_elb
      instance_id: "{{ ansible_ec2_instance_id }}"
      ec2_elbs: "{{ item }}"
      state: present
    with_items: "{{ ec2_elbs }}"
"""

import time

try:
    import boto
    import boto.ec2
    import boto.ec2.autoscale
    import boto.ec2.elb
    from boto.regioninfo import RegionInfo
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (AnsibleAWSError, HAS_BOTO, connect_to_aws, ec2_argument_spec,
                                      get_aws_connection_info)


class ElbManager:
    """Handles EC2 instance ELB registration and de-registration"""

    def __init__(self, module, instance_id=None, ec2_elbs=None,
                 region=None, **aws_connect_params):
        self.module = module
        self.instance_id = instance_id
        self.region = region
        self.aws_connect_params = aws_connect_params
        self.lbs = self._get_instance_lbs(ec2_elbs)
        self.changed = False

    def deregister(self, wait, timeout):
        """De-register the instance from all ELBs and wait for the ELB
        to report it out-of-service"""

        for lb in self.lbs:
            initial_state = self._get_instance_health(lb)
            if initial_state is None:
                # Instance isn't registered with this load
                # balancer. Ignore it and try the next one.
                continue

            # The instance is not associated with any load balancer so nothing to do
            if not self._get_instance_lbs():
                return

            lb.deregister_instances([self.instance_id])

            # The ELB is changing state in some way. Either an instance that's
            # InService is moving to OutOfService, or an instance that's
            # already OutOfService is being deregistered.
            self.changed = True

            if wait:
                self._await_elb_instance_state(lb, 'OutOfService', initial_state, timeout)

    def register(self, wait, enable_availability_zone, timeout):
        """Register the instance for all ELBs and wait for the ELB
        to report the instance in-service"""
        for lb in self.lbs:
            initial_state = self._get_instance_health(lb)

            if enable_availability_zone:
                self._enable_availailability_zone(lb)

            lb.register_instances([self.instance_id])

            if wait:
                self._await_elb_instance_state(lb, 'InService', initial_state, timeout)
            else:
                # We cannot assume no change was made if we don't wait
                # to find out
                self.changed = True

    def exists(self, lbtest):
        """ Verify that the named ELB actually exists """

        found = False
        for lb in self.lbs:
            if lb.name == lbtest:
                found = True
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

    def _await_elb_instance_state(self, lb, awaited_state, initial_state, timeout):
        """Wait for an ELB to change state
        lb: load balancer
        awaited_state : state to poll for (string)"""

        wait_timeout = time.time() + timeout
        while True:
            instance_state = self._get_instance_health(lb)

            if not instance_state:
                msg = ("The instance %s could not be put in service on %s."
                       " Reason: Invalid Instance")
                self.module.fail_json(msg=msg % (self.instance_id, lb))

            if instance_state.state == awaited_state:
                # Check the current state against the initial state, and only set
                # changed if they are different.
                if (initial_state is None) or (instance_state.state != initial_state.state):
                    self.changed = True
                break
            elif self._is_instance_state_pending(instance_state):
                # If it's pending, we'll skip further checks and continue waiting
                pass
            elif (awaited_state == 'InService'
                  and instance_state.reason_code == "Instance"
                  and time.time() >= wait_timeout):
                # If the reason_code for the instance being out of service is
                # "Instance" this indicates a failure state, e.g. the instance
                # has failed a health check or the ELB does not have the
                # instance's availability zone enabled. The exact reason why is
                # described in InstantState.description.
                msg = ("The instance %s could not be put in service on %s."
                       " Reason: %s")
                self.module.fail_json(msg=msg % (self.instance_id,
                                                 lb,
                                                 instance_state.description))
            time.sleep(1)

    def _is_instance_state_pending(self, instance_state):
        """
        Determines whether the instance_state is "pending", meaning there is
        an operation under way to bring it in service.
        """
        # This is messy, because AWS provides no way to distinguish between
        # an instance that is is OutOfService because it's pending vs. OutOfService
        # because it's failing health checks. So we're forced to analyze the
        # description, which is likely to be brittle.
        return (instance_state and 'pending' in instance_state.description)

    def _get_instance_health(self, lb):
        """
        Check instance health, should return status object or None under
        certain error conditions.
        """
        try:
            status = lb.get_instance_health([self.instance_id])[0]
        except boto.exception.BotoServerError as e:
            if e.error_code == 'InvalidInstance':
                return None
            else:
                raise
        return status

    def _get_instance_lbs(self, ec2_elbs=None):
        """Returns a list of ELBs attached to self.instance_id
        ec2_elbs: an optional list of elb names that will be used
                  for elb lookup instead of returning what elbs
                  are attached to self.instance_id"""

        if not ec2_elbs:
            ec2_elbs = self._get_auto_scaling_group_lbs()

        try:
            elb = connect_to_aws(boto.ec2.elb, self.region, **self.aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            self.module.fail_json(msg=str(e))

        elbs = []
        marker = None
        while True:
            try:
                newelbs = elb.get_all_load_balancers(marker=marker)
                marker = newelbs.next_marker
                elbs.extend(newelbs)
                if not marker:
                    break
            except TypeError:
                # Older version of boto do not allow for params
                elbs = elb.get_all_load_balancers()
                break

        if ec2_elbs:
            lbs = sorted(lb for lb in elbs if lb.name in ec2_elbs)
        else:
            lbs = []
            for lb in elbs:
                for info in lb.instances:
                    if self.instance_id == info.id:
                        lbs.append(lb)
        return lbs

    def _get_auto_scaling_group_lbs(self):
        """Returns a list of ELBs associated with self.instance_id
           indirectly through its auto scaling group membership"""

        try:
            asg = connect_to_aws(boto.ec2.autoscale, self.region, **self.aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            self.module.fail_json(msg=str(e))

        asg_instances = asg.get_all_autoscaling_instances([self.instance_id])
        if len(asg_instances) > 1:
            self.module.fail_json(msg="Illegal state, expected one auto scaling group instance.")

        if not asg_instances:
            asg_elbs = []
        else:
            asg_name = asg_instances[0].group_name

            asgs = asg.get_all_groups([asg_name])
            if len(asg_instances) != 1:
                self.module.fail_json(msg="Illegal state, expected one auto scaling group.")

            asg_elbs = asgs[0].load_balancers

        return asg_elbs

    def _get_instance(self):
        """Returns a boto.ec2.InstanceObject for self.instance_id"""
        try:
            ec2 = connect_to_aws(boto.ec2, self.region, **self.aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            self.module.fail_json(msg=str(e))
        return ec2.get_only_instances(instance_ids=[self.instance_id])[0]


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state={'required': True},
        instance_id={'required': True},
        ec2_elbs={'default': None, 'required': False, 'type': 'list'},
        enable_availability_zone={'default': True, 'required': False, 'type': 'bool'},
        wait={'required': False, 'default': True, 'type': 'bool'},
        wait_timeout={'required': False, 'default': 0, 'type': 'int'}
    )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if not region:
        module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")

    ec2_elbs = module.params['ec2_elbs']
    wait = module.params['wait']
    enable_availability_zone = module.params['enable_availability_zone']
    timeout = module.params['wait_timeout']

    if module.params['state'] == 'present' and 'ec2_elbs' not in module.params:
        module.fail_json(msg="ELBs are required for registration")

    instance_id = module.params['instance_id']
    elb_man = ElbManager(module, instance_id, ec2_elbs, region=region, **aws_connect_params)

    if ec2_elbs is not None:
        for elb in ec2_elbs:
            if not elb_man.exists(elb):
                msg = "ELB %s does not exist" % elb
                module.fail_json(msg=msg)

    if module.params['state'] == 'present':
        elb_man.register(wait, enable_availability_zone, timeout)
    elif module.params['state'] == 'absent':
        elb_man.deregister(wait, timeout)

    ansible_facts = {'ec2_elbs': [lb.name for lb in elb_man.lbs]}
    ec2_facts_result = dict(changed=elb_man.changed, ansible_facts=ansible_facts)

    module.exit_json(**ec2_facts_result)


if __name__ == '__main__':
    main()
