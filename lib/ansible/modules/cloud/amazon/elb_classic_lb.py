#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = """
---
module: elb_classic_lb
description:
  - Returns information about the load balancer.
  - Will be marked changed when called only if state is changed.
short_description: Creates or destroys Amazon ELB.
version_added: "1.5"
author:
  - "Jim Dalton (@jsdalton)"
options:
  state:
    description:
      - Create or destroy the ELB
    choices: ["present", "absent"]
    required: true
  name:
    description:
      - The name of the ELB
    required: true
  listeners:
    description:
      - List of ports/protocols for this ELB to listen on (see example)
  purge_listeners:
    description:
      - Purge existing listeners on ELB that are not found in listeners
    type: bool
    default: 'yes'
  instance_ids:
    description:
      - List of instance ids to attach to this ELB
    version_added: "2.1"
  purge_instance_ids:
    description:
      - Purge existing instance ids on ELB that are not found in instance_ids
    type: bool
    default: 'no'
    version_added: "2.1"
  zones:
    description:
      - List of availability zones to enable on this ELB
  purge_zones:
    description:
      - Purge existing availability zones on ELB that are not found in zones
    type: bool
    default: 'no'
  security_group_ids:
    description:
      - A list of security groups to apply to the elb
    version_added: "1.6"
  security_group_names:
    description:
      - A list of security group names to apply to the elb
    version_added: "2.0"
  health_check:
    description:
      - An associative array of health check configuration settings (see example)
  access_logs:
    description:
      - An associative array of access logs configuration settings (see example)
    version_added: "2.0"
  subnets:
    description:
      - A list of VPC subnets to use when creating ELB. Zones should be empty if using this.
    version_added: "1.7"
  purge_subnets:
    description:
      - Purge existing subnet on ELB that are not found in subnets
    type: bool
    default: 'no'
    version_added: "1.7"
  scheme:
    description:
      - The scheme to use when creating the ELB. For a private VPC-visible ELB use 'internal'.
        If you choose to update your scheme with a different value the ELB will be destroyed and
        recreated. To update scheme you must use the option wait.
    choices: ["internal", "internet-facing"]
    default: 'internet-facing'
    version_added: "1.7"
  validate_certs:
    description:
      - When set to C(no), SSL certificates will not be validated for boto versions >= 2.6.0.
    type: bool
    default: 'yes'
    version_added: "1.5"
  connection_draining_timeout:
    description:
      - Wait a specified timeout allowing connections to drain before terminating an instance
    version_added: "1.8"
  idle_timeout:
    description:
      - ELB connections from clients and to servers are timed out after this amount of time
    version_added: "2.0"
  cross_az_load_balancing:
    description:
      - Distribute load across all configured Availability Zones
    type: bool
    default: 'no'
    version_added: "1.8"
  stickiness:
    description:
      - An associative array of stickiness policy settings. Policy will be applied to all listeners ( see example )
    version_added: "2.0"
  wait:
    description:
      - When specified, Ansible will check the status of the load balancer to ensure it has been successfully
        removed from AWS.
    type: bool
    default: 'no'
    version_added: "2.1"
  wait_timeout:
    description:
      - Used in conjunction with wait. Number of seconds to wait for the elb to be terminated.
        A maximum of 600 seconds (10 minutes) is allowed.
    default: 60
    version_added: "2.1"
  tags:
    description:
      - An associative array of tags. To delete all tags, supply an empty dict.
    version_added: "2.1"

extends_documentation_fragment:
    - aws
    - ec2
"""

EXAMPLES = """
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

# Basic provisioning example (non-VPC)

- elb_classic_lb:
    name: "test-please-delete"
    state: present
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http # options are http, https, ssl, tcp
        load_balancer_port: 80
        instance_port: 80
        proxy_protocol: True
      - protocol: https
        load_balancer_port: 443
        instance_protocol: http # optional, defaults to value of protocol setting
        instance_port: 80
        # ssl certificate required for https or ssl
        ssl_certificate_id: "arn:aws:iam::123456789012:server-certificate/company/servercerts/ProdServerCert"
  delegate_to: localhost

# Internal ELB example

- elb_classic_lb:
    name: "test-vpc"
    scheme: internal
    state: present
    instance_ids:
      - i-abcd1234
    purge_instance_ids: true
    subnets:
      - subnet-abcd1234
      - subnet-1a2b3c4d
    listeners:
      - protocol: http # options are http, https, ssl, tcp
        load_balancer_port: 80
        instance_port: 80
  delegate_to: localhost

# Configure a health check and the access logs
- elb_classic_lb:
    name: "test-please-delete"
    state: present
    zones:
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    health_check:
        ping_protocol: http # options are http, https, ssl, tcp
        ping_port: 80
        ping_path: "/index.html" # not required for tcp or ssl
        response_timeout: 5 # seconds
        interval: 30 # seconds
        unhealthy_threshold: 2
        healthy_threshold: 10
    access_logs:
        interval: 5 # minutes (defaults to 60)
        s3_location: "my-bucket" # This value is required if access_logs is set
        s3_prefix: "logs"
  delegate_to: localhost

# Ensure ELB is gone
- elb_classic_lb:
    name: "test-please-delete"
    state: absent
  delegate_to: localhost

# Ensure ELB is gone and wait for check (for default timeout)
- elb_classic_lb:
    name: "test-please-delete"
    state: absent
    wait: yes
  delegate_to: localhost

# Ensure ELB is gone and wait for check with timeout value
- elb_classic_lb:
    name: "test-please-delete"
    state: absent
    wait: yes
    wait_timeout: 600
  delegate_to: localhost

# Normally, this module will purge any listeners that exist on the ELB
# but aren't specified in the listeners parameter. If purge_listeners is
# false it leaves them alone
- elb_classic_lb:
    name: "test-please-delete"
    state: present
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    purge_listeners: no
  delegate_to: localhost

# Normally, this module will leave availability zones that are enabled
# on the ELB alone. If purge_zones is true, then any extraneous zones
# will be removed
- elb_classic_lb:
    name: "test-please-delete"
    state: present
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    purge_zones: yes
  delegate_to: localhost

# Creates a ELB and assigns a list of subnets to it.
- elb_classic_lb:
    state: present
    name: 'New ELB'
    security_group_ids: 'sg-123456, sg-67890'
    region: us-west-2
    subnets: 'subnet-123456,subnet-67890'
    purge_subnets: yes
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
  delegate_to: localhost

# Create an ELB with connection draining, increased idle timeout and cross availability
# zone load balancing
- elb_classic_lb:
    name: "New ELB"
    state: present
    connection_draining_timeout: 60
    idle_timeout: 300
    cross_az_load_balancing: "yes"
    region: us-east-1
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
  delegate_to: localhost

# Create an ELB with load balancer stickiness enabled
- elb_classic_lb:
    name: "New ELB"
    state: present
    region: us-east-1
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    stickiness:
      type: loadbalancer
      enabled: yes
      expiration: 300
  delegate_to: localhost

# Create an ELB with application stickiness enabled
- elb_classic_lb:
    name: "New ELB"
    state: present
    region: us-east-1
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    stickiness:
      type: application
      enabled: yes
      cookie: SESSIONID
  delegate_to: localhost

# Create an ELB and add tags
- elb_classic_lb:
    name: "New ELB"
    state: present
    region: us-east-1
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    tags:
      Name: "New ELB"
      stack: "production"
      client: "Bob"
  delegate_to: localhost

# Delete all tags from an ELB
- elb_classic_lb:
    name: "New ELB"
    state: present
    region: us-east-1
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    tags: {}
  delegate_to: localhost
"""

import random
import time
import traceback

try:
    import boto
    import boto.ec2.elb
    import boto.ec2.elb.attributes
    import boto.vpc
    from boto.ec2.elb.healthcheck import HealthCheck
    from boto.ec2.tag import Tag
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, connect_to_aws, AnsibleAWSError, get_aws_connection_info
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native


def _throttleable_operation(max_retries):
    def _operation_wrapper(op):
        def _do_op(*args, **kwargs):
            retry = 0
            while True:
                try:
                    return op(*args, **kwargs)
                except boto.exception.BotoServerError as e:
                    if retry < max_retries and e.code in \
                            ("Throttling", "RequestLimitExceeded"):
                        retry = retry + 1
                        time.sleep(min(random.random() * (2 ** retry), 300))
                        continue
                    else:
                        raise
        return _do_op
    return _operation_wrapper


def _get_vpc_connection(module, region, aws_connect_params):
    try:
        return connect_to_aws(boto.vpc, region, **aws_connect_params)
    except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
        module.fail_json(msg=str(e))


_THROTTLING_RETRIES = 5


class ElbManager(object):
    """Handles ELB creation and destruction"""

    def __init__(self, module, name, listeners=None, purge_listeners=None,
                 zones=None, purge_zones=None, security_group_ids=None,
                 health_check=None, subnets=None, purge_subnets=None,
                 scheme="internet-facing", connection_draining_timeout=None,
                 idle_timeout=None,
                 cross_az_load_balancing=None, access_logs=None,
                 stickiness=None, wait=None, wait_timeout=None, tags=None,
                 region=None,
                 instance_ids=None, purge_instance_ids=None, **aws_connect_params):

        self.module = module
        self.name = name
        self.listeners = listeners
        self.purge_listeners = purge_listeners
        self.instance_ids = instance_ids
        self.purge_instance_ids = purge_instance_ids
        self.zones = zones
        self.purge_zones = purge_zones
        self.security_group_ids = security_group_ids
        self.health_check = health_check
        self.subnets = subnets
        self.purge_subnets = purge_subnets
        self.scheme = scheme
        self.connection_draining_timeout = connection_draining_timeout
        self.idle_timeout = idle_timeout
        self.cross_az_load_balancing = cross_az_load_balancing
        self.access_logs = access_logs
        self.stickiness = stickiness
        self.wait = wait
        self.wait_timeout = wait_timeout
        self.tags = tags

        self.aws_connect_params = aws_connect_params
        self.region = region

        self.changed = False
        self.status = 'gone'
        self.elb_conn = self._get_elb_connection()

        try:
            self.elb = self._get_elb()
        except boto.exception.BotoServerError as e:
            module.fail_json(msg='unable to get all load balancers: %s' % e.message, exception=traceback.format_exc())

        self.ec2_conn = self._get_ec2_connection()

    @_throttleable_operation(_THROTTLING_RETRIES)
    def ensure_ok(self):
        """Create the ELB"""
        if not self.elb:
            # Zones and listeners will be added at creation
            self._create_elb()
        else:
            if self._get_scheme():
                # the only way to change the scheme is by recreating the resource
                self.ensure_gone()
                self._create_elb()
            else:
                self._set_zones()
                self._set_security_groups()
                self._set_elb_listeners()
                self._set_subnets()
        self._set_health_check()
        # boto has introduced support for some ELB attributes in
        # different versions, so we check first before trying to
        # set them to avoid errors
        if self._check_attribute_support('connection_draining'):
            self._set_connection_draining_timeout()
        if self._check_attribute_support('connecting_settings'):
            self._set_idle_timeout()
        if self._check_attribute_support('cross_zone_load_balancing'):
            self._set_cross_az_load_balancing()
        if self._check_attribute_support('access_log'):
            self._set_access_log()
        # add sitcky options
        self.select_stickiness_policy()

        # ensure backend server policies are correct
        self._set_backend_policies()
        # set/remove instance ids
        self._set_instance_ids()

        self._set_tags()

    def ensure_gone(self):
        """Destroy the ELB"""
        if self.elb:
            self._delete_elb()
            if self.wait:
                elb_removed = self._wait_for_elb_removed()
                # Unfortunately even though the ELB itself is removed quickly
                # the interfaces take longer so reliant security groups cannot
                # be deleted until the interface has registered as removed.
                elb_interface_removed = self._wait_for_elb_interface_removed()
                if not (elb_removed and elb_interface_removed):
                    self.module.fail_json(msg='Timed out waiting for removal of load balancer.')

    def get_info(self):
        try:
            check_elb = self.elb_conn.get_all_load_balancers(self.name)[0]
        except:
            check_elb = None

        if not check_elb:
            info = {
                'name': self.name,
                'status': self.status,
                'region': self.region
            }
        else:
            try:
                lb_cookie_policy = check_elb.policies.lb_cookie_stickiness_policies[0].__dict__['policy_name']
            except:
                lb_cookie_policy = None
            try:
                app_cookie_policy = check_elb.policies.app_cookie_stickiness_policies[0].__dict__['policy_name']
            except:
                app_cookie_policy = None

            info = {
                'name': check_elb.name,
                'dns_name': check_elb.dns_name,
                'zones': check_elb.availability_zones,
                'security_group_ids': check_elb.security_groups,
                'status': self.status,
                'subnets': self.subnets,
                'scheme': check_elb.scheme,
                'hosted_zone_name': check_elb.canonical_hosted_zone_name,
                'hosted_zone_id': check_elb.canonical_hosted_zone_name_id,
                'lb_cookie_policy': lb_cookie_policy,
                'app_cookie_policy': app_cookie_policy,
                'proxy_policy': self._get_proxy_protocol_policy(),
                'backends': self._get_backend_policies(),
                'instances': [instance.id for instance in check_elb.instances],
                'out_of_service_count': 0,
                'in_service_count': 0,
                'unknown_instance_state_count': 0,
                'region': self.region
            }

            # status of instances behind the ELB
            if info['instances']:
                info['instance_health'] = [dict(
                    instance_id=instance_state.instance_id,
                    reason_code=instance_state.reason_code,
                    state=instance_state.state
                ) for instance_state in self.elb_conn.describe_instance_health(self.name)]
            else:
                info['instance_health'] = []

            # instance state counts: InService or OutOfService
            if info['instance_health']:
                for instance_state in info['instance_health']:
                    if instance_state['state'] == "InService":
                        info['in_service_count'] += 1
                    elif instance_state['state'] == "OutOfService":
                        info['out_of_service_count'] += 1
                    else:
                        info['unknown_instance_state_count'] += 1

            if check_elb.health_check:
                info['health_check'] = {
                    'target': check_elb.health_check.target,
                    'interval': check_elb.health_check.interval,
                    'timeout': check_elb.health_check.timeout,
                    'healthy_threshold': check_elb.health_check.healthy_threshold,
                    'unhealthy_threshold': check_elb.health_check.unhealthy_threshold,
                }

            if check_elb.listeners:
                info['listeners'] = [self._api_listener_as_tuple(l)
                                     for l in check_elb.listeners]
            elif self.status == 'created':
                # When creating a new ELB, listeners don't show in the
                # immediately returned result, so just include the
                # ones that were added
                info['listeners'] = [self._listener_as_tuple(l)
                                     for l in self.listeners]
            else:
                info['listeners'] = []

            if self._check_attribute_support('connection_draining'):
                info['connection_draining_timeout'] = int(self.elb_conn.get_lb_attribute(self.name, 'ConnectionDraining').timeout)

            if self._check_attribute_support('connecting_settings'):
                info['idle_timeout'] = self.elb_conn.get_lb_attribute(self.name, 'ConnectingSettings').idle_timeout

            if self._check_attribute_support('cross_zone_load_balancing'):
                is_cross_az_lb_enabled = self.elb_conn.get_lb_attribute(self.name, 'CrossZoneLoadBalancing')
                if is_cross_az_lb_enabled:
                    info['cross_az_load_balancing'] = 'yes'
                else:
                    info['cross_az_load_balancing'] = 'no'

            # return stickiness info?

            info['tags'] = self.tags

        return info

    @_throttleable_operation(_THROTTLING_RETRIES)
    def _wait_for_elb_removed(self):
        polling_increment_secs = 15
        max_retries = (self.wait_timeout // polling_increment_secs)
        status_achieved = False

        for x in range(0, max_retries):
            try:
                self.elb_conn.get_all_lb_attributes(self.name)
            except (boto.exception.BotoServerError, Exception) as e:
                if "LoadBalancerNotFound" in e.code:
                    status_achieved = True
                    break
                else:
                    time.sleep(polling_increment_secs)

        return status_achieved

    @_throttleable_operation(_THROTTLING_RETRIES)
    def _wait_for_elb_interface_removed(self):
        polling_increment_secs = 15
        max_retries = (self.wait_timeout // polling_increment_secs)
        status_achieved = False

        elb_interfaces = self.ec2_conn.get_all_network_interfaces(
            filters={'attachment.instance-owner-id': 'amazon-elb',
                     'description': 'ELB {0}'.format(self.name)})

        for x in range(0, max_retries):
            for interface in elb_interfaces:
                try:
                    result = self.ec2_conn.get_all_network_interfaces(interface.id)
                    if result == []:
                        status_achieved = True
                        break
                    else:
                        time.sleep(polling_increment_secs)
                except (boto.exception.BotoServerError, Exception) as e:
                    if 'InvalidNetworkInterfaceID' in e.code:
                        status_achieved = True
                        break
                    else:
                        self.module.fail_json(msg=to_native(e), exception=traceback.format_exc())

        return status_achieved

    @_throttleable_operation(_THROTTLING_RETRIES)
    def _get_elb(self):
        elbs = self.elb_conn.get_all_load_balancers()
        for elb in elbs:
            if self.name == elb.name:
                self.status = 'ok'
                return elb

    def _get_elb_connection(self):
        try:
            return connect_to_aws(boto.ec2.elb, self.region,
                                  **self.aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            self.module.fail_json(msg=str(e))

    def _get_ec2_connection(self):
        try:
            return connect_to_aws(boto.ec2, self.region,
                                  **self.aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, Exception) as e:
            self.module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    @_throttleable_operation(_THROTTLING_RETRIES)
    def _delete_elb(self):
        # True if succeeds, exception raised if not
        result = self.elb_conn.delete_load_balancer(name=self.name)
        if result:
            self.changed = True
            self.status = 'deleted'

    def _create_elb(self):
        listeners = [self._listener_as_tuple(l) for l in self.listeners]
        self.elb = self.elb_conn.create_load_balancer(name=self.name,
                                                      zones=self.zones,
                                                      security_groups=self.security_group_ids,
                                                      complex_listeners=listeners,
                                                      subnets=self.subnets,
                                                      scheme=self.scheme)
        if self.elb:
            # HACK: Work around a boto bug in which the listeners attribute is
            # always set to the listeners argument to create_load_balancer, and
            # not the complex_listeners
            # We're not doing a self.elb = self._get_elb here because there
            # might be eventual consistency issues and it doesn't necessarily
            # make sense to wait until the ELB gets returned from the EC2 API.
            # This is necessary in the event we hit the throttling errors and
            # need to retry ensure_ok
            # See https://github.com/boto/boto/issues/3526
            self.elb.listeners = self.listeners
            self.changed = True
            self.status = 'created'

    def _create_elb_listeners(self, listeners):
        """Takes a list of listener tuples and creates them"""
        # True if succeeds, exception raised if not
        self.changed = self.elb_conn.create_load_balancer_listeners(self.name,
                                                                    complex_listeners=listeners)

    def _delete_elb_listeners(self, listeners):
        """Takes a list of listener tuples and deletes them from the elb"""
        ports = [l[0] for l in listeners]

        # True if succeeds, exception raised if not
        self.changed = self.elb_conn.delete_load_balancer_listeners(self.name,
                                                                    ports)

    def _set_elb_listeners(self):
        """
        Creates listeners specified by self.listeners; overwrites existing
        listeners on these ports; removes extraneous listeners
        """
        listeners_to_add = []
        listeners_to_remove = []
        listeners_to_keep = []

        # Check for any listeners we need to create or overwrite
        for listener in self.listeners:
            listener_as_tuple = self._listener_as_tuple(listener)

            # First we loop through existing listeners to see if one is
            # already specified for this port
            existing_listener_found = None
            for existing_listener in self.elb.listeners:
                # Since ELB allows only one listener on each incoming port, a
                # single match on the incoming port is all we're looking for
                if existing_listener[0] == int(listener['load_balancer_port']):
                    existing_listener_found = self._api_listener_as_tuple(existing_listener)
                    break

            if existing_listener_found:
                # Does it match exactly?
                if listener_as_tuple != existing_listener_found:
                    # The ports are the same but something else is different,
                    # so we'll remove the existing one and add the new one
                    listeners_to_remove.append(existing_listener_found)
                    listeners_to_add.append(listener_as_tuple)
                else:
                    # We already have this listener, so we're going to keep it
                    listeners_to_keep.append(existing_listener_found)
            else:
                # We didn't find an existing listener, so just add the new one
                listeners_to_add.append(listener_as_tuple)

        # Check for any extraneous listeners we need to remove, if desired
        if self.purge_listeners:
            for existing_listener in self.elb.listeners:
                existing_listener_tuple = self._api_listener_as_tuple(existing_listener)
                if existing_listener_tuple in listeners_to_remove:
                    # Already queued for removal
                    continue
                if existing_listener_tuple in listeners_to_keep:
                    # Keep this one around
                    continue
                # Since we're not already removing it and we don't need to keep
                # it, let's get rid of it
                listeners_to_remove.append(existing_listener_tuple)

        if listeners_to_remove:
            self._delete_elb_listeners(listeners_to_remove)

        if listeners_to_add:
            self._create_elb_listeners(listeners_to_add)

    def _api_listener_as_tuple(self, listener):
        """Adds ssl_certificate_id to ELB API tuple if present"""
        base_tuple = listener.get_complex_tuple()
        if listener.ssl_certificate_id and len(base_tuple) < 5:
            return base_tuple + (listener.ssl_certificate_id,)
        return base_tuple

    def _listener_as_tuple(self, listener):
        """Formats listener as a 4- or 5-tuples, in the order specified by the
        ELB API"""
        # N.B. string manipulations on protocols below (str(), upper()) is to
        # ensure format matches output from ELB API
        listener_list = [
            int(listener['load_balancer_port']),
            int(listener['instance_port']),
            str(listener['protocol'].upper()),
        ]

        # Instance protocol is not required by ELB API; it defaults to match
        # load balancer protocol. We'll mimic that behavior here
        if 'instance_protocol' in listener:
            listener_list.append(str(listener['instance_protocol'].upper()))
        else:
            listener_list.append(str(listener['protocol'].upper()))

        if 'ssl_certificate_id' in listener:
            listener_list.append(str(listener['ssl_certificate_id']))

        return tuple(listener_list)

    def _enable_zones(self, zones):
        try:
            self.elb.enable_zones(zones)
        except boto.exception.BotoServerError as e:
            self.module.fail_json(msg='unable to enable zones: %s' % e.message, exception=traceback.format_exc())

        self.changed = True

    def _disable_zones(self, zones):
        try:
            self.elb.disable_zones(zones)
        except boto.exception.BotoServerError as e:
            self.module.fail_json(msg='unable to disable zones: %s' % e.message, exception=traceback.format_exc())
        self.changed = True

    def _attach_subnets(self, subnets):
        self.elb_conn.attach_lb_to_subnets(self.name, subnets)
        self.changed = True

    def _detach_subnets(self, subnets):
        self.elb_conn.detach_lb_from_subnets(self.name, subnets)
        self.changed = True

    def _set_subnets(self):
        """Determine which subnets need to be attached or detached on the ELB"""
        if self.subnets:
            if self.purge_subnets:
                subnets_to_detach = list(set(self.elb.subnets) - set(self.subnets))
                subnets_to_attach = list(set(self.subnets) - set(self.elb.subnets))
            else:
                subnets_to_detach = None
                subnets_to_attach = list(set(self.subnets) - set(self.elb.subnets))

            if subnets_to_attach:
                self._attach_subnets(subnets_to_attach)
            if subnets_to_detach:
                self._detach_subnets(subnets_to_detach)

    def _get_scheme(self):
        """Determine if the current scheme is different than the scheme of the ELB"""
        if self.scheme:
            if self.elb.scheme != self.scheme:
                if not self.wait:
                    self.module.fail_json(msg="Unable to modify scheme without using the wait option")
                return True
        return False

    def _set_zones(self):
        """Determine which zones need to be enabled or disabled on the ELB"""
        if self.zones:
            if self.purge_zones:
                zones_to_disable = list(set(self.elb.availability_zones) -
                                        set(self.zones))
                zones_to_enable = list(set(self.zones) -
                                       set(self.elb.availability_zones))
            else:
                zones_to_disable = None
                zones_to_enable = list(set(self.zones) -
                                       set(self.elb.availability_zones))
            if zones_to_enable:
                self._enable_zones(zones_to_enable)
            # N.B. This must come second, in case it would have removed all zones
            if zones_to_disable:
                self._disable_zones(zones_to_disable)

    def _set_security_groups(self):
        if self.security_group_ids is not None and set(self.elb.security_groups) != set(self.security_group_ids):
            self.elb_conn.apply_security_groups_to_lb(self.name, self.security_group_ids)
            self.changed = True

    def _set_health_check(self):
        """Set health check values on ELB as needed"""
        if self.health_check:
            # This just makes it easier to compare each of the attributes
            # and look for changes. Keys are attributes of the current
            # health_check; values are desired values of new health_check
            health_check_config = {
                "target": self._get_health_check_target(),
                "timeout": self.health_check['response_timeout'],
                "interval": self.health_check['interval'],
                "unhealthy_threshold": self.health_check['unhealthy_threshold'],
                "healthy_threshold": self.health_check['healthy_threshold'],
            }

            update_health_check = False

            # The health_check attribute is *not* set on newly created
            # ELBs! So we have to create our own.
            if not self.elb.health_check:
                self.elb.health_check = HealthCheck()

            for attr, desired_value in health_check_config.items():
                if getattr(self.elb.health_check, attr) != desired_value:
                    setattr(self.elb.health_check, attr, desired_value)
                    update_health_check = True

            if update_health_check:
                self.elb.configure_health_check(self.elb.health_check)
                self.changed = True

    def _check_attribute_support(self, attr):
        return hasattr(boto.ec2.elb.attributes.LbAttributes(), attr)

    def _set_cross_az_load_balancing(self):
        attributes = self.elb.get_attributes()
        if self.cross_az_load_balancing:
            if not attributes.cross_zone_load_balancing.enabled:
                self.changed = True
            attributes.cross_zone_load_balancing.enabled = True
        else:
            if attributes.cross_zone_load_balancing.enabled:
                self.changed = True
            attributes.cross_zone_load_balancing.enabled = False
        self.elb_conn.modify_lb_attribute(self.name, 'CrossZoneLoadBalancing',
                                          attributes.cross_zone_load_balancing.enabled)

    def _set_access_log(self):
        attributes = self.elb.get_attributes()
        if self.access_logs:
            if 's3_location' not in self.access_logs:
                self.module.fail_json(msg='s3_location information required')

            access_logs_config = {
                "enabled": True,
                "s3_bucket_name": self.access_logs['s3_location'],
                "s3_bucket_prefix": self.access_logs.get('s3_prefix', ''),
                "emit_interval": self.access_logs.get('interval', 60),
            }

            update_access_logs_config = False
            for attr, desired_value in access_logs_config.items():
                if getattr(attributes.access_log, attr) != desired_value:
                    setattr(attributes.access_log, attr, desired_value)
                    update_access_logs_config = True
            if update_access_logs_config:
                self.elb_conn.modify_lb_attribute(self.name, 'AccessLog', attributes.access_log)
                self.changed = True
        elif attributes.access_log.enabled:
            attributes.access_log.enabled = False
            self.changed = True
            self.elb_conn.modify_lb_attribute(self.name, 'AccessLog', attributes.access_log)

    def _set_connection_draining_timeout(self):
        attributes = self.elb.get_attributes()
        if self.connection_draining_timeout is not None:
            if not attributes.connection_draining.enabled or \
                    attributes.connection_draining.timeout != self.connection_draining_timeout:
                self.changed = True
            attributes.connection_draining.enabled = True
            attributes.connection_draining.timeout = self.connection_draining_timeout
            self.elb_conn.modify_lb_attribute(self.name, 'ConnectionDraining', attributes.connection_draining)
        else:
            if attributes.connection_draining.enabled:
                self.changed = True
            attributes.connection_draining.enabled = False
            self.elb_conn.modify_lb_attribute(self.name, 'ConnectionDraining', attributes.connection_draining)

    def _set_idle_timeout(self):
        attributes = self.elb.get_attributes()
        if self.idle_timeout is not None:
            if attributes.connecting_settings.idle_timeout != self.idle_timeout:
                self.changed = True
            attributes.connecting_settings.idle_timeout = self.idle_timeout
            self.elb_conn.modify_lb_attribute(self.name, 'ConnectingSettings', attributes.connecting_settings)

    def _policy_name(self, policy_type):
        return 'elb-classic-lb-{0}'.format(to_native(policy_type, errors='surrogate_or_strict'))

    def _create_policy(self, policy_param, policy_meth, policy):
        getattr(self.elb_conn, policy_meth)(policy_param, self.elb.name, policy)

    def _delete_policy(self, elb_name, policy):
        self.elb_conn.delete_lb_policy(elb_name, policy)

    def _update_policy(self, policy_param, policy_meth, policy_attr, policy):
        self._delete_policy(self.elb.name, policy)
        self._create_policy(policy_param, policy_meth, policy)

    def _set_listener_policy(self, listeners_dict, policy=None):
        policy = [] if policy is None else policy

        for listener_port in listeners_dict:
            if listeners_dict[listener_port].startswith('HTTP'):
                self.elb_conn.set_lb_policies_of_listener(self.elb.name, listener_port, policy)

    def _set_stickiness_policy(self, elb_info, listeners_dict, policy, **policy_attrs):
        for p in getattr(elb_info.policies, policy_attrs['attr']):
            if str(p.__dict__['policy_name']) == str(policy[0]):
                if str(p.__dict__[policy_attrs['dict_key']]) != str(policy_attrs['param_value'] or 0):
                    self._set_listener_policy(listeners_dict)
                    self._update_policy(policy_attrs['param_value'], policy_attrs['method'], policy_attrs['attr'], policy[0])
                    self.changed = True
                break
        else:
            self._create_policy(policy_attrs['param_value'], policy_attrs['method'], policy[0])
            self.changed = True

        self._set_listener_policy(listeners_dict, policy)

    def select_stickiness_policy(self):
        if self.stickiness:

            if 'cookie' in self.stickiness and 'expiration' in self.stickiness:
                self.module.fail_json(msg='\'cookie\' and \'expiration\' can not be set at the same time')

            elb_info = self.elb_conn.get_all_load_balancers(self.elb.name)[0]
            d = {}
            for listener in elb_info.listeners:
                d[listener[0]] = listener[2]
            listeners_dict = d

            if self.stickiness['type'] == 'loadbalancer':
                policy = []
                policy_type = 'LBCookieStickinessPolicyType'

                if self.module.boolean(self.stickiness['enabled']):

                    if 'expiration' not in self.stickiness:
                        self.module.fail_json(msg='expiration must be set when type is loadbalancer')

                    try:
                        expiration = self.stickiness['expiration'] if int(self.stickiness['expiration']) else None
                    except ValueError:
                        self.module.fail_json(msg='expiration must be set to an integer')

                    policy_attrs = {
                        'type': policy_type,
                        'attr': 'lb_cookie_stickiness_policies',
                        'method': 'create_lb_cookie_stickiness_policy',
                        'dict_key': 'cookie_expiration_period',
                        'param_value': expiration
                    }
                    policy.append(self._policy_name(policy_attrs['type']))

                    self._set_stickiness_policy(elb_info, listeners_dict, policy, **policy_attrs)
                elif not self.module.boolean(self.stickiness['enabled']):
                    if len(elb_info.policies.lb_cookie_stickiness_policies):
                        if elb_info.policies.lb_cookie_stickiness_policies[0].policy_name == self._policy_name(policy_type):
                            self.changed = True
                    else:
                        self.changed = False
                    self._set_listener_policy(listeners_dict)
                    self._delete_policy(self.elb.name, self._policy_name(policy_type))

            elif self.stickiness['type'] == 'application':
                policy = []
                policy_type = 'AppCookieStickinessPolicyType'
                if self.module.boolean(self.stickiness['enabled']):

                    if 'cookie' not in self.stickiness:
                        self.module.fail_json(msg='cookie must be set when type is application')

                    policy_attrs = {
                        'type': policy_type,
                        'attr': 'app_cookie_stickiness_policies',
                        'method': 'create_app_cookie_stickiness_policy',
                        'dict_key': 'cookie_name',
                        'param_value': self.stickiness['cookie']
                    }
                    policy.append(self._policy_name(policy_attrs['type']))
                    self._set_stickiness_policy(elb_info, listeners_dict, policy, **policy_attrs)
                elif not self.module.boolean(self.stickiness['enabled']):
                    if len(elb_info.policies.app_cookie_stickiness_policies):
                        if elb_info.policies.app_cookie_stickiness_policies[0].policy_name == self._policy_name(policy_type):
                            self.changed = True
                    self._set_listener_policy(listeners_dict)
                    self._delete_policy(self.elb.name, self._policy_name(policy_type))

            else:
                self._set_listener_policy(listeners_dict)

    def _get_backend_policies(self):
        """Get a list of backend policies"""
        policies = []
        if self.elb.backends is not None:
            for backend in self.elb.backends:
                if backend.policies is not None:
                    for policy in backend.policies:
                        policies.append(str(backend.instance_port) + ':' + policy.policy_name)

        return policies

    def _set_backend_policies(self):
        """Sets policies for all backends"""
        ensure_proxy_protocol = False
        replace = []
        backend_policies = self._get_backend_policies()

        # Find out what needs to be changed
        for listener in self.listeners:
            want = False

            if 'proxy_protocol' in listener and listener['proxy_protocol']:
                ensure_proxy_protocol = True
                want = True

            if str(listener['instance_port']) + ':ProxyProtocol-policy' in backend_policies:
                if not want:
                    replace.append({'port': listener['instance_port'], 'policies': []})
            elif want:
                replace.append({'port': listener['instance_port'], 'policies': ['ProxyProtocol-policy']})

        # enable or disable proxy protocol
        if ensure_proxy_protocol:
            self._set_proxy_protocol_policy()

        # Make the backend policies so
        for item in replace:
            self.elb_conn.set_lb_policies_of_backend_server(self.elb.name, item['port'], item['policies'])
            self.changed = True

    def _get_proxy_protocol_policy(self):
        """Find out if the elb has a proxy protocol enabled"""
        if self.elb.policies is not None and self.elb.policies.other_policies is not None:
            for policy in self.elb.policies.other_policies:
                if policy.policy_name == 'ProxyProtocol-policy':
                    return policy.policy_name

        return None

    def _set_proxy_protocol_policy(self):
        """Install a proxy protocol policy if needed"""
        proxy_policy = self._get_proxy_protocol_policy()

        if proxy_policy is None:
            self.elb_conn.create_lb_policy(
                self.elb.name, 'ProxyProtocol-policy', 'ProxyProtocolPolicyType', {'ProxyProtocol': True}
            )
            self.changed = True

        # TODO: remove proxy protocol policy if not needed anymore? There is no side effect to leaving it there

    def _diff_list(self, a, b):
        """Find the entries in list a that are not in list b"""
        b = set(b)
        return [aa for aa in a if aa not in b]

    def _get_instance_ids(self):
        """Get the current list of instance ids installed in the elb"""
        instances = []
        if self.elb.instances is not None:
            for instance in self.elb.instances:
                instances.append(instance.id)

        return instances

    def _set_instance_ids(self):
        """Register or deregister instances from an lb instance"""
        assert_instances = self.instance_ids or []

        has_instances = self._get_instance_ids()

        add_instances = self._diff_list(assert_instances, has_instances)
        if add_instances:
            self.elb_conn.register_instances(self.elb.name, add_instances)
            self.changed = True

        if self.purge_instance_ids:
            remove_instances = self._diff_list(has_instances, assert_instances)
            if remove_instances:
                self.elb_conn.deregister_instances(self.elb.name, remove_instances)
                self.changed = True

    def _set_tags(self):
        """Add/Delete tags"""
        if self.tags is None:
            return

        params = {'LoadBalancerNames.member.1': self.name}

        tagdict = dict()

        # get the current list of tags from the ELB, if ELB exists
        if self.elb:
            current_tags = self.elb_conn.get_list('DescribeTags', params,
                                                  [('member', Tag)])
            tagdict = dict((tag.Key, tag.Value) for tag in current_tags
                           if hasattr(tag, 'Key'))

        # Add missing tags
        dictact = dict(set(self.tags.items()) - set(tagdict.items()))
        if dictact:
            for i, key in enumerate(dictact):
                params['Tags.member.%d.Key' % (i + 1)] = key
                params['Tags.member.%d.Value' % (i + 1)] = dictact[key]

            self.elb_conn.make_request('AddTags', params)
            self.changed = True

        # Remove extra tags
        dictact = dict(set(tagdict.items()) - set(self.tags.items()))
        if dictact:
            for i, key in enumerate(dictact):
                params['Tags.member.%d.Key' % (i + 1)] = key

            self.elb_conn.make_request('RemoveTags', params)
            self.changed = True

    def _get_health_check_target(self):
        """Compose target string from healthcheck parameters"""
        protocol = self.health_check['ping_protocol'].upper()
        path = ""

        if protocol in ['HTTP', 'HTTPS'] and 'ping_path' in self.health_check:
            path = self.health_check['ping_path']

        return "%s:%s%s" % (protocol, self.health_check['ping_port'], path)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state={'required': True, 'choices': ['present', 'absent']},
        name={'required': True},
        listeners={'default': None, 'required': False, 'type': 'list'},
        purge_listeners={'default': True, 'required': False, 'type': 'bool'},
        instance_ids={'default': None, 'required': False, 'type': 'list'},
        purge_instance_ids={'default': False, 'required': False, 'type': 'bool'},
        zones={'default': None, 'required': False, 'type': 'list'},
        purge_zones={'default': False, 'required': False, 'type': 'bool'},
        security_group_ids={'default': None, 'required': False, 'type': 'list'},
        security_group_names={'default': None, 'required': False, 'type': 'list'},
        health_check={'default': None, 'required': False, 'type': 'dict'},
        subnets={'default': None, 'required': False, 'type': 'list'},
        purge_subnets={'default': False, 'required': False, 'type': 'bool'},
        scheme={'default': 'internet-facing', 'required': False, 'choices': ['internal', 'internet-facing']},
        connection_draining_timeout={'default': None, 'required': False, 'type': 'int'},
        idle_timeout={'default': None, 'type': 'int', 'required': False},
        cross_az_load_balancing={'default': None, 'type': 'bool', 'required': False},
        stickiness={'default': None, 'required': False, 'type': 'dict'},
        access_logs={'default': None, 'required': False, 'type': 'dict'},
        wait={'default': False, 'type': 'bool', 'required': False},
        wait_timeout={'default': 60, 'type': 'int', 'required': False},
        tags={'default': None, 'required': False, 'type': 'dict'}
    )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['security_group_ids', 'security_group_names']]
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")

    name = module.params['name']
    state = module.params['state']
    listeners = module.params['listeners']
    purge_listeners = module.params['purge_listeners']
    instance_ids = module.params['instance_ids']
    purge_instance_ids = module.params['purge_instance_ids']
    zones = module.params['zones']
    purge_zones = module.params['purge_zones']
    security_group_ids = module.params['security_group_ids']
    security_group_names = module.params['security_group_names']
    health_check = module.params['health_check']
    access_logs = module.params['access_logs']
    subnets = module.params['subnets']
    purge_subnets = module.params['purge_subnets']
    scheme = module.params['scheme']
    connection_draining_timeout = module.params['connection_draining_timeout']
    idle_timeout = module.params['idle_timeout']
    cross_az_load_balancing = module.params['cross_az_load_balancing']
    stickiness = module.params['stickiness']
    wait = module.params['wait']
    wait_timeout = module.params['wait_timeout']
    tags = module.params['tags']

    if state == 'present' and not listeners:
        module.fail_json(msg="At least one listener is required for ELB creation")

    if state == 'present' and not (zones or subnets):
        module.fail_json(msg="At least one availability zone or subnet is required for ELB creation")

    if wait_timeout > 600:
        module.fail_json(msg='wait_timeout maximum is 600 seconds')

    if security_group_names:
        security_group_ids = []
        try:
            ec2 = connect_to_aws(boto.ec2, region, **aws_connect_params)
            if subnets:  # We have at least one subnet, ergo this is a VPC
                vpc_conn = _get_vpc_connection(module=module, region=region, aws_connect_params=aws_connect_params)
                vpc_id = vpc_conn.get_all_subnets([subnets[0]])[0].vpc_id
                filters = {'vpc_id': vpc_id}
            else:
                filters = None
            grp_details = ec2.get_all_security_groups(filters=filters)

            for group_name in security_group_names:
                if isinstance(group_name, string_types):
                    group_name = [group_name]

                group_id = [str(grp.id) for grp in grp_details if str(grp.name) in group_name]
                security_group_ids.extend(group_id)
        except boto.exception.NoAuthHandlerFound as e:
            module.fail_json(msg=str(e))

    elb_man = ElbManager(module, name, listeners, purge_listeners, zones,
                         purge_zones, security_group_ids, health_check,
                         subnets, purge_subnets, scheme,
                         connection_draining_timeout, idle_timeout,
                         cross_az_load_balancing,
                         access_logs, stickiness, wait, wait_timeout, tags,
                         region=region, instance_ids=instance_ids, purge_instance_ids=purge_instance_ids,
                         **aws_connect_params)

    # check for unsupported attributes for this version of boto
    if cross_az_load_balancing and not elb_man._check_attribute_support('cross_zone_load_balancing'):
        module.fail_json(msg="You must install boto >= 2.18.0 to use the cross_az_load_balancing attribute")

    if connection_draining_timeout and not elb_man._check_attribute_support('connection_draining'):
        module.fail_json(msg="You must install boto >= 2.28.0 to use the connection_draining_timeout attribute")

    if idle_timeout and not elb_man._check_attribute_support('connecting_settings'):
        module.fail_json(msg="You must install boto >= 2.33.0 to use the idle_timeout attribute")

    if state == 'present':
        elb_man.ensure_ok()
    elif state == 'absent':
        elb_man.ensure_gone()

    ansible_facts = {'ec2_elb': 'info'}
    ec2_facts_result = dict(changed=elb_man.changed,
                            elb=elb_man.get_info(),
                            ansible_facts=ansible_facts)

    module.exit_json(**ec2_facts_result)


if __name__ == '__main__':
    main()
