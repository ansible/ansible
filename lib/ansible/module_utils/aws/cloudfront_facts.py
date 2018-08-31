# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Willem van Ketwich
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# Author:
#   - Willem van Ketwich <willem@vanketwich.com.au>
#
# Common functionality to be used by the modules:
#   - cloudfront_distribution
#   - cloudfront_invalidation
#   - cloudfront_origin_access_identity


"""
Common cloudfront facts shared between modules
"""

from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict

try:
    import botocore
except ImportError:
    pass


class CloudFrontFactsServiceManager(object):
    """Handles CloudFront Facts Services"""

    def __init__(self, module):
        self.module = module

        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        self.client = boto3_conn(module, conn_type='client',
                                 resource='cloudfront', region=region,
                                 endpoint=ec2_url, **aws_connect_kwargs)

    def get_distribution(self, distribution_id):
        try:
            return self.client.get_distribution(Id=distribution_id)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error describing distribution")

    def get_distribution_config(self, distribution_id):
        try:
            return self.client.get_distribution_config(Id=distribution_id)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error describing distribution configuration")

    def get_origin_access_identity(self, origin_access_identity_id):
        try:
            return self.client.get_cloud_front_origin_access_identity(Id=origin_access_identity_id)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error describing origin access identity")

    def get_origin_access_identity_config(self, origin_access_identity_id):
        try:
            return self.client.get_cloud_front_origin_access_identity_config(Id=origin_access_identity_id)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error describing origin access identity configuration")

    def get_invalidation(self, distribution_id, invalidation_id):
        try:
            return self.client.get_invalidation(DistributionId=distribution_id, Id=invalidation_id)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error describing invalidation")

    def get_streaming_distribution(self, distribution_id):
        try:
            return self.client.get_streaming_distribution(Id=distribution_id)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error describing streaming distribution")

    def get_streaming_distribution_config(self, distribution_id):
        try:
            return self.client.get_streaming_distribution_config(Id=distribution_id)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error describing streaming distribution")

    def list_origin_access_identities(self):
        try:
            paginator = self.client.get_paginator('list_cloud_front_origin_access_identities')
            result = paginator.paginate().build_full_result().get('CloudFrontOriginAccessIdentityList', {})
            return result.get('Items', [])
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error listing cloud front origin access identities")

    def list_distributions(self, keyed=True):
        try:
            paginator = self.client.get_paginator('list_distributions')
            result = paginator.paginate().build_full_result().get('DistributionList', {})
            distribution_list = result.get('Items', [])
            if not keyed:
                return distribution_list
            return self.keyed_list_helper(distribution_list)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error listing distributions")

    def list_distributions_by_web_acl_id(self, web_acl_id):
        try:
            result = self.client.list_distributions_by_web_acl_id(WebAclId=web_acl_id)
            distribution_list = result.get('DistributionList', {}).get('Items', [])
            return self.keyed_list_helper(distribution_list)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error listing distributions by web acl id")

    def list_invalidations(self, distribution_id):
        try:
            paginator = self.client.get_paginator('list_invalidations')
            result = paginator.paginate(DistributionId=distribution_id).build_full_result()
            return result.get('InvalidationList', {}).get('Items', [])
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error listing invalidations")

    def list_streaming_distributions(self, keyed=True):
        try:
            paginator = self.client.get_paginator('list_streaming_distributions')
            result = paginator.paginate().build_full_result()
            streaming_distribution_list = result.get('StreamingDistributionList', {}).get('Items', [])
            if not keyed:
                return streaming_distribution_list
            return self.keyed_list_helper(streaming_distribution_list)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error listing streaming distributions")

    def summary(self):
        summary_dict = {}
        summary_dict.update(self.summary_get_distribution_list(False))
        summary_dict.update(self.summary_get_distribution_list(True))
        summary_dict.update(self.summary_get_origin_access_identity_list())
        return summary_dict

    def summary_get_origin_access_identity_list(self):
        try:
            origin_access_identity_list = {'origin_access_identities': []}
            origin_access_identities = self.list_origin_access_identities()
            for origin_access_identity in origin_access_identities:
                oai_id = origin_access_identity['Id']
                oai_full_response = self.get_origin_access_identity(oai_id)
                oai_summary = {'Id': oai_id, 'ETag': oai_full_response['ETag']}
                origin_access_identity_list['origin_access_identities'].append(oai_summary)
            return origin_access_identity_list
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error generating summary of origin access identities")

    def summary_get_distribution_list(self, streaming=False):
        try:
            list_name = 'streaming_distributions' if streaming else 'distributions'
            key_list = ['Id', 'ARN', 'Status', 'LastModifiedTime', 'DomainName', 'Comment', 'PriceClass', 'Enabled']
            distribution_list = {list_name: []}
            distributions = self.list_streaming_distributions(False) if streaming else self.list_distributions(False)
            for dist in distributions:
                temp_distribution = {}
                for key_name in key_list:
                    temp_distribution[key_name] = dist[key_name]
                temp_distribution['Aliases'] = [alias for alias in dist['Aliases'].get('Items', [])]
                temp_distribution['ETag'] = self.get_etag_from_distribution_id(dist['Id'], streaming)
                if not streaming:
                    temp_distribution['WebACLId'] = dist['WebACLId']
                    invalidation_ids = self.get_list_of_invalidation_ids_from_distribution_id(dist['Id'])
                    if invalidation_ids:
                        temp_distribution['Invalidations'] = invalidation_ids
                resource_tags = self.client.list_tags_for_resource(Resource=dist['ARN'])
                temp_distribution['Tags'] = boto3_tag_list_to_ansible_dict(resource_tags['Tags'].get('Items', []))
                distribution_list[list_name].append(temp_distribution)
            return distribution_list
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error generating summary of distributions")
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error generating summary of distributions")

    def get_etag_from_distribution_id(self, distribution_id, streaming):
        distribution = {}
        if not streaming:
            distribution = self.get_distribution(distribution_id)
        else:
            distribution = self.get_streaming_distribution(distribution_id)
        return distribution['ETag']

    def get_list_of_invalidation_ids_from_distribution_id(self, distribution_id):
        try:
            invalidation_ids = []
            invalidations = self.list_invalidations(distribution_id)
            for invalidation in invalidations:
                invalidation_ids.append(invalidation['Id'])
            return invalidation_ids
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error getting list of invalidation ids")

    def get_distribution_id_from_domain_name(self, domain_name):
        try:
            distribution_id = ""
            distributions = self.list_distributions(False)
            distributions += self.list_streaming_distributions(False)
            for dist in distributions:
                if 'Items' in dist['Aliases']:
                    for alias in dist['Aliases']['Items']:
                        if str(alias).lower() == domain_name.lower():
                            distribution_id = dist['Id']
                            break
            return distribution_id
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error getting distribution id from domain name")

    def get_aliases_from_distribution_id(self, distribution_id):
        try:
            distribution = self.get_distribution(distribution_id)
            return distribution['DistributionConfig']['Aliases'].get('Items', [])
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error getting list of aliases from distribution_id")

    def keyed_list_helper(self, list_to_key):
        keyed_list = dict()
        for item in list_to_key:
            distribution_id = item['Id']
            if 'Items' in item['Aliases']:
                aliases = item['Aliases']['Items']
                for alias in aliases:
                    keyed_list.update({alias: item})
            keyed_list.update({distribution_id: item})
        return keyed_list
