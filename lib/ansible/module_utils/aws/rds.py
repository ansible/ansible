# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils._text import to_text
from ansible.module_utils.aws.waiters import get_waiter
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict
from ansible.module_utils.ec2 import compare_aws_tags, AWSRetry, ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError, WaiterError
except ImportError:
    pass

from collections import namedtuple
from time import sleep


Boto3ClientMethod = namedtuple('Boto3ClientMethod', ['name', 'waiter', 'operation_description', 'cluster', 'instance'])
# Whitelist boto3 client methods for cluster and instance resources
cluster_method_names = [
    'create_db_cluster', 'restore_db_cluster_from_db_snapshot', 'restore_db_cluster_from_s3',
    'restore_db_cluster_to_point_in_time', 'modify_db_cluster', 'delete_db_cluster', 'add_tags_to_resource',
    'remove_tags_from_resource', 'list_tags_for_resource', 'promote_read_replica_db_cluster'
]
instance_method_names = [
    'create_db_instance', 'restore_db_instance_to_point_in_time', 'restore_db_instance_from_s3',
    'restore_db_instance_from_db_snapshot', 'create_db_instance_read_replica', 'modify_db_instance',
    'delete_db_instance', 'add_tags_to_resource', 'remove_tags_from_resource', 'list_tags_for_resource',
    'promote_read_replica', 'stop_db_instance', 'start_db_instance', 'reboot_db_instance'
]


def get_rds_method_attribute(method_name, module):
    readable_op = method_name.replace('_', ' ').replace('db', 'DB')
    if method_name in cluster_method_names and 'new_db_cluster_identifier' in module.params:
        cluster = True
        instance = False
        if method_name == 'delete_db_cluster':
            waiter = 'cluster_deleted'
        else:
            waiter = 'cluster_available'
    elif method_name in instance_method_names and 'new_db_instance_identifier' in module.params:
        cluster = False
        instance = True
        if method_name == 'delete_db_instance':
            waiter = 'db_instance_deleted'
        elif method_name == 'stop_db_instance':
            waiter = 'db_instance_stopped'
        else:
            waiter = 'db_instance_available'
    else:
        raise NotImplementedError("method {0} hasn't been added to the list of accepted methods to use a waiter in module_utils/aws/rds.py".format(method_name))

    return Boto3ClientMethod(name=method_name, waiter=waiter, operation_description=readable_op, cluster=cluster, instance=instance)


def get_final_identifier(method_name, module):
    apply_immediately = module.params['apply_immediately']
    if get_rds_method_attribute(method_name, module).cluster:
        identifier = module.params['db_cluster_identifier']
        updated_identifier = module.params['new_db_cluster_identifier']
    elif get_rds_method_attribute(method_name, module).instance:
        identifier = module.params['db_instance_identifier']
        updated_identifier = module.params['new_db_instance_identifier']
    else:
        raise NotImplementedError("method {0} hasn't been added to the list of accepted methods in module_utils/aws/rds.py".format(method_name))
    if not module.check_mode and updated_identifier and apply_immediately:
        identifier = updated_identifier
    return identifier


def handle_errors(module, exception, method_name, parameters):

    if not isinstance(exception, ClientError):
        module.fail_json_aws(exception, msg="Unexpected failure for method {0} with parameters {1}".format(method_name, parameters))

    changed = True
    error_code = exception.response['Error']['Code']
    if method_name == 'modify_db_instance' and error_code == 'InvalidParameterCombination':
        if 'No modifications were requested' in to_text(exception):
            changed = False
        elif 'ModifyDbCluster API' in to_text(exception):
            module.fail_json_aws(exception, msg='It appears you are trying to modify attributes that are managed at the cluster level. Please see rds_cluster')
        else:
            module.fail_json_aws(exception, msg='Unable to {0}'.format(get_rds_method_attribute(method_name, module).operation_description))
    elif method_name == 'promote_read_replica' and error_code == 'InvalidDBInstanceState':
        if 'DB Instance is not a read replica' in to_text(exception):
            changed = False
        else:
            module.fail_json_aws(exception, msg='Unable to {0}'.format(get_rds_method_attribute(method_name, module).operation_description))
    elif method_name == 'create_db_instance' and exception.response['Error']['Code'] == 'InvalidParameterValue':
        accepted_engines = [
            'aurora', 'aurora-mysql', 'aurora-postgresql', 'mariadb', 'mysql', 'oracle-ee', 'oracle-se',
            'oracle-se1', 'oracle-se2', 'postgres', 'sqlserver-ee', 'sqlserver-ex', 'sqlserver-se', 'sqlserver-web'
        ]
        if parameters.get('Engine') not in accepted_engines:
            module.fail_json_aws(exception, msg='DB engine {0} should be one of {1}'.format(parameters.get('Engine'), accepted_engines))
        else:
            module.fail_json_aws(exception, msg='Unable to {0}'.format(get_rds_method_attribute(method_name, module).operation_description))
    else:
        module.fail_json_aws(exception, msg='Unable to {0}'.format(get_rds_method_attribute(method_name, module).operation_description))

    return changed


def call_method(client, module, method_name, parameters):
    result = {}
    changed = True
    if not module.check_mode:
        wait = module.params['wait']
        # TODO: stabilize by adding get_rds_method_attribute(method_name).extra_retry_codes
        method = getattr(client, method_name)
        try:
            if method_name == 'modify_db_instance':
                # check if instance is in an available state first, if possible
                if wait:
                    wait_for_status(client, module, module.params['db_instance_identifier'], method_name)
                result = AWSRetry.jittered_backoff(catch_extra_error_codes=['InvalidDBInstanceState'])(method)(**parameters)
            else:
                result = AWSRetry.jittered_backoff()(method)(**parameters)
        except (BotoCoreError, ClientError) as e:
            changed = handle_errors(module, e, method_name, parameters)

        if wait and changed:
            identifier = get_final_identifier(method_name, module)
            wait_for_status(client, module, identifier, method_name)
    return result, changed


def wait_for_instance_status(client, module, db_instance_id, waiter_name):
    def wait(client, db_instance_id, waiter_name, extra_retry_codes):
        retry = AWSRetry.jittered_backoff(catch_extra_error_codes=extra_retry_codes)
        try:
            waiter = client.get_waiter(waiter_name)
        except ValueError:
            # using a waiter in ansible.module_utils.aws.waiters
            waiter = get_waiter(client, waiter_name)
        waiter.wait(WaiterConfig={'Delay': 60, 'MaxAttempts': 60}, DBInstanceIdentifier=db_instance_id)

    waiter_expected_status = {
        'db_instance_deleted': 'deleted',
        'db_instance_stopped': 'stopped',
    }
    expected_status = waiter_expected_status.get(waiter_name, 'available')
    if expected_status == 'available':
        extra_retry_codes = ['DBInstanceNotFound']
    else:
        extra_retry_codes = []
    for attempt_to_wait in range(0, 10):
        try:
            wait(client, db_instance_id, waiter_name, extra_retry_codes)
            break
        except WaiterError as e:
            # Instance may be renamed and AWSRetry doesn't handle WaiterError
            if e.last_response.get('Error', {}).get('Code') == 'DBInstanceNotFound':
                sleep(10)
                continue
            module.fail_json_aws(e, msg='Error while waiting for DB instance {0} to be {1}'.format(db_instance_id, expected_status))
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg='Unexpected error while waiting for DB instance {0} to be {1}'.format(
                db_instance_id, expected_status)
            )


def wait_for_cluster_status(client, module, db_cluster_id, waiter_name):
    try:
        waiter = get_waiter(client, waiter_name).wait(DBClusterIdentifier=db_cluster_id)
    except WaiterError as e:
        if waiter_name == 'cluster_deleted':
            msg = "Failed to wait for DB cluster {0} to be deleted".format(db_cluster_id)
        else:
            msg = "Failed to wait for DB cluster {0} to be available".format(db_cluster_id)
        module.fail_json_aws(e, msg=msg)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed with an unexpected error while waiting for the DB cluster {0}".format(db_cluster_id))


def wait_for_status(client, module, identifier, method_name):
    waiter_name = get_rds_method_attribute(method_name, module).waiter
    if get_rds_method_attribute(method_name, module).cluster:
        wait_for_cluster_status(client, module, identifier, waiter_name)
    elif get_rds_method_attribute(method_name, module).instance:
        wait_for_instance_status(client, module, identifier, waiter_name)
    else:
        raise NotImplementedError("method {0} hasn't been added to the whitelist of handled methods".format(method_name))


def get_tags(client, module, cluster_arn):
    try:
        return boto3_tag_list_to_ansible_dict(
            client.list_tags_for_resource(ResourceName=cluster_arn)['TagList']
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe tags")


def arg_spec_to_rds_params(options_dict):
    tags = options_dict.pop('tags')
    has_processor_features = False
    if 'processor_features' in options_dict:
        has_processor_features = True
        processor_features = options_dict.pop('processor_features')
    camel_options = snake_dict_to_camel_dict(options_dict, capitalize_first=True)
    for key in list(camel_options.keys()):
        for old, new in (('Db', 'DB'), ('Iam', 'IAM'), ('Az', 'AZ')):
            if old in key:
                camel_options[key.replace(old, new)] = camel_options.pop(key)
    camel_options['Tags'] = tags
    if has_processor_features:
        camel_options['ProcessorFeatures'] = processor_features
    return camel_options


def ensure_tags(client, module, resource_arn, existing_tags, tags, purge_tags):
    if tags is None:
        return False
    tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, tags, purge_tags)
    changed = bool(tags_to_add or tags_to_remove)
    if tags_to_add:
        call_method(
            client, module, method_name='add_tags_to_resource',
            parameters={'ResourceName': resource_arn, 'Tags': ansible_dict_to_boto3_tag_list(tags_to_add)}
        )
    if tags_to_remove:
        call_method(
            client, module, method_name='remove_tags_from_resource',
            parameters={'ResourceName': resource_arn, 'TagKeys': tags_to_remove}
        )
    return changed
