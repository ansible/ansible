#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jeroen Hoekx <jeroen.hoekx@dsquare.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import os
import shutil
import time
import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: jboss
version_added: "1.4"
short_description: deploy applications to JBoss
description:
  - Deploy applications to JBoss standalone using the filesystem
options:
  deployment:
    required: true
    description:
      - The name of the deployment
  src:
    required: false
    description:
      - The remote path of the application ear or war to deploy
  deploy_path:
    required: false
    default: /var/lib/jbossas/standalone/deployments
    description:
      - The location in the filesystem where the deployment scanner listens
  deployment_strategy:
    required: false
    choices: [ http, filesystem, jboss-cli ]
    default: filesystem
    description:
      - Whether the application should be deployed through the HTTP management API or filesystem
    version_added: 2.4
  state:
    required: false
    choices: [ deployed, undeployed, present, absent ]
    default: deployed
    description:
      - Whether the application should be deployed or undeployed. Present and absent have been deprecated.
  url_username:
    required: false
    description:
      - Username for JBoss management user
    version_added: 2.4
  url_password:
    required: false
    description:
      - Password for JBoss management user
    version_added: 2.4
  hostname:
    required: false
    default: localhost
    description:
      - Hostname of JBoss instance running HTTP management API
    version_added:2.4
  port:
    required: false
    default: 9990
    description:
      - Port binding for HTTP management API
    version_added:2.4
notes:
  - "The filesystem deployment strategy requires the deployment scanner to be enabled."
  - "The http deployment strategy requires the requests package to be installed on each host."
  - "Ensure no identically named application is deployed through the JBoss CLI"
  - "At a minimum, url_password should be vaulted."
  - "HTTP management API is supported in JBoss AS 7.1, Wildfly >= 8, and JBoss EAP >= 6."
  - "JBoss 5 supports filesystem deployments only."
  - "Filesystem deployments should be avoided in production environments where possible."
author: "Jeroen Hoekx (@jhoekx)"
"""

EXAMPLES = """
# Deploy a hello world application using filesystem
- jboss:
    src: /tmp/hello-1.0-SNAPSHOT.war
    deployment: hello.war
    state: deployed

# Update the hello world application using filesystem
- jboss:
    src: /tmp/hello-1.1-SNAPSHOT.war
    deployment: hello.war
    state: deployed

# Undeploy the hello world application using filesystem
- jboss:
    deployment: hello.war
    state: undeployed

# Deploy the hello world application using HTTP management API
- jboss:
    src: /tmp/hello-1.0-SNAPSHOT.war
    deployment: hello.war
    deployment_strategy: http
    state: deployed
    url_username: admin
    url_password: admin

# Update the hello world application using HTTP management API
- jboss:
    src: /tmp/hello-1.0-SNAPSHOT.war
    deployment: hello.war
    deployment_strategy: http
    state: deployed
    url_username: admin
    url_password: admin

# Undeploy the hello world application using HTTP management API
- jboss:
    deployment: hello.war
    deployment_strategy: http
    state: undeployed
    url_username: admin
    url_password: admin

"""

import os
import shutil
import time
import json
<<<<<<< HEAD
import requests
=======
>>>>>>> Added version_added for new options, moved imports back
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def is_deployed(module):

    if module.params['deployment_strategy'] == 'http':
        data_dict = {
            "operation": "read-resource",
            "address": {
                "deployment": module.params['deployment']
            },
            "include-runtime": True
        }

        headers = {
            'Content-Type': 'application/json'
        }

        data = json.dumps(data_dict)

        resp, info = fetch_url(module, 'http://%s:9990/management' % module.params['hostname'], data=data, headers=headers)

        return info['status'] == 200

    elif module.params['deployment_strategy'] == 'filesystem':
        return os.path.exists(os.path.join(module.params['deploy_path'], "%s.deployed" % module.params['deployment']))
    else:
        rc, stdout, stderr = module.run_command([module.params['cli_path'], '--connect', '--commands=deploy-info'])

        if rc != 0:
            return False

        lines = stdout.split()
        for line in lines:
            if module.params['deployment'] in line:
                return True
        return False


def is_undeployed(deploy_path, deployment):
    return os.path.exists(os.path.join(deploy_path, "%s.undeployed" % deployment))


def is_failed(deploy_path, deployment):
    return os.path.exists(os.path.join(deploy_path, "%s.failed" % deployment))


def fs_deploy(module, deployed):

    if not deployed:
        if not os.path.exists(module.params['src']):
            module.fail_json(msg='Source file %s does not exist.' % module.params['src'])
        if is_failed(module.params['deploy_path'], module.params['deployment']):
            # Clean up old failed deployment
            os.remove(os.path.join(module.params['deploy_path'], "%s.failed" % module.params['deployment']))

        shutil.copyfile(module.params['src'], os.path.join(module.params['deploy_path'], module.params['deployment']))

        while not deployed:
            deployed = is_deployed(module)
            if is_failed(module.params['deploy_path'], module.params['deployment']):
                module.fail_json(msg='Deploying %s failed.' % module.params['deployment'])
            time.sleep(1)
        return True
    else:
        if module.sha1(module.params['src']) != module.sha1(os.path.join(module.params['deploy_path'], module.params['deployment'])):
            os.remove(os.path.join(module.params['deploy_path'], "%s.deployed" % module.params['deployment']))
            shutil.copyfile(module.params['src'], os.path.join(module.params['deploy_path'], module.params['deployment']))
            deployed = False
            while not deployed:
                deployed = is_deployed(module)
                if is_failed(module.params['deploy_path'], module.params['deployment']):
                    module.fail_json(msg='Deploying %s failed.' % module.params['deployment'])
                time.sleep(1)
            return True
        return False


def http_deploy(module, deployed):

    if deployed:
        data_dict = {
            'operation': 'read-resource',
            'address': {
                'deployment': module.params['deployment']
            },
            'include-runtime': True
        }

        headers = {
            'Content-Type': 'application/json'
        }
        data = json.dumps(data_dict)

        resp, info = fetch_url(module, 'http://%s:%s/management' % (module.params['hostname'], module.params['port']), data=data, headers=headers)

        try:
            assert info['status'] == 200
        except AssertionError:
            module.fail_json(msg=info)

        resp_json = json.loads(resp.read())

        # Process existing deployment hash
        deployment_hash_dict = (key for key in resp_json['result']['content'] if 'hash' in key).next()
        deployment_hash_base64 = deployment_hash_dict['hash']['BYTES_VALUE']
        deployment_hash_hex = deployment_hash_base64.decode('base64').encode('hex')

        if module.sha1(module.params['src']) != deployment_hash_hex:

            import requests
            resp = requests.post(
                'http://%s:%s/management/add-content' % (module.params['hostname'], module.params['port']),
                files={'file': open(module.params['src'], 'rb')},
                auth=requests.auth.HTTPDigestAuth(module.params['url_username'], module.params['url_password'])
            )

            if resp.status_code < 400:
                return True
            else:
                module.fail_json(msg={'status': 'HTTP %s %s' % (resp.status_code, resp.reason)})
    else:

        headers = {
            'Content-Type': 'application/json'
        }

        import requests
        auth = requests.auth.HTTPDigestAuth(module.params['url_username'], module.params['url_password'])
        resp = requests.post(
            'http://%s:%s/management/add-content' % (module.params['hostname'], module.params['port']),
            files={'file': open(module.params['src'], 'rb')},
            auth=auth
        )

        try:
            assert resp.status_code == 200
        except AssertionError:
            module.fail_json(msg=resp.text)

        resp_json = resp.json()

        data_dict = {
            'operation': 'add',
            'address': [{
                'deployment': module.params['deployment']
            }],
            'enabled': True,
            'content': [{'hash': {'BYTES_VALUE': resp_json['result']['BYTES_VALUE']}}]
        }

        resp = requests.post(
            'http://%s:%s/management' % (module.params['hostname'], module.params['port']),
            json=data_dict,
            headers=headers,
            auth=auth
        )

        try:
            assert resp.status_code == 200
        except AssertionError:
            module.fail_json(msg=resp.text)

        return True

    return False


def fs_undeploy(module, deployed):

    if not deployed:
        return False

    os.remove(os.path.join(module.params['deploy_path'], "%s.deployed" % module.params['deployment']))
    while deployed:
        deployed = not is_undeployed(module.params['deploy_path'], module.params['deployment'])
        if is_failed(module.params['deploy_path'], module.params['deployment']):
            module.fail_json(msg='Undeploying %s failed.' % module.params['deployment'])
        time.sleep(1)
    return True


def http_undeploy(module, deployed):

    if not deployed:
        return False

    data_dict = {
        'operation': 'remove',
        'address': {
            'deployment': module.params['deployment']
        },
        'include-runtime': True
    }

    headers = {
        'Content-Type': 'application/json'
    }
    data = json.dumps(data_dict)

    resp, info = fetch_url(module, 'http://%s:%s/management' % (module.params['hostname'], module.params['port']), data=data, headers=headers)

    return True


def cli_deploy(module, deployed):
    rc, stdout, stderr = module.run_command([module.params['cli_path'], '--connect', '--commands=deploy %s --force' % module.params['src']])
    if rc == 0:
        return True
    else:
        module.fail_json(msg=stderr)


def cli_undeploy(module, deployed):
    rc, stdout, stderr = module.run_command([module.params['cli_path'], '--connect', '--commands=undeploy %s' % module.params['deployment']])
    if rc == 0:
        return True
    else:
        module.fail_json(msg=stderr)


DEPLOY_CALLABLES = {
    'http': {
        'deployed': http_deploy,
        'present': http_deploy,
        'undeployed': http_undeploy,
        'absent': http_undeploy
    },
    'filesystem': {
        'deployed': fs_deploy,
        'present': fs_deploy,
        'undeployed': fs_undeploy,
        'absent': fs_undeploy
    },
    'jboss-cli': {
        'deployed': cli_deploy,
        'present': cli_deploy,
        'undeployed': cli_undeploy,
        'absent': cli_undeploy
    }
}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='path'),
            deployment=dict(required=True),
            deploy_path=dict(type='path', default='/var/lib/jbossas/standalone/deployments'),
            deployment_strategy=dict(choices=['http', 'filesystem', 'jboss-cli'], default='filesystem'),
            state=dict(choices=['deployed', 'undeployed', 'present', 'absent'], default='deployed'),
            url_username=dict(required=True),
            url_password=dict(required=True),
            hostname=dict(default='localhost'),
            port=dict(default=9990),
            cli_path=dict(type='path')
        ),
        required_if=[
            ('state', ('deployed', 'present'), ('src',), True),
            ('deployment_strategy', ('http',), ('hostname', 'port')),
            ('deployment_strategy', ('jboss-cli',), ('cli_path'))
        ]
    )

    result = dict(changed=False)

    deployment_strategy = module.params['deployment_strategy']
    deploy_path = module.params['deploy_path']
    state = module.params['state']

    if state == 'present' or state == 'absent':
        module.deprecate('The "present" and "absent" values for the state key are deprecated in favor of "deployed" and "undeployed", respectively')

    if deployment_strategy == 'filesystem':
        module.warn('Filesystem deployments are not recommended for production use.')

    if not os.path.exists(deploy_path):
        module.fail_json(msg="deploy_path does not exist.")

    action = DEPLOY_CALLABLES[deployment_strategy][state]
    deployed = is_deployed(module)
    result = dict(changed=action(module, deployed))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
