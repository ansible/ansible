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
DOCUMENTATION = '''
---
module: emr
short_description: Create, terminate and add steps to EMR clusters.
description:
    - Manipulate Elastic Map Reduce clusters. If jobflow_id is not provided a new cluster will be launched with the specified configuration. If jobflow_id is provided, jar_steps steps will be added to the current cluster. If state is 'absent' the cluster will be terminated.
version_added: "1.0"
options:
  region:
    description:
      - The region in which the EMR cluster will be created.
    required: true
  cluster_name:
    description:
      - The name of the EMR cluster.
    required: true
  log_uri:
    description:
      - URI of the S3 bucket to place logs.
    required: true
  vpc_subnet_id:
    description:
      - The VPC in which the EMR will be created.
    required: true
    default: null
  jobflow_role:
    description:
      - An IAM role for the job flow. The EC2 instances of the job flow assume this role.
    required: false
    default: null
  service_role:
    description:
      - The IAM role that will be assumed by the Amazon EMR service to access AWS resources on your behalf.
    required: false
    default: null
  ec2_keyname:
    description:
      - EC2 key used for the instances.
    required: true
  visible_to_all_users:
    description:
      - Whether the job flow is visible to all IAM users of the AWS account associated with the job flow. If this value is set to True, all IAM users of that AWS account can view and (if they have the proper policy permissions set) manage the job flow. If it is set to False, only the IAM user that created the job flow can view and manage it.
    required: false
    default: true
  ami_version:
    description:
      - Amazon Machine Image (AMI) version to use for instances.
    required: false
    default: latest
  enable_debugging:
    description:
      - Denotes whether AWS console debugging should be enabled.
    required: false
    default: false
  jobflow_id:
    description:
      - The job flow id of the current running cluster.
    required: false
    default: null
  bootstrap_actions:
    description:
      - List of bootstrap actions that run before Hadoop starts.
    required: false
    default: null
  instance_groups:
    description:
      - List of instance groups to use when creating this job..
    required: true
  jar_steps:
    description:
      - List of steps to add with the job.
    required: false
    default: null
  tags:
    description:
      - A dictionary containing the name/value pairs. If you want to create only a tag name, the value for that tag should be the empty string (e.g. '') or None.
    required: false
    default: null
  keep_alive:
    description:
      - Denotes whether the cluster should stay alive upon completion.
    required: false
    default: false
  termination_protection:
    description: Enables termination protection in the cluster,
    required: false
    default: false
  state:
    description:
      - If state is set to 'present' a new EMR cluster will be created. If it's set to 'absent' it will try to terminate the cluster with the provided jobflow_id.
    required: false
    default: 'present'
  force_termination:
    description:
      - If set and state is 'absent' will terminate the cluster even if the termination protection is enabled.
    required: false
    default: false
extends_documentation_fragment:
    - aws
'''

EXAMPLES = '''
---

# Parameters:
# (passed in using --extra-vars)
#
# region: <string>: one of us-east-1, us-west-2, us-west-1
# cluster_name: <string>: name of the EMR cluster to launch
# s3_bucket: <string>: ex. ml-chain
# s3_distro_root: <string>: ex. mg-stuff/rel-281
# core_node_count: <string>: ex. 1
# task_node_count: <string>: ex. 1
# ls_dist_tar: <string>: ex. learn-dist-4.63.1-dev-tidy-mlaws-SNAPSHOT.tbz2
# ls_config_tar: <string>: ex. learn-config-2.3.0-SNAPSHOT.tbz2
# keep_alive: <boolean>: to terminate after script(s) complete

- hosts: localhost
  vars:
    vpc_subnet_id: subnet-c9c906a8
    jobflow_role: s3-read-write
    ec2_key_name: "{{ lookup('env','AWS_KEY_NAME') }}"
    ec2_access_key: "{{ lookup('env','AWS_ACCESS_KEY') }}"
    ec2_secret_key: "{{ lookup('env','AWS_SECRET_KEY') }}"
    s3_distro_path: "s3://{{ s3_bucket }}/{{ s3_distro_root }}"
    master_node_type: m2.xlarge
    core_node_type: m1.xlarge
    task_node_type: m1.xlarge
    hive_version: 0.11.0.1
    hive_site_file: "{{ s3_distro_path }}/hive/hive-site.xml"
    mysql_connector_jar_version: 5.1.28
    oozie_version: 3.3.2
    bootstrap_actions_path: "s3://{{ region }}.elasticmapreduce/bootstrap-actions"
    bootstrap_scripts_dir: "{{ s3_distro_path }}/bootstrap-scripts"
    ls_config_tar_filename: {{ ls_config_tar | default('none-given-by-streaming') }}

  tasks:
    - name: create cluster
      local_action:
        module: emr
        region: "{{ region }}"
        cluster_name: "{{ cluster_name }}"
        log_uri: "{{ s3_distro_path }}/logs"
        vpc_subnet_id: "{{ vpc_subnet_id }}"
        jobflow_role: "{{ jobflow_role }}"
        ec2_keyname: "{{ ec2_key_name }}"
        visible_to_all_users: True

        # Any instance can accept
        #   spot: <boolean>
        #   bidprice: <price> # e.g. '0.08'

        instance_groups:
          - group_type: master
            instance_type: "{{ master_node_type }}"
          - group_type: core
            instance_type: "{{ core_node_type }}"
            count: "{{ core_node_count }}"
          - group_type: task
            instance_type: "{{ task_node_type }}"
            count: "{{ task_node_count }}"

        tags:
          - name: name
            value: "dxls"
          - name: environment
            value: "development"
          - name: subcomponent
            value: "dxml"
          - name: distribution_version
            value: "{{ ls_dist_tar }}"
          - name: configuration_version
            value: "{{ ls_config_tar_filename }}"

        jar_steps:
          - name: Setup Hive
            jar_uri: "s3://{{ region }}.elasticmapreduce/libs/script-runner/script-runner.jar"
            args: "s3://{{ region }}.elasticmapreduce/libs/hive/hive-script,--base-path,s3://us-east-1.elasticmapreduce/libs/hive/,--install-hive,--hive-versions,{{ hive_version }}"
            action_on_failure: "TERMINATE_JOB_FLOW"

          - name: Install Hive Site Configuration
            jar_uri: "s3://{{ region }}.elasticmapreduce/libs/script-runner/script-runner.jar"
            args: "s3://{{ region }}.elasticmapreduce/libs/hive/hive-script,--base-path,s3://us-east-1.elasticmapreduce/libs/hive/,--install-hive-site,--hive-site={{ s3_distro_path }}/hive/hive-site.xml,--hive-versions,{{ hive_version }}"
            action_on_failure: "TERMINATE_JOB_FLOW"

          - name: Setup Mysql JAR
            jar_uri: "s3://{{ region }}.elasticmapreduce/libs/script-runner/script-runner.jar"
            args: "{{ s3_distro_path }}/scripts/setup_mysql_jar.sh,{{ mysql_connector_jar_version }}"
            action_on_failure: "TERMINATE_JOB_FLOW"

          - name: Run Custom JAR
            jar_uri: "s3://bucket/path/to/custom.jar"
            main: "MainClass"
            args: "arg1,arg2"
            action_on_failure: "CONTINUE"

        # Add as many bootstrap actions as needed here.
        # args are separated by commas.
        bootstrap_actions:
          - name: set_memory_intensive
            action: '{{ bootstrap_actions_path }}/configurations/latest/memory-intensive'

          - name: add_swap
            action: '{{ bootstrap_actions_path }}/add-swap'
            args: '2048'

          - name: configure_hadoop
            action: '{{ bootstrap_actions_path }}/configure-hadoop'
            args: '-c,hadoop.proxyuser.oozie.hosts=*,-c,hadoop.proxyuser.oozie.groups=*,-c,hadoop.proxyuser.hadoop.hosts=*,-c,hadoop.proxyuser.hadoop.groups=*,-h,dfs.permissions=false,-c,fs.s3n.multipart.uploads.enabled=true,-c,fs.s3n.multipart.uploads.split.size=134217728,-s,mapred.tasktracker.map.tasks.maximum=8,-s,mapred.tasktracker.reduce.tasks.maximum=2,-s,mapred.min.split.size=134217728,-s,mapred.max.split.size=536870912,-m,mapred.job.reuse.jvm.num.tasks=-1'

          - name: sleep_if_master
            action: '{{ bootstrap_actions_path }}/run-if'
            args: 'instance.isMaster=true,sleep 60'

          - name: optimization_setup
            action: '{{ bootstrap_actions_path }}/run-if'
            args: 'instance.isMaster=true,{{ bootstrap_scripts_dir }}/setup_optimization.sh,{{ ls_config_tar_filename }},{{ ls_dist_tar }},{{ s3_distro_root }},{{ cluster_name }},{{ region }}'

          - name: configure_module_props
            action: '{{ bootstrap_actions_path }}/run-if'
            args: 'instance.isMaster=true,{{ bootstrap_scripts_dir }}/config_module_props.sh'

          - name: setup_oozie
            action: '{{ bootstrap_actions_path }}/run-if'
            args: 'instance.isMaster=true,{{ bootstrap_scripts_dir }}/setup_oozie.sh,{{ oozie_version }}'

          - name: setup_classpath
            action: '{{ bootstrap_scripts_dir }}/setup_classpath.sh'

          - name: setup_hadoop_heap
            action: '{{ bootstrap_scripts_dir }}/setup_hadoop_heap.sh'
'''

import sys
import time
from datetime import datetime

try:
    import boto.emr
    from boto.emr.connection import EmrConnection
    from boto.emr.instance_group import InstanceGroup
    from boto.emr.step import JarStep
    from boto.emr.step import InstallHiveStep
    from boto.emr.bootstrap_action import BootstrapAction
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

class ElasticMapReduceManager(object):
    """ Manages an elastic map reduce cluster. """

    def __init__(self, _module, _aws_access_key, _aws_secret_key, _region, **kwargs):

        self.module = _module
        self.aws_access_key = _aws_access_key
        self.aws_secret_key = _aws_secret_key
        self.region = _region

        if not self.region:
            self.module.fail_json(msg=str("Either region or EC2_REGION environment variable must be set."))

        self.ec2_keyname = kwargs.get('ec2_keyname')
        self.cluster_name = kwargs.get('cluster_name')
        self.jobflow_id = kwargs.get('jobflow_id')
        self.bootstrap_actions = kwargs.get('bootstrap_actions')
        self.log_uri = kwargs.get('log_uri')
        self.vpc_subnet_id = kwargs.get('vpc_subnet_id')
        self.ami_version = kwargs.get('ami_version')
        self.jobflow_role = kwargs.get('jobflow_role')
        self.service_role = kwargs.get('service_role')
        self.visible_to_all_users = kwargs.get('visible_to_all_users')
        self.instance_groups = kwargs.get('instance_groups')
        self.jar_steps = kwargs.get('jar_steps')
        self.tags = kwargs.get('tags')
        self.keep_alive = kwargs.get('keep_alive')
        self.enable_debugging = kwargs.get('enable_debugging')
        self.termination_protection = kwargs.get('termination_protection')
        self.changed = False
        self.data = None
        self.jobflow_instance_groups = []
        self.jobflow_bootstrap_actions = []
        self.jobflow_jar_steps = []
        self.cluster_tags = None
        self.should_terminate = kwargs.get('state') == 'absent'
        self.force_termination = kwargs.get('force_termination')

        self.conn = self.get_elasticmap_reduce_connection()

        if self.instance_groups:
            self.jobflow_instance_groups = self.set_jobflow_instance_groups()
        if self.bootstrap_actions:
            self.jobflow_bootstrap_actions = self.set_jobflow_bootstrap_actions()
        if self.jar_steps:
            self.jobflow_jar_steps = self.set_jobflow_jar_steps()
        if self.tags:
            self.cluster_tags = self.set_cluster_tags()

    def get_info(self):
        """ Return basic info about the EMR cluster. """

        info = {
            'region': self.region,
            'jobflow_id': self.jobflow_id,
        }

        return info

    def get_elasticmap_reduce_connection(self):
        """
        Connect to EMR on specific region.
        """

        try:
            conn = boto.emr.connect_to_region(self.region,
                                              aws_access_key_id=self.aws_access_key,
                                              aws_secret_access_key=self.aws_secret_key)
            return(conn)

        except boto.exception.NoAuthHandlerFound, e:
            self.module.fail_json(msg="Unable to create connection: {0}".format(str(e)))

    def set_jobflow_instance_groups(self):
        """
        :param module: AnsibleModule object
        :returns list: list of boto.emr.InstanceGroup objects
        """

        jobflow_instance_groups = []

        for ig in self.instance_groups:
            group_type = ig.get('group_type', None)
            instance_type = ig.get('instance_type', None)
            instance_count = ig.get('count', 1)
            my_spot = self.module.boolean(ig.get('spot'))
            my_bidprice = ig.get('bidprice', None)

            if int(instance_count) <= 0 or instance_type is None:
                continue

            if my_spot:
                my_market='SPOT'
                if not my_bidprice:
                    self.module.fail_json(msg='SPOT instances require a bidprice')
            else:
                my_market='ON_DEMAND'

            jobflow_instance_groups.append(InstanceGroup(int(instance_count),
                                                         group_type.upper(),
                                                         instance_type,
                                                         my_market,
                                                         "{0}_GROUP".format(group_type.upper()),
                                                         bidprice=my_bidprice))
        return(jobflow_instance_groups)

    def set_jobflow_bootstrap_actions(self):
        """
        :param module: AnsibleModule object
        :returns list: list of boto.emr.emrobject.BootstrapAction objects
        """

        my_bootstrap_actions = []
        for bootstrap in self.bootstrap_actions:
            args = []
            raw_args = bootstrap.get('args', None)
            if raw_args:
                args = [x.strip() for x in raw_args.split(',')]

            my_bootstrap_actions.append(BootstrapAction(bootstrap['name'],
                                                        bootstrap['action'],
                                                        args))
        return(my_bootstrap_actions)

    def set_jobflow_jar_steps(self):
        """
        :returns list: list of boto.emr.step.JarStep
        """

        my_jar_steps = []
        for jar_step in self.jar_steps:
            args = []
            raw_args = jar_step.get('args', None)
            if raw_args:
                args = [x.strip() for x in raw_args.split(',')]

            my_jar_steps.append(JarStep(jar_step['name'],
                                        jar_step['jar_uri'],
                                        jar_step['main'] if 'main' in jar_step else None,
                                        jar_step['action_on_failure'],
                                        args))
        return(my_jar_steps)

    def set_cluster_tags(self):
        """
        :returns map: a map of key/value pairs
        """

        tag_dict = {}

        for tag in self.tags:
            name = tag['name']
            value = tag['value']
            tag_dict[name] = value

        return tag_dict

    def run_jobflow(self):
        """
        :returns EMR object: The ID of the created job flow
        """

        if self.vpc_subnet_id:
            my_api_params = {'Instances.Ec2SubnetId': self.vpc_subnet_id}
        else:
            my_api_params = None

        self.jobflow_id = self.conn.run_jobflow(name=self.cluster_name,
                                                ec2_keyname=self.ec2_keyname,
                                                keep_alive=self.keep_alive,
                                                enable_debugging=self.enable_debugging,
                                                log_uri='{0}/{1}'.format(self.log_uri, datetime.now().strftime("%Y-%m-%d %H-%M-%S")),
                                                api_params=my_api_params,
                                                ami_version=self.ami_version,
                                                job_flow_role=self.jobflow_role,
                                                service_role=self.service_role,
                                                visible_to_all_users=self.visible_to_all_users,
                                                instance_groups=self.jobflow_instance_groups,
                                                bootstrap_actions=self.jobflow_bootstrap_actions,
                                                steps=self.jobflow_jar_steps)

        if self.cluster_tags:
            self.conn.add_tags(self.jobflow_id, self.cluster_tags)
        # add termination protection if necessary
        if self.termination_protection:
            self.conn.set_termination_protection(self.jobflow_id, self.termination_protection)

    def add_jobflow_steps(self):
        """
        Adds jobs provided in the playbook to an existing cluster/jobflow.

        :returns: nada
        """

        self.conn.add_jobflow_steps(self.jobflow_id, self.jobflow_jar_steps)

    def termiante_jobflow(self):
        """
        Terminates the jobflow.
        """
        if self.force_termination:
            self.conn.set_termination_protection(self.jobflow_id, False)
        self.conn.terminate_jobflow(self.jobflow_id)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            ec2_keyname={'default': None},
            cluster_name={},
            jobflow_id={'default': None},
            log_uri={},
            ec2_secret_key={'default': None, 'aliases': ['aws_secret_key', 'secret_key'], 'no_log': True},
            ec2_access_key={'default': None, 'aliases': ['aws_access_key', 'access_key']},
            region={'default': None, 'aliases': ['aws_region', 'ec2_region'], 'choices': AWS_REGIONS},
            bootstrap_actions={'type': 'list', 'default': None},
            jar_steps={'type': 'list', 'default': None},
            tags={'type': 'list', 'default': None},
            vpc_subnet_id={'default': None},
            ami_version={'default': 'latest'},
            jobflow_role={'default': None, 'aliases': ['iamrole']},
            service_role={'default': None, 'aliases': ['service_iamrole']},
            visible_to_all_users={'default': True, 'type': 'bool'},
            instance_groups={'type': 'list', 'default': None},
            enable_debugging={'default': False, 'type': 'bool'},
            keep_alive={'default': False, 'type': 'bool'},
            termination_protection={'default': False, 'type': 'bool'},
            force_termination={'default': False, 'type': 'bool'},
            state={'default': 'present'}
        )
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    _, aws_access_key, aws_secret_key, region = get_ec2_creds(module)
    emrm = ElasticMapReduceManager(module, aws_access_key, aws_secret_key, region, **module.params)
    if emrm.should_terminate:
        if emrm.jobflow_id:
            emrm.termiante_jobflow()
        else :
            module.fail_json(msg="No jobflow_id with state 'absent'. "
                                 "Please provide the jobflow_id that needs to be terminated.")
    elif not emrm.jobflow_id:
        if emrm.ec2_keyname:
            emrm.run_jobflow()
        else:
            module.fail_json(msg="No 'ec2_keyname' was provided.")
    else:
        emrm.add_jobflow_steps()

    facts_result = dict(changed=emrm.changed, elasticmapreduce=emrm.get_info())

    module.exit_json(**facts_result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
