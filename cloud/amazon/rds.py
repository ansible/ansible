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
short_description: create, delete, or modify an Amazon rds instance
description:
     - Creates, deletes, or modifies rds instances.  When creating an instance it can be either a new instance or a read-only replica of an existing instance. This module has a dependency on python-boto >= 2.5. The 'promote' command requires boto >= 2.18.0.
options:
  command:
    description:
      - Specifies the action to take.  
    required: true
    default: null
    aliases: []
    choices: [ 'create', 'replicate', 'delete', 'facts', 'modify' , 'promote', 'snapshot', 'restore' ]
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
    choices: [ 'MySQL', 'oracle-se1', 'oracle-se', 'oracle-ee', 'sqlserver-ee', 'sqlserver-se', 'sqlserver-ex', 'sqlserver-web', 'postgres']
  size:
    description:
      - Size in gigabytes of the initial storage for the DB instance. Used only when command=create or command=modify.
    required: false
    default: null
    aliases: []
  instance_type:
    description:
      - The instance type of the database.  Must be specified when command=create. Optional when command=replicate, command=modify or command=restore. If not specified then the replica inherits the same instance type as the source instance. 
    required: false
    default: null
    aliases: []
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
      - The license model for this DB instance. Used only when command=create or command=restore. 
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
      - Comma separated list of one or more security groups.  Used only when command=create or command=modify.
    required: false
    default: null
    aliases: []
  vpc_security_groups:
    description:
      - Comma separated list of one or more vpc security group ids. Also requires `subnet` to be specified. Used only when command=create or command=modify.
    required: false
    default: null
    aliases: []
  port:
    description:
      - Port number that the DB instance uses for connections.  Defaults to 3306 for mysql. Must be changed to 1521 for Oracle, 1443 for SQL Server, 5432 for PostgreSQL. Used only when command=create or command=replicate.
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
      - availability zone in which to launch the instance. Used only when command=create, command=replicate or command=restore.
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
      - Name of snapshot to take. When command=delete, if no snapshot name is provided then no snapshot is taken. Used only when command=delete or command=snapshot.
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
      - When command=create, replicate, modify or restore then wait for the database to enter the 'available' state.  When command=delete wait for the database to be terminated.
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
  new_instance_name:
    description:
      - Name to rename an instance to. Used only when command=modify.
    required: false
    default: null
    aliases: []
    version_added: 1.5
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

# Rename an instance and wait for the change to take effect
- rds: >
      command=modify
      instance_name=new_database
      new_instance_name=renamed_database
      wait=yes
    
'''

import sys
import time

try:
    import boto.rds
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

def get_current_resource(conn, resource, command):
    # There will be exceptions but we want the calling code to handle them
    if command == 'snapshot':
        return conn.get_all_dbsnapshots(snapshot_id=resource)[0]
    else:
        return conn.get_all_dbinstances(resource)[0]


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            command           = dict(choices=['create', 'replicate', 'delete', 'facts', 'modify', 'promote', 'snapshot', 'restore'], required=True),
            instance_name     = dict(required=True),
            source_instance   = dict(required=False),
            db_engine         = dict(choices=['MySQL', 'oracle-se1', 'oracle-se', 'oracle-ee', 'sqlserver-ee', 'sqlserver-se', 'sqlserver-ex', 'sqlserver-web', 'postgres'], required=False),
            size              = dict(required=False), 
            instance_type     = dict(aliases=['type'], required=False),
            username          = dict(required=False),
            password          = dict(no_log=True, required=False),
            db_name           = dict(required=False),
            engine_version    = dict(required=False),
            parameter_group   = dict(required=False),
            license_model     = dict(choices=['license-included', 'bring-your-own-license', 'general-public-license'], required=False),
            multi_zone        = dict(type='bool', default=False),
            iops              = dict(required=False), 
            security_groups   = dict(required=False),
            vpc_security_groups = dict(type='list', required=False),
            port              = dict(required=False),
            upgrade           = dict(type='bool', default=False),
            option_group      = dict(required=False),
            maint_window      = dict(required=False),
            backup_window     = dict(required=False),
            backup_retention  = dict(required=False), 
            zone              = dict(aliases=['aws_zone', 'ec2_zone'], required=False),
            subnet            = dict(required=False),
            wait              = dict(type='bool', default=False),
            wait_timeout      = dict(default=300),
            snapshot          = dict(required=False),
            apply_immediately = dict(type='bool', default=False),
            new_instance_name = dict(required=False),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
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
    vpc_security_groups = module.params.get('vpc_security_groups')
    port               = module.params.get('port')
    upgrade            = module.params.get('upgrade')
    option_group       = module.params.get('option_group')
    maint_window       = module.params.get('maint_window')
    subnet             = module.params.get('subnet')
    backup_window      = module.params.get('backup_window')
    backup_retention   = module.params.get('backup_retention')
    region             = module.params.get('region')
    zone               = module.params.get('zone')
    aws_secret_key     = module.params.get('aws_secret_key')
    aws_access_key     = module.params.get('aws_access_key')
    wait               = module.params.get('wait')
    wait_timeout       = int(module.params.get('wait_timeout'))
    snapshot           = module.params.get('snapshot')
    apply_immediately  = module.params.get('apply_immediately')
    new_instance_name  = module.params.get('new_instance_name')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg = str("region not specified and unable to determine region from EC2_REGION."))

    # connect to the rds endpoint
    try:
        conn = connect_to_aws(boto.rds, region, **aws_connect_params)
    except boto.exception.BotoServerError, e:
        module.fail_json(msg = e.error_message)

    def invalid_security_group_type(subnet):
        if subnet:
            return 'security_groups'
        else:
            return 'vpc_security_groups'

    # Package up the optional parameters
    params = {}

    # Validate parameters for each command
    if command == 'create':
        required_vars = [ 'instance_name', 'db_engine', 'size', 'instance_type', 'username', 'password' ]
        invalid_vars  = [ 'source_instance', 'snapshot', 'apply_immediately', 'new_instance_name' ] + [invalid_security_group_type(subnet)]

    elif command == 'replicate':
        required_vars = [ 'instance_name', 'source_instance' ]
        invalid_vars  = [ 'db_engine', 'size', 'username', 'password', 'db_name', 'engine_version', 'parameter_group', 'license_model', 'multi_zone', 'iops', 'vpc_security_groups', 'security_groups', 'option_group', 'maint_window', 'backup_window', 'backup_retention', 'subnet', 'snapshot', 'apply_immediately', 'new_instance_name' ]

    elif command == 'delete':
        required_vars = [ 'instance_name' ]
        invalid_vars  = [ 'db_engine', 'size', 'instance_type', 'username', 'password', 'db_name', 'engine_version', 'parameter_group', 'license_model', 'multi_zone', 'iops', 'vpc_security_groups' ,'security_groups', 'option_group', 'maint_window', 'backup_window', 'backup_retention', 'port', 'upgrade', 'subnet', 'zone' , 'source_instance', 'apply_immediately', 'new_instance_name' ]

    elif command == 'facts':
        required_vars = [ 'instance_name' ]
        invalid_vars  = [ 'db_engine', 'size', 'instance_type', 'username', 'password', 'db_name', 'engine_version', 'parameter_group', 'license_model', 'multi_zone', 'iops', 'vpc_security_groups', 'security_groups', 'option_group', 'maint_window', 'backup_window', 'backup_retention', 'port', 'upgrade', 'subnet', 'zone', 'wait', 'source_instance' 'apply_immediately', 'new_instance_name' ]

    elif command == 'modify':
        required_vars = [ 'instance_name' ]
        if password:
            params["master_password"] = password
        invalid_vars = [ 'db_engine', 'username', 'db_name', 'engine_version',  'license_model', 'option_group', 'port', 'upgrade', 'subnet', 'zone', 'source_instance']

    elif command == 'promote':
        required_vars = [ 'instance_name' ]
        invalid_vars = [ 'db_engine', 'size', 'username', 'password', 'db_name', 'engine_version', 'parameter_group', 'license_model', 'multi_zone', 'iops', 'vpc_security_groups', 'security_groups', 'option_group', 'maint_window', 'subnet', 'source_instance', 'snapshot', 'apply_immediately', 'new_instance_name' ]
    
    elif command == 'snapshot':
        required_vars = [ 'instance_name', 'snapshot']
        invalid_vars = [ 'db_engine', 'size', 'username', 'password', 'db_name', 'engine_version', 'parameter_group', 'license_model', 'multi_zone', 'iops', 'vpc_security_groups', 'security_groups', 'option_group', 'maint_window', 'subnet', 'source_instance', 'apply_immediately', 'new_instance_name' ]

    elif command == 'restore':
        required_vars = [ 'instance_name', 'snapshot', 'instance_type' ]
        invalid_vars = [ 'db_engine', 'db_name', 'username', 'password', 'engine_version',  'option_group', 'source_instance', 'apply_immediately', 'new_instance_name', 'vpc_security_groups', 'security_groups' ]
 
    for v in required_vars:
        if not module.params.get(v):
            module.fail_json(msg = str("Parameter %s required for %s command" % (v, command)))
            
    for v in invalid_vars:
        if module.params.get(v):
            module.fail_json(msg = str("Parameter %s invalid for %s command" % (v, command)))

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
        params["security_groups"] = security_groups.split(',')

    if vpc_security_groups:
        groups_list = []
        for x in vpc_security_groups:
            groups_list.append(boto.rds.VPCSecurityGroupMembership(vpc_group=x))
        params["vpc_security_groups"] = groups_list

    if new_instance_name:
        params["new_instance_id"] = new_instance_name

    changed = True

    if command in ['create', 'restore', 'facts']:
        try:
            result = conn.get_all_dbinstances(instance_name)[0]
            changed = False
        except boto.exception.BotoServerError, e:
            try:
                if command == 'create': 
                    result = conn.create_dbinstance(instance_name, size, instance_type, username, password, **params)
                if command == 'restore':
                    result = conn.restore_dbinstance_from_dbsnapshot(snapshot, instance_name, instance_type, **params)
                if command == 'facts':
                    module.fail_json(msg = "DB Instance %s does not exist" % instance_name)
            except boto.exception.BotoServerError, e:
                module.fail_json(msg = e.error_message)

    if command == 'snapshot':
        try:
            result = conn.get_all_dbsnapshots(snapshot)[0]
            changed = False
        except boto.exception.BotoServerError, e:
            try:
                result = conn.create_dbsnapshot(snapshot, instance_name)
            except boto.exception.BotoServerError, e:
                module.fail_json(msg = e.error_message)
        
    if command == 'delete':
        try:
            result = conn.get_all_dbinstances(instance_name)[0]
            if result.status == 'deleting':
                module.exit_json(changed=False)
        except boto.exception.BotoServerError, e:
            module.exit_json(changed=False)
        try:
            if snapshot:
                params["skip_final_snapshot"] = False
                params["final_snapshot_id"] = snapshot
            else:
                params["skip_final_snapshot"] = True
            result = conn.delete_dbinstance(instance_name, **params)
        except boto.exception.BotoServerError, e:
            module.fail_json(msg = e.error_message)

    if command == 'replicate':
        try: 
            if instance_type:
                params["instance_class"] = instance_type
            result = conn.create_dbinstance_read_replica(instance_name, source_instance, **params)
        except boto.exception.BotoServerError, e:
            module.fail_json(msg = e.error_message)

    if command == 'modify':
        try:
            params["apply_immediately"] = apply_immediately
            result = conn.modify_dbinstance(instance_name, **params)
        except boto.exception.BotoServerError, e:
            module.fail_json(msg = e.error_message)
        if apply_immediately:
            if new_instance_name:
                # Wait until the new instance name is valid
                found = 0
                while found == 0:
                    instances = conn.get_all_dbinstances()
                    for i in instances:
                        if i.id == new_instance_name:
                            instance_name = new_instance_name
                            found = 1
                    if found == 0:
                        time.sleep(5)

                # The name of the database has now changed, so we have
                # to force result to contain the new instance, otherwise
                # the call below to get_current_resource will fail since it
                # will be looking for the old instance name.
                result.id = new_instance_name
            else:
                # Wait for a few seconds since it takes a while for AWS
                # to change the instance from 'available' to 'modifying'
                time.sleep(5)

    if command == 'promote':
        try:
            result = conn.promote_read_replica(instance_name, **params)
        except boto.exception.BotoServerError, e:
            module.fail_json(msg = e.error_message)

    # If we're not waiting for a delete to complete then we're all done
    # so just return
    if command == 'delete' and not wait:
        module.exit_json(changed=True)

    try:
       resource = get_current_resource(conn, result.id, command)
    except boto.exception.BotoServerError, e:
        module.fail_json(msg = e.error_message)

    # Wait for the resource to be available if requested
    if wait:
        try: 
            wait_timeout = time.time() + wait_timeout
            time.sleep(5)

            while wait_timeout > time.time() and resource.status != 'available':
                time.sleep(5)
                if wait_timeout <= time.time():
                    module.fail_json(msg = "Timeout waiting for resource %s" % resource.id)
                resource = get_current_resource(conn, result.id, command)
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
    if command == 'snapshot':
        d = { 
            'id'                 : resource.id,
            'create_time'        : resource.snapshot_create_time,
            'status'             : resource.status,
            'availability_zone'  : resource.availability_zone,
            'instance_id'        : resource.instance_id,
            'instance_created'   : resource.instance_create_time,
        }
        try:
            d["snapshot_type"] = resource.snapshot_type
            d["iops"] = resource.iops
        except AttributeError, e:
            pass # needs boto >= 2.21.0

        return module.exit_json(changed=changed, snapshot=d)

    d = {
        'id'                 : resource.id,
        'create_time'        : resource.create_time,
        'status'             : resource.status,
        'availability_zone'  : resource.availability_zone,
        'backup_retention'   : resource.backup_retention_period,
        'backup_window'      : resource.preferred_backup_window,
        'maintenance_window' : resource.preferred_maintenance_window,
        'multi_zone'         : resource.multi_az,
        'instance_type'      : resource.instance_class,
        'username'           : resource.master_username,
        'iops'               : resource.iops
        }

    # Endpoint exists only if the instance is available
    if resource.status == 'available' and command != 'snapshot':
        d["endpoint"] = resource.endpoint[0]
        d["port"] = resource.endpoint[1]
        if resource.vpc_security_groups is not None:
            d["vpc_security_groups"] = ','.join(x.vpc_group for x in resource.vpc_security_groups)
        else:
            d["vpc_security_groups"] = None
    else:
        d["endpoint"] = None
        d["port"] = None
        d["vpc_security_groups"] = None

    # ReadReplicaSourceDBInstanceIdentifier may or may not exist
    try:
        d["replication_source"] = resource.ReadReplicaSourceDBInstanceIdentifier
    except Exception, e:
        d["replication_source"] = None

    module.exit_json(changed=changed, instance=d)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
