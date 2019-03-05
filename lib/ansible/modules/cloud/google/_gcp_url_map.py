#!/usr/bin/python
# Copyright 2017 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gcp_url_map
version_added: "2.4"
short_description: Create, Update or Destory a Url_Map.
description:
    - Create, Update or Destory a Url_Map. See
      U(https://cloud.google.com/compute/docs/load-balancing/http/url-map) for an overview.
      More details on the Url_Map API can be found at
      U(https://cloud.google.com/compute/docs/reference/latest/urlMaps#resource).
requirements:
  - "python >= 2.6"
  - "google-api-python-client >= 1.6.2"
  - "google-auth >= 0.9.0"
  - "google-auth-httplib2 >= 0.0.2"
notes:
  - Only supports global Backend Services.
  - Url_Map tests are not currently supported.
author:
  - "Tom Melendez (@supertom) <tom@supertom.com>"
deprecated:
    removed_in: "2.12"
    why: Updated modules released with increased functionality
    alternative: Use M(gcp_compute_url_map) instead.
options:
  url_map_name:
    description:
       - Name of the Url_Map.
    required: true
  default_service:
    description:
       - Default Backend Service if no host rules match.
    required: true
  host_rules:
    description:
       - The list of HostRules to use against the URL. Contains
         a list of hosts and an associated path_matcher.
       - The 'hosts' parameter is a list of host patterns to match. They
         must be valid hostnames, except * will match any string of
         ([a-z0-9-.]*). In that case, * must be the first character
         and must be followed in the pattern by either - or ..
       - The 'path_matcher' parameter is name of the PathMatcher to use
         to match the path portion of the URL if the hostRule matches the URL's
         host portion.
    required: false
  path_matchers:
    description:
       - The list of named PathMatchers to use against the URL. Contains
         path_rules, which is a list of paths and an associated service. A
         default_service can also be specified for each path_matcher.
       - The 'name' parameter to which this path_matcher is referred by the
         host_rule.
       - The 'default_service' parameter is the name of the
         BackendService resource. This will be used if none of the path_rules
         defined by this path_matcher is matched by the URL's path portion.
       - The 'path_rules' parameter is a list of dictionaries containing a
         list of paths and a service to direct traffic to. Each path item must
         start with / and the only place a * is allowed is at the end following
         a /. The string fed to the path matcher does not include any text after
         the first ? or #, and those chars are not allowed here.
    required: false
'''

EXAMPLES = '''
- name: Create Minimal Url_Map
  gcp_url_map:
    service_account_email: "{{ service_account_email }}"
    credentials_file: "{{ credentials_file }}"
    project_id: "{{ project_id }}"
    url_map_name: my-url_map
    default_service: my-backend-service
    state: present
- name: Create UrlMap with pathmatcher
  gcp_url_map:
    service_account_email: "{{ service_account_email }}"
    credentials_file: "{{ credentials_file }}"
    project_id: "{{ project_id }}"
    url_map_name: my-url-map-pm
    default_service: default-backend-service
    path_matchers:
    - name: 'path-matcher-one'
      description: 'path matcher one'
      default_service: 'bes-pathmatcher-one-default'
      path_rules:
      - service: 'my-one-bes'
        paths:
        - '/data'
        - '/aboutus'
    host_rules:
      - hosts:
        - '*.'
        path_matcher: 'path-matcher-one'
    state: "present"
'''

RETURN = '''
host_rules:
    description: List of HostRules.
    returned: If specified.
    type: dict
    sample: [ { hosts: ["*."], "path_matcher": "my-pm" } ]
path_matchers:
    description: The list of named PathMatchers to use against the URL.
    returned: If specified.
    type: dict
    sample: [ { "name": "my-pm", "path_rules": [ { "paths": [ "/data" ] } ], "service": "my-service" } ]
state:
    description: state of the Url_Map
    returned: Always.
    type: str
    sample: present
updated_url_map:
    description: True if the url_map has been updated. Will not appear on
                 initial url_map creation.
    returned: if the url_map has been updated.
    type: bool
    sample: true
url_map_name:
    description: Name of the Url_Map
    returned: Always
    type: str
    sample: my-url-map
url_map:
    description: GCP Url_Map dictionary
    returned: Always. Refer to GCP documentation for detailed field descriptions.
    type: dict
    sample: { "name": "my-url-map", "hostRules": [...], "pathMatchers": [...] }
'''

try:
    from ast import literal_eval
    HAS_PYTHON26 = True
except ImportError:
    HAS_PYTHON26 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gcp import check_params, get_google_api_client, GCPUtils
from ansible.module_utils.six import string_types


USER_AGENT_PRODUCT = 'ansible-url_map'
USER_AGENT_VERSION = '0.0.1'


def _validate_params(params):
    """
    Validate url_map params.

    This function calls _validate_host_rules_params to verify
    the host_rules-specific parameters.

    This function calls _validate_path_matchers_params to verify
    the path_matchers-specific parameters.

    :param params: Ansible dictionary containing configuration.
    :type  params: ``dict``

    :return: True or raises ValueError
    :rtype: ``bool`` or `class:ValueError`
    """
    fields = [
        {'name': 'default_service', 'type': str, 'required': True},
        {'name': 'host_rules', 'type': list},
        {'name': 'path_matchers', 'type': list},
    ]
    try:
        check_params(params, fields)
        if 'path_matchers' in params and params['path_matchers'] is not None:
            _validate_path_matcher_params(params['path_matchers'])
        if 'host_rules' in params and params['host_rules'] is not None:
            _validate_host_rules_params(params['host_rules'])
    except Exception:
        raise

    return (True, '')


def _validate_path_matcher_params(path_matchers):
    """
    Validate configuration for path_matchers.

    :param path_matchers: Ansible dictionary containing path_matchers
                     configuration (only).
    :type  path_matchers: ``dict``

    :return: True or raises ValueError
    :rtype: ``bool`` or `class:ValueError`
    """
    fields = [
        {'name': 'name', 'type': str, 'required': True},
        {'name': 'default_service', 'type': str, 'required': True},
        {'name': 'path_rules', 'type': list, 'required': True},
        {'name': 'max_rate', 'type': int},
        {'name': 'max_rate_per_instance', 'type': float},
    ]
    pr_fields = [
        {'name': 'service', 'type': str, 'required': True},
        {'name': 'paths', 'type': list, 'required': True},
    ]

    if not path_matchers:
        raise ValueError(('path_matchers should be a list. %s (%s) provided'
                          % (path_matchers, type(path_matchers))))

    for pm in path_matchers:
        try:
            check_params(pm, fields)
            for pr in pm['path_rules']:
                check_params(pr, pr_fields)
                for path in pr['paths']:
                    if not path.startswith('/'):
                        raise ValueError("path for %s must start with /" % (
                            pm['name']))
        except Exception:
            raise

    return (True, '')


def _validate_host_rules_params(host_rules):
    """
    Validate configuration for host_rules.

    :param host_rules: Ansible dictionary containing host_rules
                     configuration (only).
    :type  host_rules ``dict``

    :return: True or raises ValueError
    :rtype: ``bool`` or `class:ValueError`
    """
    fields = [
        {'name': 'path_matcher', 'type': str, 'required': True},
    ]

    if not host_rules:
        raise ValueError('host_rules should be a list.')

    for hr in host_rules:
        try:
            check_params(hr, fields)
            for host in hr['hosts']:
                if not isinstance(host, string_types):
                    raise ValueError("host in hostrules must be a string")
                elif '*' in host:
                    if host.index('*') != 0:
                        raise ValueError("wildcard must be first char in host, %s" % (
                            host))
                    else:
                        if host[1] not in ['.', '-', ]:
                            raise ValueError("wildcard be followed by a '.' or '-', %s" % (
                                host))

        except Exception:
            raise

    return (True, '')


def _build_path_matchers(path_matcher_list, project_id):
    """
    Reformat services in path matchers list.

    Specifically, builds out URLs.

    :param path_matcher_list: The GCP project ID.
    :type path_matcher_list: ``list`` of ``dict``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: list suitable for submission to GCP
             UrlMap API Path Matchers list.
    :rtype ``list`` of ``dict``
    """
    url = ''
    if project_id:
        url = GCPUtils.build_googleapi_url(project_id)
    for pm in path_matcher_list:
        if 'defaultService' in pm:
            pm['defaultService'] = '%s/global/backendServices/%s' % (url,
                                                                     pm['defaultService'])
        if 'pathRules' in pm:
            for rule in pm['pathRules']:
                if 'service' in rule:
                    rule['service'] = '%s/global/backendServices/%s' % (url,
                                                                        rule['service'])
    return path_matcher_list


def _build_url_map_dict(params, project_id=None):
    """
    Reformat services in Ansible Params.

    :param params: Params from AnsibleModule object
    :type params: ``dict``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: dictionary suitable for submission to GCP UrlMap API.
    :rtype ``dict``
    """
    url = ''
    if project_id:
        url = GCPUtils.build_googleapi_url(project_id)
    gcp_dict = GCPUtils.params_to_gcp_dict(params, 'url_map_name')
    if 'defaultService' in gcp_dict:
        gcp_dict['defaultService'] = '%s/global/backendServices/%s' % (url,
                                                                       gcp_dict['defaultService'])
    if 'pathMatchers' in gcp_dict:
        gcp_dict['pathMatchers'] = _build_path_matchers(gcp_dict['pathMatchers'], project_id)

    return gcp_dict


def get_url_map(client, name, project_id=None):
    """
    Get a Url_Map from GCP.

    :param client: An initialized GCE Compute Disovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param name: Name of the Url Map.
    :type name:  ``str``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: A dict resp from the respective GCP 'get' request.
    :rtype: ``dict``
    """
    try:
        req = client.urlMaps().get(project=project_id, urlMap=name)
        return GCPUtils.execute_api_client_req(req, raise_404=False)
    except Exception:
        raise


def create_url_map(client, params, project_id):
    """
    Create a new Url_Map.

    :param client: An initialized GCE Compute Disovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param params: Dictionary of arguments from AnsibleModule.
    :type params:  ``dict``

    :return: Tuple with changed status and response dict
    :rtype: ``tuple`` in the format of (bool, dict)
    """
    gcp_dict = _build_url_map_dict(params, project_id)
    try:
        req = client.urlMaps().insert(project=project_id, body=gcp_dict)
        return_data = GCPUtils.execute_api_client_req(req, client, raw=False)
        if not return_data:
            return_data = get_url_map(client,
                                      name=params['url_map_name'],
                                      project_id=project_id)
        return (True, return_data)
    except Exception:
        raise


def delete_url_map(client, name, project_id):
    """
    Delete a Url_Map.

    :param client: An initialized GCE Compute Disover resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param name: Name of the Url Map.
    :type name:  ``str``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: Tuple with changed status and response dict
    :rtype: ``tuple`` in the format of (bool, dict)
    """
    try:
        req = client.urlMaps().delete(project=project_id, urlMap=name)
        return_data = GCPUtils.execute_api_client_req(req, client)
        return (True, return_data)
    except Exception:
        raise


def update_url_map(client, url_map, params, name, project_id):
    """
    Update a Url_Map.

    If the url_map has not changed, the update will not occur.

    :param client: An initialized GCE Compute Disovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param url_map: Name of the Url Map.
    :type url_map:  ``dict``

    :param params: Dictionary of arguments from AnsibleModule.
    :type params:  ``dict``

    :param name: Name of the Url Map.
    :type name:  ``str``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: Tuple with changed status and response dict
    :rtype: ``tuple`` in the format of (bool, dict)
    """
    gcp_dict = _build_url_map_dict(params, project_id)

    ans = GCPUtils.are_params_equal(url_map, gcp_dict)
    if ans:
        return (False, 'no update necessary')

    gcp_dict['fingerprint'] = url_map['fingerprint']
    try:
        req = client.urlMaps().update(project=project_id,
                                      urlMap=name, body=gcp_dict)
        return_data = GCPUtils.execute_api_client_req(req, client=client, raw=False)
        return (True, return_data)
    except Exception:
        raise


def main():
    module = AnsibleModule(argument_spec=dict(
        url_map_name=dict(required=True),
        state=dict(choices=['absent', 'present'], default='present'),
        default_service=dict(required=True),
        path_matchers=dict(type='list', required=False),
        host_rules=dict(type='list', required=False),
        service_account_email=dict(),
        service_account_permissions=dict(type='list'),
        pem_file=dict(),
        credentials_file=dict(),
        project_id=dict(), ), required_together=[
            ['path_matchers', 'host_rules'], ])

    client, conn_params = get_google_api_client(module, 'compute', user_agent_product=USER_AGENT_PRODUCT,
                                                user_agent_version=USER_AGENT_VERSION)

    params = {}
    params['state'] = module.params.get('state')
    params['url_map_name'] = module.params.get('url_map_name')
    params['default_service'] = module.params.get('default_service')
    if module.params.get('path_matchers'):
        params['path_matchers'] = module.params.get('path_matchers')
    if module.params.get('host_rules'):
        params['host_rules'] = module.params.get('host_rules')

    try:
        _validate_params(params)
    except Exception as e:
        module.fail_json(msg=e.message, changed=False)

    changed = False
    json_output = {'state': params['state']}
    url_map = get_url_map(client,
                          name=params['url_map_name'],
                          project_id=conn_params['project_id'])

    if not url_map:
        if params['state'] == 'absent':
            # Doesn't exist in GCE, and state==absent.
            changed = False
            module.fail_json(
                msg="Cannot delete unknown url_map: %s" %
                (params['url_map_name']))
        else:
            # Create
            changed, json_output['url_map'] = create_url_map(client,
                                                             params=params,
                                                             project_id=conn_params['project_id'])
    elif params['state'] == 'absent':
        # Delete
        changed, json_output['url_map'] = delete_url_map(client,
                                                         name=params['url_map_name'],
                                                         project_id=conn_params['project_id'])
    else:
        changed, json_output['url_map'] = update_url_map(client,
                                                         url_map=url_map,
                                                         params=params,
                                                         name=params['url_map_name'],
                                                         project_id=conn_params['project_id'])
        json_output['updated_url_map'] = changed

    json_output['changed'] = changed
    json_output.update(params)
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
