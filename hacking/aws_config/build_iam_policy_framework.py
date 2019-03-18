# Requires pandas, bs4, html5lib, and lxml
#
# Call script with the output from aws_resource_actions callback, e.g.
# python build_iam_policy_framework.py ['ec2:AuthorizeSecurityGroupEgress', 'ec2:AuthorizeSecurityGroupIngress', 'sts:GetCallerIdentity']
#
# The sample output:
# {
#     "Version": "2012-10-17",
#     "Statement": [
#         {
#             "Sid": "AnsibleEditor0",
#             "Effect": "Allow",
#             "Action": [
#                 "ec2:AuthorizeSecurityGroupEgress",
#                 "ec2:AuthorizeSecurityGroupIngress"
#             ],
#             "Resource": "arn:aws:ec2:${Region}:${Account}:security-group/${SecurityGroupId}"
#         },
#         {
#             "Sid": "AnsibleEditor1",
#             "Effect": "Allow",
#             "Action": [
#                 "sts:GetCallerIdentity"
#             ],
#             "Resource": "*"
#         }
#     ]
# }
#
# Policy troubleshooting:
#    - If there are more actions in the policy than you provided, AWS has documented dependencies for some of your actions and
#      those have been added to the policy.
#    - If there are fewer actions in the policy than you provided, some of your actions are not in the IAM table of actions for
#      that service. For example, the API call s3:DeleteObjects does not actually correlate to the permission needed in a policy.
#      In this case s3:DeleteObject is the permission required to allow both the s3:DeleteObjects action and the s3:DeleteObject action.
#    - The policies output are only as accurate as the AWS documentation. If the policy does not permit the
#      necessary actions, look for undocumented dependencies. For example, redshift:CreateCluster requires ec2:DescribeVpcs,
#      ec2:DescribeSubnets, ec2:DescribeSecurityGroups, and ec2:DescribeInternetGateways, but AWS does not document this.
#

import json
import requests
import sys

missing_dependencies = []
try:
    import pandas as pd
except ImportError:
    missing_dependencies.append('pandas')
try:
    import bs4
except ImportError:
    missing_dependencies.append('bs4')
try:
    import html5lib
except ImportError:
    missing_dependencies.append('html5lib')
try:
    import lxml
except ImportError:
    missing_dependencies.append('lxml')


irregular_service_names = {
    'a4b': 'alexaforbusiness',
    'appstream': 'appstream2.0',
    'acm': 'certificatemanager',
    'acm-pca': 'certificatemanagerprivatecertificateauthority',
    'aws-marketplace-management': 'marketplacemanagementportal',
    'ce': 'costexplorerservice',
    'cognito-identity': 'cognitoidentity',
    'cognito-sync': 'cognitosync',
    'cognito-idp': 'cognitouserpools',
    'cur': 'costandusagereport',
    'dax': 'dynamodbacceleratordax',
    'dlm': 'datalifecyclemanager',
    'dms': 'databasemigrationservice',
    'ds': 'directoryservice',
    'ec2messages': 'messagedeliveryservice',
    'ecr': 'ec2containerregistry',
    'ecs': 'elasticcontainerservice',
    'eks': 'elasticcontainerserviceforkubernetes',
    'efs': 'elasticfilesystem',
    'es': 'elasticsearchservice',
    'events': 'cloudwatchevents',
    'firehose': 'kinesisfirehose',
    'fms': 'firewallmanager',
    'health': 'healthapisandnotifications',
    'importexport': 'importexportdiskservice',
    'iot1click': 'iot1-click',
    'kafka': 'managedstreamingforkafka',
    'kinesisvideo': 'kinesisvideostreams',
    'kms': 'keymanagementservice',
    'license-manager': 'licensemanager',
    'logs': 'cloudwatchlogs',
    'opsworks-cm': 'opsworksconfigurationmanagement',
    'mediaconnect': 'elementalmediaconnect',
    'mediaconvert': 'elementalmediaconvert',
    'medialive': 'elementalmedialive',
    'mediapackage': 'elementalmediapackage',
    'mediastore': 'elementalmediastore',
    'mgh': 'migrationhub',
    'mobiletargeting': 'pinpoint',
    'pi': 'performanceinsights',
    'pricing': 'pricelist',
    'ram': 'resourceaccessmanager',
    'resource-groups': 'resourcegroups',
    'sdb': 'simpledb',
    'servicediscovery': 'cloudmap',
    'serverlessrepo': 'serverlessapplicationrepository',
    'sms': 'servermigrationservice',
    'sms-voice': 'pinpointsmsandvoiceservice',
    'sso-directory': 'ssodirectory',
    'ssm': 'systemsmanager',
    'ssmmessages': 'sessionmanagermessagegatewayservice',
    'states': 'stepfunctions',
    'sts': 'securitytokenservice',
    'swf': 'simpleworkflowservice',
    'tag': 'resourcegrouptaggingapi',
    'transfer': 'transferforsftp',
    'waf-regional': 'wafregional',
    'wam': 'workspacesapplicationmanager',
    'xray': 'x-ray'
}

irregular_service_links = {
    'apigateway': [
        'https://docs.aws.amazon.com/IAM/latest/UserGuide/list_manageamazonapigateway.html'
    ],
    'aws-marketplace': [
        'https://docs.aws.amazon.com/IAM/latest/UserGuide/list_awsmarketplace.html',
        'https://docs.aws.amazon.com/IAM/latest/UserGuide/list_awsmarketplacemeteringservice.html',
        'https://docs.aws.amazon.com/IAM/latest/UserGuide/list_awsprivatemarketplace.html'
    ],
    'discovery': [
        'https://docs.aws.amazon.com/IAM/latest/UserGuide/list_applicationdiscovery.html'
    ],
    'elasticloadbalancing': [
        'https://docs.aws.amazon.com/IAM/latest/UserGuide/list_elasticloadbalancing.html',
        'https://docs.aws.amazon.com/IAM/latest/UserGuide/list_elasticloadbalancingv2.html'
    ],
    'globalaccelerator': [
        'https://docs.aws.amazon.com/IAM/latest/UserGuide/list_globalaccelerator.html'
    ]
}


def get_docs_by_prefix(prefix):
    amazon_link_form = 'https://docs.aws.amazon.com/IAM/latest/UserGuide/list_amazon{0}.html'
    aws_link_form = 'https://docs.aws.amazon.com/IAM/latest/UserGuide/list_aws{0}.html'

    if prefix in irregular_service_links:
        links = irregular_service_links[prefix]
    else:
        if prefix in irregular_service_names:
            prefix = irregular_service_names[prefix]
        links = [amazon_link_form.format(prefix), aws_link_form.format(prefix)]

    return links


def get_html(links):
    html_list = []
    for link in links:
        html = requests.get(link).content
        try:
            parsed_html = pd.read_html(html)
            html_list.append(parsed_html)
        except ValueError as e:
            if 'No tables found' in str(e):
                pass
            else:
                raise e

    return html_list


def get_tables(service):
    links = get_docs_by_prefix(service)
    html_list = get_html(links)
    action_tables = []
    arn_tables = []
    for df_list in html_list:
        for df in df_list:
            table = json.loads(df.to_json(orient='split'))
            table_data = table['data'][0]
            if 'Actions' in table_data and 'Resource Types (*required)' in table_data:
                action_tables.append(table['data'][1::])
            elif 'Resource Types' in table_data and 'ARN' in table_data:
                arn_tables.append(table['data'][1::])

    # Action table indices:
    # 0: Action, 1: Description, 2: Access level, 3: Resource type, 4: Condition keys, 5: Dependent actions
    # ARN tables indices:
    # 0: Resource type, 1: ARN template, 2: Condition keys
    return action_tables, arn_tables


def add_dependent_action(resources, dependency):
    resource, action = dependency.split(':')
    if resource in resources:
        resources[resource].append(action)
    else:
        resources[resource] = [action]
    return resources


def get_dependent_actions(resources):
    for service in dict(resources):
        action_tables, arn_tables = get_tables(service)
        for found_action_table in action_tables:
            for action_stuff in found_action_table:
                if action_stuff is None:
                    continue
                if action_stuff[0] in resources[service] and action_stuff[5]:
                    dependencies = action_stuff[5].split()
                    if isinstance(dependencies, list):
                        for dependency in dependencies:
                            resources = add_dependent_action(resources, dependency)
                    else:
                        resources = add_dependent_action(resources, dependencies)
    return resources


def get_actions_by_service(resources):
    service_action_dict = {}
    dependencies = {}
    for service in resources:
        action_tables, arn_tables = get_tables(service)

        # Create dict of the resource type to the corresponding ARN
        arn_dict = {}
        for found_arn_table in arn_tables:
            for arn_stuff in found_arn_table:
                arn_dict["{0}*".format(arn_stuff[0])] = arn_stuff[1]

        # Create dict of the action to the corresponding ARN
        action_dict = {}
        for found_action_table in action_tables:
            for action_stuff in found_action_table:
                if action_stuff[0] is None:
                    continue
                if arn_dict.get(action_stuff[3]):
                    action_dict[action_stuff[0]] = arn_dict[action_stuff[3]]
                else:
                    action_dict[action_stuff[0]] = None
        service_action_dict[service] = action_dict
    return service_action_dict


def get_resource_arns(aws_actions, action_dict):
    resource_arns = {}
    for resource_action in aws_actions:
        resource, action = resource_action.split(':')
        if action not in action_dict:
            continue
        if action_dict[action] is None:
            resource = "*"
        else:
            resource = action_dict[action].replace("${Partition}", "aws")
        if resource not in resource_arns:
            resource_arns[resource] = []
        resource_arns[resource].append(resource_action)
    return resource_arns


def get_resources(actions):
    resources = {}
    for action in actions:
        resource, action = action.split(':')
        if resource not in resources:
            resources[resource] = []
        resources[resource].append(action)
    return resources


def combine_arn_actions(resources, service_action_arn_dict):
    arn_actions = {}
    for service in service_action_arn_dict:
        service_arn_actions = get_resource_arns(aws_actions, service_action_arn_dict[service])
        for resource in service_arn_actions:
            if resource in arn_actions:
                arn_actions[resource].extend(service_arn_actions[resource])
            else:
                arn_actions[resource] = service_arn_actions[resource]
    return arn_actions


def combine_actions_and_dependent_actions(resources):
    aws_actions = []
    for resource in resources:
        for action in resources[resource]:
            aws_actions.append('{0}:{1}'.format(resource, action))
    return set(aws_actions)


def get_actions_restricted_by_arn(aws_actions):
    resources = get_resources(aws_actions)
    resources = get_dependent_actions(resources)
    service_action_arn_dict = get_actions_by_service(resources)
    aws_actions = combine_actions_and_dependent_actions(resources)
    return combine_arn_actions(aws_actions, service_action_arn_dict)


def main(aws_actions):
    arn_actions = get_actions_restricted_by_arn(aws_actions)
    statement = []
    for resource_restriction in arn_actions:
        statement.append({
            "Sid": "AnsibleEditor{0}".format(len(statement)),
            "Effect": "Allow",
            "Action": arn_actions[resource_restriction],
            "Resource": resource_restriction
        })

    policy = {"Version": "2012-10-17", "Statement": statement}
    print(json.dumps(policy, indent=4))


if __name__ == '__main__':
    if missing_dependencies:
        sys.exit('Missing Python libraries: {0}'.format(', '.join(missing_dependencies)))
    actions = sys.argv[1:]
    if len(actions) == 1:
        actions = sys.argv[1].split(',')
    aws_actions = [action.strip('[], "\'') for action in actions]
    main(aws_actions)
