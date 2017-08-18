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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
# from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: rds_instance
short_description: create, delete, or modify an Amaz`on rds instance
description:
     - Creates, deletes, or modifies rds instances. When creating an instance
       it can be either a new instance or a read-only replica of an exising instance.
     - RDS modifications are mostly done asyncronously so it is very likely that if you
       don't give the correct parameters then the modifications you request will not be
       done until long after the module is run (e.g. at the next maintainance window).  If
       you want to have an immediate change and see the results then you should give both
       the 'wait' and the 'apply_immediately' parameters.  In this case, when the module
       returns
     - The behavior in the case where only one of apply_immediately is given is complex
       and subject to change.  It should reflect the status after renaming is applied but
       the instance state is likely to continue to change.  Please do not rely on the
       return value to match the status soon afterwards.
     - In the case that apply_immediately is not given then the return value from
requirements:
    - "python >= 2.6"
    - "boto3"
version_added: "2.4"
author:
    - Bruce Pennypacker (@bpennypacker)
    - Will Thames (@willthames)
    - Michael De La Rue (@mikedlr)
options:
  state:
    description:
      - Describes the desired state of the database instance. N.B. restarted is allowed as an alias for rebooted.
    required: false
    default: present
    choices: [ 'present', 'absent', 'rebooted' ]
  db_instance_identifier:
    description:
      - Database instance identifier.
    required: true
  source_instance:
    description:
      - Name of the database when sourcing from a replica
    required: false
  replica:
    description:
    - whether or not a database is a read replica
    default: False
  db_engine:
    description:
      - The type of database. Used only when state=present.
    required: false
    choices: [ 'mariadb', 'MySQL', 'oracle-se1', 'oracle-se2', 'oracle-se', 'oracle-ee', 'sqlserver-ee',
                sqlserver-se', 'sqlserver-ex', 'sqlserver-web', 'postgres', 'aurora']
  size:
    description:
      - Size in gigabytes of the initial storage for the DB instance.
    required: false
  storage_type:
    description:
      - Specifies the storage type to be associated with the DB instance. C(iops) must
        be specified if C(io1) is chosen.
    choices: ['standard', 'gp2', 'io1' ]
    default: standard unless iops is set
  instance_type:
    description:
      - The instance type of the database. If source_instance is specified then the replica inherits
        the same instance type as the source instance.
  username:
    description:
      - Master database username.
  password:
    description:
      - Password for the master database username.
  db_name:
    description:
      - Name of a database to create within the instance. If not specified then no database is created.
  engine_version:
    description:
      - Version number of the database engine to use. If not specified then
      - the current Amazon RDS default engine version is used.
  parameter_group:
    description:
      - Name of the DB parameter group to associate with this instance. If omitted
      - then the RDS default DBParameterGroup will be used.
    required: false
  license_model:
    description:
      - The license model for this DB instance.
    required: false
    choices:  [ 'license-included', 'bring-your-own-license', 'general-public-license', 'postgresql-license' ]
  multi_zone:
    description:
      - Specifies if this is a Multi-availability-zone deployment. Can not be used in conjunction with zone parameter.
    choices: [ "yes", "no" ]
    required: false
  iops:
    description:
      - Specifies the number of IOPS for the instance. Must be an integer greater than 1000.
    required: false
  security_groups:
    description: Comma separated list of one or more security groups.
    required: false
  vpc_security_groups:
    description: Comma separated list of one or more vpc security group ids. Also requires `subnet` to be specified.
    required: false
  port:
    description: Port number that the DB instance uses for connections.
    required: false
    default: 3306 for mysql, 1521 for Oracle, 1433 for SQL Server, 5432 for PostgreSQL.
  upgrade:
    description: Indicates that minor version upgrades should be applied automatically.
    required: false
    default: no
    choices: [ "yes", "no" ]
  option_group:
    description: The name of the option group to use. If not specified then the default option group is used.
    required: false
  maint_window:
    description:
       - "Maintenance window in format of ddd:hh24:mi-ddd:hh24:mi (Example: Mon:22:00-Mon:23:15). "
       - "If not specified then AWS will assign a random maintenance window."
    required: false
  backup_window:
    description:
       - "Backup window in format of hh24:mi-hh24:mi (Example: 04:00-05:45). If not specified "
       - "then AWS will assign a random backup window."
    required: false
  backup_retention:
    description:
       - "Number of days backups are retained. Set to 0 to disable backups. Default is 1 day. "
       - "Valid range: 0-35."
    required: false
  zone:
    description:
      - availability zone in which to launch the instance.
    required: false
    aliases: ['aws_zone', 'ec2_zone']
  subnet:
    description:
      - VPC subnet group. If specified then a VPC instance is created.
    required: false
  snapshot:
    description:
      - Name of snapshot to take when state=absent - if no snapshot name is provided then no snapshot is taken.
    required: false
  wait:
    description:
      - Wait for the database to enter the desired state.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
  apply_immediately:
    description:
      - If enabled, the modifications will be applied as soon as possible rather
      - than waiting for the next preferred maintenance window.
    default: no
    choices: [ "yes", "no" ]
  force_failover:
    description:
      - Used only when state=rebooted. If enabled, the reboot is done using a MultiAZ failover.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  force_password_update:
    description:
      - Whether to try to update the DB password for an existing database. There is no API method to
        determine whether or not a password will be updated, and it causes problems with later operations
        if a password is updated unnecessarily.
    default: "no"
    choices: [ "yes", "no" ]
  old_db_instance_identifier:
    description:
      - Name to rename an instance from.
    required: false
  character_set_name:
    description:
      - Associate the DB instance with a specified character set.
    required: false
  publicly_accessible:
    description:
      - explicitly set whether the resource should be publicly accessible or not.
    required: false
  cluster:
    description:
      -  The identifier of the DB cluster that the instance will belong to.
    required: false
  tags:
    description:
      - tags dict to apply to a resource.
    required: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Basic mysql provisioning example
- rds_instance:
    id: new-database
    db_engine: MySQL
    size: 10
    instance_type: db.m1.small
    username: mysql_admin
    password: 1nsecure
    tags:
      Environment: testing
      Application: cms

# Create a read-only replica and wait for it to become available
- rds_instance:
    id: new-database-replica
    source_instance: new_database
    wait: yes
    wait_timeout: 600

# Promote the read replica to a standalone database by removing the source_instance
# setting.  We use the full parameter names matching the ones AWS uses.
- rds_instance:
    db_instance_identifier: new-database-replica
    wait: yes
    wait_timeout: 600

# Delete an instance, but create a snapshot before doing so
- rds_instance:
    state: absent
    db_instance_identifier: new-database
    snapshot: new_database_snapshot

# Rename an instance and wait for the change to take effect
- rds_instance:
    old_db_instance_identifier: new-database
    db_instance_identifier: renamed-database
    wait: yes

# Reboot an instance and wait for it to become available again
- rds_instance:
    state: rebooted
    id: database
    wait: yes

# Restore a Postgres db instance from a snapshot, wait for it to become available again, and
#  then modify it to add your security group. Also, display the new endpoint.
#  Note that the "publicly_accessible" option is allowed here just as it is in the AWS CLI
- rds_instance:
     snapshot: mypostgres-snapshot
     id: MyNewInstanceID
     region: us-west-2
     zone: us-west-2b
     subnet: default-vpc-xx441xxx
     publicly_accessible: yes
     wait: yes
     wait_timeout: 600
     tags:
         Name: pg1_test_name_tag
  register: rds

- rds_instance:
     id: MyNewInstanceID
     region: us-west-2
     vpc_security_groups: sg-xxx945xx

- debug:
    msg: "The new db endpoint is {{ rds.instance.endpoint }}"
'''

RETURN = '''
instance:
  description:
    - the information returned in data from boto3 get_db_instance or from modify_db_instance
      converted from a CamelCase dictionary into a snake_case dictionary
  returned: success
  type: dict
changed:
  description:
    - whether the RDS instance configuration has been changed.  Please see the main module
      description.  Changes may be delayed so, unless the correct parameters are given
      this does not mean that the changed configuration has already been implemented.
response:
  description:
    - the raw response from the last call to AWS if available.  This will likely include
      the configuration of the RDS in CamelCase if needed
'''

import time
import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn
from ansible.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict
from ansible.module_utils.ec2 import ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict
from ansible.module_utils.aws.rds import get_db_instance, instance_to_facts, instance_facts_diff
from ansible.module_utils.aws.rds import DEFAULT_PORTS, DB_ENGINES, LICENSE_MODELS

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3


def eprint(*args, **kwargs):
    pass
#    print(args, file=sys.stderr, **kwargs)


def await_resource(conn, instance_id, status, module, await_pending=None):
    wait_timeout = module.params.get('wait_timeout') + time.time()
    # Refresh the resource immediately in case we just changed it's state;
    # should we sleep first?
    resource = get_db_instance(conn, instance_id)
    eprint(str(resource))
    eprint("wait is {0} {1} await_pending is {2} status is {3}".format(
        str(wait_timeout), str(time.time()), str(await_pending), str(resource['DBInstanceStatus'])))
    rdat = resource["PendingModifiedValues"]
    eprint("wait timeout repr: " + repr(wait_timeout) + "\n")
    while ((await_pending and rdat) or resource['DBInstanceStatus'] != status) and wait_timeout > time.time():
        time.sleep(5)
        # Temporary until all the rds2 commands have their responses parsed
        id = resource.get('DBInstanceIdentifier')
        if id is None:
            module.fail_json(
                msg="There was a problem waiting for RDS instance %s" % resource.instance)
        resource = get_db_instance(conn, id)
        if resource is None:
            break
        rdat = resource["PendingModifiedValues"]
        eprint(str(resource))
    # resource will be none if it has actually been removed - e.g. we were waiting for deleted
    # status; maybe that should be an error in other situations?
    if wait_timeout <= time.time() and resource is not None and resource['DBInstanceStatus'] != status:
        module.fail_json(msg="Timeout waiting for RDS resource %s status is %s should be %s" % (
            resource.get('DBInstanceIdentifier'), resource['DBInstanceStatus'], status))
    return resource


def create_db_instance(module, conn):
    if module.params.get('db_engine') in ['aurora']:
        required_vars = ['db_instance_identifier', 'instance_type', 'db_engine']
        valid_vars = ['apply_immediately', 'character_set_name', 'cluster', 'db_name',
                      'engine_version', 'instance_type', 'license_model', 'maint_window',
                      'option_group', 'parameter_group', 'port', 'publicly_accessible',
                      'subnet', 'upgrade', 'tags', 'zone']
    else:
        required_vars = ['db_instance_identifier', 'db_engine', 'size', 'instance_type',
                         'username', 'password']
        valid_vars = ['backup_retention', 'backup_window',
                      'character_set_name', 'cluster', 'db_name', 'engine_version',
                      'instance_type', 'license_model', 'maint_window', 'multi_zone',
                      'option_group', 'parameter_group', 'port', 'publicly_accessible',
                      'storage_type', 'subnet', 'upgrade', 'tags', 'security_groups',
                      'vpc_security_groups', 'zone']

    if module.params.get('subnet'):
        valid_vars.append('vpc_security_groups')
    else:
        valid_vars.append('security_groups')
    params = select_parameters(module, required_vars, valid_vars)

    instance_id = module.params.get('db_instance_identifier')

    changed = False
    instance = get_db_instance(conn, instance_id)
    if instance is None:
        try:
            response = conn.create_db_instance(**params)
            instance = get_db_instance(conn, instance_id)
            changed = True
        except Exception as e:
            module.fail_json_aws(e, msg="trying to create instance")

    if module.params.get('wait'):
        resource = await_resource(conn, instance_id, 'available', module)
    else:
        resource = get_db_instance(conn, instance_id)

    return dict(changed=changed, instance=resource, response=response)


def replicate_db_instance(module, conn):
    """if the database doesn't exist, create it as a replica of an existing instance
    """

    required_vars = ['db_instance_identifier', 'source_instance']
    valid_vars = ['instance_type', 'iops', 'option_group', 'port',
                  'publicly_accessible', 'storage_type',
                  'tags', 'upgrade', 'zone']
    params = select_parameters(module, required_vars, valid_vars)
    instance_id = module.params.get('db_instance_identifier')

    instance = get_db_instance(conn, instance_id)
    if instance:
        instance_source = instance.get('SourceDBInstanceIdentifier')
        if not instance_source:
            module.fail_json(msg="instance %s already exists; cannot overwrite with replica"
                             % instance_id)
        if instance_source != params('SourceDBInstanceIdentifier'):
            module.fail_json(msg="instance %s already exists with wrong source %s cannot overwrite"
                             % (instance_id, params('SourceDBInstanceIdentifier')))

        changed = False
    else:
        try:
            response = conn.create_db_instance_read_replica(**params)
            instance = get_db_instance(conn, instance_id)
            changed = True
        except Exception as e:
            module.fail_json_aws(e, msg="trying to create read replica of instance")

    if module.params.get('wait'):
        resource = await_resource(conn, instance_id, 'available', module)
    else:
        resource = get_db_instance(conn, instance_id)

    return dict(changed=changed, instance=resource, response=response)


def delete_db_instance(module, conn):
    required_vars = ['db_instance_identifier']

    # we have to accept but ignore variables which have defaults
    valid_vars = ['snapshot', 'skip_final_snapshot', 'storage_type']

    try:
        del(module.params['storage_type'])
    except KeyError:
        pass

    params = select_parameters(module, required_vars, valid_vars)
    instance_id = module.params.get('db_instance_identifier')
    snapshot = module.params.get('snapshot')

    result = get_db_instance(conn, instance_id)
    if not result:
        return dict(changed=False)
    if result['DBInstanceStatus'] == 'deleting':
        return dict(changed=False)
    try:
        if snapshot:
            params["SkipFinalSnapshot"] = False
            params["FinalDBSnapshotIdentifier"] = snapshot
            del(params['DBSnapshotIdentifier'])
        else:
            params["SkipFinalSnapshot"] = True
        response = conn.delete_db_instance(**params)
        instance = result
    except Exception as e:
        module.fail_json_aws(e, msg="trying to delete instance")

    # If we're not waiting for a delete to complete then we're all done
    # so just return
    if not module.params.get('wait'):
        return dict(changed=True, response=response)
    try:
        instance = await_resource(conn, instance_id, 'deleted', module)
    except botocore.exceptions.ClientError as e:
        if e.code == 'DBInstanceNotFound':
            return dict(changed=True)
        else:
            module.fail_json_aws(e, msg="waiting for rds deletion to complete")
    except Exception as e:
            module.fail_json_aws(e, msg="waiting for rds deletion to complete")

    return dict(changed=True, response=response, instance=instance)


def update_rds_tags(module, conn, resource, current_tags, desired_tags):
    changed = False
    # it's much easier to do set manipulation in ansible form
    current_tags = boto3_tag_list_to_ansible_dict(current_tags)
    desired_tags = boto3_tag_list_to_ansible_dict(desired_tags)
    current_keys = set(current_tags.keys())
    desired_keys = set(desired_tags.keys())
    to_add = desired_keys - current_keys
    to_delete = current_keys - desired_keys

    for k in desired_keys & current_keys:
        if current_tags[k] != desired_tags[k]:
            to_delete.add(k)
            to_add.add(k)

    if to_delete:
        try:
            conn.remove_tags_from_resource(ResourceName=resource, TagKeys=list(to_delete))
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e, msg="trying to remove old tags from instance")
        changed = True

    if to_add:
        tag_map = [{'Key': k, 'Value': desired_tags[k]} for k in to_add]
        try:
            conn.add_tags_to_resource(ResourceName=resource, Tags=tag_map)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e, msg="trying to add new tags to instance")
        changed = True

    return dict(changed=changed)


def abort_on_impossible_changes(module, before_facts):
    for immutable_key in ['username', 'db_engine', 'db_name']:
        if immutable_key in module.params:
            try:
                keys_different = module.params[immutable_key] != before_facts[immutable_key]
            except KeyError:
                keys_different = False
            if (keys_different):
                module.fail_json(msg="Cannot modify parameter %s for instance %s" %
                                 (immutable_key, before_facts['db_instance_identifier']))


def snake_dict_to_cap_camel_dict(snake_dict):
    """ like snake_dict_to_camel_dict but capitalize the first word too """

    def camelize(complex_type):
        if complex_type is None:
            return
        new_type = type(complex_type)()
        if isinstance(complex_type, dict):
            for key in complex_type:
                new_type[camel(key)] = camelize(complex_type[key])
        elif isinstance(complex_type, list):
            for i in range(len(complex_type)):
                new_type.append(camelize(complex_type[i]))
        else:
            return complex_type
        return new_type

    def camel(words):
        return ''.join(x.capitalize() or '_' for x in words.split('_'))

    return camelize(snake_dict)


def prepare_params_for_modify(module, before_facts):
    """extract parameters from module and convert to format for modify_db_instance call

    Select those parameters we want, convert them to AWS CamelCase, change a few from
    the naming used in the create call to the naming used in the modify call.
    """
    force_password_update = module.params.get('force_password_update')

    # FIXME: we should use this for filtering in the diff!
    # valid_vars = ['apply_immediately', 'backup_retention', 'backup_window',
    #               'engine_version', 'instance_type', 'iops', 'license_model',
    #               'maint_window', 'multi_zone', 'option_group',
    #               'parameter_group', 'password', 'port', 'publicly_accessible', 'size',
    #               'storage_type', 'subnet', 'upgrade',
    #               'security_groups', 'vpc_security_groups']

    abort_on_impossible_changes(module, before_facts)

    will_change = instance_facts_diff(before_facts, module.params)
    if not will_change:
        return {}
    facts_to_change = will_change['after']

    mod_params = module.params

    # we have to filter down to the parameters handled by modify (e.g. not tags) and
    # convert from fact format to the AWS call CamelCase format.

    params = snake_dict_to_cap_camel_dict(facts_to_change)

    if facts_to_change.get('security_groups'):
        params['DBSecurityGroups'] = facts_to_change.get('security_groups').split(',')

    # modify_db_instance takes DBPortNumber in contrast to
    # create_db_instance which takes Port
    try:
        params['DBPortNumber'] = params.pop('Port')
    except KeyError:
        pass

    # modify_db_instance does not cope with DBSubnetGroup not moving VPC!
    try:
        if (before_facts['subnet'] == params.get('DBSubnetGroupName')):
            del(params['DBSubnetGroupName'])
    except KeyError:
        pass
    if not force_password_update:
        try:
            del(params['MasterUserPassword'])
        except KeyError:
            pass

    if before_facts['db_instance_identifier'] != mod_params['db_instance_identifier']:
        params['DBInstanceIdentifier'] = mod_params['old_db_instance_identifier']
        params['NewDBInstanceIdentifier'] = mod_params['db_instance_identifier']

    return params


def wait_for_new_instance_id(conn, after_instance_id):
    # Wait until the new instance name is valid
    after_instance = None
    while not after_instance:
        # FIXME: Timeout!!!
        after_instance = get_db_instance(conn, after_instance_id)
        time.sleep(5)
    return after_instance


def modify_db_instance(module, conn):
    """make aws call to modify a DB instance, gathering needed parameters and returning if changed

    old_db_instance_identifier may be given as an argument to the module but it must be deleted by
    the time we get here if we are not to use it.

    """
    instance_id = module.params.get('db_instance_identifier')
    old_instance_id = module.params.get('old_db_instance_identifier')
    if old_instance_id is not None:
        before_instance = get_db_instance(conn, old_instance_id)
        if before_instance is None:
            module.fail_json("old RDS instance disappeared under us.  Maybe try again?")
    else:
        before_instance = get_db_instance(conn, instance_id)

    before_facts = instance_to_facts(before_instance)
    params = prepare_params_for_modify(module, before_facts)

    if not params:
        return dict(changed=False, instance=before_facts)

    return_instance = None
    try:
        response = conn.modify_db_instance(**params)
        return_instance = response['DBInstance']
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e, msg="trying to modify RDS instance")

    # Why can this happen? I do not know, go ask your dad.
    # Better safe than sorry, however.
    if return_instance is None:
        return_instance = before_instance

    apply_immediately = params.get('apply_immediately')
    if not apply_immediately:
        return dict(changed=True, instance=instance_to_facts(return_instance))

    # as currently defined, if we get apply_immediately we will wait for the rename to
    # complete even if we don't get the wait parameter.  This makes sense since it means
    # any future playbook actions will apply reliably to the correct instance.  If the
    # user doesn't want to wait (renames can also take a long time) then they can
    # explicitly run this as an asynchronous task.
    if old_instance_id:
        return_instance = wait_for_new_instance_id(module, instance_id)
        instance_id_now = instance_id
        if module.params.get('wait'):
            # Found instance but it briefly flicks to available
            # before rebooting so let's wait until we see it rebooting
            # before we check whether to 'wait'
            return_instance = await_resource(conn, instance_id, 'rebooting', module)
    else:
        # SLIGHTLY DOUBTFUL: We have a race condition here where, if we are unlucky, the
        # name of the instance set to change without apply_immediately _could_ change
        # before we return.  The user is responsible to know that though so should be
        # fine.
        instance_id_now = old_instance_id

    if module.params.get('wait'):
        eprint("about to wait")
        return_instance = await_resource(conn, instance_id_now, 'available', module,
                                         await_pending=apply_immediately)
    else:
        eprint("not waiting for update of rds")

    diff = instance_facts_diff(before_instance, return_instance)
    changed = not not diff  # "not not" casts from dict to boolean!

    # boto3 modify_db_instance can't modify tags directly
    current_tags = conn.list_tags_for_resource(ResourceName=response['DBInstance']['DBInstanceArn'])['TagList']
    if update_rds_tags(module, conn, response['DBInstance']['DBInstanceArn'], current_tags, module.params.get('tags')):
        changed = True
    return dict(changed=changed, instance=return_instance, diff=diff)


def promote_db_instance(module, conn):
    required_vars = ['db_instance_identifier']
    valid_vars = ['backup_retention', 'backup_window']
    params = select_parameters(module, required_vars, valid_vars)
    instance_id = module.params.get('db_instance_identifier')

    result = get_db_instance(conn, instance_id)
    if not result:
        module.fail_json(msg="DB Instance %s does not exist" % instance_id)

    if result.get('replication_source'):
        try:
            response = conn.promote_read_replica(**params)
            instance = response['DBInstance']
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to promote replica instance: %s " % str(e),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    else:
        changed = False

    if module.params.get('wait'):
        instance = await_resource(conn, instance, 'available', module)
    else:
        instance = get_db_instance(conn, instance_id)

    return dict(changed=changed, instance=instance)


def reboot_db_instance(module, conn):
    required_vars = ['db_instance_identifier']
    valid_vars = ['force_failover']

    params = select_parameters(module, required_vars, valid_vars)
    instance_id = module.params.get('db_instance_identifier')
    instance = get_db_instance(conn, instance_id)
    try:
        response = conn.reboot_db_instance(**params)
        instance = response['DBInstance']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to reboot instance: %s " % str(e),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    if module.params.get('wait'):
        instance = await_resource(conn, instance, 'available', module)
    else:
        instance = get_db_instance(conn, instance_id)

    return dict(changed=True, instance=instance)


def restore_db_instance(module, conn):
    required_vars = ['db_instance_identifier', 'snapshot']
    valid_vars = ['db_name', 'iops', 'license_model', 'multi_zone',
                  'option_group', 'port', 'publicly_accessible', 'storage_type',
                  'subnet', 'tags', 'upgrade', 'zone', 'instance_type']
    params = select_parameters(module, required_vars, valid_vars)
    instance_id = module.params.get('db_instance_identifier')

    changed = False
    instance = get_db_instance(conn, instance_id)
    if not instance:
        try:
            response = conn.restore_db_instance_from_db_snapshot(**params)
            instance = response['DBInstance']
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to restore instance: %s " % str(e),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if module.params.get('wait'):
        instance = await_resource(conn, instance, 'available', module)
    else:
        instance = get_db_instance(conn, instance_id)

    return dict(changed=changed, instance=instance)


def ensure_db_state(module, conn):
    instance_id = module.params.get('db_instance_identifier')
    instance = get_db_instance(conn, instance_id)
    if not instance:
        return create_db_instance(module, conn)
    else:
        if instance.get('replication_source') and not module.params.get('source_instance'):
            promote_db_instance(module, conn)
        return modify_db_instance(module, conn)


def validate_parameters(module):
    """provide parameter validation beyond the normal ansible module semantics
    """
    params = module.params
    if params.get('db_instance_identifier') == params.get('old_db_instance_identifier'):
        module.fail_json(msg="if specified, old_db_instance_identifier must be different from db_instance_identifier")


def select_parameters(module, required_vars, valid_vars):
    """select parameters for use in an AWS API call converting them to boto3 naming

    select_parameters takes a list of required variables and valid variables.  Each
    variable is pulled from the module parameters.  If the required variables are missing
    then execution is aborted with an error.  Extra parameters on the module are ignored.

    """
    facts = {}

    for k in required_vars:
        if not module.params.get(k):
            raise Exception("Parameter %s required" % k)
        facts[k] = module.params[k]

    for k in valid_vars:
        try:
            facts[k] = module.params[k]
        except KeyError:
            pass

    params = snake_dict_to_cap_camel_dict(facts)

    if params.get('security_groups'):
        params['DBSecurityGroups'] = facts.get('security_groups').split(',')

    # Convert tags dict to list of tuples that boto expects
    if 'Tags' in params:
        params['Tags'] = ansible_dict_to_boto3_tag_list(module.params['tags'])
    return params


argument_spec = ec2_argument_spec()
argument_spec.update(
    dict(
        state=dict(choices=['absent', 'present', 'rebooted', 'restarted'], default='present'),
        db_instance_identifier=dict(aliases=["id"], required=True),
        source_instance=dict(),
        db_engine=dict(choices=DB_ENGINES),
        size=dict(type='int'),
        instance_type=dict(aliases=['type']),
        username=dict(),
        password=dict(no_log=True),
        db_name=dict(),
        engine_version=dict(),
        parameter_group=dict(),
        license_model=dict(choices=LICENSE_MODELS),
        multi_zone=dict(type='bool', default=False),
        iops=dict(type='int'),
        storage_type=dict(
            choices=['standard', 'io1', 'gp2'], default='standard'),
        security_groups=dict(),
        vpc_security_groups=dict(type='list'),
        port=dict(type='int'),
        upgrade=dict(type='bool', default=False),
        option_group=dict(),
        maint_window=dict(),
        backup_window=dict(),
        backup_retention=dict(type='int'),
        zone=dict(aliases=['aws_zone', 'ec2_zone']),
        subnet=dict(),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=600),
        snapshot=dict(),
        skip_final_snapshot=dict(type='bool'),
        apply_immediately=dict(type='bool', default=False),
        old_db_instance_identifier=dict(aliases=['old_id']),
        tags=dict(type='dict'),
        publicly_accessible=dict(type='bool'),
        character_set_name=dict(),
        force_failover=dict(type='bool', default=False),
        force_password_update=dict(type='bool', default=False),
    )
)
required_if = [
    ('storage_type', 'io1', ['iops']),
]


def setup_client(module):
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg="region must be specified")
    return boto3_conn(module, 'client', 'rds', region, **aws_connect_params)


def setup_module_object():
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if
    )
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for rds_instance module')
    return module


def set_module_defaults(module):
    # set port to per db defaults if not specified
    if module.params['port'] is None and module.params['db_engine'] is not None:
        if '-' in module.params['db_engine']:
            engine = module.params['db_engine'].split('-')[0]
        else:
            engine = module.params['db_engine']
        module.params['port'] = DEFAULT_PORTS[engine.lower()]

"""creating instances from replicas, renames and so on

this module is currently a preview and this section is more aspirational than truly known
to be implemeneted.

The aim of this module is to be as safe as reasonable for use in production.  This in no
way excuses the operator from the need to keep offline backups, however it does mean we
should try to be careful.

* try not to destroy data unless we are sure we are told to
 * when things don't match our expectations tend to abort or not do things
 * create replicas and new databses only when there is no pre-existing database
* try not to create new databases when we should use an old one

* if we are told a database should be a replica, normally create a new replica
 * if we are told that it should be a replica
   and
 * there is a pre-existing database with the old databse name
   and
 * that database is already a replica of the new


"""


def run_task(module, conn):
    """run all actual changes to the rds"""
    if module.params['state'] == 'absent':
        return delete_db_instance(module, conn)
    if module.params['state'] in ['rebooted', 'restarted']:
        # FIXME: check the parameters match??
        return reboot_db_instance(module, conn)
    if module.params['state'] == 'present':
        if module.params.get('source_instance'):
            replicate_return_dict = replicate_db_instance(module, conn)
        if module.params.get('snapshot'):
            restore_return_dict = restore_db_instance(module, conn)
        ensure_return_dict = ensure_db_state(module, conn)

        if ensure_return_dict['change']:
            return_dict = ensure_return_dict
        else:
            if restore_return_dict['change']:
                return_dict = restore_return_dict
            else:
                if replicate_return_dict['change']:
                    return_dict = replicate_return_dict
                else:
                    return_dict = ensure_return_dict

    try:
        instance = return_dict['instance']
        return_dict['id'] = instance['db_instance_identifier']
        return_dict['engine'] = instance['engine']
        # FIXME: add endpoint url
    except KeyError:
        pass

    return return_dict


def main():
    module = setup_module_object()
    set_module_defaults(module)
    validate_parameters(module)
    conn = setup_client(module)
    return_dict = run_task(module, conn)
    module.exit_json(return_dict)


if __name__ == '__main__':
    main()
