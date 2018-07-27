#!/usr/bin/python
# Copyright: (c) 2018, Yaakov Kuperman <ykuperman@gmail.com>
# GNU General Public License v3.0+ # (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    # we can handle the lack of boto3 based on the ec2 module
    pass

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict


ANSIBLE_METADATA = {"metadata_version": "1.1",
                    "status": ["preview"],
                    "supported_by": "community"}


DOCUMENTATION = """
---
module: elbv2_instance
short_description: De-registers or registers an EC2 instance from all ELBv2
                   target groups to which it is associated
description:
  - This module deregisters or reregisters an AWS EC2 instance from the target
    groups that it belongs to.
  - Returns fact "ec2_tgs" which is a list of dicts representing target groups
    formerly attached to the instance if C(state=absent) is passed as an
    argument. This will also work in check mode, returning the list of target
    groups that would have been operated on.
  - Will be marked changed when called if registration or deregistration
    occurs on any target group.
  - Will ignore target groups that are not associated with any load balancers.

version_added: "2.7"
author: "Yaakov Kuperman (@yaakov-github)"
options:
  state:
    description:
      - Whether the instance should or should not be in any target groups.
    required: true
    choices:
        - present
        - absent
  instance_id:
    description:
      - Instance ID to be registered or deregistered.
    required: true
  ec2_tgs:
    description:
      - List of dicts representing ec2 target groups to be registered.
        The ec2_tgs fact should be used if there was a previous de-register -
        which is the intended usage for this module.
      - Required when C(state=present)
      - This variable is not valid when C(state=absent)
  wait:
    description:
      - Wait for instance registration or deregistration to complete
        successfully before returning. This will wait the I(wait_timeout)
        duration for each target group, but will fail if a single target
        fails to register or deregister.
    type: bool
    default: yes
  wait_timeout:
    description:
      - Number of seconds to wait registration or deregistration to complete.
        Ignored when C(wait=no).
    default: 60
requirements:
    - boto3
    - botocore
extends_documentation_fragment:
    - aws
    - ec2
"""

EXAMPLES = """
# basic pre_task and post_task example
pre_tasks:
  - name: Gathering ec2 facts
    action: ec2_facts
  - name: Deregister instance
    elbv2_instance:
      instance_id: "{{ ansible_ec2_instance_id }}"
      region: "{{ ansible_ec2_placement_region }}"
      state: absent
    delegate_to: localhost
roles:
  - myrole
post_tasks:
  - name: Reregister instance
    elbv2_instance:
      instance_id: "{{ ansible_ec2_instance_id }}"
      region: "{{ ansible_ec2_placement_region }}"
      ec2_tgs: "{{ ec2_tgs }}"
      state: present
    delegate_to: localhost

# registration with custom target groups
- name: register instance using custom tgs
  elbv2_instance:
    instance_id: "{{ ansible_ec2_instance_id }}"
    region: "{{ ansible_ec2_placement_region }}"
    ec2_tgs:
      - arn: "some_arn"
        targets:
          - port: 8081
            target_id: "{{ ansible_ec2_instance_id }}"
        tg_type: "instance"
      - arn: "some_arn_1"
        targets:
          - port: 8080
            target_id: "{{ ansible_ec2_instance_id }}"
        tg_type: "instance"
      - arn: "some_arn_2"
        targets:
          - port: 22
            target_id: "{{ ansible_ec2_instance_identity_document_privateip }}"
        tg_type: "ip"
  delegate_to: localhost
  wait: true
  wait_timeout: 300
  state: present

# using the ec2_tgs fact to generate AWS CLI commands to reregister the
# instance - useful in case the playbook fails mid-run and manual
#            rollback is required
- name: "reregistration commands: ELBv2s"
  debug:
    msg: >
           aws --region {{ansible_ec2_placement_region}} elbv2
           register-targets --target-group-arn {{item.arn}}
           --targets{%for target in item.targets %}
           Id={{target.target_id}},
           Port={{target.port}}{%if target.az%},AvailabilityZone={{target.az}}
           {%endif%}
           {%endfor%}
  with_items: "{{ec2_tgs}}"
"""

RETURN = """
ec2_tgs:
    description: a list of target groups to which the instance was
                 registered or deregistered
    returned: always
    type: complex
    contains:
        arn:
            description: The ARN of the target group
            type: string
            returned: always
            sample:
                - "arn:aws:elasticloadbalancing:eu-west-1:111111111111:targetgroup/target-group/deadbeefdeadbeef"
        tg_type:
            description: Which target type is used for this group
            returned: always
            type: string
            sample:
                - ip
                - instance
        targets:
            description: A list of targets that point to this instance ID
            returned: always
            type: complex
            contains:
                target_id:
                    description: the target ID referiing to this instance
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
"""


class Target:
    """Models a target in a target group"""
    def __init__(self, target_id, port, az, raw_target_health):
        self.target_port = port
        self.target_id = target_id
        self.target_az = az
        self.target_health = self.convert_target_health(raw_target_health)

    def convert_target_health(self, raw_target_health):
        return camel_dict_to_snake_dict(raw_target_health)


class TargetGroup:
    """Models an elbv2 target group"""
    # constants for target group types
    ip = "ip"
    instance = "instance"

    def __init__(self, **kwargs):
        self.tg_type = kwargs["tg_type"]
        if self.tg_type != self.ip and self.tg_type != self.instance:
            raise Exception("Unsupported target group type %s" % self.tg_type)
        self.target_group_arn = kwargs["target_group_arn"]
        # the relevant targets associated with this group
        self.targets = []

    def add_target(self, target_id, target_port, target_az, raw_target_health):
        self.targets.append(Target(target_id,
                                   target_port,
                                   target_az,
                                   raw_target_health))

    def to_dict(self):
        object_dict = self.__dict__
        object_dict["targets"] = [each.__dict__ for each in self.get_targets()]
        return object_dict

    def get_targets(self):
        return list(self.targets)


class TargetFactsGatherer:

    def __init__(self, module, instance_id, get_unused_target_groups):
        self.module = module
        self.instance_id = instance_id
        self.get_unused_target_groups = get_unused_target_groups
        self.tgs = self._get_target_groups()

    def _get_instance_ips(self):
        """Fetch all IPs associated with this instance so that we can determine
           whether or not an instance is in an IP-based target group"""
        try:
            ec2 = self.module.client("ec2")
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e,
                                      msg="Couldn't connect to ec2 during" +
                                      " attempt to get instance IPs"
                                      )

        try:
            # get ahold of the instance in the API
            reservations = ec2.describe_instances(
                InstanceIds=[self.instance_id]
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

    # TODO refactor for simplicity
    def _get_target_groups(self):
        # do this first since we need the IPs later on in this function
        self.instance_ips = self._get_instance_ips()

        try:
            elbv2 = self.module.client("elbv2")
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e,
                                      msg="Could not connect to elbv2 when" +
                                          " attempting to get target groups"
                                      )
        # TODO paginator
        try:
            tg_response = elbv2.describe_target_groups()
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e,
                                      msg="Could not describe target" +
                                          " groups"
                                      )

        # build list of TargetGroup objects representing every target group in
        # the system
        target_groups = []
        while True:
            for each_tg in tg_response["TargetGroups"]:
                if not self.get_unused_target_groups and \
                        len(each_tg["LoadBalancerArns"]) < 1:
                    # only collect target groups that actually are connected
                    # to LBs
                    continue

                target_groups.append(
                    TargetGroup(target_group_arn=each_tg["TargetGroupArn"],
                                tg_type=each_tg["TargetType"],
                                )
                )
            if "NextMarker" in tg_response:
                try:
                    tg_response = elbv2.describe_target_groups(
                        Marker=tg_response["NextMarker"]
                    )
                except (BotoCoreError, ClientError) as e:
                    self.module.fail_json_aws(e,
                                              msg="Could not describe target" +
                                                  " groups"
                                              )
            else:
                break

        # now build a list of all the target groups pointing to this instance
        # based on the previous list
        tgs = set()
        # loop through all the target groups
        for tg in target_groups:
            try:
                # get the list of targets for that target group
                response = elbv2.describe_target_health(
                              TargetGroupArn=tg.target_group_arn
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

                    # TODO add health info
                    tg.add_target(t["Target"]["Id"],
                                  t["Target"]["Port"],
                                  az,
                                  t["TargetHealth"])
                    # since tgs is a set, each target group will be added only
                    # once, even though we call add on each successful match
                    tgs.add(tg)
        return list(tgs)


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

    if not HAS_BOTO3:
        module.fail_json(msg="boto3 and botocore are required for this module")

    instance_id = module.params["instance_id"]
    get_unused_target_groups = module.params["get_unused_target_groups"]

    tg_gatherer = TargetFactsGatherer(module,
                                      instance_id,
                                      get_unused_target_groups
                                      )

    ansible_facts = {"ec2_tgs": [each.to_dict() for each in tg_gatherer.tgs]}
    facts_result = dict(ansible_facts=ansible_facts)

    module.exit_json(**facts_result)


if __name__ == "__main__":
    main()
