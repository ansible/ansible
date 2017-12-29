#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ettore Simone (@esimone74) <ettore.simone@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: marathon_app

short_description: Manage Mesos Marathon applications

version_added: "2.5"

author: "Ettore Simone (@esimone74) <ettore.simone@gmail.com>"

description:
  - Manage the life cycle of applications and containers with Marathon in a Mesos cluster.

options:
  marathon_uri:
    description:
      - Base URI of the Marathon master.
    required: false
    default: "http://marathon.mesos:8080"
    aliases:
      - marathon_url
      - uri
      - url
  username:
    description:
      - The username to connect to the Marathon server with.
    required: false
    default: null
    aliases:
      - user
  password:
    description:
      - The password to connect to the Marathon server with.
    required: false
    default: null
    aliases:
      - pass
  state:
    description:
      - The desired action to take on the Marathon data.
    required: true
    default: present
    choices:
      - present
      - absent
      - update
      - replace
      - restart
  inline_data:
    description:
      - The Marathon JSON data to send to the API I(marathon_uri). This option is
        mutually exclusive with C('file_reference').
    required: true
    default: null
  file_reference:
    description:
      - Specify full path to a Marathon JSON file to send to API I(marathon_uri).
        This option is mutually exclusive with C('inline_data').
    required: false
    default: null
  sleep:
    description:
      - Number of seconds to sleep between checks.
    required: false
    default: 1.0
  wait:
    description:
      - Wait for deployments completion.
    required: false
    default: false
  force:
    description:
      - setting force will cancel the current deployment if any.
    required: false
    default: false

'''

EXAMPLES = '''
# Replaces parameters of a running application with in-line JSON.
# If no application with the given id exists, it will be created.
# If there is an application with this id, all running instances
# get upgraded to the new definition.
- name: Create a Marathon application
  marathon_app:
    url: http://marathon.mesos:8080
    inline_data:
      id: /foo
      instances: 5
      cmd: "sleep infinity"
      cpus: 0.1
      mem: 16
    state: present

# Replaces parameters of a running application with in-line JSON.
# If no application with the given id exists, it will return an
# error.
# All running instances get upgraded to the new definition.
- name: Scale a Marathon application
  marathon_app:
    url: https://admin:changeme@marathon.mesos:8443
    inline_data:
      id: /foo
      instances: 10
    state: update
    wait: yes

# Replaces parameters of a running application from a JSON file.
# If no application with the given id exists, it will be created.
# If there is an application with this id, all running instances
# get upgraded to the new definition.
- name: Create a Marathon application
  marathon_app:
    url: http://marathon.mesos:8080
    file_reference: /path/to/app.json
    state: present

# Destroy an application. All data about that application will be
# deleted.
- name: Create a Marathon application
  marathon_app:
    url: https://marathon.mesos:8443
    url_username: admin
    url_password: changeme
    inline_data:
      id: /foo
    state: absent
'''

RETURN = '''
# TBD
'''

from ansible.module_utils.basic import load_platform_subclass, AnsibleModule
from ansible.module_utils.urls import fetch_url
import time

has_lib_yaml = True
has_lib_json = True

try:
    import yaml
except ImportError:
    has_lib_yaml = False

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        has_lib_json = False


class DictDiff(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """

    def __init__(self, src, tgt):
        self.tgt, self.src = tgt, src
        self.set_tgt, self.set_src = set(tgt.keys()), set(src.keys())
        self.intersect = self.set_tgt.intersection(self.set_src)

    def added(self):
        return self.set_tgt - self.intersect

    def removed(self):
        return self.set_src - self.intersect

    def changed(self):
        return set(o for o in self.intersect if self.src[o] != self.tgt[o])

    def unchanged(self):
        return set(o for o in self.intersect if self.src[o] == self.tgt[o])


class MarathonApp(object):
    """
    Marathon Application
    """

    def __init__(self, module):
        super(MarathonApp, self).__init__()

        self.module = module
        self.state = module.params['state']
        self.marathon_uri = module.params['marathon_uri']
        self.changed = False
        self.results = []
        self.sleep = module.params['sleep']
        self.wait = module.params['wait']

        if not self.marathon_uri.endswith('/'):
            self.marathon_uri = self.marathon_uri + '/'

    def get_id(self, data=None):
        name = data.get('id', {})
        if name is None:
            self.module.fail_json(msg="Missing the application id in object metadata")
        if not name.startswith('/'):
            name = '/' + name
        return name

    def api_request(self, url, method="GET", headers=None, data=None):
        if data:
            data = json.dumps(data)
        response, info = fetch_url(self.module, url, method=method, headers=headers, data=data)
        if int(info['status']) == -1:
            self.module.fail_json(msg="Failed to execute the API request: %s" % info['msg'], url=url)
        return response, info

    def send_request(self, path, method=None, data=None):
        body = None
        url = self.marathon_uri + path
        ret, info = self.api_request(url, method=method, headers={"Content-Type": "application/json"}, data=data)
        if ret is not None:
            body = json.load(ret)
        if info['status'] >= 400:
            return False, json.loads(info['body'])
        return True, body

    def wait_for_deployments(self, path):
        while self.wait:
            ret, check = self.send_request(path)
            if ret and check['app']['deployments'] == []:
                break
            time.sleep(self.sleep)

    def create_app(self, data=None):
        app_id = self.get_id(data)
        ret, info = self.send_request('v2/apps' + self.get_id(data))
        diff = DictDiff(info['app'] if ret else {}, data)
        self.module.debug(msg="Added: %s, Changed: %s" % (diff.added(), diff.changed()))
        if diff.added() or diff.changed():
            ret, info = self.send_request('v2/apps' + app_id, method='PUT', data=data)
            self.changed = self.changed or bool(ret)
            if ret:
                self.wait_for_deployments('v2/apps' + app_id)
            return info
        else:
            return {"message": "App '%s' already exist" % app_id}

    def delete_app(self, data=None):
        app_id = self.get_id(data)
        ret, info = self.send_request('v2/apps' + app_id, method='DELETE', data=data)
        self.changed = self.changed or bool(ret)
        if ret:
            self.wait_for_deployments('v2/apps' + app_id)
        return info

    def restart_app(self, data=None):
        app_id = self.get_id(data)
        ret, info = self.send_request('v2/apps' + app_id + '/restart', method='POST')
        if not ret:
            self.module.fail_json(msg=info)
        self.changed = self.changed or bool(ret)
        if ret:
            self.wait_for_deployments('v2/apps' + app_id)
        return info


def main():
    module_args = dict(
        marathon_uri=dict(type='str', default='http://marathon.mesos:8080', aliases=['marathon_url', 'uri', 'url']),
        state=dict(type='str', choices=['present', 'absent', 'update', 'replace', 'restart']),
        url_username=dict(type='str', default=None, aliases=['username']),
        url_password=dict(type='str', default=None, no_log=True, aliases=['password']),
        file_reference=dict(required=False),
        inline_data=dict(required=False),
        sleep=dict(type='float', default=1.0),
        wait=dict(type='bool', default=False),
        force=dict(type='bool', default=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=(('file_reference', 'inline_data'),),
        required_one_of=(('file_reference', 'inline_data'),),
    )

    if not has_lib_yaml:
        module.fail_json(msg="missing python library: yaml")
    if not has_lib_json:
        module.fail_json(msg="missing python library: json")

    if module.params['url_username'] is not None or module.params['url_password'] is not None:
        module.params['force_basic_auth'] = True

    inline_data = module.params['inline_data']
    file_reference = module.params['file_reference']

    if inline_data:
        if not isinstance(inline_data, dict) and not isinstance(inline_data, list):
            try:
                data = json.loads(inline_data)
            except:
                data = yaml.safe_load(inline_data)
        else:
            data = inline_data
    else:
        try:
            f = open(file_reference, "r")
            data = json.load(f)
            f.close()
            if not data:
                module.fail_json(msg="No valid data could be found.")
        except:
            module.fail_json(msg="The file '%s' was not found or contained invalid JSON data" % file_reference)

    marathon = MarathonApp(module)

    if module.params['state'] in ['absent', 'replace']:
        body = marathon.delete_app(data)
        marathon.results.append(body)
    if module.params['state'] in ['present', 'update', 'replace']:
        body = marathon.create_app(data)
        marathon.results.append(body)
    if module.params['state'] in ['restart']:
        body = marathon.restart_app(data)
        marathon.results.append(body)

    module.exit_json(changed=marathon.changed, api_response=marathon.results)

if __name__ == '__main__':
    main()
