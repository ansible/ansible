#!/usr/bin/python
# Copyright: (c) 2018, Yaakov Kuperman <ykuperman@gmail.com>
# GNU General Public License v3.0+ # (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {"metadata_version": "1.1",
                    "status": ["preview"],
                    "supported_by": "community"}


DOCUMENTATION = """
---
module: elb_target_info
short_description: Gathers which target groups a target is associated with.
description:
  - This module will search through every target group in a region to find
    which ones have registered a given instance ID or IP.
  - This module was called C(elb_target_facts) before Ansible 2.9. The usage did not change.

version_added: "2.7"
author: "Yaakov Kuperman (@yaakov-github)"
options:
  instance_id:
    description:
      - What instance ID to get information for.
    type: str
    required: true
  get_unused_target_groups:
    description:
      - Whether or not to get target groups not used by any load balancers.
    type: bool
    default: true

requirements:
    - boto3
    - botocore
extends_documentation_fragment:
    - aws
    - ec2
"""

EXAMPLES = """
# practical use case - dynamically deregistering and reregistering nodes

  - name: Get EC2 Metadata
    action: ec2_metadata_facts

  - name: Get initial list of target groups
    delegate_to: localhost
    elb_target_info:
      instance_id: "{{ ansible_ec2_instance_id }}"
      region: "{{ ansible_ec2_placement_region }}"
    register: target_info

  - name: save fact for later
    set_fact:
      original_tgs: "{{ target_info.instance_target_groups }}"

  - name: Deregister instance from all target groups
    delegate_to: localhost
    elb_target:
        target_group_arn: "{{ item.0.target_group_arn }}"
        target_port: "{{ item.1.target_port }}"
        target_az: "{{ item.1.target_az }}"
        target_id: "{{ item.1.target_id }}"
        state: absent
        target_status: "draining"
        region: "{{ ansible_ec2_placement_region }}"
    with_subelements:
      - "{{ original_tgs }}"
      - "targets"

    # This avoids having to wait for 'elb_target' to serially deregister each
    # target group.  An alternative would be to run all of the 'elb_target'
    # tasks async and wait for them to finish.

  - name: wait for all targets to deregister simultaneously
    delegate_to: localhost
    elb_target_info:
      get_unused_target_groups: false
      instance_id: "{{ ansible_ec2_instance_id }}"
      region: "{{ ansible_ec2_placement_region }}"
    register: target_info
    until: (target_info.instance_target_groups | length) == 0
    retries: 60
    delay: 10

  - name: reregister in elbv2s
    elb_target:
      region: "{{ ansible_ec2_placement_region }}"
      target_group_arn: "{{ item.0.target_group_arn }}"
      target_port: "{{ item.1.target_port }}"
      target_az: "{{ item.1.target_az }}"
      target_id: "{{ item.1.target_id }}"
      state: present
      target_status: "initial"
    with_subelements:
      - "{{ original_tgs }}"
      - "targets"

  # wait until all groups associated with this instance are 'healthy' or
  # 'unused'
  - name: wait for registration
    elb_target_info:
      get_unused_target_groups: false
      instance_id: "{{ ansible_ec2_instance_id }}"
      region: "{{ ansible_ec2_placement_region }}"
    register: target_info
    until: (target_info.instance_target_groups |
            map(attribute='targets') |
            flatten |
            map(attribute='target_health') |
            rejectattr('state', 'equalto', 'healthy') |
            rejectattr('state', 'equalto', 'unused') |
            list |
            length) == 0
    retries: 61
    delay: 10

# using the target groups to generate AWS CLI commands to reregister the
# instance - useful in case the playbook fails mid-run and manual
#            rollback is required
  - name: "reregistration commands: ELBv2s"
    debug:
      msg: >
             aws --region {{ansible_ec2_placement_region}} elbv2
             register-targets --target-group-arn {{item.target_group_arn}}
             --targets{%for target in item.targets%}
             Id={{target.target_id}},
             Port={{target.target_port}}{%if target.target_az%},AvailabilityZone={{target.target_az}}
             {%endif%}
             {%endfor%}
    loop: "{{target_info.instance_target_groups}}"

"""

RETURN = """
instance_target_groups:
    description: a list of target groups to which the instance is registered to
    returned: always
    type: complex
    contains:
        target_group_arn:
            description: The ARN of the target group
            type: str
            returned: always
            sample:
                - "arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/target-group/deadbeefdeadbeef"
        target_group_type:
            description: Which target type is used for this group
            returned: always
            type: str
            sample:
                - ip
                - instance
        targets:
            description: A list of targets that point to this instance ID
            returned: always
            type: complex
            contains:
                target_id:
                    description: the target ID referring to this instance
                    type: str
                    returned: always
                    sample:
                        - i-deadbeef
                        - 1.2.3.4
                target_port:
                    description: which port this target is listening on
                    type: str
                    returned: always
                    sample:
                        - 80
                target_az:
                    description: which availability zone is explicitly
                                 associated with this target
                    type: str
                    returned: when an AZ is associated with this instance
                    sample:
                        - us-west-2a
                target_health:
                    description: the target health description
                                 (see U(https://boto3.readthedocs.io/en/latest/
                                  reference/services/elbv2.html#ElasticLoadBalancingv2.Client.describe_target_health))
                                 for all possible values
                    returned: always
                    type: complex
                    contains:
                        description:
                            description: description of target health
                            returned: if I(state!=present)
                            sample:
                                - "Target desregistration is in progress"
                        reason:
                            description: reason code for target health
                            returned: if I(state!=healthy)
                            sample:
                                - "Target.Deregistration in progress"
                        state:
                            description: health state
                            returned: always
                            sample:
                                - "healthy"
                                - "draining"
                                - "initial"
                                - "unhealthy"
                                - "unused"
                                - "unavailable"
"""

__metaclass__ = type

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    # we can handle the lack of boto3 based on the ec2 module
    pass

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (HAS_BOTO3, camel_dict_to_snake_dict,
                                      AWSRetry)


class Target(object):
    """Models a target in a target group"""
    def __init__(self, target_id, port, az, raw_target_health):
        self.target_port = port
        self.target_id = target_id
        self.target_az = az
        self.target_health = self.convert_target_health(raw_target_health)

    def convert_target_health(self, raw_target_health):
        return camel_dict_to_snake_dict(raw_target_health)


class TargetGroup(object):
    """Models an elbv2 target group"""

    def __init__(self, **kwargs):
        self.target_group_type = kwargs["target_group_type"]
        self.target_group_arn = kwargs["target_group_arn"]
        # the relevant targets associated with this group
        self.targets = []

    def add_target(self, target_id, target_port, target_az, raw_target_health):
        self.targets.append(Target(target_id,
                                   target_port,
                                   target_az,
                                   raw_target_health))

    def to_dict(self):
        object_dict = vars(self)
        object_dict["targets"] = [vars(each) for each in self.get_targets()]
        return object_dict

    def get_targets(self):
        return list(self.targets)


class TargetInfoGatherer(object):

    def __init__(self, module, instance_id, get_unused_target_groups):
        self.module = module
        try:
            self.ec2 = self.module.client(
                "ec2",
                retry_decorator=AWSRetry.jittered_backoff(retries=10)
            )
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e,
                                      msg="Couldn't connect to ec2"
                                      )

        try:
            self.elbv2 = self.module.client(
                "elbv2",
                retry_decorator=AWSRetry.jittered_backoff(retries=10)
            )
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e,
                                      msg="Could not connect to elbv2"
                                      )

        self.instance_id = instance_id
        self.get_unused_target_groups = get_unused_target_groups
        self.tgs = self._get_target_groups()

    def _get_instance_ips(self):
        """Fetch all IPs associated with this instance so that we can determine
           whether or not an instance is in an IP-based target group"""
        try:
            # get ahold of the instance in the API
            reservations = self.ec2.describe_instances(
                InstanceIds=[self.instance_id],
                aws_retry=True
            )["Reservations"]
        except (BotoCoreError, ClientError) as e:
            # typically this will happen if the instance doesn't exist
            self.module.fail_json_aws(e,
                                      msg="Could not get instance info" +
                                          " for instance '%s'" %
                                          (self.instance_id)
                                      )

        if len(reservations) < 1:
            self.module.fail_json(
                msg="Instance ID %s could not be found" % self.instance_id
            )

        instance = reservations[0]["Instances"][0]

        # IPs are represented in a few places in the API, this should
        # account for all of them
        ips = set()
        ips.add(instance["PrivateIpAddress"])
        for nic in instance["NetworkInterfaces"]:
            ips.add(nic["PrivateIpAddress"])
            for ip in nic["PrivateIpAddresses"]:
                ips.add(ip["PrivateIpAddress"])

        return list(ips)

    def _get_target_group_objects(self):
        """helper function to build a list of TargetGroup objects based on
           the AWS API"""
        try:
            paginator = self.elbv2.get_paginator(
                "describe_target_groups"
            )
            tg_response = paginator.paginate().build_full_result()
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e,
                                      msg="Could not describe target" +
                                          " groups"
                                      )

        # build list of TargetGroup objects representing every target group in
        # the system
        target_groups = []
        for each_tg in tg_response["TargetGroups"]:
            if not self.get_unused_target_groups and \
                    len(each_tg["LoadBalancerArns"]) < 1:
                # only collect target groups that actually are connected
                # to LBs
                continue

            target_groups.append(
                TargetGroup(target_group_arn=each_tg["TargetGroupArn"],
                            target_group_type=each_tg["TargetType"],
                            )
            )
        return target_groups

    def _get_target_descriptions(self, target_groups):
        """Helper function to build a list of all the target descriptions
           for this target in a target group"""
        # Build a list of all the target groups pointing to this instance
        # based on the previous list
        tgs = set()
        # Loop through all the target groups
        for tg in target_groups:
            try:
                # Get the list of targets for that target group
                response = self.elbv2.describe_target_health(
                    TargetGroupArn=tg.target_group_arn,
                    aws_retry=True
                )
            except (BotoCoreError, ClientError) as e:
                self.module.fail_json_aws(e,
                                          msg="Could not describe target " +
                                              "health for target group %s" %
                                              tg.target_group_arn
                                          )

            for t in response["TargetHealthDescriptions"]:
                # If the target group has this instance as a target, add to
                # list. This logic also accounts for the possibility of a
                # target being in the target group multiple times with
                # overridden ports
                if t["Target"]["Id"] == self.instance_id or \
                   t["Target"]["Id"] in self.instance_ips:

                    # The 'AvailabilityZone' parameter is a weird one, see the
                    # API docs for more.  Basically it's only supposed to be
                    # there under very specific circumstances, so we need
                    # to account for that
                    az = t["Target"]["AvailabilityZone"] \
                        if "AvailabilityZone" in t["Target"] \
                        else None

                    tg.add_target(t["Target"]["Id"],
                                  t["Target"]["Port"],
                                  az,
                                  t["TargetHealth"])
                    # since tgs is a set, each target group will be added only
                    # once, even though we call add on each successful match
                    tgs.add(tg)
        return list(tgs)

    def _get_target_groups(self):
        # do this first since we need the IPs later on in this function
        self.instance_ips = self._get_instance_ips()

        # build list of target groups
        target_groups = self._get_target_group_objects()
        return self._get_target_descriptions(target_groups)


def main():
    argument_spec = dict(
        instance_id={"required": True, "type": "str"},
        get_unused_target_groups={"required": False,
                                  "default": True, "type": "bool"}
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    if module._name == 'elb_target_facts':
        module.deprecate("The 'elb_target_facts' module has been renamed to 'elb_target_info'", version='2.13')

    instance_id = module.params["instance_id"]
    get_unused_target_groups = module.params["get_unused_target_groups"]

    tg_gatherer = TargetInfoGatherer(module,
                                     instance_id,
                                     get_unused_target_groups
                                     )

    instance_target_groups = [each.to_dict() for each in tg_gatherer.tgs]

    module.exit_json(instance_target_groups=instance_target_groups)


if __name__ == "__main__":
    main()
