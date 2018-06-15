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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: route53_health_check
short_description: add or delete health-checks in Amazons Route53 DNS service
description:
  - Creates and deletes DNS Health checks in Amazons Route53 service
  - Only the port, resource_path, string_match and request_interval are
    considered when updating existing health-checks.
version_added: "2.0"
options:
  state:
    description:
      - Specifies the action to take.
    required: true
    choices: [ 'present', 'absent' ]
  ip_address:
    description:
      - IP address of the end-point to check. Either this or `fqdn` has to be
        provided.
  port:
    description:
      - The port on the endpoint on which you want Amazon Route 53 to perform
        health checks. Required for TCP checks.
  type:
    description:
      - The type of health check that you want to create, which indicates how
        Amazon Route 53 determines whether an endpoint is healthy.
    required: true
    choices: [ 'HTTP', 'HTTPS', 'HTTP_STR_MATCH', 'HTTPS_STR_MATCH', 'TCP' ]
  resource_path:
    description:
      - The path that you want Amazon Route 53 to request when performing
        health checks. The path can be any value for which your endpoint will
        return an HTTP status code of 2xx or 3xx when the endpoint is healthy,
        for example the file /docs/route53-health-check.html.
      - Required for all checks except TCP.
      - The path must begin with a /
      - Maximum 255 characters.
  fqdn:
    description:
      - Domain name of the endpoint to check. Either this or `ip_address` has
        to be provided. When both are given the `fqdn` is used in the `Host:`
        header of the HTTP request.
  string_match:
    description:
      - If the check type is HTTP_STR_MATCH or HTTP_STR_MATCH, the string
        that you want Amazon Route 53 to search for in the response body from
        the specified resource. If the string appears in the first 5120 bytes
        of the response body, Amazon Route 53 considers the resource healthy.
  request_interval:
    description:
      - The number of seconds between the time that Amazon Route 53 gets a
        response from your endpoint and the time that it sends the next
        health-check request.
    required: true
    default: 30
    choices: [ 10, 30 ]
  failure_threshold:
    description:
      - The number of consecutive health checks that an endpoint must pass or
        fail for Amazon Route 53 to change the current status of the endpoint
        from unhealthy to healthy or vice versa.
    required: true
    default: 3
    choices: [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ]
author: "zimbatm (@zimbatm)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Create a health-check for host1.example.com and use it in record
- route53_health_check:
    state: present
    fqdn: host1.example.com
    type: HTTP_STR_MATCH
    resource_path: /
    string_match: "Hello"
    request_interval: 10
    failure_threshold: 2
  register: my_health_check

- route53:
    action: create
    zone: "example.com"
    type: CNAME
    record: "www.example.com"
    value: host1.example.com
    ttl: 30
    # Routing policy
    identifier: "host1@www"
    weight: 100
    health_check: "{{ my_health_check.health_check.id }}"

# Delete health-check
- route53_health_check:
    state: absent
    fqdn: host1.example.com

'''

import uuid

try:
    import boto
    import boto.ec2
    from boto import route53
    from boto.route53 import Route53Connection, exception
    from boto.route53.healthcheck import HealthCheck
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info


# Things that can't get changed:
#  protocol
#  ip_address or domain
#  request_interval
#  string_match if not previously enabled
def find_health_check(conn, wanted):
    """Searches for health checks that have the exact same set of immutable values"""
    for check in conn.get_list_health_checks().HealthChecks:
        config = check.HealthCheckConfig
        if (
            config.get('IPAddress') == wanted.ip_addr and
            config.get('FullyQualifiedDomainName') == wanted.fqdn and
            config.get('Type') == wanted.hc_type and
            config.get('RequestInterval') == str(wanted.request_interval) and
            config.get('Port') == str(wanted.port)
        ):
            return check
    return None


def to_health_check(config):
    return HealthCheck(
        config.get('IPAddress'),
        int(config.get('Port')),
        config.get('Type'),
        config.get('ResourcePath'),
        fqdn=config.get('FullyQualifiedDomainName'),
        string_match=config.get('SearchString'),
        request_interval=int(config.get('RequestInterval')),
        failure_threshold=int(config.get('FailureThreshold')),
    )


def health_check_diff(a, b):
    a = a.__dict__
    b = b.__dict__
    if a == b:
        return {}
    diff = {}
    for key in set(a.keys()) | set(b.keys()):
        if a.get(key) != b.get(key):
            diff[key] = b.get(key)
    return diff


def to_template_params(health_check):
    params = {
        'ip_addr_part': '',
        'port': health_check.port,
        'type': health_check.hc_type,
        'resource_path_part': '',
        'fqdn_part': '',
        'string_match_part': '',
        'request_interval': health_check.request_interval,
        'failure_threshold': health_check.failure_threshold,
    }
    if health_check.ip_addr:
        params['ip_addr_part'] = HealthCheck.XMLIpAddrPart % {'ip_addr': health_check.ip_addr}
    if health_check.resource_path:
        params['resource_path_part'] = XMLResourcePathPart % {'resource_path': health_check.resource_path}
    if health_check.fqdn:
        params['fqdn_part'] = HealthCheck.XMLFQDNPart % {'fqdn': health_check.fqdn}
    if health_check.string_match:
        params['string_match_part'] = HealthCheck.XMLStringMatchPart % {'string_match': health_check.string_match}
    return params

XMLResourcePathPart = """<ResourcePath>%(resource_path)s</ResourcePath>"""

POSTXMLBody = """
    <CreateHealthCheckRequest xmlns="%(xmlns)s">
        <CallerReference>%(caller_ref)s</CallerReference>
        <HealthCheckConfig>
            %(ip_addr_part)s
            <Port>%(port)s</Port>
            <Type>%(type)s</Type>
            %(resource_path_part)s
            %(fqdn_part)s
            %(string_match_part)s
            <RequestInterval>%(request_interval)s</RequestInterval>
            <FailureThreshold>%(failure_threshold)s</FailureThreshold>
        </HealthCheckConfig>
    </CreateHealthCheckRequest>
    """

UPDATEHCXMLBody = """
    <UpdateHealthCheckRequest xmlns="%(xmlns)s">
        <HealthCheckVersion>%(health_check_version)s</HealthCheckVersion>
        %(ip_addr_part)s
        <Port>%(port)s</Port>
        %(resource_path_part)s
        %(fqdn_part)s
        %(string_match_part)s
        <FailureThreshold>%(failure_threshold)i</FailureThreshold>
    </UpdateHealthCheckRequest>
    """


def create_health_check(conn, health_check, caller_ref=None):
    if caller_ref is None:
        caller_ref = str(uuid.uuid4())
    uri = '/%s/healthcheck' % conn.Version
    params = to_template_params(health_check)
    params.update(xmlns=conn.XMLNameSpace, caller_ref=caller_ref)

    xml_body = POSTXMLBody % params
    response = conn.make_request('POST', uri, {'Content-Type': 'text/xml'}, xml_body)
    body = response.read()
    boto.log.debug(body)
    if response.status == 201:
        e = boto.jsonresponse.Element()
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        return e
    else:
        raise exception.DNSServerError(response.status, response.reason, body)


def update_health_check(conn, health_check_id, health_check_version, health_check):
    uri = '/%s/healthcheck/%s' % (conn.Version, health_check_id)
    params = to_template_params(health_check)
    params.update(
        xmlns=conn.XMLNameSpace,
        health_check_version=health_check_version,
    )
    xml_body = UPDATEHCXMLBody % params
    response = conn.make_request('POST', uri, {'Content-Type': 'text/xml'}, xml_body)
    body = response.read()
    boto.log.debug(body)
    if response.status not in (200, 204):
        raise exception.DNSServerError(response.status,
                                       response.reason,
                                       body)
    e = boto.jsonresponse.Element()
    h = boto.jsonresponse.XmlHandler(e, None)
    h.parse(body)
    return e


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(choices=['present', 'absent'], default='present'),
        ip_address=dict(),
        port=dict(type='int'),
        type=dict(required=True, choices=['HTTP', 'HTTPS', 'HTTP_STR_MATCH', 'HTTPS_STR_MATCH', 'TCP']),
        resource_path=dict(),
        fqdn=dict(),
        string_match=dict(),
        request_interval=dict(type='int', choices=[10, 30], default=30),
        failure_threshold=dict(type='int', choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], default=3),
    )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto 2.27.0+ required for this module')

    state_in = module.params.get('state')
    ip_addr_in = module.params.get('ip_address')
    port_in = module.params.get('port')
    type_in = module.params.get('type')
    resource_path_in = module.params.get('resource_path')
    fqdn_in = module.params.get('fqdn')
    string_match_in = module.params.get('string_match')
    request_interval_in = module.params.get('request_interval')
    failure_threshold_in = module.params.get('failure_threshold')

    if ip_addr_in is None and fqdn_in is None:
        module.fail_json(msg="parameter 'ip_address' or 'fqdn' is required")

    # Default port
    if port_in is None:
        if type_in in ['HTTP', 'HTTP_STR_MATCH']:
            port_in = 80
        elif type_in in ['HTTPS', 'HTTPS_STR_MATCH']:
            port_in = 443
        else:
            module.fail_json(msg="parameter 'port' is required for 'type' TCP")

    # string_match in relation with type
    if type_in in ['HTTP_STR_MATCH', 'HTTPS_STR_MATCH']:
        if string_match_in is None:
            module.fail_json(msg="parameter 'string_match' is required for the HTTP(S)_STR_MATCH types")
        elif len(string_match_in) > 255:
            module.fail_json(msg="parameter 'string_match' is limited to 255 characters max")
    elif string_match_in:
        module.fail_json(msg="parameter 'string_match' argument is only for the HTTP(S)_STR_MATCH types")

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)
    # connect to the route53 endpoint
    try:
        conn = Route53Connection(**aws_connect_kwargs)
    except boto.exception.BotoServerError as e:
        module.fail_json(msg=e.error_message)

    changed = False
    action = None
    check_id = None
    wanted_config = HealthCheck(ip_addr_in, port_in, type_in, resource_path_in, fqdn_in, string_match_in, request_interval_in, failure_threshold_in)
    existing_check = find_health_check(conn, wanted_config)
    if existing_check:
        check_id = existing_check.Id
        existing_config = to_health_check(existing_check.HealthCheckConfig)

    if state_in == 'present':
        if existing_check is None:
            action = "create"
            check_id = create_health_check(conn, wanted_config).HealthCheck.Id
            changed = True
        else:
            diff = health_check_diff(existing_config, wanted_config)
            if diff:
                action = "update"
                update_health_check(conn, existing_check.Id, int(existing_check.HealthCheckVersion), wanted_config)
                changed = True
    elif state_in == 'absent':
        if check_id:
            action = "delete"
            conn.delete_health_check(check_id)
            changed = True
    else:
        module.fail_json(msg="Logic Error: Unknown state")

    module.exit_json(changed=changed, health_check=dict(id=check_id), action=action)


if __name__ == '__main__':
    main()
