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
module: ec2_elb_lb
description:
  - Returns information about the load balancer.
  - Will be marked changed when called only if state is changed.
short_description: Creates or destroys Amazon ELB.
version_added: "1.5"
author: Jim Dalton
options:
  state:
    description:
      - Create or destroy the ELB
    required: true
  name:
    description:
      - The name of the ELB
    required: true
  listeners:
    description:
      - List of ports/protocols for this ELB to listen on (see example)
    required: false
  purge_listeners:
    description:
      - Purge existing listeners on ELB that are not found in listeners
    required: false
    default: true
  zones:
    description:
      - List of availability zones to enable on this ELB
    required: false
  purge_zones:
    description:
      - Purge existing availability zones on ELB that are not found in zones
    required: false
    default: false
  security_group_ids:
    description:
      - A list of security groups to apply to the elb
    require: false
    default: None
    version_added: "1.6"
  health_check:
    description:
      - An associative array of health check configuration settigs (see example)
    require: false
    default: None
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    aliases: ['aws_region', 'ec2_region']
  subnets:
    description:
      - A list of VPC subnets to use when creating ELB. Zones should be empty if using this. 
    required: false
    default: None
    aliases: []
    version_added: "1.7"
  purge_subnets:
    description:
      - Purge existing subnet on ELB that are not found in subnets
    required: false
    default: false  
    version_added: "1.7"
  scheme:
    description:
      - The scheme to use when creating the ELB. For a private VPC-visible ELB use 'internal'.
    required: false
    default: 'internet-facing'
    version_added: "1.7"
  validate_certs:
    description:
      - When set to "no", SSL certificates will not be validated for boto versions >= 2.6.0.
    required: false
    default: "yes"
    choices: ["yes", "no"]
    aliases: []
    version_added: "1.5"
  connection_draining_timeout:
    description:
      - Wait a specified timeout allowing connections to drain before terminating an instance
    required: false
    aliases: []
    version_added: "1.8"
  cross_az_load_balancing:
    description:
      - Distribute load across all configured Availablity Zones
    required: false
    default: "no"
    choices: ["yes", "no"]
    aliases: []
    version_added: "1.8"

extends_documentation_fragment: aws
"""

EXAMPLES = """
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

# Basic provisioning example (non-VPC)

- local_action:
    module: ec2_elb_lb
    name: "test-please-delete"
    state: present
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http # options are http, https, ssl, tcp
        load_balancer_port: 80
        instance_port: 80
      - protocol: https
        load_balancer_port: 443
        instance_protocol: http # optional, defaults to value of protocol setting
        instance_port: 80
        # ssl certificate required for https or ssl
        ssl_certificate_id: "arn:aws:iam::123456789012:server-certificate/company/servercerts/ProdServerCert"

# Internal ELB example

- local_action:
    module: ec2_elb_lb
    name: "test-vpc"
    scheme: internal
    state: present
    subnets: 
      - subnet-abcd1234
      - subnet-1a2b3c4d
    listeners:
      - protocol: http # options are http, https, ssl, tcp
        load_balancer_port: 80
        instance_port: 80

# Configure a health check
- local_action:
    module: ec2_elb_lb
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

# Ensure ELB is gone
- local_action:
    module: ec2_elb_lb
    name: "test-please-delete"
    state: absent

# Normally, this module will purge any listeners that exist on the ELB
# but aren't specified in the listeners parameter. If purge_listeners is
# false it leaves them alone
- local_action:
    module: ec2_elb_lb
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

# Normally, this module will leave availability zones that are enabled
# on the ELB alone. If purge_zones is true, then any extreneous zones
# will be removed
- local_action:
    module: ec2_elb_lb
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

# Creates a ELB and assigns a list of subnets to it. 
- local_action:
    module: ec2_elb_lb
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

# Create an ELB with connection draining and cross availability
# zone load balancing
- local_action:
    module: ec2_elb_lb
    name: "New ELB"
    state: present
    connection_draining_timeout: 60
    cross_az_load_balancing: "yes"
    region: us-east-1
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocols: http
      - load_balancer_port: 80
      - instance_port: 80
"""

import sys
import os

try:
    import boto
    import boto.ec2.elb
    import boto.ec2.elb.attributes
    from boto.ec2.elb.healthcheck import HealthCheck
    from boto.regioninfo import RegionInfo
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)


class ElbManager(object):
    """Handles ELB creation and destruction"""

    def __init__(self, module, name, listeners=None, purge_listeners=None,
                 zones=None, purge_zones=None, security_group_ids=None, 
                 health_check=None, subnets=None, purge_subnets=None,
                 scheme="internet-facing", connection_draining_timeout=None,
                 cross_az_load_balancing=None,  region=None, **aws_connect_params):

        self.module = module
        self.name = name
        self.listeners = listeners
        self.purge_listeners = purge_listeners
        self.zones = zones
        self.purge_zones = purge_zones
        self.security_group_ids = security_group_ids
        self.health_check = health_check
        self.subnets = subnets
        self.purge_subnets = purge_subnets
        self.scheme = scheme
        self.connection_draining_timeout = connection_draining_timeout
        self.cross_az_load_balancing = cross_az_load_balancing

        self.aws_connect_params = aws_connect_params
        self.region = region

        self.changed = False
        self.status = 'gone'
        self.elb_conn = self._get_elb_connection()
        self.elb = self._get_elb()

    def ensure_ok(self):
        """Create the ELB"""
        if not self.elb:
            # Zones and listeners will be added at creation
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
        if self._check_attribute_support('cross_zone_load_balancing'):
            self._set_cross_az_load_balancing()

    def ensure_gone(self):
        """Destroy the ELB"""
        if self.elb:
            self._delete_elb()

    def get_info(self):
        try:
            check_elb = self.elb_conn.get_all_load_balancers(self.name)[0]
        except:
            check_elb = None

        if not check_elb:
            info = {
                'name': self.name,
                'status': self.status
            }
        else:
            info = {
                'name': check_elb.name,
                'dns_name': check_elb.dns_name,
                'zones': check_elb.availability_zones,
                'security_group_ids': check_elb.security_groups,
                'status': self.status,
                'subnets': self.subnets,
                'scheme': check_elb.scheme,
                'hosted_zone_name': check_elb.canonical_hosted_zone_name,
                'hosted_zone_id': check_elb.canonical_hosted_zone_name_id
            }

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
                info['connection_draining_timeout'] = self.elb_conn.get_lb_attribute(self.name, 'ConnectionDraining').timeout

            if self._check_attribute_support('cross_zone_load_balancing'):
                is_cross_az_lb_enabled = self.elb_conn.get_lb_attribute(self.name, 'CrossZoneLoadBalancing')
                if is_cross_az_lb_enabled:
                    info['cross_az_load_balancing'] = 'yes'
                else:
                    info['cross_az_load_balancing'] = 'no'

        return info

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
        except (boto.exception.NoAuthHandlerFound, StandardError), e:
            self.module.fail_json(msg=str(e))

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
                # single match on the incomping port is all we're looking for
                if existing_listener[0] == listener['load_balancer_port']:
                    existing_listener_found = self._api_listener_as_tuple(existing_listener)
                    break

            if existing_listener_found:
                # Does it match exactly?
                if listener_as_tuple != existing_listener_found:
                    # The ports are the same but something else is different,
                    # so we'll remove the exsiting one and add the new one
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
            listener['load_balancer_port'],
            listener['instance_port'],
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
        except boto.exception.BotoServerError, e:
            if "Invalid Availability Zone" in e.error_message:
                self.module.fail_json(msg=e.error_message)
            else:
                self.module.fail_json(msg="an unknown server error occurred, please try again later")
        self.changed = True

    def _disable_zones(self, zones):
        try:
            self.elb.disable_zones(zones)
        except boto.exception.BotoServerError, e:
            if "Invalid Availability Zone" in e.error_message:
                self.module.fail_json(msg=e.error_message)
            else:
                self.module.fail_json(msg="an unknown server error occurred, please try again later")
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
        if self.security_group_ids != None and set(self.elb.security_groups) != set(self.security_group_ids):
            self.elb_conn.apply_security_groups_to_lb(self.name, self.security_group_ids)
            self.Changed = True

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

            for attr, desired_value in health_check_config.iteritems():
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
            attributes.cross_zone_load_balancing.enabled = True
        else:
            attributes.cross_zone_load_balancing.enabled = False
        self.elb_conn.modify_lb_attribute(self.name, 'CrossZoneLoadBalancing',
                                          attributes.cross_zone_load_balancing.enabled)

    def _set_connection_draining_timeout(self):
        attributes = self.elb.get_attributes()
        if self.connection_draining_timeout is not None:
            attributes.connection_draining.enabled = True
            attributes.connection_draining.timeout = self.connection_draining_timeout
            self.elb_conn.modify_lb_attribute(self.name, 'ConnectionDraining', attributes.connection_draining)
        else:
            attributes.connection_draining.enabled = False
            self.elb_conn.modify_lb_attribute(self.name, 'ConnectionDraining', attributes.connection_draining)

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
            zones={'default': None, 'required': False, 'type': 'list'},
            purge_zones={'default': False, 'required': False, 'type': 'bool'},
            security_group_ids={'default': None, 'required': False, 'type': 'list'},
            health_check={'default': None, 'required': False, 'type': 'dict'},
            subnets={'default': None, 'required': False, 'type': 'list'},
            purge_subnets={'default': False, 'required': False, 'type': 'bool'},
            scheme={'default': 'internet-facing', 'required': False},
            connection_draining_timeout={'default': None, 'required': False},
            cross_az_load_balancing={'default': None, 'required': False}
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")

    name = module.params['name']
    state = module.params['state']
    listeners = module.params['listeners']
    purge_listeners = module.params['purge_listeners']
    zones = module.params['zones']
    purge_zones = module.params['purge_zones']
    security_group_ids = module.params['security_group_ids']
    health_check = module.params['health_check']
    subnets = module.params['subnets']
    purge_subnets = module.params['purge_subnets']
    scheme = module.params['scheme']
    connection_draining_timeout = module.params['connection_draining_timeout']
    cross_az_load_balancing = module.params['cross_az_load_balancing']

    if state == 'present' and not listeners:
        module.fail_json(msg="At least one port is required for ELB creation")

    if state == 'present' and not (zones or subnets):
        module.fail_json(msg="At least one availability zone or subnet is required for ELB creation")

    elb_man = ElbManager(module, name, listeners, purge_listeners, zones,
                         purge_zones, security_group_ids, health_check,
                         subnets, purge_subnets, scheme,
                         connection_draining_timeout, cross_az_load_balancing,
                         region=region, **aws_connect_params)

    # check for unsupported attributes for this version of boto
    if cross_az_load_balancing and not elb_man._check_attribute_support('cross_zone_load_balancing'):
        module.fail_json(msg="You must install boto >= 2.18.0 to use the cross_az_load_balancing attribute")

    if connection_draining_timeout and not elb_man._check_attribute_support('connection_draining'):
        module.fail_json(msg="You must install boto >= 2.28.0 to use the connection_draining_timeout attribute")

    if state == 'present':
        elb_man.ensure_ok()
    elif state == 'absent':
        elb_man.ensure_gone()

    ansible_facts = {'ec2_elb': 'info'}
    ec2_facts_result = dict(changed=elb_man.changed,
                            elb=elb_man.get_info(),
                            ansible_facts=ansible_facts)

    module.exit_json(**ec2_facts_result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
