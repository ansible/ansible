#!/usr/bin/python
# Copyright 2013 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gce_lb
version_added: "1.5"
short_description: create/destroy GCE load-balancer resources
description:
    - This module can create and destroy Google Compute Engine C(loadbalancer)
      and C(httphealthcheck) resources.  The primary LB resource is the
      C(load_balancer) resource and the health check parameters are all
      prefixed with I(httphealthcheck).
      The full documentation for Google Compute Engine load balancing is at
      U(https://developers.google.com/compute/docs/load-balancing/).  However,
      the ansible module simplifies the configuration by following the
      libcloud model.
      Full install/configuration instructions for the gce* modules can
      be found in the comments of ansible/test/gce_tests.py.
options:
  httphealthcheck_name:
    description:
      - the name identifier for the HTTP health check
  httphealthcheck_port:
    description:
      - the TCP port to use for HTTP health checking
    default: 80
  httphealthcheck_path:
    description:
      - the url path to use for HTTP health checking
    default: "/"
  httphealthcheck_interval:
    description:
      - the duration in seconds between each health check request
    default: 5
  httphealthcheck_timeout:
    description:
      - the timeout in seconds before a request is considered a failed check
    default: 5
  httphealthcheck_unhealthy_count:
    description:
      - number of consecutive failed checks before marking a node unhealthy
    default: 2
  httphealthcheck_healthy_count:
    description:
      - number of consecutive successful checks before marking a node healthy
    default: 2
  httphealthcheck_host:
    description:
      - host header to pass through on HTTP check requests
  name:
    description:
      - name of the load-balancer resource
  protocol:
    description:
      - the protocol used for the load-balancer packet forwarding, tcp or udp
    default: "tcp"
    choices: ['tcp', 'udp']
  region:
    description:
      - the GCE region where the load-balancer is defined
  external_ip:
    description:
      - the external static IPv4 (or auto-assigned) address for the LB
  port_range:
    description:
      - the port (range) to forward, e.g. 80 or 8000-8888 defaults to all ports
  members:
    description:
      - a list of zone/nodename pairs, e.g ['us-central1-a/www-a', ...]
    aliases: ['nodes']
  state:
    description:
      - desired state of the LB
    default: "present"
    choices: ["active", "present", "absent", "deleted"]
  service_account_email:
    version_added: "1.6"
    description:
      - service account email
  pem_file:
    version_added: "1.6"
    description:
      - path to the pem file associated with the service account email
        This option is deprecated. Use 'credentials_file'.
  credentials_file:
    version_added: "2.1.0"
    description:
      - path to the JSON file associated with the service account email
  project_id:
    version_added: "1.6"
    description:
      - your GCE project ID

requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 0.13.3, >= 0.17.0 if using JSON credentials"
author: "Eric Johnson (@erjohnso) <erjohnso@google.com>"
'''

EXAMPLES = '''
# Simple example of creating a new LB, adding members, and a health check
- local_action:
    module: gce_lb
    name: testlb
    region: us-central1
    members: ["us-central1-a/www-a", "us-central1-b/www-b"]
    httphealthcheck_name: hc
    httphealthcheck_port: 80
    httphealthcheck_path: "/up"
'''

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.loadbalancer.types import Provider as Provider_lb
    from libcloud.loadbalancer.providers import get_driver as get_driver_lb
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, ResourceExistsError, ResourceNotFoundError

    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import USER_AGENT_PRODUCT, USER_AGENT_VERSION, gce_connect, unexpected_error_msg


def main():
    module = AnsibleModule(
        argument_spec=dict(
            httphealthcheck_name=dict(),
            httphealthcheck_port=dict(default=80),
            httphealthcheck_path=dict(default='/'),
            httphealthcheck_interval=dict(default=5),
            httphealthcheck_timeout=dict(default=5),
            httphealthcheck_unhealthy_count=dict(default=2),
            httphealthcheck_healthy_count=dict(default=2),
            httphealthcheck_host=dict(),
            name=dict(),
            protocol=dict(default='tcp'),
            region=dict(),
            external_ip=dict(),
            port_range=dict(),
            members=dict(type='list'),
            state=dict(default='present'),
            service_account_email=dict(),
            pem_file=dict(type='path'),
            credentials_file=dict(type='path'),
            project_id=dict(),
        )
    )

    if not HAS_LIBCLOUD:
        module.fail_json(msg='libcloud with GCE support (0.13.3+) required for this module.')

    gce = gce_connect(module)

    httphealthcheck_name = module.params.get('httphealthcheck_name')
    httphealthcheck_port = module.params.get('httphealthcheck_port')
    httphealthcheck_path = module.params.get('httphealthcheck_path')
    httphealthcheck_interval = module.params.get('httphealthcheck_interval')
    httphealthcheck_timeout = module.params.get('httphealthcheck_timeout')
    httphealthcheck_unhealthy_count = module.params.get('httphealthcheck_unhealthy_count')
    httphealthcheck_healthy_count = module.params.get('httphealthcheck_healthy_count')
    httphealthcheck_host = module.params.get('httphealthcheck_host')
    name = module.params.get('name')
    protocol = module.params.get('protocol')
    region = module.params.get('region')
    external_ip = module.params.get('external_ip')
    port_range = module.params.get('port_range')
    members = module.params.get('members')
    state = module.params.get('state')

    try:
        gcelb = get_driver_lb(Provider_lb.GCE)(gce_driver=gce)
        gcelb.connection.user_agent_append("%s/%s" % (
            USER_AGENT_PRODUCT, USER_AGENT_VERSION))
    except Exception as e:
        module.fail_json(msg=unexpected_error_msg(e), changed=False)

    changed = False
    json_output = {'name': name, 'state': state}

    if not name and not httphealthcheck_name:
        module.fail_json(msg='Nothing to do, please specify a "name" ' + 'or "httphealthcheck_name" parameter', changed=False)

    if state in ['active', 'present']:
        # first, create the httphealthcheck if requested
        hc = None
        if httphealthcheck_name:
            json_output['httphealthcheck_name'] = httphealthcheck_name
            try:
                hc = gcelb.ex_create_healthcheck(httphealthcheck_name,
                                                 host=httphealthcheck_host, path=httphealthcheck_path,
                                                 port=httphealthcheck_port,
                                                 interval=httphealthcheck_interval,
                                                 timeout=httphealthcheck_timeout,
                                                 unhealthy_threshold=httphealthcheck_unhealthy_count,
                                                 healthy_threshold=httphealthcheck_healthy_count)
                changed = True
            except ResourceExistsError:
                hc = gce.ex_get_healthcheck(httphealthcheck_name)
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)

            if hc is not None:
                json_output['httphealthcheck_host'] = hc.extra['host']
                json_output['httphealthcheck_path'] = hc.path
                json_output['httphealthcheck_port'] = hc.port
                json_output['httphealthcheck_interval'] = hc.interval
                json_output['httphealthcheck_timeout'] = hc.timeout
                json_output['httphealthcheck_unhealthy_count'] = hc.unhealthy_threshold
                json_output['httphealthcheck_healthy_count'] = hc.healthy_threshold

        # create the forwarding rule (and target pool under the hood)
        lb = None
        if name:
            if not region:
                module.fail_json(msg='Missing required region name',
                                 changed=False)
            nodes = []
            output_nodes = []
            json_output['name'] = name
            # members is a python list of 'zone/inst' strings
            if members:
                for node in members:
                    try:
                        zone, node_name = node.split('/')
                        nodes.append(gce.ex_get_node(node_name, zone))
                        output_nodes.append(node)
                    except:
                        # skip nodes that are badly formatted or don't exist
                        pass
            try:
                if hc is not None:
                    lb = gcelb.create_balancer(name, port_range, protocol,
                                               None, nodes, ex_region=region, ex_healthchecks=[hc],
                                               ex_address=external_ip)
                else:
                    lb = gcelb.create_balancer(name, port_range, protocol,
                                               None, nodes, ex_region=region, ex_address=external_ip)
                changed = True
            except ResourceExistsError:
                lb = gcelb.get_balancer(name)
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)

            if lb is not None:
                json_output['members'] = output_nodes
                json_output['protocol'] = protocol
                json_output['region'] = region
                json_output['external_ip'] = lb.ip
                json_output['port_range'] = lb.port
                hc_names = []
                if 'healthchecks' in lb.extra:
                    for hc in lb.extra['healthchecks']:
                        hc_names.append(hc.name)
                json_output['httphealthchecks'] = hc_names

    if state in ['absent', 'deleted']:
        # first, delete the load balancer (forwarding rule and target pool)
        # if specified.
        if name:
            json_output['name'] = name
            try:
                lb = gcelb.get_balancer(name)
                gcelb.destroy_balancer(lb)
                changed = True
            except ResourceNotFoundError:
                pass
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)

        # destroy the health check if specified
        if httphealthcheck_name:
            json_output['httphealthcheck_name'] = httphealthcheck_name
            try:
                hc = gce.ex_get_healthcheck(httphealthcheck_name)
                gce.ex_destroy_healthcheck(hc)
                changed = True
            except ResourceNotFoundError:
                pass
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)

    json_output['changed'] = changed
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
