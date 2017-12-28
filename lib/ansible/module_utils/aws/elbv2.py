#!/usr/bin/env python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Ansible imports
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, get_ec2_security_group_ids_from_names, \
    ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict
from ansible.module_utils.aws.elb_utils import get_elb, get_elb_listener, convert_tg_name_to_arn

# Non-ansible imports
try:
    from botocore.exceptions import ClientError
except ImportError:
    pass
import traceback
import time
from copy import deepcopy


class ElasticLoadBalancerV2(object):

    def __init__(self, connection, module):

        self.connection = connection
        self.module = module
        self.changed = False
        self.new_load_balancer = False
        self.scheme = module.params.get("scheme")
        self.name = module.params.get("name")
        self.subnet_mappings = module.params.get("subnet_mappings")
        self.subnets = module.params.get("subnets")
        self.deletion_protection = module.params.get("deletion_protection")
        self.wait = module.params.get("wait")

        if module.params.get("tags"):
            self.tags = ansible_dict_to_boto3_tag_list(module.params.get("tags"))
        else:
            self.tags = None
        self.purge_tags = module.params.get("purge_tags")

        self.elb = get_elb(connection, module, self.name)
        if self.elb is not None:
            self.elb_attributes = self.get_elb_attributes()
            self.elb['tags'] = self.get_elb_tags()
        else:
            self.elb_attributes = None

    def wait_for_status(self, elb_name, status):
        polling_increment_secs = 15
        max_retries = self.module.params.get('wait_timeout') // polling_increment_secs
        status_achieved = False

        for x in range(0, max_retries):
            try:
                response = get_elb(self.connection, self.module, elb_name)
                if response['State']['Code'] == status:
                    status_achieved = True
                    break
                else:
                    time.sleep(polling_increment_secs)
            except ClientError as e:
                self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        result = response

        return status_achieved, result

    def get_elb_attributes(self):
        """
        Get load balancer attributes

        :return:
        """

        try:
            elb_attributes = boto3_tag_list_to_ansible_dict(self.connection.describe_load_balancer_attributes(
                                                            LoadBalancerArn=self.elb['LoadBalancerArn'])['Attributes'])
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        # Replace '.' with '_' in attribute key names to make it more Ansibley
        return dict((k.replace('.', '_'), v) for k, v in elb_attributes.items())

    def update_elb_attributes(self):
        """
        Update the elb_attributes parameter
        :return:
        """
        self.elb_attributes = self.get_elb_attributes()

    def get_elb_tags(self):
        """
        Get load balancer tags

        :return:
        """

        try:
            return self.connection.describe_tags(ResourceArns=[self.elb['LoadBalancerArn']])['TagDescriptions'][0]['Tags']
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    def delete_tags(self, tags_to_delete):
        """
        Delete elb tags

        :return:
        """

        try:
            self.connection.remove_tags(ResourceArns=[self.elb['LoadBalancerArn']], TagKeys=tags_to_delete)
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        self.changed = True

    def modify_tags(self):
        """
        Modify elb tags

        :return:
        """

        try:
            self.connection.add_tags(ResourceArns=[self.elb['LoadBalancerArn']], Tags=self.tags)
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        self.changed = True

    def delete(self):
        """
        Delete elb
        :return:
        """

        try:
            self.connection.delete_load_balancer(LoadBalancerArn=self.elb['LoadBalancerArn'])
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        self.changed = True

    def compare_subnets(self):
        """
        Compare user subnets with current ELB subnets

        :return: bool True if they match otherwise False
        """

        subnet_id_list = []
        subnets = []

        # Check if we're dealing with subnets or subnet_mappings
        if self.subnets is not None:
            # We need to first get the subnet ID from the list
            subnets = self.subnets

        if self.subnet_mappings is not None:
            # Make a list from the subnet_mappings dict
            subnets_from_mappings = []
            for subnet_mapping in self.subnet_mappings:
                subnets.append(subnet_mapping['SubnetId'])

        for subnet in self.elb['AvailabilityZones']:
            subnet_id_list.append(subnet['SubnetId'])

        if set(subnet_id_list) != set(subnets):
            return False
        else:
            return True

    def modify_subnets(self):
        """
        Modify elb subnets to match module parameters
        :return:
        """

        try:
            self.connection.set_subnets(LoadBalancerArn=self.elb['LoadBalancerArn'], Subnets=self.subnets)
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        self.changed = True

    def update(self):
        """
        Update the elb from AWS
        :return:
        """

        self.elb = get_elb(self.connection, self.module, self.module.params.get("name"))
        self.elb['tags'] = self.get_elb_tags()


class ApplicationLoadBalancer(ElasticLoadBalancerV2):

    def __init__(self, connection, connection_ec2, module):
        """

        :param connection: boto3 connection
        :param module: Ansible module
        """
        super(ApplicationLoadBalancer, self).__init__(connection, module)

        self.connection_ec2 = connection_ec2

        # Ansible module parameters specific to ALBs
        self.type = 'application'
        if module.params.get('security_groups') is not None:
            try:
                self.security_groups = get_ec2_security_group_ids_from_names(module.params.get('security_groups'), self.connection_ec2, boto3=True)
            except ValueError as e:
                module.fail_json(msg=str(e), exception=traceback.format_exc())
            except ClientError as e:
                module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        else:
            self.security_groups = module.params.get('security_groups')
        self.access_logs_enabled = module.params.get("access_logs_enabled")
        self.access_logs_s3_bucket = module.params.get("access_logs_s3_bucket")
        self.access_logs_s3_prefix = module.params.get("access_logs_s3_prefix")
        self.idle_timeout = module.params.get("idle_timeout")

    def create_elb(self):
        """
        Create a load balancer
        :return:
        """

        # Required parameters
        params = dict()
        params['Name'] = self.name
        params['Type'] = self.type

        # Other parameters
        if self.subnets is not None:
            params['Subnets'] = self.subnets
        if self.security_groups is not None:
            params['SecurityGroups'] = self.security_groups
        params['Scheme'] = self.scheme
        if self.tags is not None:
            params['Tags'] = self.tags

        try:
            self.elb = self.connection.create_load_balancer(**params)['LoadBalancers'][0]
            self.changed = True
            self.new_load_balancer = True
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        if self.wait:
            status_achieved, new_elb = self.wait_for_status('active', self.name)

    def modify_elb_attributes(self):
        """
        Update ELB attributes if required
        :return:
        """

        update_attributes = []

        if self.access_logs_enabled and self.elb_attributes['access_logs_s3_enabled'] != "true":
            update_attributes.append({'Key': 'access_logs.s3.enabled', 'Value': "true"})
        if not self.access_logs_enabled and self.elb_attributes['access_logs_s3_enabled'] != "false":
            update_attributes.append({'Key': 'access_logs.s3.enabled', 'Value': 'false'})
        if self.access_logs_s3_bucket is not None and self.access_logs_s3_bucket != self.elb_attributes['access_logs_s3_bucket']:
            update_attributes.append({'Key': 'access_logs.s3.bucket', 'Value': self.access_logs_s3_bucket})
        if self.access_logs_s3_prefix is not None and self.access_logs_s3_prefix != self.elb_attributes['access_logs_s3_prefix']:
            update_attributes.append({'Key': 'access_logs.s3.prefix', 'Value': self.access_logs_s3_prefix})
        if self.deletion_protection and self.elb_attributes['deletion_protection_enabled'] != "true":
            update_attributes.append({'Key': 'deletion_protection.enabled', 'Value': "true"})
        if self.deletion_protection is not None and not self.deletion_protection and self.elb_attributes['deletion_protection_enabled'] != "false":
            update_attributes.append({'Key': 'deletion_protection.enabled', 'Value': "false"})
        if self.idle_timeout is not None and str(self.idle_timeout) != self.elb_attributes['idle_timeout_timeout_seconds']:
            update_attributes.append({'Key': 'idle_timeout.timeout_seconds', 'Value': str(self.idle_timeout)})

        if update_attributes:
            try:
                self.connection.modify_load_balancer_attributes(LoadBalancerArn=self.elb['LoadBalancerArn'], Attributes=update_attributes)
                self.changed = True
            except ClientError as e:
                # Something went wrong setting attributes. If this ELB was created during this task, delete it to leave a consistent state
                if self.new_load_balancer:
                    self.connection.delete_load_balancer(LoadBalancerArn=self.elb['LoadBalancerArn'])
                self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    def compare_security_groups(self):
        """
        Compare user security groups with current ELB security groups

        :return: bool True if they match otherwise False
        """

        if set(self.elb['SecurityGroups']) != set(self.security_groups):
            return False
        else:
            return True

    def modify_security_groups(self):
        """
        Modify elb security groups to match module parameters
        :return:
        """

        try:
            self.connection.set_security_groups(LoadBalancerArn=self.elb['LoadBalancerArn'], SecurityGroups=self.security_groups)
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        self.changed = True


class NetworkLoadBalancer(ElasticLoadBalancerV2):

    def __init__(self, connection, connection_ec2, module):

        """

        :param connection: boto3 connection
        :param module: Ansible module
        """
        super(NetworkLoadBalancer, self).__init__(connection, module)

        self.connection_ec2 = connection_ec2

        # Ansible module parameters specific to ALBs
        self.type = 'network'

    def create_elb(self):
        """
        Create a load balancer
        :return:
        """

        # Required parameters
        params = dict()
        params['Name'] = self.name
        params['Type'] = self.type

        # Other parameters
        if self.subnets is not None:
            params['Subnets'] = self.subnets
        params['Scheme'] = self.scheme
        if self.tags is not None:
            params['Tags'] = self.tags

        try:
            self.elb = self.connection.create_load_balancer(**params)['LoadBalancers'][0]
            self.changed = True
            self.new_load_balancer = True
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        if self.wait:
            status_achieved, new_elb = self.wait_for_status('active', self.name)

    def modify_elb_attributes(self):
        """
        Update ELB attributes if required
        :return:
        """

        update_attributes = []

        if self.deletion_protection and self.elb_attributes['deletion_protection_enabled'] != "true":
            update_attributes.append({'Key': 'deletion_protection.enabled', 'Value': "true"})
        if self.deletion_protection is not None and not self.deletion_protection and self.elb_attributes['deletion_protection_enabled'] != "false":
            update_attributes.append({'Key': 'deletion_protection.enabled', 'Value': "false"})

        if update_attributes:
            try:
                self.connection.modify_load_balancer_attributes(LoadBalancerArn=self.elb['LoadBalancerArn'], Attributes=update_attributes)
                self.changed = True
            except ClientError as e:
                # Something went wrong setting attributes. If this ELB was created during this task, delete it to leave a consistent state
                if self.new_load_balancer:
                    self.connection.delete_load_balancer(LoadBalancerArn=self.elb['LoadBalancerArn'])
                self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


class ELBListeners:

    def __init__(self, connection, module, elb_arn):

        self.connection = connection
        self.module = module
        self.elb_arn = elb_arn
        self.listeners = self._ensure_listeners_default_action_has_arn(module.params.get("listeners"))
        self.current_listeners = self._get_elb_listeners()
        self.purge_listeners = module.params.get("purge_listeners")
        self.changed = False

    def update(self):
        """
        Update the listeners for the ELB

        :return:
        """
        self.current_listeners = self._get_elb_listeners()

    def _get_elb_listeners(self):
        """
        Get ELB listeners

        :return:
        """

        try:
            listener_paginator = self.connection.get_paginator('describe_listeners')
            return (listener_paginator.paginate(LoadBalancerArn=self.elb_arn).build_full_result())['Listeners']
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    def _ensure_listeners_default_action_has_arn(self, listeners):
        """
        If a listener DefaultAction has been passed with a Target Group Name instead of ARN, lookup the ARN and
        replace the name.

        :param listeners: a list of listener dicts
        :return: the same list of dicts ensuring that each listener DefaultActions dict has TargetGroupArn key. If a TargetGroupName key exists, it is removed.
        """

        if not listeners:
            listeners = []

        for listener in listeners:
            if 'TargetGroupName' in listener['DefaultActions'][0]:
                listener['DefaultActions'][0]['TargetGroupArn'] = convert_tg_name_to_arn(self.connection, self.module,
                                                                                         listener['DefaultActions'][0]['TargetGroupName'])
                del listener['DefaultActions'][0]['TargetGroupName']

        return listeners

    def compare_listeners(self):
        """

        :return:
        """
        listeners_to_modify = []
        listeners_to_delete = []
        listeners_to_add = deepcopy(self.listeners)

        # Check each current listener port to see if it's been passed to the module
        for current_listener in self.current_listeners:
            current_listener_passed_to_module = False
            for new_listener in self.listeners[:]:
                new_listener['Port'] = int(new_listener['Port'])
                if current_listener['Port'] == new_listener['Port']:
                    current_listener_passed_to_module = True
                    # Remove what we match so that what is left can be marked as 'to be added'
                    listeners_to_add.remove(new_listener)
                    modified_listener = self._compare_listener(current_listener, new_listener)
                    if modified_listener:
                        modified_listener['Port'] = current_listener['Port']
                        modified_listener['ListenerArn'] = current_listener['ListenerArn']
                        listeners_to_modify.append(modified_listener)
                    break

            # If the current listener was not matched against passed listeners and purge is True, mark for removal
            if not current_listener_passed_to_module and self.purge_listeners:
                listeners_to_delete.append(current_listener['ListenerArn'])

        return listeners_to_add, listeners_to_modify, listeners_to_delete

    def _compare_listener(self, current_listener, new_listener):
        """
        Compare two listeners.

        :param current_listener:
        :param new_listener:
        :return:
        """

        modified_listener = {}

        # Port
        if current_listener['Port'] != new_listener['Port']:
            modified_listener['Port'] = new_listener['Port']

        # Protocol
        if current_listener['Protocol'] != new_listener['Protocol']:
            modified_listener['Protocol'] = new_listener['Protocol']

        # If Protocol is HTTPS, check additional attributes
        if current_listener['Protocol'] == 'HTTPS' and new_listener['Protocol'] == 'HTTPS':
            # Cert
            if current_listener['SslPolicy'] != new_listener['SslPolicy']:
                modified_listener['SslPolicy'] = new_listener['SslPolicy']
            if current_listener['Certificates'][0]['CertificateArn'] != new_listener['Certificates'][0]['CertificateArn']:
                modified_listener['Certificates'] = []
                modified_listener['Certificates'].append({})
                modified_listener['Certificates'][0]['CertificateArn'] = new_listener['Certificates'][0]['CertificateArn']
        elif current_listener['Protocol'] != 'HTTPS' and new_listener['Protocol'] == 'HTTPS':
            modified_listener['SslPolicy'] = new_listener['SslPolicy']
            modified_listener['Certificates'] = []
            modified_listener['Certificates'].append({})
            modified_listener['Certificates'][0]['CertificateArn'] = new_listener['Certificates'][0]['CertificateArn']

        # Default action
        #   We wont worry about the Action Type because it is always 'forward'
        if current_listener['DefaultActions'][0]['TargetGroupArn'] != new_listener['DefaultActions'][0]['TargetGroupArn']:
            modified_listener['DefaultActions'] = []
            modified_listener['DefaultActions'].append({})
            modified_listener['DefaultActions'][0]['TargetGroupArn'] = new_listener['DefaultActions'][0]['TargetGroupArn']
            modified_listener['DefaultActions'][0]['Type'] = 'forward'

        if modified_listener:
            return modified_listener
        else:
            return None


class ELBListener:

    def __init__(self, connection, module, listener, elb_arn):
        """

        :param connection:
        :param module:
        :param listener:
        :param elb_arn:
        """

        self.connection = connection
        self.module = module
        self.listener = listener
        self.elb_arn = elb_arn

    def add(self):

        try:
            # Rules is not a valid parameter for create_listener
            if 'Rules' in self.listener:
                self.listener.pop('Rules')
            self.connection.create_listener(LoadBalancerArn=self.elb_arn, **self.listener)
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    def modify(self):

        try:
            # Rules is not a valid parameter for modify_listener
            if 'Rules' in self.listener:
                self.listener.pop('Rules')
            self.connection.modify_listener(**self.listener)
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    def delete(self):

        try:
            self.connection.delete_listener(ListenerArn=self.listener)
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


class ELBListenerRules:

    def __init__(self, connection, module, elb_arn, listener_rules, listener_port):

        self.connection = connection
        self.module = module
        self.elb_arn = elb_arn
        self.rules = self._ensure_rules_action_has_arn(listener_rules)
        self.changed = False

        # Get listener based on port so we can use ARN
        self.current_listener = get_elb_listener(connection, module, elb_arn, listener_port)
        self.listener_arn = self.current_listener['ListenerArn']
        self.rules_to_add = deepcopy(self.rules)
        self.rules_to_modify = []
        self.rules_to_delete = []

        # If the listener exists (i.e. has an ARN) get rules for the listener
        if 'ListenerArn' in self.current_listener:
            self.current_rules = self._get_elb_listener_rules()
        else:
            self.current_rules = []

    def _ensure_rules_action_has_arn(self, rules):
        """
        If a rule Action has been passed with a Target Group Name instead of ARN, lookup the ARN and
        replace the name.

        :param rules: a list of rule dicts
        :return: the same list of dicts ensuring that each rule Actions dict has TargetGroupArn key. If a TargetGroupName key exists, it is removed.
        """

        for rule in rules:
            if 'TargetGroupName' in rule['Actions'][0]:
                rule['Actions'][0]['TargetGroupArn'] = convert_tg_name_to_arn(self.connection, self.module, rule['Actions'][0]['TargetGroupName'])
                del rule['Actions'][0]['TargetGroupName']

        return rules

    def _get_elb_listener_rules(self):

        try:
            return self.connection.describe_rules(ListenerArn=self.current_listener['ListenerArn'])['Rules']
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    def _compare_condition(self, current_conditions, condition):
        """

        :param current_conditions:
        :param condition:
        :return:
        """

        condition_found = False

        for current_condition in current_conditions:
            if current_condition['Field'] == condition['Field'] and current_condition['Values'][0] == condition['Values'][0]:
                condition_found = True
                break

        return condition_found

    def _compare_rule(self, current_rule, new_rule):
        """

        :return:
        """

        modified_rule = {}

        # Priority
        if current_rule['Priority'] != new_rule['Priority']:
            modified_rule['Priority'] = new_rule['Priority']

        # Actions
        #   We wont worry about the Action Type because it is always 'forward'
        if current_rule['Actions'][0]['TargetGroupArn'] != new_rule['Actions'][0]['TargetGroupArn']:
            modified_rule['Actions'] = []
            modified_rule['Actions'].append({})
            modified_rule['Actions'][0]['TargetGroupArn'] = new_rule['Actions'][0]['TargetGroupArn']
            modified_rule['Actions'][0]['Type'] = 'forward'

        # Conditions
        modified_conditions = []
        for condition in new_rule['Conditions']:
            if not self._compare_condition(current_rule['Conditions'], condition):
                modified_conditions.append(condition)

        if modified_conditions:
            modified_rule['Conditions'] = modified_conditions

        return modified_rule

    def compare_rules(self):
        """

        :return:
        """

        rules_to_modify = []
        rules_to_delete = []
        rules_to_add = deepcopy(self.rules)

        for current_rule in self.current_rules:
            current_rule_passed_to_module = False
            for new_rule in self.rules[:]:
                if current_rule['Priority'] == new_rule['Priority']:
                    current_rule_passed_to_module = True
                    # Remove what we match so that what is left can be marked as 'to be added'
                    rules_to_add.remove(new_rule)
                    modified_rule = self._compare_rule(current_rule, new_rule)
                    if modified_rule:
                        modified_rule['Priority'] = int(current_rule['Priority'])
                        modified_rule['RuleArn'] = current_rule['RuleArn']
                        modified_rule['Actions'] = new_rule['Actions']
                        modified_rule['Conditions'] = new_rule['Conditions']
                        rules_to_modify.append(modified_rule)
                    break

            # If the current rule was not matched against passed rules, mark for removal
            if not current_rule_passed_to_module and not current_rule['IsDefault']:
                rules_to_delete.append(current_rule['RuleArn'])

        return rules_to_add, rules_to_modify, rules_to_delete


class ELBListenerRule:

    def __init__(self, connection, module, rule, listener_arn):

        self.connection = connection
        self.module = module
        self.rule = rule
        self.listener_arn = listener_arn
        self.changed = False

    def create(self):
        """
        Create a listener rule

        :return:
        """

        try:
            self.rule['ListenerArn'] = self.listener_arn
            self.rule['Priority'] = int(self.rule['Priority'])
            self.connection.create_rule(**self.rule)
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        self.changed = True

    def modify(self):
        """
        Modify a listener rule

        :return:
        """

        try:
            del self.rule['Priority']
            self.connection.modify_rule(**self.rule)
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        self.changed = True

    def delete(self):
        """
        Delete a listener rule

        :return:
        """

        try:
            self.connection.delete_rule(RuleArn=self.rule['RuleArn'])
        except ClientError as e:
            self.module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        self.changed = True
