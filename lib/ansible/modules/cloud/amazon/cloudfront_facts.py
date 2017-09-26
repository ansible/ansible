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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cloudfront_facts
short_description: Obtain facts about an AWS CloudFront distribution
description:
  - Gets information about an AWS CloudFront distribution
requirements:
  - boto3 >= 1.0.0
  - python >= 2.6
version_added: "2.3"
author: Willem van Ketwich (@wilvk)
options:
    distribution_id:
        description:
          - The id of the CloudFront distribution. Used with I(distribution), I(distribution_config),
            I(invalidation), I(streaming_distribution), I(streaming_distribution_config), I(list_invalidations).
        required: false
    invalidation_id:
        description:
          - The id of the invalidation to get information about. Used with I(invalidation).
        required: false
    origin_access_identity_id:
        description:
          - The id of the cloudfront origin access identity to get information about.
        required: false
    web_acl_id:
        description:
          - Used with I(list_distributions_by_web_acl_id).
        required: false
    domain_name_alias:
        description:
          - Can be used instead of I(distribution_id) - uses the aliased CNAME for the cloudfront
            distribution to get the distribution id where required.
        required: false
    all_lists:
        description:
          - Get all cloudfront lists that do not require parameters.
        required: false
        default: false
    origin_access_identity:
        description:
          - Get information about an origin access identity. Requires I(origin_access_identity_id)
            to be specified.
        required: false
        default: false
    origin_access_identity_config:
        description:
          - Get the configuration information about an origin access identity. Requires
            I(origin_access_identity_id) to be specified.
        required: false
        default: false
    distribution:
        description:
          - Get information about a distribution. Requires I(distribution_id) or I(domain_name_alias)
            to be specified.
        required: false
        default: false
    distribution_config:
        description:
          - Get the configuration information about a distribution. Requires I(distribution_id)
            or I(domain_name_alias) to be specified.
        required: false
        default: false
    invalidation:
        description:
            - Get information about an invalidation. Requires I(invalidation_id) to be specified.
        required: false
        default: false
    streaming_distribution:
        description:
            - Get information about a specified RTMP distribution. Requires I(distribution_id) or
              I(domain_name_alias) to be specified.
        required: false
        default: false
    streaming_distribution_configuration:
        description:
            - Get the configuration information about a specified RTMP distribution.
              Requires I(distribution_id) or I(domain_name_alias) to be specified.
        required: false
        default: false
    list_origin_access_identities:
        description:
            - Get a list of cloudfront origin access identities. Requires I(origin_access_identity_id) to be set.
        required: false
        default: false
    list_distributions:
        description:
            - Get a list of cloudfront distributions.
        required: false
        default: false
    list_distributions_by_web_acl_id:
        description:
            - Get a list of distributions using web acl id as a filter. Requires I(web_acl_id) to be set.
        required: false
        default: false
    list_invalidations:
        description:
            - Get a list of invalidations. Requires I(distribution_id) or I(domain_name_alias) to be specified.
        required: false
        default: false
    list_streaming_distributions:
        description:
            - Get a list of streaming distributions.
        required: false
        default: false
    summary:
        description:
            - Returns a summary of all distributions, streaming distributions and origin_access_identities.
              This is the default behaviour if no option is selected.
        required: false
        default: false

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Get a summary of distributions
- cloudfront_facts:
    summary: true

# Get information about a distribution
- cloudfront_facts:
    distribution: true
    distribution_id: my-cloudfront-distribution-id

# Get information about a distribution using the CNAME of the cloudfront distribution.
- cloudfront_facts:
    distribution: true
    domain_name_alias: www.my-website.com

# Facts are published in ansible_facts['cloudfront'][<distribution_name>]
- debug:
    msg: "{{ ansible_facts['cloudfront']['my-cloudfront-distribution-id'] }}"

- debug:
    msg: "{{ ansible_facts['cloudfront']['www.my-website.com'] }}"

# Get all information about an invalidation for a distribution.
- cloudfront_facts:
    invalidation: true
    distribution_id: my-cloudfront-distribution-id
    invalidation_id: my-cloudfront-invalidation-id

# Get all information about a cloudfront origin access identity.
- cloudfront_facts:
    origin_access_identity: true
    origin_access_identity_id: my-cloudfront-origin-access-identity-id

# Get all information about lists not requiring parameters (ie. list_origin_access_identities, list_distributions, list_streaming_distributions)
- cloudfront_facts:
    origin_access_identity: true
    origin_access_identity_id: my-cloudfront-origin-access-identity-id

# Get all information about lists not requiring parameters (ie. list_origin_access_identities, list_distributions, list_streaming_distributions)
- cloudfront_facts:
    all_lists: true
'''

RETURN = '''
origin_access_identity:
    description: Describes the origin access identity information. Requires I(origin_access_identity_id) to be set.
    returned: only if I(origin_access_identity) is true
    type: dict
origin_access_identity_configuration:
    description: Describes the origin access identity information configuration information. Requires I(origin_access_identity_id) to be set.
    returned: only if I(origin_access_identity_configuration) is true
    type: dict
distribution:
    description: >
      Facts about a cloudfront distribution. Requires I(distribution_id) or I(domain_name_alias)
      to be specified. Requires I(origin_access_identity_id) to be set.
    returned: only if distribution is true
    type: dict
distribution_config:
    description: >
      Facts about a cloudfront distribution's config. Requires I(distribution_id) or I(domain_name_alias)
      to be specified.
    returned: only if I(distribution_config) is true
    type: dict
invalidation:
    description: >
      Describes the invalidation information for the distribution. Requires
      I(invalidation_id) to be specified and either I(distribution_id) or I(domain_name_alias.)
    returned: only if invalidation is true
    type: dict
streaming_distribution:
    description: >
      Describes the streaming information for the distribution. Requires
      I(distribution_id) or I(domain_name_alias) to be specified.
    returned: only if I(streaming_distribution) is true
    type: dict
streaming_distribution_configuration:
    description: >
      Describes the streaming configuration information for the distribution.
      Requires I(distribution_id) or I(domain_name_alias) to be specified.
    returned: only if I(streaming_distribution_configuration) is true
    type: dict
summary:
    description: Gives a summary of distributions, streaming distributions and origin access identities.
    returned: as default or if summary is true
    type: dict
'''

from ansible.module_utils.ec2 import ec2_argument_spec, HAS_BOTO3
from ansible.module_utils.aws.cloudfront_facts import CloudFrontFactsServiceManager
from ansible.module_utils.basic import AnsibleModule


def set_facts_for_distribution_id_and_alias(details, facts, distribution_id, aliases):
    facts[distribution_id].update(details)
    for alias in aliases:
        facts[alias].update(details)
    return facts


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        distribution_id=dict(required=False, type='str'),
        invalidation_id=dict(required=False, type='str'),
        origin_access_identity_id=dict(required=False, type='str'),
        domain_name_alias=dict(required=False, type='str'),
        all_lists=dict(required=False, default=False, type='bool'),
        distribution=dict(required=False, default=False, type='bool'),
        distribution_config=dict(required=False, default=False, type='bool'),
        origin_access_identity=dict(required=False, default=False, type='bool'),
        origin_access_identity_config=dict(required=False, default=False, type='bool'),
        invalidation=dict(required=False, default=False, type='bool'),
        streaming_distribution=dict(required=False, default=False, type='bool'),
        streaming_distribution_config=dict(required=False, default=False, type='bool'),
        list_origin_access_identities=dict(required=False, default=False, type='bool'),
        list_distributions=dict(required=False, default=False, type='bool'),
        list_distributions_by_web_acl_id=dict(required=False, default=False, type='bool'),
        list_invalidations=dict(required=False, default=False, type='bool'),
        list_streaming_distributions=dict(required=False, default=False, type='bool'),
        summary=dict(required=False, default=False, type='bool')
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    service_mgr = CloudFrontFactsServiceManager(module)

    distribution_id = module.params.get('distribution_id')
    invalidation_id = module.params.get('invalidation_id')
    origin_access_identity_id = module.params.get('origin_access_identity_id')
    web_acl_id = module.params.get('web_acl_id')
    domain_name_alias = module.params.get('domain_name_alias')
    all_lists = module.params.get('all_lists')
    distribution = module.params.get('distribution')
    distribution_config = module.params.get('distribution_config')
    origin_access_identity = module.params.get('origin_access_identity')
    origin_access_identity_config = module.params.get('origin_access_identity_config')
    invalidation = module.params.get('invalidation')
    streaming_distribution = module.params.get('streaming_distribution')
    streaming_distribution_config = module.params.get('streaming_distribution_config')
    list_origin_access_identities = module.params.get('list_origin_access_identities')
    list_distributions = module.params.get('list_distributions')
    list_distributions_by_web_acl_id = module.params.get('list_distributions_by_web_acl_id')
    list_invalidations = module.params.get('list_invalidations')
    list_streaming_distributions = module.params.get('list_streaming_distributions')
    summary = module.params.get('summary')

    aliases = []
    result = {'cloudfront': {}}
    facts = {}

    require_distribution_id = (distribution or distribution_config or invalidation or streaming_distribution or streaming_distribution_config or
                               list_invalidations)

    # set default to summary if no option specified
    summary = summary or not (distribution or distribution_config or origin_access_identity or origin_access_identity_config or invalidation or
                              streaming_distribution or streaming_distribution_config or list_origin_access_identities or
                              list_distributions_by_web_acl_id or list_invalidations or list_streaming_distributions or list_distributions)

    # validations
    if require_distribution_id and distribution_id is None and domain_name_alias is None:
        module.fail_json(msg='Error distribution_id or domain_name_alias have not been specified.')
    if (invalidation and invalidation_id is None):
        module.fail_json(msg='Error invalidation_id has not been specified.')
    if (origin_access_identity or origin_access_identity_config) and origin_access_identity_id is None:
        module.fail_json(msg='Error origin_access_identity_id has not been specified.')
    if list_distributions_by_web_acl_id and web_acl_id is None:
        module.fail_json(msg='Error web_acl_id has not been specified.')

    # get distribution id from domain name alias
    if require_distribution_id and distribution_id is None:
        distribution_id = service_mgr.get_distribution_id_from_domain_name(domain_name_alias)
        if not distribution_id:
            module.fail_json(msg='Error unable to source a distribution id from domain_name_alias')

    # set appropriate cloudfront id
    if distribution_id and not list_invalidations:
        facts = {distribution_id: {}}
        aliases = service_mgr.get_aliases_from_distribution_id(distribution_id)
        for alias in aliases:
            facts.update({alias: {}})
        if invalidation_id:
            facts.update({invalidation_id: {}})
    elif distribution_id and list_invalidations:
        facts = {distribution_id: {}}
        aliases = service_mgr.get_aliases_from_distribution_id(distribution_id)
        for alias in aliases:
            facts.update({alias: {}})
    elif origin_access_identity_id:
        facts = {origin_access_identity_id: {}}
    elif web_acl_id:
        facts = {web_acl_id: {}}

    # get details based on options
    if distribution:
        facts_to_set = service_mgr.get_distribution(distribution_id)
    if distribution_config:
        facts_to_set = service_mgr.get_distribution_config(distribution_id)
    if origin_access_identity:
        facts[origin_access_identity_id].update(service_mgr.get_origin_access_identity(origin_access_identity_id))
    if origin_access_identity_config:
        facts[origin_access_identity_id].update(service_mgr.get_origin_access_identity_config(origin_access_identity_id))
    if invalidation:
        facts_to_set = service_mgr.get_invalidation(distribution_id, invalidation_id)
        facts[invalidation_id].update(facts_to_set)
    if streaming_distribution:
        facts_to_set = service_mgr.get_streaming_distribution(distribution_id)
    if streaming_distribution_config:
        facts_to_set = service_mgr.get_streaming_distribution_config(distribution_id)
    if list_invalidations:
        facts_to_set = {'invalidations': service_mgr.list_invalidations(distribution_id)}
    if 'facts_to_set' in vars():
        facts = set_facts_for_distribution_id_and_alias(facts_to_set, facts, distribution_id, aliases)

    # get list based on options
    if all_lists or list_origin_access_identities:
        facts['origin_access_identities'] = service_mgr.list_origin_access_identities()
    if all_lists or list_distributions:
        facts['distributions'] = service_mgr.list_distributions()
    if all_lists or list_streaming_distributions:
        facts['streaming_distributions'] = service_mgr.list_streaming_distributions()
    if list_distributions_by_web_acl_id:
        facts['distributions_by_web_acl_id'] = service_mgr.list_distributions_by_web_acl_id(web_acl_id)
    if list_invalidations:
        facts['invalidations'] = service_mgr.list_invalidations(distribution_id)

    # default summary option
    if summary:
        facts['summary'] = service_mgr.summary()

    result['changed'] = False
    result['cloudfront'].update(facts)
    module.exit_json(msg="Retrieved cloudfront facts.", ansible_facts=result)


if __name__ == '__main__':
    main()
