#!/usr/bin/python
#
# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: jenkins_job_generator

short_description: Manage jenkins jobs through YAML config files.

version_added: "2.7"

description:
    - Manage jenkins jobs through YAML config files.
    - This is a wrapper around jenkins job builder.
    - Using this module all jobs would be in idempotency state.
    - "Please use the JJB documentation - https://docs.openstack.org/infra/jenkins-job-builder/
    to get information about how to write job YAML config files"
    - "Please note, all YAML configuration files should be on a remote server.
    Copy them before running this module task"

options:
    jenkins_server:
        description:
            - Jenkins server address. Default is http://127.0.0.1:8080
        required: false
        default: http://127.0.0.1:8080
    user:
        description:
            - Username to access jenkins server API
        required: false
        default: ''
    password:
        description:
            - User password
        required: false
        default: ''
    jobs:
        description: "List of jobs which you want to add or delete.
        Note: In case adding jobs, path variable should be set"
        required: false
    path:
        description:
            - Path to job configuration files
        required: true
    file:
        description:
            - File name wth job configuration. You shouldn't set jobs variable with this variable
        required: true
    workers:
        description:
            - Number of workers
        required: false
        default: 1
    delete_old:
        description:
            - Delete old jobs
        required: false
        default: false
        type: bool
    state:
        description:
            - Attribute that specifies the job state (present, absent, enabled, disabled)
        required: true
        default: present
        choices:
           - present
           - absent
           - enabled
           - disabled

requirements:
    - "python-jenkins >= 0.4.12"
    - jenkins-job-builder

author: "Aleksei Philippov (@lelik9)"
'''

EXAMPLES = '''
# Copy job configuration from template
- name: Create job template
  template:
    src: jobs/production.yaml.j2
    dest: /tmp/production.yaml

# Update or create all jobs from file
- name: Generate jobs
  jenkins_job_generator:
    file: production.yaml
    path: /tmp
    state: present
    user: jenkins
    password: jenkins

# Update or create all jobs in the path with non default jenkins server address
- name: Generate jobs
  jenkins_job_generator:
    path: /tmp
    state: present
    user: jenkins
    password: jenkins
    jenkins_server: "http://127.0.0.1:8000"

# Update or create selected jobs in the path
- name: Generate jobs
  jenkins_job_generator:
    path: /tmp
    jobs:
      - build
      - test
    state: present
    user: jenkins
    password: jenkins

# Delete particular job
- name: delete jobs
  jenkins_job_generator:
    jobs:
      - test
    state: absent
    user: jenkins
    password: jenkins

# Disable particular job
- name: disable jobs
  jenkins_job_generator:
    jobs:
      - build
    state: disabled
'''

RETURN = '''
---
state:
  description: State of the jenkins jobs.
  returned: success
  type: string
  sample: "Disabled jenkins job(s): test"
'''

import xml.etree.ElementTree as ET

from ansible.module_utils.basic import AnsibleModule

# Import Jenkins builder
try:
    from jenkins import NotFoundException

    is_jenkins_lib = True
except ImportError:
    is_jenkins_lib = False

try:
    from jenkins_jobs.builder import JenkinsManager
    from jenkins_jobs.cli.entry import JenkinsJobs
    from jenkins_jobs.cli.subcommand.update import UpdateSubCommand
    from jenkins_jobs.parser import YamlParser
    from jenkins_jobs.registry import ModuleRegistry
    from jenkins_jobs.xml_config import XmlJobGenerator
    from jenkins_jobs.xml_config import XmlViewGenerator
    from jenkins_jobs.errors import JenkinsJobsException

    is_jenkins_builder_lib = True
except ImportError as e:
    is_jenkins_builder_lib = False


def test_dependencies(module):
    if not is_jenkins_lib:
        module.fail_json(msg="python-jenkins required for this module. "
                             "see http://python-jenkins.readthedocs.io/en/latest/install.html")

    if not is_jenkins_builder_lib:
        module.fail_json(msg="jenkins-job-builder required for this module. "
                             "see https://docs.openstack.org/infra/jenkins-job-builder/")


def get_job_builder():
    class JobBuilder(JenkinsManager):

        def changed(self, job):
            return self._is_job_changed(job=job)

        def xml_compare(self, x1, x2):
            """
            Compares two xml etrees
            :param x1: the first tree
            :param x2: the second tree
            :return:
                True if both files match
            """

            if x1.tag != x2.tag:
                return False
            for name, value in x1.attrib.items():
                if x2.attrib.get(name) != value:
                    return False
            for name in x2.attrib.keys():
                if name not in x1.attrib:
                    return False
            if not self.text_compare(x1.text, x2.text):
                return False
            if not self.text_compare(x1.tail, x2.tail):
                return False
            cl1 = x1.getchildren()
            cl2 = x2.getchildren()
            if len(cl1) != len(cl2):
                return False
            i = 0
            for c1, c2 in zip(cl1, cl2):
                i += 1
                if not self.xml_compare(c1, c2):
                    return False
            return True

        def is_job_enabled(self, job):
            return self.jenkins.get_job_info(job).get('buildable')

        def disable_job(self, job):
            self.jenkins.disable_job(job)

        def enable_job(self, job):
            self.jenkins.enable_job(job)

        @staticmethod
        def text_compare(t1, t2):
            """
            Compare two text strings
            :param t1: text one
            :param t2: text two
            :return:
                True if a match
            """
            if not t1 and not t2:
                return True
            if t1 == '*' or t2 == '*':
                return True
            return (t1 or '').strip() == (t2 or '').strip()

        def _is_job_changed(self, job):
            try:
                job_config = self.jenkins.get_job_config(job.name)
            except NotFoundException:
                return True
            current_job_config = job.output()

            xml1 = ET.fromstring(job_config)
            xml2 = ET.fromstring(current_job_config)

            return not self.xml_compare(xml1, xml2)

    return JobBuilder


def get_executor():
    class Executor(UpdateSubCommand):
        def _generate_xmljobs(self, options, jjb_config=None):
            job_builder = get_job_builder()
            builder = job_builder(jjb_config)

            # Generate XML
            parser = YamlParser(jjb_config)
            registry = ModuleRegistry(jjb_config, builder.plugins_list)
            xml_job_generator = XmlJobGenerator(registry)
            xml_view_generator = XmlViewGenerator(registry)

            parser.load_files(options.path)
            registry.set_parser_data(parser.data)

            job_data_list, view_data_list = parser.expandYaml(
                registry, options.names)

            xml_jobs = xml_job_generator.generateXML(job_data_list)
            xml_views = xml_view_generator.generateXML(view_data_list)

            return builder, xml_jobs, xml_views

        def execute(self, options, jjb_config):
            if options.n_workers < 0:
                raise JenkinsJobsException(
                    'Number of workers must be equal or greater than 0')

            builder, xml_jobs, xml_views = self._generate_xmljobs(
                options, jjb_config)

            if len(xml_jobs) == 0 and len(xml_views) == 0:
                raise Exception('No jobs or view found')

            jobs, num_updated_jobs = builder.update_jobs(
                xml_jobs, n_workers=options.n_workers)

            views, num_updated_views = builder.update_views(
                xml_views, n_workers=options.n_workers)

            keep_jobs = [job.name for job in xml_jobs]
            if options.delete_old:
                builder.delete_old_managed(keep=keep_jobs)

            return num_updated_jobs, num_updated_views

    return Executor()


class ActionRunner(object):
    def __init__(self, jenkins_server, user, password, result, **kwargs):
        self.result = result
        self.jenkins_server = jenkins_server
        self.user = user
        self.password = password
        self.options = [
            '--user', user,
            '--password', password,
            '-l debug'
        ]

    def present(self, delete_old, workers, path=None, file=None, jobs=None, **kwargs):
        executor = get_executor()

        action_options = [
            'update',
            '--workers', str(workers),
        ]

        if delete_old:
            action_options.insert(1, '--delete_old')

        if path is not None and jobs is not None:
            action_options.append(path)
            action_options.extend(jobs)
        elif path is not None and file is not None:
            action_options.append(path + '/' + file)
        elif path is not None:
            action_options.append(path)
        else:
            raise Exception('Incorrect options. File or path with job files should be provided')

        self.options.extend(action_options)

        jjb_configs = JenkinsJobs(self.options)
        jjb_configs.jjb_config.jenkins['url'] = self.jenkins_server

        num_updated_jobs, num_updated_views = \
            executor.execute(options=jjb_configs.options, jjb_config=jjb_configs.jjb_config)

        if num_updated_jobs == 0 & num_updated_views == 0:
            self.result['status'] = 'Nothing changed'
        else:
            self.result['changed'] = True
            self.result['status'] = 'Changed jobs: %s. Changed views: %s.' % (num_updated_jobs,
                                                                              num_updated_views)
        return self.result

    def absent(self, jobs, **kwargs):
        self.options.append('list')

        job_builder = self._get_job_builder()

        removed_jobs = []
        for job in jobs:
            is_job = job_builder.is_job(job, False)
            if is_job:
                job_builder.delete_job(job)
                removed_jobs.append(job)
        if removed_jobs:
            self.result['changed'] = True
            self.result['status'] = "Removed jenkins job(s): %s" % ", ".join(removed_jobs)
        else:
            self.result['status'] = "Nothing to delete"

        return self.result

    def enabled(self, jobs, **kwargs):
        self.options.append('list')

        job_builder = self._get_job_builder()

        enabled_jobs = []
        for job in jobs:
            is_enabled = job_builder.is_job_enabled(job)

            if not is_enabled:
                job_builder.enable_job(job)
                enabled_jobs.append(job)

        if enabled_jobs:
            self.result['changed'] = True
            self.result['status'] = "Enabled jenkins job(s): %s" % ", ".join(enabled_jobs)
        else:
            self.result['status'] = "Nothing to enable"

        return self.result

    def disabled(self, jobs, **kwargs):
        self.options.append('list')

        job_builder = self._get_job_builder()

        disabled_jobs = []
        for job in jobs:
            is_enabled = job_builder.is_job_enabled(job)

            if is_enabled:
                job_builder.disable_job(job)
                disabled_jobs.append(job)

        if disabled_jobs:
            self.result['changed'] = True
            self.result['status'] = "Disabled jenkins job(s): %s" % ", ".join(disabled_jobs)
        else:
            self.result['status'] = "Nothing to enable"

        return self.result

    def _get_job_builder(self):
        jjb_configs = JenkinsJobs(self.options)
        jjb_configs.jjb_config.jenkins['url'] = self.jenkins_server

        return get_job_builder()(jjb_configs.jjb_config)


def run_module():
    module_args = dict(
        jenkins_server=dict(type='str', required=False, default='http://127.0.0.1:8080'),
        user=dict(type='str', required=False, default=''),
        password=dict(type='str', required=False, default='', no_log=True),
        jobs=dict(type='list', required=False),
        path=dict(type='str', required=False),
        file=dict(type='str', required=False),
        workers=dict(type='int', required=False, default=1),
        delete_old=dict(type='bool', required=False, default=False),
        state=dict(choices=[
            'present',
            'absent',
            'enabled',
            'disabled'
        ],
            default='present'),
    )

    result = dict(
        changed=False,
        status=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    test_dependencies(module)

    try:
        action = ActionRunner(result=result, **module.params)

        result = action.__getattribute__(module.params['state'])(**module.params)

    except Exception as e:
        result['status'] = str(e)
        module.fail_json(**result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
