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
module: rds
version_added: "1.3"
short_description: create or delete an Amazon rds instance
description:
     - Creates or deletes rds instances.  When creating an instance it can be either a new instance or a read-only replica of an existing instance. This module has a dependency on python-boto >= 2.5.
options:
  command:
    description:
      - Specifies the action to take.  
    required: true
    default: null
    aliases: []
    choices: [ 'create', 'replicate', 'delete', 'facts', 'modify' ]
  instance_name:
    description:
      - Database instance identifier.
    required: true
    default: null
    aliases: []
  source_instance:
    description:
      - Name of the database to replicate. Used only when command=replicate.
    required: false
    default: null
    aliases: []
  db_engine:
    description:
      - The type of database.  Used only when command=create. 
    required: false
    default: null
    aliases: []
    choices: [ 'MySQL', 'oracle-se1', 'oracle-se', 'oracle-ee', 'sqlserver-ee', 'sqlserver-se', 'sqlserver-ex', 'sqlserver-web' ]
  size:
    description:
      - Size in gigabytes of the initial storage for the DB instance. Used only when command=create or command=modify.
    required: false
    default: null
    aliases: []
  instance_type:
    description:
      - The instance type of the database.  Must be specified when command=create. Optional when command=replicate or command=modify. If not specified then the replica inherits the same instance type as the source instance. 
    required: false
    default: null
    aliases: []
    choices: [ 'db.t1.micro', 'db.m1.small', 'db.m1.medium', 'db.m1.large', 'db.m1.xlarge', 'db.m2.xlarge', 'db.m2.2xlarge', 'db.m2.4xlarge' ]
  username:
    description:
      - Master database username. Used only when command=create.
    required: false
    default: null
    aliases: []
  password:
    description:
      - Password for the master database username. Used only when command=create or command=modify.
    required: false
    default: null
    aliases: []
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: true
    default: null
    aliases: [ 'aws_region', 'ec2_region' ]
  db_name:
    description:
      - Name of a database to create within the instance.  If not specified then no database is created. Used only when command=create.
    required: false
    default: null
    aliases: []
  engine_version:
    description:
      - Version number of the database engine to use. Used only when command=create. If not specified then the current Amazon RDS default engine version is used.
    required: false
    default: null
    aliases: []
  parameter_group:
    description:
      - Name of the DB parameter group to associate with this instance.  If omitted then the RDS default DBParameterGroup will be used. Used only when command=create or command=modify.
    required: false
    default: null
    aliases: []
  license_model:
    description:
      - The license model for this DB instance. Used only when command=create. 
    required: false
    default: null
    aliases: []
    choices:  [ 'license-included', 'bring-your-own-license', 'general-public-license' ]
  multi_zone:
    description:
      - Specifies if this is a Multi-availability-zone deployment. Can not be used in conjunction with zone parameter. Used only when command=create or command=modify.
    choices: [ "yes", "no" ] 
    required: false
    default: null
    aliases: []
  iops:
    description:
      - Specifies the number of IOPS for the instance.  Used only when command=create or command=modify. Must be an integer greater than 1000.
    required: false
    default: null
    aliases: []
  security_groups:
    description:
      - Comma separated list of one or more security groups.  Used only when command=create or command=modify. If a subnet is specified then this is treated as a list of VPC security groups.
    required: false
    default: null
    aliases: []
  port:
    description:
      - Port number that the DB instance uses for connections.  Defaults to 3306 for mysql, 1521 for Oracle, 1443 for SQL Server. Used only when command=create or command=replicate.
    required: false
    default: null
    aliases: []
  upgrade:
    description:
      - Indicates that minor version upgrades should be applied automatically. Used only when command=create or command=replicate. 
    required: false
    default: no
    choices: [ "yes", "no" ]
    aliases: []
  option_group:
    description:
      - The name of the option group to use.  If not specified then the default option group is used. Used only when command=create.
    required: false
    default: null
    aliases: []
  maint_window:
    description:
      - "Maintenance window in format of ddd:hh24:mi-ddd:hh24:mi.  (Example: Mon:22:00-Mon:23:15) If not specified then a random maintenance window is assigned. Used only when command=create or command=modify."
    required: false
    default: null
    aliases: []
  backup_window:
    description:
      - Backup window in format of hh24:mi-hh24:mi.  If not specified then a random backup window is assigned. Used only when command=create or command=modify.
    required: false
    default: null
    aliases: []
  backup_retention:
    description:
      - "Number of days backups are retained.  Set to 0 to disable backups.  Default is 1 day.  Valid range: 0-35. Used only when command=create or command=modify."
    required: false
    default: null
    aliases: []
  zone:
    description:
      - availability zone in which to launch the instance. Used only when command=create or command=replicate.
    required: false
    default: null
    aliases: ['aws_zone', 'ec2_zone']
  subnet:
    description:
      - VPC subnet group.  If specified then a VPC instance is created. Used only when command=create.
    required: false
    default: null
    aliases: []
  snapshot:
    description:
      - Name of final snapshot to take when deleting an instance.  If no snapshot name is provided then no snapshot is taken. Used only when command=delete.
    required: false
    default: null
    aliases: []
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY environment variable is used. 
    required: false
    default: null
    aliases: [ 'ec2_secret_key', 'secret_key' ]
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY environment variable is used.
    required: false
    default: null
    aliases: [ 'ec2_access_key', 'access_key' ]
  wait:
    description:
      - When command=create, replicate, or modify then wait for the database to enter the 'available' state.  When command=delete wait for the database to be terminated.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    aliases: []
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
    aliases: []
  apply_immediately:
    description:
      - Used only when command=modify.  If enabled, the modifications will be applied as soon as possible rather than waiting for the next preferred maintenance window.
    default: no
    choices: [ "yes", "no" ]
    aliases: []
requirements: [ "boto" ]
author: Bruce Pennypacker
'''

EXAMPLES = '''
# Basic mysql provisioning example
- rds: >
      command=create
      instance_name=new_database
      db_engine=MySQL
      size=10
      instance_type=db.m1.small
      username=mysql_admin
      password=1nsecure

# Create a read-only replica and wait for it to become available
- rds: >
      command=replicate
      instance_name=new_database_replica
      source_instance=new_database
      wait=yes
      wait_timeout=600

# Delete an instance, but create a snapshot before doing so
- rds: >
      command=delete
      instance_name=new_database
      snapshot=new_database_snapshot

# Get facts about an instance
- rds: >
      command=facts
      instance_name=new_database
      register: new_database_facts
    
'''

import sys
import time

AWS_REGIONS = ['ap-northeast-1',
               'ap-southeast-1',
               'ap-southeast-2',
               'eu-west-1',
               'sa-east-1',
               'us-east-1',
               'us-west-1',
               'us-west-2']

try:
    import boto.rds
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            command           = dict(choices=['create', 'replicate', 'delete', 'facts', 'modify'], required=True),
            instance_name     = dict(required=True),
            source_instance   = dict(required=False),
            db_engine         = dict(choices=['MySQL', 'oracle-se1', 'oracle-se', 'oracle-ee', 'sqlserver-ee', 'sqlserver-se', 'sqlserver-ex', 'sqlserver-web'], required=False),
            size              = dict(required=False), 
            instance_type     = dict(aliases=['type'], choices=['db.t1.micro', 'db.m1.small', 'db.m1.medium', 'db.m1.large', 'db.m1.xlarge', 'db.m2.xlarge', 'db.m2.2xlarge', 'db.m2.4xlarge'], required=False),
            username          = dict(required=False),
            password          = dict(no_log=True, required=False),
            db_name           = dict(required=False),
            engine_version    = dict(required=False),
            parameter_group   = dict(required=False),
            license_model     = dict(choices=['license-included', 'bring-your-own-license', 'general-public-license'], required=False),
            multi_zone        = dict(type='bool', default=False),
            iops              = dict(required=False), 
            security_groups   = dict(required=False),
            port              = dict(required=False),
            upgrade           = dict(type='bool', default=False),
            option_group      = dict(required=False),
            maint_window      = dict(required=False),
            backup_window     = dict(required=False),
            backup_retention  = dict(required=False), 
            region            = dict(aliases=['aws_region', 'ec2_region'], choices=AWS_REGIONS, required=False),
            zone              = dict(aliases=['aws_zone', 'ec2_zone'], required=False),
            subnet            = dict(required=False),
            aws_secret_key    = dict(aliases=['ec2_secret_key', 'secret_key'], no_log=True, required=False),
            aws_access_key    = dict(aliases=['ec2_access_key', 'access_key'], required=False),
            wait              = dict(type='bool', default=False),
            wait_timeout      = dict(default=300),
            snapshot          = dict(required=False),
            apply_immediately = dict(type='bool', default=False),
        )
    )

    command            = module.params.get('command')
    instance_name      = module.params.get('instance_name')
    source_instance    = module.params.get('source_instance')
    db_engine          = module.params.get('db_engine')
    size               = module.params.get('size')
    instance_type      = module.params.get('instance_type')
    username           = module.params.get('username')
    password           = module.params.get('password')
    db_name            = module.params.get('db_name')
    engine_version     = module.params.get('engine_version')
    parameter_group    = module.params.get('parameter_group')
    license_model      = module.params.get('license_model')
    multi_zone         = module.params.get('multi_zone')
    iops               = module.params.get('iops')
    security_groups    = module.params.get('security_groups')
    port               = module.params.get('port')
    upgrade            = module.params.get('upgrade')
    option_group       = module.params.get('option_group')
    maint_window       = module.params.get('maint_window')
    subnet             = module.params.get('subnet')
    backup_window      = module.params.get('backup_window')
    backup_retention   = module.params.get('module_retention')
    region             = module.params.get('region')
    zone               = module.params.get('zone')
    aws_secret_key     = module.params.get('aws_secret_key')
    aws_access_key     = module.params.get('aws_access_key')
    wait               = module.params.get('wait')
    wait_timeout       = int(module.params.get('wait_timeout'))
    snapshot           = module.params.get('snapshot')
    apply_immediately  = module.params.get('apply_immediately')

    # allow environment variables to be used if ansible vars aren't set
    if not region:
        if   'AWS_REGION' in os.environ:
            region = os.environ['AWS_REGION']
        elif   'EC2_REGION' in os.environ:
            region = os.environ['EC2_REGION']

    if not aws_secret_key:
        if  'AWS_SECRET_KEY' in os.environ:
            aws_secret_key = os.environ['AWS_SECRET_KEY']
        elif 'EC2_SECRET_KEY' in os.environ:
            aws_secret_key = os.environ['EC2_SECRET_KEY']

    if not aws_access_key:
        if 'AWS_ACCESS_KEY' in os.environ:
            aws_access_key = os.environ['AWS_ACCESS_KEY']
        elif 'EC2_ACCESS_KEY' in os.environ:
            aws_access_key = os.environ['EC2_ACCESS_KEY']

    if not region:
        module.fail_json(msg = str("region not specified and unable to determine region from EC2_REGION."))

    # connect to the rds endpoint
    try:
        conn = boto.rds.connect_to_region(region, aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    except boto.exception.BotoServerError, e:
        module.fail_json(msg = e.error_message)

    # Validate parameters for each command
    if command == 'create':
        required_vars = [ 'instance_name', 'db_engine', 'size', 'instance_type', 'username', 'password' ]
        invalid_vars  = [ 'source_instance', 'snapshot', 'apply_immediately' ]

    elif command == 'replicate':
        required_vars = [ 'instance_name', 'source_instance' ]
        invalid_vars  = [ 'db_engine', 'size', 'username', 'password', 'db_name', 'engine_version', 'parameter_group', 'license_model', 'multi_zone', 'iops', 'security_groups', 'option_group', 'maint_window', 'backup_window', 'backup_retention', 'subnet', 'snapshot', 'apply_immediately' ]

    elif command == 'delete':
        required_vars = [ 'instance_name' ]
        invalid_vars  = [ 'db_engine', 'size', 'instance_type', 'username', 'password', 'db_name', 'engine_version', 'parameter_group', 'license_model', 'multi_zone', 'iops', 'security_groups', 'option_group', 'maint_window', 'backup_window', 'backup_retention', 'port', 'upgrade', 'subnet', 'zone' , 'source_instance', 'apply_immediately' ]

    elif command == 'facts':
        required_vars = [ 'instance_name' ]
        invalid_vars  = [ 'db_engine', 'size', 'instance_type', 'username', 'password', 'db_name', 'engine_version', 'parameter_group', 'license_model', 'multi_zone', 'iops', 'security_groups', 'option_group', 'maint_window', 'backup_window', 'backup_retention', 'port', 'upgrade', 'subnet', 'zone', 'wait', 'source_instance' 'apply_immediately' ]

    elif command == 'modify':
        required_vars = [ 'instance_name' ]
        if password:
            params["master_password"] = password
        invalid_vars = [ 'db_engine', 'username', 'db_name', 'engine_version',  'license_model', 'option_group', 'port', 'upgrade', 'subnet', 'zone', 'source_instance' ]
 
    for v in required_vars:
        if not module.params.get(v):
            module.fail_json(msg = str("Parameter %s required for %s command" % (v, command)))
            
    for v in invalid_vars:
        if module.params.get(v):
            module.fail_json(msg = str("Parameter %s invalid for %s command" % (v, command)))

    # Package up the optional parameters
    params = {}

    if db_engine:
        params["engine"] = db_engine

    if port:
        params["port"] = port

    if db_name:
        params["db_name"] = db_name

    if parameter_group:
        params["param_group"] = parameter_group

    if zone:
        params["availability_zone"] = zone
  
    if maint_window:
        params["preferred_maintenance_window"] = maint_window

    if backup_window:
        params["preferred_backup_window"] = backup_window

    if backup_retention:
        params["backup_retention_period"] = backup_retention

    if multi_zone:
        params["multi_az"] = multi_zone

    if engine_version:
        params["engine_version"] = engine_version

    if upgrade:
        params["auto_minor_version_upgrade"] = upgrade

    if subnet:
        params["db_subnet_group_name"] = subnet

    if license_model:
        params["license_model"] = license_model

    if option_group:
        params["option_group_name"] = option_group

    if iops:
        params["iops"] = iops

    if security_groups:
        if subnet:
            params["vpc_security_groups"] = security_groups.split(',')
        else:
            params["security_groups"] = security_groups.split(',')

    try: 
        if command == 'create':
            db = conn.create_dbinstance(instance_name, size, instance_type, username, password, **params)
        elif command == 'replicate':
            if instance_type:
                params["instance_class"] = instance_type
            db = conn.create_dbinstance_read_replica(instance_name, source_instance, **params)
        elif command == 'delete':
            if snapshot:
                params["skip_final_snapshot"] = False
                params["final_snapshot_id"] = snapshot
            else:
                params["skip_final_snapshot"] = True

            db = conn.delete_dbinstance(instance_name, **params)
        elif command == 'modify':
            params["apply_immediately"] = apply_immediately
            db = conn.modify_dbinstance(instance_name, **params)

    # Don't do anything for the 'facts' command since we'll just drop down
    # to get_all_dbinstances below to collect the facts

    except boto.exception.BotoServerError, e:
        module.fail_json(msg = e.error_message)

    # If we're not waiting for a delete to complete then we're all done
    # so just return
    if command == 'delete' and not wait:
        module.exit_json(changed=True)

    try: 
        instances = conn.get_all_dbinstances(instance_name)
        my_inst = instances[0]
    except boto.exception.BotoServerError, e:
        module.fail_json(msg = e.error_message)


    # Wait for the instance to be available if requested
    if wait:
        try: 
            wait_timeout = time.time() + wait_timeout
            time.sleep(5)

            while wait_timeout > time.time() and my_inst.status != 'available':
                time.sleep(5)
                if wait_timeout <= time.time():
                    module.fail_json(msg = "Timeout waiting for database instance %s" % instance_name)
                instances = conn.get_all_dbinstances(instance_name)
                my_inst = instances[0]
        except boto.exception.BotoServerError, e:
            # If we're waiting for an instance to be deleted then
            # get_all_dbinstances will eventually throw a 
            # DBInstanceNotFound error.
            if command == 'delete' and e.error_code == 'DBInstanceNotFound':
                module.exit_json(changed=True)                
            else:
                module.fail_json(msg = e.error_message)

    # If we got here then pack up all the instance details to send
    # back to ansible
    d = {
        'id'                 : my_inst.id,
        'create_time'        : my_inst.create_time,
        'status'             : my_inst.status,
        'availability_zone'  : my_inst.availability_zone,
        'backup_retention'   : my_inst.backup_retention_period,
        'backup_window'      : my_inst.preferred_backup_window,
        'maintenance_window' : my_inst.preferred_maintenance_window,
        'multi_zone'         : my_inst.multi_az,
        'instance_type'      : my_inst.instance_class,
        'username'           : my_inst.master_username,
        'iops'               : my_inst.iops
        }

    # Endpoint exists only if the instance is available
    if my_inst.status == 'available':
        d["endpoint"] = my_inst.endpoint[0]
        d["port"] = my_inst.endpoint[1]
    else:
        d["endpoint"] = None
        d["port"] = None

    # ReadReplicaSourceDBInstanceIdentifier may or may not exist
    try:
        d["replication_source"] = my_inst.ReadReplicaSourceDBInstanceIdentifier
    except Exception, e:
        d["replication_source"] = None

    module.exit_json(changed=True, instance=d)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()
