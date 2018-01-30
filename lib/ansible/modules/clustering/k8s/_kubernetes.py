#!/usr/bin/python

# Copyright: (c) 2015, Google Inc. All Rights Reserved.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: kubernetes
version_added: "2.1"
deprecated:
  removed_in: "2.9"
  why: This module used the oc command line tool, where as M(k8s_raw) goes over the REST API.
  alternative: Use M(k8s_raw) instead.
short_description: Manage Kubernetes resources
description:
    - This module can manage Kubernetes resources on an existing cluster using
      the Kubernetes server API. Users can specify in-line API data, or
      specify an existing Kubernetes YAML file.
    - Currently, this module
      (1) Only supports HTTP Basic Auth
      (2) Only supports 'strategic merge' for update, http://goo.gl/fCPYxT
      SSL certs are not working, use C(validate_certs=off) to disable.
options:
  api_endpoint:
    description:
      - The IPv4 API endpoint of the Kubernetes cluster.
    required: true
    aliases: [ endpoint ]
  inline_data:
    description:
      - The Kubernetes YAML data to send to the API I(endpoint). This option is
        mutually exclusive with C('file_reference').
    required: true
  file_reference:
    description:
      - Specify full path to a Kubernets YAML file to send to API I(endpoint).
        This option is mutually exclusive with C('inline_data').
  patch_operation:
    description:
      - Specify patch operation for Kubernetes resource update.
      - For details, see the description of PATCH operations at
        U(https://github.com/kubernetes/kubernetes/blob/release-1.5/docs/devel/api-conventions.md#patch-operations).
    default: Strategic Merge Patch
    choices: [ JSON Patch, Merge Patch, Strategic Merge Patch ]
    aliases: [ patch_strategy ]
    version_added: 2.4
  certificate_authority_data:
    description:
      - Certificate Authority data for Kubernetes server. Should be in either
        standard PEM format or base64 encoded PEM data. Note that certificate
        verification is broken until ansible supports a version of
        'match_hostname' that can match the IP address against the CA data.
  state:
    description:
      - The desired action to take on the Kubernetes data.
    required: true
    choices: [ absent, present, replace, update ]
    default: present
  url_password:
    description:
      - The HTTP Basic Auth password for the API I(endpoint). This should be set
        unless using the C('insecure') option.
    aliases: [ password ]
  url_username:
    description:
      - The HTTP Basic Auth username for the API I(endpoint). This should be set
        unless using the C('insecure') option.
    default: admin
    aliases: [ username ]
  insecure:
    description:
      - Reverts the connection to using HTTP instead of HTTPS. This option should
        only be used when execuing the M('kubernetes') module local to the Kubernetes
        cluster using the insecure local port (locahost:8080 by default).
  validate_certs:
    description:
      - Enable/disable certificate validation. Note that this is set to
        C(false) until Ansible can support IP address based certificate
        hostname matching (exists in >= python3.5.0).
    type: bool
    default: 'no'
author:
- Eric Johnson (@erjohnso) <erjohnso@google.com>
'''

EXAMPLES = '''
# Create a new namespace with in-line YAML.
- name: Create a kubernetes namespace
  kubernetes:
    api_endpoint: 123.45.67.89
    url_username: admin
    url_password: redacted
    inline_data:
      kind: Namespace
      apiVersion: v1
      metadata:
        name: ansible-test
        labels:
          label_env: production
          label_ver: latest
        annotations:
          a1: value1
          a2: value2
    state: present

# Create a new namespace from a YAML file.
- name: Create a kubernetes namespace
  kubernetes:
    api_endpoint: 123.45.67.89
    url_username: admin
    url_password: redacted
    file_reference: /path/to/create_namespace.yaml
    state: present

# Do the same thing, but using the insecure localhost port
- name: Create a kubernetes namespace
  kubernetes:
    api_endpoint: 123.45.67.89
    insecure: true
    file_reference: /path/to/create_namespace.yaml
    state: present

'''

RETURN = '''
# Example response from creating a Kubernetes Namespace.
api_response:
    description: Raw response from Kubernetes API, content varies with API.
    returned: success
    type: complex
    contains:
        apiVersion: "v1"
        kind: "Namespace"
        metadata:
            creationTimestamp: "2016-01-04T21:16:32Z"
            name: "test-namespace"
            resourceVersion: "509635"
            selfLink: "/api/v1/namespaces/test-namespace"
            uid: "6dbd394e-b328-11e5-9a02-42010af0013a"
        spec:
            finalizers:
                - kubernetes
        status:
            phase: "Active"
'''

import base64
import json

try:
    import yaml
    HAS_LIB_YAML = True
except ImportError:
    HAS_LIB_YAML = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


############################################################################
############################################################################
# For API coverage, this Anislbe module provides capability to operate on
# all Kubernetes objects that support a "create" call (except for 'Events').
# In order to obtain a valid list of Kubernetes objects, the v1 spec file
# was referenced and the below python script was used to parse the JSON
# spec file, extract only the objects with a description starting with
# 'create a'. The script then iterates over all of these base objects
# to get the endpoint URL and was used to generate the KIND_URL map.
#
# import json
# from urllib2 import urlopen
#
# r = urlopen("https://raw.githubusercontent.com/kubernetes"
#            "/kubernetes/master/api/swagger-spec/v1.json")
# v1 = json.load(r)
#
# apis = {}
# for a in v1['apis']:
#     p = a['path']
#     for o in a['operations']:
#         if o["summary"].startswith("create a") and o["type"] != "v1.Event":
#             apis[o["type"]] = p
#
# def print_kind_url_map():
#     results = []
#     for a in apis.keys():
#         results.append('"%s": "%s"' % (a[3:].lower(), apis[a]))
#     results.sort()
#     print("KIND_URL = {")
#     print(",\n".join(results))
#     print("}")
#
# if __name__ == '__main__':
#     print_kind_url_map()
############################################################################
############################################################################

KIND_URL = {
    "binding": "/api/v1/namespaces/{namespace}/bindings",
    "configmap": "/api/v1/namespaces/{namespace}/configmaps",
    "endpoints": "/api/v1/namespaces/{namespace}/endpoints",
    "limitrange": "/api/v1/namespaces/{namespace}/limitranges",
    "namespace": "/api/v1/namespaces",
    "node": "/api/v1/nodes",
    "persistentvolume": "/api/v1/persistentvolumes",
    "persistentvolumeclaim": "/api/v1/namespaces/{namespace}/persistentvolumeclaims",  # NOQA
    "pod": "/api/v1/namespaces/{namespace}/pods",
    "podtemplate": "/api/v1/namespaces/{namespace}/podtemplates",
    "replicationcontroller": "/api/v1/namespaces/{namespace}/replicationcontrollers",  # NOQA
    "resourcequota": "/api/v1/namespaces/{namespace}/resourcequotas",
    "secret": "/api/v1/namespaces/{namespace}/secrets",
    "service": "/api/v1/namespaces/{namespace}/services",
    "serviceaccount": "/api/v1/namespaces/{namespace}/serviceaccounts",
    "daemonset": "/apis/extensions/v1beta1/namespaces/{namespace}/daemonsets",
    "deployment": "/apis/extensions/v1beta1/namespaces/{namespace}/deployments",
    "horizontalpodautoscaler": "/apis/extensions/v1beta1/namespaces/{namespace}/horizontalpodautoscalers",  # NOQA
    "ingress": "/apis/extensions/v1beta1/namespaces/{namespace}/ingresses",
    "job": "/apis/extensions/v1beta1/namespaces/{namespace}/jobs",
}
USER_AGENT = "ansible-k8s-module/0.0.1"


# TODO(erjohnso): SSL Certificate validation is currently unsupported.
# It can be made to work when the following are true:
# - Ansible consistently uses a "match_hostname" that supports IP Address
#   matching. This is now true in >= python3.5.0. Currently, this feature
#   is not yet available in backports.ssl_match_hostname (still 3.4).
# - Ansible allows passing in the self-signed CA cert that is created with
#   a kubernetes master. The lib/ansible/module_utils/urls.py method,
#   SSLValidationHandler.get_ca_certs() needs a way for the Kubernetes
#   CA cert to be passed in and included in the generated bundle file.
# When this is fixed, the following changes can be made to this module,
# - Remove the 'return' statement in line 254 below
# - Set 'required=true' for certificate_authority_data and ensure that
#   ansible's SSLValidationHandler.get_ca_certs() can pick up this CA cert
# - Set 'required=true' for the validate_certs param.

def decode_cert_data(module):
    return
    # pylint: disable=unreachable
    d = module.params.get("certificate_authority_data")
    if d and not d.startswith("-----BEGIN"):
        module.params["certificate_authority_data"] = base64.b64decode(d)


def api_request(module, url, method="GET", headers=None, data=None):
    body = None
    if data:
        data = json.dumps(data)
    response, info = fetch_url(module, url, method=method, headers=headers, data=data)
    if int(info['status']) == -1:
        module.fail_json(msg="Failed to execute the API request: %s" % info['msg'], url=url, method=method, headers=headers)
    if response is not None:
        body = json.loads(response.read())
    return info, body


def k8s_create_resource(module, url, data):
    info, body = api_request(module, url, method="POST", data=data, headers={"Content-Type": "application/json"})
    if info['status'] == 409:
        name = data["metadata"].get("name", None)
        info, body = api_request(module, url + "/" + name)
        return False, body
    elif info['status'] >= 400:
        module.fail_json(msg="failed to create the resource: %s" % info['msg'], url=url)
    return True, body


def k8s_delete_resource(module, url, data):
    name = data.get('metadata', {}).get('name')
    if name is None:
        module.fail_json(msg="Missing a named resource in object metadata when trying to remove a resource")

    url = url + '/' + name
    info, body = api_request(module, url, method="DELETE")
    if info['status'] == 404:
        return False, "Resource name '%s' already absent" % name
    elif info['status'] >= 400:
        module.fail_json(msg="failed to delete the resource '%s': %s" % (name, info['msg']), url=url)
    return True, "Successfully deleted resource name '%s'" % name


def k8s_replace_resource(module, url, data):
    name = data.get('metadata', {}).get('name')
    if name is None:
        module.fail_json(msg="Missing a named resource in object metadata when trying to replace a resource")

    headers = {"Content-Type": "application/json"}
    url = url + '/' + name
    info, body = api_request(module, url, method="PUT", data=data, headers=headers)
    if info['status'] == 409:
        name = data["metadata"].get("name", None)
        info, body = api_request(module, url + "/" + name)
        return False, body
    elif info['status'] >= 400:
        module.fail_json(msg="failed to replace the resource '%s': %s" % (name, info['msg']), url=url)
    return True, body


def k8s_update_resource(module, url, data, patch_operation):
    # PATCH operations are explained in details at:
    # https://github.com/kubernetes/kubernetes/blob/release-1.5/docs/devel/api-conventions.md#patch-operations
    PATCH_OPERATIONS_MAP = {
        'JSON Patch': 'application/json-patch+json',
        'Merge Patch': 'application/merge-patch+json',
        'Strategic Merge Patch': 'application/strategic-merge-patch+json',
    }

    name = data.get('metadata', {}).get('name')
    if name is None:
        module.fail_json(msg="Missing a named resource in object metadata when trying to update a resource")

    headers = {"Content-Type": PATCH_OPERATIONS_MAP[patch_operation]}
    url = url + '/' + name
    info, body = api_request(module, url, method="PATCH", data=data, headers=headers)
    if info['status'] == 409:
        name = data["metadata"].get("name", None)
        info, body = api_request(module, url + "/" + name)
        return False, body
    elif info['status'] >= 400:
        module.fail_json(msg="failed to update the resource '%s': %s" % (name, info['msg']), url=url)
    return True, body


def main():
    module = AnsibleModule(
        argument_spec=dict(
            http_agent=dict(type='str', default=USER_AGENT),
            url_username=dict(type='str', default='admin', aliases=['username']),
            url_password=dict(type='str', default='', no_log=True, aliases=['password']),
            force_basic_auth=dict(type='bool', default=True),
            validate_certs=dict(type='bool', default=False),
            certificate_authority_data=dict(type='str'),
            insecure=dict(type='bool', default=False),
            api_endpoint=dict(type='str', required=True),
            patch_operation=dict(type='str', default='Strategic Merge Patch', aliases=['patch_strategy'],
                                 choices=['JSON Patch', 'Merge Patch', 'Strategic Merge Patch']),
            file_reference=dict(type='str'),
            inline_data=dict(type='str'),
            state=dict(type='str', default='present', choices=['absent', 'present', 'replace', 'update'])
        ),
        mutually_exclusive=(('file_reference', 'inline_data'),
                            ('url_username', 'insecure'),
                            ('url_password', 'insecure')),
        required_one_of=(('file_reference', 'inline_data')),
    )

    if not HAS_LIB_YAML:
        module.fail_json(msg="missing python library: yaml")

    decode_cert_data(module)

    api_endpoint = module.params.get('api_endpoint')
    state = module.params.get('state')
    insecure = module.params.get('insecure')
    inline_data = module.params.get('inline_data')
    file_reference = module.params.get('file_reference')
    patch_operation = module.params.get('patch_operation')

    if inline_data:
        if not isinstance(inline_data, dict) and not isinstance(inline_data, list):
            data = yaml.safe_load(inline_data)
        else:
            data = inline_data
    else:
        try:
            f = open(file_reference, "r")
            data = [x for x in yaml.safe_load_all(f)]
            f.close()
            if not data:
                module.fail_json(msg="No valid data could be found.")
        except:
            module.fail_json(msg="The file '%s' was not found or contained invalid YAML/JSON data" % file_reference)

    # set the transport type and build the target endpoint url
    transport = 'https'
    if insecure:
        transport = 'http'

    target_endpoint = "%s://%s" % (transport, api_endpoint)

    body = []
    changed = False

    # make sure the data is a list
    if not isinstance(data, list):
        data = [data]

    for item in data:
        namespace = "default"
        if item and 'metadata' in item:
            namespace = item.get('metadata', {}).get('namespace', "default")
            kind = item.get('kind', '').lower()
            try:
                url = target_endpoint + KIND_URL[kind]
            except KeyError:
                module.fail_json(msg="invalid resource kind specified in the data: '%s'" % kind)
            url = url.replace("{namespace}", namespace)
        else:
            url = target_endpoint

        if state == 'present':
            item_changed, item_body = k8s_create_resource(module, url, item)
        elif state == 'absent':
            item_changed, item_body = k8s_delete_resource(module, url, item)
        elif state == 'replace':
            item_changed, item_body = k8s_replace_resource(module, url, item)
        elif state == 'update':
            item_changed, item_body = k8s_update_resource(module, url, item, patch_operation)

        changed |= item_changed
        body.append(item_body)

    module.exit_json(changed=changed, api_response=body)


if __name__ == '__main__':
    main()
