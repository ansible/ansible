#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: jenkins_job
short_description: Manage jenkins jobs
description:
    - Manage Jenkins jobs by using Jenkins REST API
requirements:
  - "python-jenkins >= 0.4.12"
  - "lxml >= 3.3.3"
version_added: "2.2"
author: "Sergio Millan Rodriguez (@sermilrod)"
options:
  config:
    description:
      - config in XML format.
      - Required if job does not yet exist.
      - Mututally exclusive with C(enabled).
      - Considered if C(state=present).
    required: false
  enabled:
    description:
      - Whether the job should be enabled or disabled.
      - Mututally exclusive with C(config).
      - Considered if C(state=present).
    required: false
  name:
    description:
      - Name of the Jenkins job.
    required: true
  password:
    description:
      - Password to authenticate with the Jenkins server.
    required: false
  state:
    description:
      - Attribute that specifies if the job has to be created or deleted.
    required: false
    default: present
    choices: ['present', 'absent']
  token:
    description:
      - API token used to authenticate alternatively to password.
    required: false
  url:
    description:
      - Url where the Jenkins server is accessible.
    required: false
    default: http://localhost:8080
  user:
    description:
       - User to authenticate with the Jenkins server.
    required: false
'''

EXAMPLES = '''
# Create a jenkins job using basic authentication
- jenkins_job:
    config: "{{ lookup('file', 'templates/test.xml') }}"
    name: test
    password: admin
    url: "http://localhost:8080"
    user: admin

# Create a jenkins job using the token
- jenkins_job:
    config: "{{ lookup('template', 'templates/test.xml.j2') }}"
    name: test
    token: asdfasfasfasdfasdfadfasfasdfasdfc
    url: "http://localhost:8080"
    user: admin

# Delete a jenkins job using basic authentication
- jenkins_job:
    name: test
    password: admin
    state: absent
    url: "http://localhost:8080"
    user: admin

# Delete a jenkins job using the token
- jenkins_job:
    name: test
    token: asdfasfasfasdfasdfadfasfasdfasdfc
    state: absent
    url: "http://localhost:8080"
    user: admin

# Disable a jenkins job using basic authentication
- jenkins_job:
    name: test
    password: admin
    enabled: false
    url: "http://localhost:8080"
    user: admin

# Disable a jenkins job using the token
- jenkins_job:
    name: test
    token: asdfasfasfasdfasdfadfasfasdfasdfc
    enabled: false
    url: "http://localhost:8080"
    user: admin
'''

RETURN = '''
---
name:
  description: Name of the jenkins job.
  returned: success
  type: string
  sample: test-job
state:
  description: State of the jenkins job.
  returned: success
  type: string
  sample: present
url:
  description: Url to connect to the Jenkins server.
  returned: success
  type: string
  sample: https://jenkins.mydomain.com
'''

try:
    import jenkins
    python_jenkins_installed = True
except ImportError:
    python_jenkins_installed = False

try:
    from lxml import etree as ET
    python_lxml_installed = True
except ImportError:
    python_lxml_installed = False

class Jenkins:
    def __init__(self, config, name, password, state, enabled, token, url, user):
        self.config = config
        self.name = name
        self.password = password
        self.state = state
        self.enabled = enabled
        self.token = token
        self.user = user
        self.jenkins_url = url
        self.server = self.get_jenkins_connection()
        self.diff = {
            'before': "",
            'after': "",
        }

    def get_jenkins_connection(self):
        try:
            if (self.user and self.password):
                return jenkins.Jenkins(self.jenkins_url, self.user, self.password)
            elif (self.user and self.token):
                return jenkins.Jenkins(self.jenkins_url, self.user, self.token)
            elif (self.user and not (self.password or self.token)):
                return jenkins.Jenkins(self.jenkins_url, self.user)
            else:
                return jenkins.Jenkins(self.jenkins_url)
        except Exception:
            e = get_exception()
            module.fail_json(msg='Unable to connect to Jenkins server, %s' % str(e))

    def get_job_status(self, module):
        try:
            return self.server.get_job_info(self.name)['color'].encode('utf-8')
        except Exception:
            e = get_exception()
            module.fail_json(msg='Unable to fetch job information, %s' % str(e))

    def job_exists(self, module):
        try:
            return bool(self.server.job_exists(self.name))
        except Exception:
            e = get_exception()
            module.fail_json(msg='Unable to validate if job exists, %s for %s' % (str(e), self.jenkins_url))

    def build(self, module):
        if self.state == 'present':
            self.update_job(module)
        else:
            self.delete_job(module)

    def get_config(self):
        return job_config_to_string(self.config)

    def configuration_changed(self):
        # config is optional, if not provided we keep the current config as is
        if self.config is None:
            return False

        changed = False
        config_file = self.get_config()
        self.diff['after'] = config_file
        machine_file = job_config_to_string(self.server.get_job_config(self.name).encode('utf-8'))
        self.diff['before'] = machine_file
        if machine_file != config_file:
            changed = True
        return changed

    def update_job(self, module):
        if self.config is None and self.enabled is None:
            module.fail_json(msg='one of the following params is required on state=present: config,enabled')

        if not self.job_exists(module):
            self.create_job(module)
        else:
            self.reconfig_job(module)

    def state_changed(self, status):
        # Keep in current state if enabled arg_spec is not given
        if self.enabled is None:
            return False

        changed = False
        if ( (self.enabled == False and status != "disabled") or (self.enabled == True and status == "disabled") ):
            changed = True

        return changed

    def change_state(self):
        if self.enabled == False:
            self.server.disable_job(self.name)
        else:
            self.server.enable_job(self.name)

    def reconfig_job(self, module):
        changed = False
        try:
            status = self.get_job_status(module)

            # Handle job config
            if self.configuration_changed():
                changed = True
                if not module.check_mode:
                    self.server.reconfig_job(self.name, self.get_config())

            # Handle job disable/enable
            elif self.state_changed(status):
                changed = True
                if not module.check_mode:
                    self.change_state()

        except Exception:
            e = get_exception()
            module.fail_json(msg='Unable to reconfigure job, %s for %s' % (str(e), self.jenkins_url))

        module.exit_json(changed=changed, name=self.name, state=self.state, url=self.jenkins_url, diff=self.diff)

    def create_job(self, module):

        if self.config is None:
            module.fail_json(msg='missing required param: config')

        changed = True
        try:
            config_file = self.get_config()
            self.diff['after'] = config_file
            if not module.check_mode:
                self.server.create_job(self.name, config_file)
                self.change_state()
        except Exception:
            e = get_exception()
            module.fail_json(msg='Unable to create job, %s for %s' % (str(e), self.jenkins_url))

        module.exit_json(changed=changed, name=self.name, state=self.state, url=self.jenkins_url, diff=self.diff)

    def delete_job(self, module):
        changed = False
        if self.job_exists(module):
            changed = True
            self.diff['before'] = job_config_to_string(self.server.get_job_config(self.name).encode('utf-8'))
            if not module.check_mode:
                try:
                    self.server.delete_job(self.name)
                except Exception:
                    e = get_exception()
                    module.fail_json(msg='Unable to delete job, %s for %s' % (str(e), self.jenkins_url))

        module.exit_json(changed=changed, name=self.name, state=self.state, url=self.jenkins_url, diff=self.diff)

def test_dependencies(module):
    if not python_jenkins_installed:
        module.fail_json(msg="python-jenkins required for this module. "\
              "see http://python-jenkins.readthedocs.io/en/latest/install.html")

    if not python_lxml_installed:
        module.fail_json(msg="lxml required for this module. "\
              "see http://lxml.de/installation.html")

def job_config_to_string(xml_str):
    return ET.tostring(ET.fromstring(xml_str))

def jenkins_builder(module):
    return Jenkins(
        module.params.get('config'),
        module.params.get('name'),
        module.params.get('password'),
        module.params.get('state'),
        module.params.get('enabled'),
        module.params.get('token'),
        module.params.get('url'),
        module.params.get('user')
    )

def main():
    module = AnsibleModule(
        argument_spec = dict(
            config      = dict(required=False),
            name        = dict(required=True),
            password    = dict(required=False, no_log=True),
            state       = dict(required=False, choices=['present', 'absent'], default="present"),
            enabled     = dict(required=False, type='bool'),
            token       = dict(required=False, no_log=True),
            url         = dict(required=False, default="http://localhost:8080"),
            user        = dict(required=False)
        ),
        mutually_exclusive = [
            ['password', 'token'],
            ['config', 'enabled'],
        ],
        supports_check_mode=True,
    )

    test_dependencies(module)
    jenkins = jenkins_builder(module)
    jenkins.build(module)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
