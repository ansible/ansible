#!/usr/bin/python
# Copyright (c) 2014-2017 Ansible Project
# Copyright (c) 2017 Will Thames
# Copyright (c) 2017 Michael De La Rue
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# This is a derivative of rds.py although no untouched lines survive.  See also that module.

# from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

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
     - The behavior in the case where only one of apply_immediately or wait is given is
       complex and subject to change.  It currently waits a bit to see the rename actually
       happens and should reflect the status after renaming is applied but the instance
       state is likely to continue to change afterwards.  Please do not rely on the return
       value to match the status soon afterwards.
     - In the case that apply_immediately is not given then the return value from
notes:
     - Whilst this module aims to be safe for use in production and will attempt to never
       destroy data unless explicitly told to, this is currently more an aspiration than
       something to rely on.  Please ensure you have a tested restore strategy in place
       for your data which does not rely on the contents of the RDS instance.
requirements:
    - "python >= 2.6"
    - "boto3"
version_added: "2.5"
author:
    - Bruce Pennypacker (@bpennypacker)
    - Will Thames (@willthames)
    - Michael De La Rue (@mikedlr)
options:
  state:
    description:
      - Describes the desired state of the database instance. N.B. restarted is allowed as an alias for rebooted.
    default: present
    choices: [ 'present', 'absent', 'rebooted' ]
  db_instance_identifier:
    aliases:
      - id
    description:
      - Database instance identifier.
    required: true
  source_db_instance_identifier:
    description:
      - Name of the database when sourcing from a replica
  replica:
    description:
    - whether or not a database is a read replica
    default: False
  engine:
    description:
      - The type of database. Used only when state=present.
    choices: [ 'mariadb', 'mysql', 'oracle-se1', 'oracle-se2', 'oracle-se', 'oracle-ee', 'sqlserver-ee',
                sqlserver-se', 'sqlserver-ex', 'sqlserver-web', 'postgres', 'aurora']
  allocated_storage:
    description:
      - Size in gigabytes of the initial storage for the DB instance.  See
        [API documentation](https://botocore.readthedocs.io/en/latest/reference/services/rds.html#RDS.Client.create_db_instance)
        for details of limits
      - Required unless the database type is aurora.
  storage_type:
    description:
      - Specifies the storage type to be associated with the DB instance. C(iops) must
        be specified if C(io1) is chosen.
    choices: ['standard', 'gp2', 'io1' ]
    default: standard unless iops is set
  db_instance_class:
    description:
      - The instance type of the database. If source_db_instance_identifier is specified then the replica inherits
        the same instance type as the source instance.
  master_username:
    description:
      - Master database username.
  master_user_password:
    description:
      - Password for the master database username.
  db_name:
    description:
      - Name of a database to create within the instance. If not specified then no database is created.
  engine_version:
    description:
      - Version number of the database engine to use. If not specified then
      - the current Amazon RDS default engine version is used.
  db_parameter_group_name:
    description:
      - Name of the DB parameter group to associate with this instance. If omitted
      - then the RDS default DBParameterGroup will be used.
  license_model:
    description:
      - The license model for this DB instance.
    choices:  [ 'license-included', 'bring-your-own-license', 'general-public-license', 'postgresql-license' ]
  multi_az:
    description:
      - Specifies if this is a Multi-availability-zone deployment. Can not be used in conjunction with zone parameter.
    choices: [ "yes", "no" ]
  iops:
    description:
      - Specifies the number of IOPS for the instance. Must be an integer greater than 1000.
  db_security_groups:
    description: Comma separated list of one or more security groups.
  vpc_security_group_ids:
    description: Comma separated list of one or more vpc security group ids. Also requires I(subnet) to be specified.
    aliases:
      - security_groups
  port:
    description: Port number that the DB instance uses for connections.
    default: 3306 for mysql, 1521 for Oracle, 1433 for SQL Server, 5432 for PostgreSQL.
  auto_minor_version_upgrade:
    description: Indicates that minor version upgrades should be applied automatically.
    default: "no"
    choices: [ "yes", "no" ]
  option_group_name:
    description: The name of the option group to use. If not specified then the default option group is used.
  preferred_maintenance_window:
    description:
       - "Maintenance window in format of ddd:hh24:mi-ddd:hh24:mi (Example: Mon:22:00-Mon:23:15). "
       - "If not specified then AWS will assign a random maintenance window."
  preferred_backup_window:
    description:
       - "Backup window in format of hh24:mi-hh24:mi (Example: 04:00-05:45). If not specified "
       - "then AWS will assign a random backup window."
  backup_retention_period:
    description:
       - "Number of days backups are retained. Set to 0 to disable backups. Default is 1 day. "
       - "Valid range: 0-35."
  availability_zone:
    description:
      - availability zone in which to launch the instance.
    aliases: ['aws_zone', 'ec2_zone']
  db_subnet_group_name:
    description:
      - VPC subnet group. If specified then a VPC instance is created.
    aliases: ['subnet']
  final_db_snapshot_identifier:
    description:
      - Name of snapshot to take when state=absent - if no snapshot name is provided then no
        snapshot is taken.
  db_snapshot_identifier:
    description:
      - Name of snapshot to use when restoring a database with state=present
        snapshot is taken.
  snapshot:
    description:
      - snapshot provides a default for either final_db_snapshot_identifier or db_snapshot_identifier
        allowing the same parameter to be used for both backup and restore.
  wait:
    description:
      - Wait for the database to enter the desired state.
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
    default: "no"
    choices: [ "yes", "no" ]
  force_failover:
    description:
      - Used only when state=rebooted. If enabled, the reboot is done using a MultiAZ failover.
    default: "no"
    choices: [ "yes", "no" ]
  force_password_update:
    description:
      - Whether to try to update the DB password for an existing database. There is no API method
        to determine whether or not a password needs to be updated, and it causes problems with
        later operations if a password is updated unnecessarily.
    default: "no"
    choices: [ "yes", "no" ]
  old_db_instance_identifier:
    description:
      - Name to rename an instance from.
  character_set_name:
    description:
      - Associate the DB instance with a specified character set.
  publicly_accessible:
    description:
      - explicitly set whether the resource should be publicly accessible or not.
  cluster:
    description:
      -  The identifier of the DB cluster that the instance will belong to.
  tags:
    description:
      - tags dict to apply to a resource.  If None then tags are ignored.  Use {} to set to empty.
  purge_tags:
    description:
      - whether to remove existing tags that aren't passed in the C(tags) parameter
    default: no
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Basic mysql provisioning example
- rds_instance:
    id: new-database
    engine: mysql
    allocated_storage: 10
    db_instance_class: db.m1.small
    master_username: mysql_admin
    master_user_password: 1nsecure
    tags:
      Environment: testing
      Application: cms

# Create a read-only replica and wait for it to become available
- rds_instance:
    id: new-database-replica
    source_db_instance_identifier: new_database
    wait: yes
    wait_timeout: 600

# Promote the read replica to a standalone database by removing the source_db_instance_identifier
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
     availability_zone: us-west-2b
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
     vpc_security_group_ids: sg-xxx945xx

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
  returned: success
  type: bool
response:
  description:
    - the raw response from the last call to AWS if available.  This will likely include
      the configuration of the RDS in CamelCase if needed
  returned: when available
  type: dict
'''

from ansible.module_utils.six import print_
import sys
import time
import traceback
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, snake_dict_to_camel_dict, AWSRetry
from ansible.module_utils.ec2 import ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict, compare_aws_tags
from ansible.module_utils.aws.rds import get_db_instance, instance_to_facts, instance_facts_diff
from ansible.module_utils.aws.rds import DEFAULT_PORTS, DB_ENGINES, LICENSE_MODELS
try:
    import botocore
    from botocore import xform_name
except ImportError:
    pass  # caught by imported AnsibleAWSModule


# NOTE ON DATA STRUCTURES AND NAMING:

# We use raw dictionaries in two variants as our main data structures.  One format is the
# snake_case formatted facts dictionaries whilst the other is the CamelCased AWS parameter
# dictionaries.  We try to keep data for as long as reasonable in the format it arrived
# in.
#
#   - Generally AWS CamelCased formatted dictionaries of instance data are named instance*
#   - Generally Ansible snake_case formatted dictionaries of facts about instaces are named fact*
#
# the one exception is that our final return is in fact format but the return parameter
# with the instance facts is called "instance".
#
# Dicts are chosen rather than than objects becuase
#   - they match with use elsewhere (AWS returns a dict, facts are passed in dicts)
#   - they are somewhat simpler to manipluate in many cases
#


# Q is a simple logging framework NOT suitable for production use but handy in development.
# try:
#     import q
#     HAS_Q = True
# except:
#     HAS_Q = False

HAS_Q = False


def q(junk):
    pass


# Ansible avoids proper python logging for reasons too complicted for
# me to fully understand but including the need to properly handle
# security (see proposals, many tickets and a number of PRs), so we
# make a little improvised logger here which goes through module.log
# we can always point to a more sophisticated logger when one exists.


class the_logger():
    default_log_level = 20
    default_module = None
    q = False

    def __init__(self, **kwargs):
        my_mod = kwargs.get('module')
        if my_mod:
            self.module = my_mod
        else:
            self.module = the_logger.default_module

        my_level = kwargs.get('log_level')
        if my_level:
            self.level = my_level
        else:
            self.level = the_logger.default_log_level

    def config(self, my_mod):
        self.module = my_mod

    def log(self, level, message):
        if HAS_Q and the_logger.q:
            q("log message: " + message)
        if self.level > level:
            return
        if self.module is None:
            print_(message, file=sys.stderr)
        else:
            self.module.log(message)

    def log_print(self, level, *args, **kwargs):
        if HAS_Q and the_logger.q:
            q("log print args: " + " ".join(args) + " " + repr(kwargs))
        if self.level > level:
            return
        if self.module is None:
            print_(args, file=sys.stderr, **kwargs)
        else:
            self.module.log()


main_logger = the_logger()


def await_resource(conn, instance_id, status, module, await_pending=None):
    """wait for a resource to change into a given status

    Await resource repeatedly polls an RDS waiting for it to change
    into a given status or disappear.

    N.B. If the resource disappears it will return None and this mightn
    happen while awaiting _any_ state.
    """
    wait_timeout = module.params.get('wait_timeout') + time.time()
    # Refresh the resource immediately in case we just changed it's state;
    # should we sleep first?
    assert instance_id is not None
    resource = get_db_instance(conn, instance_id)
    main_logger.log(50, "await_resource called for " + instance_id)
    main_logger.log(40, "wait is {0} {1} await_pending is {2} status is {3}".format(
        str(wait_timeout), str(time.time()), str(await_pending), str(resource['DBInstanceStatus'])))
    rdat = resource["PendingModifiedValues"]
    while ((await_pending and rdat) or resource['DBInstanceStatus'] != status) and wait_timeout > time.time():
        main_logger.log(70, "waiting with resource{}  ".format(str(resource)))
        time.sleep(5)
        # Temporary until all the rds2 commands have their responses parsed
        current_id = resource.get('DBInstanceIdentifier')
        if current_id is None:
            module.fail_json(
                msg="There was a problem waiting for RDS instance %s" % resource.instance)
        resource = get_db_instance(conn, current_id)
        if resource is None:
            break
        rdat = resource["PendingModifiedValues"]
    # resource will be none if it has actually been removed - e.g. we were waiting for deleted
    # status; maybe that should be an error in other situations?
    if wait_timeout <= time.time() and resource is not None and resource['DBInstanceStatus'] != status:
        module.fail_json(msg="Timeout waiting for RDS resource %s status is %s should be %s" % (
            resource.get('DBInstanceIdentifier'), resource['DBInstanceStatus'], status))
    return resource


def create_db_instance(module, conn):
    main_logger.log(30, "create_db_instance called")

    params = select_parameters_meta(module, conn, 'CreateDBInstance')

    instance_id = module.params.get('db_instance_identifier')
    params['DBInstanceIdentifier'] = instance_id
    params['Tags'] = ansible_dict_to_boto3_tag_list(params.get('Tags', {}))

    changed = False
    instance = get_db_instance(conn, instance_id)
    if instance is None:
        if module.check_mode:
            module.exit_json(changed=True, create_db_instance_params=params)
        try:
            response = conn.create_db_instance(**params)
            instance = get_db_instance(conn, instance_id)
            changed = True
        except Exception as e:
            module.fail_json_aws(e, msg="trying to create instance")

    if module.params.get('wait'):
        instance = await_resource(conn, instance_id, 'available', module)
    else:
        instance = get_db_instance(conn, instance_id)

    return dict(changed=changed, instance=instance, response=response)


def replicate_db_instance(module, conn):
    """if the database doesn't exist, create it as a replica of an existing instance
    """
    main_logger.log(30, "replicate_db_instance called")
    params = select_parameters_meta(module, conn, 'CreateDBInstanceReadReplica')
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
        if module.check_mode:
            module.exit_json(changed=True, create_db_instance_read_replica_params=params)
        try:
            response = conn.create_db_instance_read_replica(**params)
            instance = get_db_instance(conn, instance_id)
            changed = True
        except Exception as e:
            module.fail_json_aws(e, msg="trying to create read replica of instance")

    if module.params.get('wait'):
        instance = await_resource(conn, instance_id, 'available', module)
    else:
        instance = get_db_instance(conn, instance_id)

    return dict(changed=changed, instance=instance, response=response)


def update_rds_tags(module, conn, db_instance):
    main_logger.log(30, "update_rds_tags called")

    db_instance_arn = db_instance['DBInstanceArn']

    # from here on code matches closely code in ec2_group so that later we can merge together
    current_tags = boto3_tag_list_to_ansible_dict(conn.list_tags_for_resource(ResourceName=db_instance_arn)['TagList'])
    if current_tags is None:
        current_tags = []
    tags = module.params.get('tags')
    if tags is None:
        tags = {}
    purge_tags = module.params.get('purge_tags')
    changed = False

    tags_need_modify, tags_to_delete = compare_aws_tags(current_tags, tags, purge_tags)

    if tags_to_delete:
        if module.check_mode:
            module.exit_json(changed=True, remove_tags_from_resource_params=tags_to_delete)
        try:
            conn.remove_tags_from_resource(ResourceName=db_instance_arn, TagKeys=tags_to_delete)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        changed = True

    # Add/update tags
    if tags_need_modify:
        if module.check_mode:
            module.exit_json(changed=True, add_tags_to_resource_params=tags_need_modify)
        try:
            conn.add_tags_to_resource(ResourceName=db_instance_arn, Tags=ansible_dict_to_boto3_tag_list(tags_need_modify))
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        changed = True

    return changed


# TODO: this is hand hackery;  we should find a way of pulling this info out of botocore.
# probably it's the list of parameters included in create but missing in modify however
# some parameters change name so this isn't trivial to do!

rds_immutable_params = ['master_username', 'engine', 'db_name']


def abort_on_impossible_changes(module, before_facts):
    for immutable_key in rds_immutable_params:
        if immutable_key in module.params and module.params[immutable_key] is not None:
            before = before_facts.get(immutable_key)
            if (module.params[immutable_key] != before):
                module.fail_json(msg="Cannot modify parameter %s for instance %s" %
                                 (immutable_key, before_facts['db_instance_identifier']))


def fix_abbrevs_case(parameter):
    result = parameter
    for word in ["Db", "Aws", "Az", "Kms"]:
        if word in parameter:
            result = result.replace(word, word.upper())
    return result


def prepare_params_for_modify(module, connection, instance):
    """extract parameters from module and convert to format for modify_db_instance call

    Select those parameters we want, convert them to AWS CamelCase, change a few from
    the naming used in the create call to the naming used in the modify call.
    """
    before_facts = instance_to_facts(instance)
    abort_on_impossible_changes(module, before_facts)

    params = prepare_changes_for_modify(module, connection, before_facts)
    if len(params) == 0:
        return None
    params.update(prepare_call_settings_for_modify(module, before_facts))

    return params


def prepare_changes_for_modify(module, connection, before_facts):
    """
    Select those parameters which are interesting and which we want to change.
    """
    force_password_update = module.params.get('force_password_update')
    will_change = instance_facts_diff(connection, before_facts, module.params)
    if not will_change:
        return {}
    facts_to_change = will_change['after']

    # modify can't handle tags
    try:
        del(facts_to_change['tags'])
    except KeyError:
        pass

    # convert from fact format to the AWS call CamelCase format.
    params = snake_dict_to_camel_dict(facts_to_change, capitalize_first=True)
    params = dict((fix_abbrevs_case(key), value) for (key, value) in params.items())

    if facts_to_change.get('db_security_groups'):
        params['DBSecurityGroups'] = facts_to_change.get('db_security_groups').split(',')

    # modify_db_instance takes DBPortNumber in contrast to
    # create_db_instance which takes Port
    try:
        params['DBPortNumber'] = params.pop('Port')
    except KeyError:
        pass

    # You can specify 9.6 when creating a DB and get 9.6.2
    # We should ignore version if the requested version is
    # a prefix of the current version
    engine_version = will_change['before'].get('engine_version')
    after_engine_version = will_change['after'].get('engine_version')
    if engine_version is not None and engine_version.startswith(after_engine_version):
        del(facts_to_change['engine_version'])

    # modify_db_instance does not cope with DBSubnetGroup not moving VPC!
    try:
        if before_facts['db_subnet_group_name'] == params.get('DBSubnetGroupName'):
            del(params['DBSubnetGroupName'])
    except KeyError:
        pass
    if not force_password_update:
        try:
            del(params['MasterUserPassword'])
        except KeyError:
            pass
    return params


def prepare_call_settings_for_modify(module, before_facts):
    """parameters that control the how the modify will be done rather than changes to make"""
    mod_params = module.params
    params = {}
    if before_facts['db_instance_identifier'] != mod_params['db_instance_identifier']:
        params['DBInstanceIdentifier'] = mod_params['old_db_instance_identifier']
        params['NewDBInstanceIdentifier'] = mod_params['db_instance_identifier']
    else:
        params['DBInstanceIdentifier'] = mod_params['db_instance_identifier']

    if mod_params.get('apply_immediately'):
        params['ApplyImmediately'] = True
    return params


def wait_for_new_instance_id(conn, after_instance_id):
    # Wait until the new instance name is valid
    after_instance = None
    while not after_instance:
        # FIXME: Timeout!!!
        after_instance = get_db_instance(conn, after_instance_id)
        time.sleep(5)
    return after_instance


def modify_db_instance(module, conn, instance):
    """make aws call to modify a DB instance, gathering needed parameters and returning if changed

    old_db_instance_identifier may be given as an argument to the module but it must be deleted by
    the time we get here if we are not to use it.

    """
    apply_immediately = module.params.get('apply_immediately')
    wait = module.params.get('wait')
    main_logger.log(30, "modify_db_instance called; wait is {0}, apply_imm. is {1}".format(
        wait, apply_immediately
    ))

    call_params = prepare_params_for_modify(module, conn, instance)
    if not call_params:
        return dict(changed=False, instance=instance)

    return_instance = None

    @AWSRetry.backoff(tries=5, delay=5, catch_extra_error_codes=['InvalidDBInstanceState'])
    def modify_the_instance(**call_params):
        main_logger.log(20, "calling boto3conn.modify_db_instance with params {0} ".format(
            repr(call_params)
        ))
        return conn.modify_db_instance(**call_params)

    if module.check_mode:
        module.exit_json(changed=True, modify_db_instance_params=call_params)
    try:
        response = modify_the_instance(**call_params)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e, msg="trying to modify RDS instance")
    return_instance = response['DBInstance']

    # Why can this happen? I do not know, go ask your dad.
    # Better safe than sorry, however.
    if return_instance is None:
        module.fail_json(msg="modify failed to return modified instance, please verify manually")

    if not apply_immediately:
        main_logger.log(90, "apply_immediately not set so nothing to wait for - return changed")
        ret_val = dict(changed=True, instance=return_instance)
        if wait:
            ret_val["warning"] = ["wait was given but since apply_immediately was not given there's nothing to wait for"]
        return ret_val

    # as currently defined, if we get apply_immediately we will wait for the rename to
    # complete even if we don't get the wait parameter.  This makes sense since it means
    # any future playbook actions will apply reliably to the correct instance.  If the
    # user doesn't want to wait (renames can also take a long time) then they can
    # explicitly run this as an asynchronous task.
    new_id = call_params.get('NewDBInstanceIdentifier')
    if new_id is not None:
        return_instance = wait_for_new_instance_id(conn, new_id)
        instance_id_now = new_id
        main_logger.log(15, "instance has been renamed from {0} to {1} ".format(
            module.params.get('old_db_instance_identifier'), new_id
        ))
        if module.params.get('wait'):
            # Found instance but it briefly flicks to available
            # before rebooting so let's wait until we see it rebooting
            # before we check whether to 'wait'
            return_instance = await_resource(conn, new_id, 'rebooting', module)
            if return_instance is None:
                module.fail_json(msg="instance disappeared during modify - possibly network error??")
    else:
        # SLIGHTLY DOUBTFUL: We have a race condition here where, if we are unlucky, the
        # name of the instance set to change without apply_immediately _could_ change
        # before we return.  The user is responsible to know that though so should be
        # fine.
        instance_id_now = instance['DBInstanceIdentifier']

    if wait:
        main_logger.log(90, "about to wait for instance reconfigure to complete")
        return_instance = await_resource(conn, instance_id_now, 'available', module,
                                         await_pending=apply_immediately)
        if return_instance is None:
            module.fail_json(msg="instance disappeared during modify - possibly network error??")
    else:
        main_logger.log(90, "not waiting for update of rds config")

    # FIXME: make diff visible; possibly implement diff option
    diff = instance_facts_diff(conn, instance, return_instance)
    # changed = not not diff  # "not not" casts from dict to boolean!
    # boto3 modify_db_instance can't modify tags directly
    return dict(changed=True, instance=return_instance, diff=diff)


def get_instance_to_work_on(module, conn):
    """based on module arguments find an unambiguous instance we can work on"""
    instance_id = module.params.get('db_instance_identifier')
    old_instance_id = module.params.get('old_db_instance_identifier')
    before_instance = None

    if old_instance_id is not None:
        before_instance = get_db_instance(conn, old_instance_id)

    if before_instance is not None:
        if get_db_instance(conn, instance_id):
            module.fail_json(
                msg="both old and new instance exist so can't act safely; please clean up one",
                exception=traceback.format_exc())
        instance = before_instance
    else:
        instance = get_db_instance(conn, instance_id)

    return instance


def promote_db_instance(module, conn, instance):
    main_logger.log(30, "promote_db_instance called")
    params = select_parameters_meta(module, conn, 'PromoteReadReplica')

    if instance.get('ReadReplicaSourceDBInstanceIdentifier'):
        if module.check_mode:
            module.exit_json(changed=True, promote_read_replica_params=params)
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
        instance = await_resource(conn, instance["DBInstanceIdentifier"], 'available', module)

    return dict(changed=changed, instance=instance)


def restore_db_instance(module, conn):
    main_logger.log(30, "resore_db_instance called")
    params = select_parameters_meta(module, conn, 'RestoreDBInstanceFromDBSnapshot')
    instance_id = module.params.get('db_instance_identifier')
    changed = False
    instance = get_db_instance(conn, instance_id)
    if not instance:
        if module.check_mode:
            module.exit_json(changed=True, restore_db_instance_from_db_snapshot_params=params)
        try:
            response = conn.restore_db_instance_from_db_snapshot(**params)
            instance = response['DBInstance']
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to restore instance: %s " % str(e),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if module.params.get('wait'):
        instance = await_resource(conn, instance_id, 'available', module)
    else:
        instance = get_db_instance(conn, instance_id)

    return dict(changed=changed, instance=instance)


def ensure_absent_db_instance(module, conn):
    main_logger.log(30, "delete_db_instance called")
    try:
        del(module.params['storage_type'])
    except KeyError:
        pass

    params = select_parameters_meta(module, conn, 'DeleteDBInstance')
    instance_id = module.params.get('db_instance_identifier')
    snapshot = module.params.get('final_db_snapshot_identifier')

    instance = get_db_instance(conn, instance_id)
    if not instance:
        return dict(changed=False)
    if instance['DBInstanceStatus'] == 'deleting':
        return dict(changed=False)
    if snapshot:
        params["SkipFinalSnapshot"] = False
        params["FinalDBSnapshotIdentifier"] = snapshot
        del(module.params['snapshot'])
    else:
        params["SkipFinalSnapshot"] = True
    if module.check_mode:
        module.exit_json(changed=True, delete_db_instance_params=params)

    # FIXME: it's possible to get "trying to delete instance: An error occurred
    # (InvalidDBInstanceState) when calling the DeleteDBInstance operation:
    # Cannot delete DB Instance with a read replica still creating",

    # our call should retry here.

    try:
        response = conn.delete_db_instance(**params)
    except Exception as e:
        module.fail_json_aws(e, msg="trying to delete instance")

    # If we're not waiting for a delete to complete then we're all done
    # so just return
    if not module.params.get('wait'):
        return dict(changed=True, response=response)
    try:
        instance = await_resource(conn, instance_id, 'deleted', module)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'DBInstanceNotFound':
            return dict(changed=True)
        else:
            module.fail_json_aws(e, msg="waiting for rds deletion to complete")
    except Exception as e:
            module.fail_json_aws(e, msg="waiting for rds deletion to complete")

    return dict(changed=True, response=response, instance=instance)


def ensure_rebooted_db_instance(module, conn):
    main_logger.log(30, "reboot_db_instance called")
    params = select_parameters_meta(module, conn, 'RebootDBInstance')
    instance_id = module.params.get('db_instance_identifier')
    instance = get_db_instance(conn, instance_id)
    if module.check_mode:
        module.exit_json(changed=True, reboot_db_instance_params=params)
    try:
        response = conn.reboot_db_instance(**params)
        instance = response['DBInstance']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to reboot instance: %s " % str(e),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    if module.params.get('wait'):
        instance = await_resource(conn, instance_id, 'available', module)
    else:
        instance = get_db_instance(conn, instance_id)

    return dict(changed=True, instance=instance)


def validate_parameters(module):
    """provide parameter validation beyond the normal ansible module semantics
    """
    params = module.params
    if params.get('db_instance_identifier') == params.get('old_db_instance_identifier'):
        module.fail_json(msg="if specified, old_db_instance_identifier must be different from db_instance_identifier")


def select_parameters_meta(module, conn, operation):
    """
    given an AWS API operation name, select those parameters that can be used for it
    """

    # we do _NOT_ enforce required parameters at this level.  That
    # should be enforced at the ansible argument parsing level to make
    # sure that incoming we have all we need and then that gets
    # checked by botocore at the moment the API call is actually made.

    params = {}

    operations_model = conn._service_model.operation_model(operation)
    relevant_parameters = operations_model.input_shape.members.keys()
    for k in relevant_parameters:
        try:
            v = module.params[xform_name(k)]
            if v is not None:
                params[k] = v
        except KeyError:
            pass

    return params


# FIXME - parameters from create missing here
#
# DBClusterIdentifier *
# Domain
# DomainIAMRoleName
# EnableIAMDatabaseAuthentication
# EnablePerformanceInsights
# KmsKeyId *
# MonitoringInterval
# MonitoringRoleArn
# PerformanceInsightsKMSKeyId
# PreferredBackupWindow * - I want this
# PromotionTier
# StorageEncrypted * - Shertel and I want this
# TdeCredentialArn
# TdeCredentialPassword
# Timezone
#
# * means this something that had a real request and is actually worth doing


argument_spec = dict(
    # module function variables
    state=dict(choices=['absent', 'present', 'rebooted', 'restarted'], default='present'),
    log_level=dict(type='int', default=10),
    apply_immediately=dict(type='bool', default=False),
    wait=dict(type='bool', default=False),
    wait_timeout=dict(type='int', default=600),

    force_password_update=dict(type='bool', default=False),

    # replication variables
    source_db_instance_identifier=dict(),

    # RDS present (create / modify) variables
    allocated_storage=dict(type='int', aliases=['size']),
    auto_minor_version_upgrade=dict(type='bool', default=False),
    availability_zone=dict(),
    backup_retention_period=dict(type='int'),
    character_set_name=dict(),
    db_instance_class=dict(),
    db_instance_identifier=dict(aliases=["id"], required=True),
    db_name=dict(),
    db_parameter_group_name=dict(),
    db_security_groups=dict(),
    db_snapshot_identifier=dict(),
    db_subnet_group_name=dict(aliases=['subnet']),
    engine=dict(choices=DB_ENGINES),
    engine_version=dict(),
    iops=dict(type='int'),
    license_model=dict(choices=LICENSE_MODELS),
    master_user_password=dict(no_log=True),
    master_username=dict(),
    multi_az=dict(type='bool', default=False),
    old_db_instance_identifier=dict(aliases=['old_id']),
    option_group_name=dict(),
    port=dict(type='int'),
    preferred_backup_window=dict(),
    preferred_maintenance_window=dict(),
    publicly_accessible=dict(type='bool'),
    snapshot=dict(),
    storage_type=dict(choices=['standard', 'io1', 'gp2'], default='standard'),
    tags=dict(type='dict'),
    vpc_security_group_ids=dict(type='list'),

    # RDS reboot only variables
    force_failover=dict(type='bool', default=False),

    # RDS absent / delete only variables
    final_db_snapshot_identifier=dict(),
    skip_final_snapshot=dict(type='bool'),
    purge_tags=dict(type='bool', default=False)
)

# FIXME allocated_storage should be required if state=present and engine is not aurora
# if aurora then parameter should be ignored.

required_if = [
    ('storage_type', 'io1', ['iops']),
    ('state', 'present', ['engine', 'db_instance_class']),
]

# 'master_username' is required if creating a database instance other
# than aurora.  This is a little bit irritating if creating a replica
# where it won't be used but seems better to require it so create is
# safe elsewhere.  There's also the interesting 'feature' that giving
# the engine when deleting an RDS will mean you also have to give the
# master_username even when normally it wouldn't be needed.

# 'master_user_password' is needed during a create but we leave it out
# below for now so that we can do modify without it.
for i in DB_ENGINES:
    if i == 'aurora':
        required_if.append(('engine', 'aurora', ['db_instance_class'])),
    else:
        required_if.append(('engine', i, ['allocated_storage', 'master_username']))


def setup_client(module):
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg="region must be specified")
    return boto3_conn(module, 'client', 'rds', region, **aws_connect_params)


def setup_module_object():
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=required_if,
        mutually_exclusive=[['old_instance_id', 'source_db_instance_identifier',
                             'db_snapshot_identifier']],
        supports_check_mode=True,
    )
    return module


def set_module_defaults(module):
    # set port to per db defaults if not specified
    if module.params['port'] is None and module.params['engine'] is not None:
        if '-' in module.params['engine']:
            engine = module.params['engine'].split('-')[0]
        else:
            engine = module.params['engine']
        module.params['port'] = DEFAULT_PORTS[engine.lower()]
    if module.params['final_db_snapshot_identifier'] is None:
        module.params['final_db_snapshot_identifier'] = module.params.get('snapshot')
    if module.params['db_snapshot_identifier'] is None:
        module.params['db_snapshot_identifier'] = module.params.get('snapshot')
    module.params.get('snapshot')


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


def ensure_present_db_instance(module, conn):
    """ensures RDS instance exists and is correctly configured"""
    changed = False
    instance = get_instance_to_work_on(module, conn)

    # TODO : Restart instance if it's stopped.
    # TODO : We throw away the response from AWS; we should probably expose
    #        the last one recieved.

    if instance is None and module.params.get('source_db_instance_identifier'):
        replicate_return_dict = replicate_db_instance(module, conn)
        instance = replicate_return_dict['instance']
        changed = True
    if instance is None and module.params.get('snapshot'):
        restore_return_dict = restore_db_instance(module, conn)
        instance = restore_return_dict['instance']
        changed = True

    if instance is None:
        return_dict = create_db_instance(module, conn)
    else:
        if instance.get('replication_source') and not module.params.get('source_db_instance_identifier'):
            return_dict = promote_db_instance(module, conn, instance)
        # tags update before modify so we don't have to guess what the database name is as
        # it changes at a random time in future.
        if update_rds_tags(module, conn, instance):
            changed = True
        return_dict = modify_db_instance(module, conn, instance)
        # if Tags are updated but otherwise unmodified need to refresh instance info.
        if changed and not return_dict["changed"]:
            return_dict['instance'] = get_instance_to_work_on(module, conn)
            return_dict['changed'] = True

    return return_dict


def fixup_return_values(return_dict):
    try:
        # order is important here - some can be missing but we still
        # want the earlier ones
        instance = instance_to_facts(return_dict["instance"])
        if instance is None:
            del(return_dict["instance"])
            return
        return_dict["instance"] = instance
        return_dict['id'] = instance['db_instance_identifier']
        return_dict['engine'] = instance['engine']
        # TODO: add endpoint url
    except KeyError:
        pass


def run_task(module, conn):
    """run all actual changes to the rds"""
    if module.params['state'] == 'stopped':
        module.fail_json(msg="TODO: stopped state is not yet implemented")
    if module.params['state'] == 'absent':
        return_dict = ensure_absent_db_instance(module, conn)
    if module.params['state'] in ['rebooted', 'restarted']:
        return_dict = ensure_rebooted_db_instance(module, conn)
    if module.params['state'] == 'present':
        return_dict = ensure_present_db_instance(module, conn)

    fixup_return_values(return_dict)
    return return_dict


def main():
    main_logger.level = 20
    module = setup_module_object()
    main_logger.level = module.params.get('log_level')
    main_logger.module = module
    module.log("Starting rds_instance with logging set to: {0}".format(module.params.get('log_level')))
    set_module_defaults(module)
    validate_parameters(module)
    conn = setup_client(module)
    return_dict = run_task(module, conn)
    module.exit_json(**return_dict)


if __name__ == '__main__':
    main()
