#!/usr/bin/python

# encoding: utf-8

# (c) 2016, James Hogarth <james.hogarth@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
author: James Hogarth
module: jenkins_script
short_description: Executes a groovy script in the jenkins instance
version_added: '2.3'
description:
    - The C(jenkins_script) module takes a script plus a dict of values
      to use within the script and returns the result of the script being run.

options:
  script:
    description:
      - The groovy script to be executed.
        This gets passed as a string Template if args is defined.
    required: true
    default: null
  url:
    description:
      - The jenkins server to execute the script against. The default is a local
        jenkins instance that is not being proxied through a webserver.
    required: false
    default: http://localhost:8080
  validate_certs:
    description:
      - If set to C(no), the SSL certificates will not be validated.
        This should only set to C(no) used on personally controlled sites
        using self-signed certificates as it avoids verifying the source site.
    required: false
    default: True
  user:
    description:
      - The username to connect to the jenkins server with.
    required: false
    default: null
  password:
    description:
      - The password to connect to the jenkins server with.
    required: false
    default: null
  timeout:
    description:
      - The request timeout in seconds
    required: false
    default: 10
    version_added: "2.4"
  args:
    description:
      - A dict of key-value pairs used in formatting the script using string.Template (see https://docs.python.org/2/library/string.html#template-strings).
    required: false
    default: null
  params:
    required: false
    default: null
    description:
      - Option used to allow the user to overwrite any of the other options. To
        remove an option, set the value of the option to C(null).
    version_added: 2.4

notes:
    - Since the script can do anything this does not report on changes.
      Knowing the script is being run it's important to set changed_when
      for the ansible output to be clear on any alterations made.

'''

EXAMPLES = '''
- name: Obtaining a list of plugins
  jenkins_script:
    script: 'println(Jenkins.instance.pluginManager.plugins)'
    user: admin
    password: admin

- name: Setting master using a variable to hold a more complicate script
  vars:
    setmaster_mode: |
        import jenkins.model.*
        instance = Jenkins.getInstance()
        instance.setMode(${jenkins_mode})
        instance.save()

- name: use the variable as the script
  jenkins_script:
    script: "{{ setmaster_mode }}"
    args:
      jenkins_mode: Node.Mode.EXCLUSIVE

- name: interacting with an untrusted HTTPS connection
  jenkins_script:
    script: "println(Jenkins.instance.pluginManager.plugins)"
    user: admin
    password: admin
    url: https://localhost
    validate_certs: no
#
# Example of how to use the params
#
# Define a variable and specify all default parameters you want to use across
# all jenkins_plugin calls:
#
# my_jenkins_params:
#   url_username: admin
#   url_password: p4ssw0rd
#   url: https://localhost:8433
#   validate_certs: no
#
- name: Say Hello!
  jenkins_script:
    script: "println('Hello, Jenkins!')"
    params: "{{ my_jenkins_params }}"
'''

RETURN = '''
output:
    description: Result of script
    returned: success
    type: string
    sample: 'Result: true'
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import fetch_url, url_argument_spec


def is_csrf_protection_enabled(module):
    resp, info = fetch_url(module,
                           module.params['url'] + '/api/json',
                           method='GET')
    if info["status"] != 200:
        module.fail_json(msg="HTTP error " + str(info["status"]) + " " + info["msg"])

    content = resp.read()
    return json.loads(content).get('useCrumbs', False)


def get_crumb(module):
    resp, info = fetch_url(module,
                           module.params['url'] + '/crumbIssuer/api/json',
                           method='GET')
    if info["status"] != 200:
        module.fail_json(msg="HTTP error " + str(info["status"]) + " " + info["msg"])

    content = resp.read()
    return json.loads(content)


def main():

    argument_spec = url_argument_spec()
    argument_spec.update(
        script=dict(required=True, type="str"),
        url=dict(required=False, type="str", default="http://localhost:8080"),
        validate_certs=dict(required=False, type="bool", default=True),
        user=dict(required=False, no_log=True, type="str", default=None),
        password=dict(required=False, no_log=True, type="str", default=None),
        timeout=dict(required=False, type="int", default=10),
        params=dict(type='dict'),
        args=dict(required=False, type="dict", default=None)
    )
    module = AnsibleModule(
        argument_spec=argument_spec
    )

    # Update module parameters by user's parameters if defined
    if 'params' in module.params and isinstance(module.params['params'], dict):
        module.params.update(module.params['params'])
        # Remove the params
        module.params.pop('params', None)

    if module.params['user'] is not None:
        if module.params['password'] is None:
            module.fail_json(msg="password required when user provided")
        module.params['url_username'] = module.params['user']
        module.params['url_password'] = module.params['password']

    # Force basic authentication
    module.params['force_basic_auth'] = True

    if module.params['args'] is not None:
        from string import Template
        script_contents = Template(module.params['script']).substitute(module.params['args'])
    else:
        script_contents = module.params['script']

    headers = {}
    if is_csrf_protection_enabled(module):
        crumb = get_crumb(module)
        headers = {crumb['crumbRequestField']: crumb['crumb']}

    resp, info = fetch_url(module,
                           module.params['url'] + "/scriptText",
                           data=urlencode({'script': script_contents}),
                           headers=headers,
                           method="POST",
                           timeout=module.params['timeout'])

    if info["status"] != 200:
        module.fail_json(msg="HTTP error " + str(info["status"]) + " " + info["msg"])

    result = resp.read()

    if 'Exception:' in result and 'at java.lang.Thread' in result:
        module.fail_json(msg="script failed with stacktrace:\n " + result)

    module.exit_json(
        output=result,
    )


if __name__ == '__main__':
    main()
