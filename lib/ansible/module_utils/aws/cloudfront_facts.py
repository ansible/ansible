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
from functools import partial
import traceback

try:
    import botocore
except ImportError:
    pass


class CloudFrontFactsServiceManager:
    """Handles CloudFront Facts Services"""

    def __init__(self, module):
        self.module = module

        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
            self.client = boto3_conn(module, conn_type='client',
                                     resource='cloudfront', region=region,
                                     endpoint=ec2_url, **aws_connect_kwargs)
        except botocore.exceptions.NoRegionError:
            self.module.fail_json(msg="Region must be specified as a parameter, in AWS_DEFAULT_REGION "
                                  "environment variable or in boto configuration file")
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Can't establish connection - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def get_distribution(self, distribution_id):
        try:
            func = partial(self.client.get_distribution, Id=distribution_id)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error describing distribution - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def get_distribution_config(self, distribution_id):
        try:
            func = partial(self.client.get_distribution_config, Id=distribution_id)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error describing distribution configuration - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def get_origin_access_identity(self, origin_access_identity_id):
        try:
            func = partial(self.client.get_cloud_front_origin_access_identity, Id=origin_access_identity_id)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error describing origin access identity - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def get_origin_access_identity_config(self, origin_access_identity_id):
        try:
            func = partial(self.client.get_cloud_front_origin_access_identity_config, Id=origin_access_identity_id)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error describing origin access identity configuration - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def get_invalidation(self, distribution_id, invalidation_id):
        try:
            func = partial(self.client.get_invalidation, DistributionId=distribution_id, Id=invalidation_id)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error describing invalidation - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def get_streaming_distribution(self, distribution_id):
        try:
            func = partial(self.client.get_streaming_distribution, Id=distribution_id)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error describing streaming distribution - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def get_streaming_distribution_config(self, distribution_id):
        try:
            func = partial(self.client.get_streaming_distribution_config, Id=distribution_id)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error describing streaming distribution - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def list_origin_access_identities(self):
        try:
            func = partial(self.client.list_cloud_front_origin_access_identities)
            origin_access_identity_list = self.paginated_response(func, 'CloudFrontOriginAccessIdentityList')
            if origin_access_identity_list['Quantity'] > 0:
                return origin_access_identity_list['Items']
            return {}
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error listing cloud front origin access identities - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def list_distributions(self, keyed=True):
        try:
            func = partial(self.client.list_distributions)
            distribution_list = self.paginated_response(func, 'DistributionList')
            if distribution_list['Quantity'] == 0:
                return {}
            else:
                distribution_list = distribution_list['Items']
            if not keyed:
                return distribution_list
            return self.keyed_list_helper(distribution_list)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error listing distributions - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def list_distributions_by_web_acl_id(self, web_acl_id):
        try:
            func = partial(self.client.list_distributions_by_web_acl_id, WebAclId=web_acl_id)
            distribution_list = self.paginated_response(func, 'DistributionList')
            if distribution_list['Quantity'] == 0:
                return {}
            else:
                distribution_list = distribution_list['Items']
            return self.keyed_list_helper(distribution_list)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error listing distributions by web acl id - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def list_invalidations(self, distribution_id):
        try:
            func = partial(self.client.list_invalidations, DistributionId=distribution_id)
            invalidation_list = self.paginated_response(func, 'InvalidationList')
            if invalidation_list['Quantity'] > 0:
                return invalidation_list['Items']
            return {}
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error listing invalidations - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def list_streaming_distributions(self, keyed=True):
        try:
            func = partial(self.client.list_streaming_distributions)
            streaming_distribution_list = self.paginated_response(func, 'StreamingDistributionList')
            if streaming_distribution_list['Quantity'] == 0:
                return {}
            else:
                streaming_distribution_list = streaming_distribution_list['Items']
            if not keyed:
                return streaming_distribution_list
            return self.keyed_list_helper(streaming_distribution_list)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error listing streaming distributions - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

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
            self.module.fail_json(msg="Error generating summary of origin access identities - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

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
            self.module.fail_json(msg="Error generating summary of distributions - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
        except Exception as e:
            self.module.fail_json(msg="Error generating summary of distributions - " + str(e),
                                  exception=traceback.format_exc())

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
            self.module.fail_json(msg="Error getting list of invalidation ids - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

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
            self.module.fail_json(msg="Error getting distribution id from domain name - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def get_aliases_from_distribution_id(self, distribution_id):
        aliases = []
        try:
            distributions = self.list_distributions(False)
            for dist in distributions:
                if dist['Id'] == distribution_id and 'Items' in dist['Aliases']:
                    for alias in dist['Aliases']['Items']:
                        aliases.append(alias)
                    break
            return aliases
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error getting list of aliases from distribution_id - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def paginated_response(self, func, result_key=""):
        '''
        Returns expanded response for paginated operations.
        The 'result_key' is used to define the concatenated results that are combined from each paginated response.
        '''
        args = dict()
        results = dict()
        loop = True
        while loop:
            response = func(**args)
            if result_key == "":
                result = response
                result.pop('ResponseMetadata', None)
            else:
                result = response.get(result_key)
            results.update(result)
            args['NextToken'] = response.get('NextToken')
            loop = args['NextToken'] is not None
        return results

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
