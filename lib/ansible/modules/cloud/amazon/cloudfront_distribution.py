#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---

module: cloudfront_distribution

short_description: create, update and delete aws cloudfront distributions.

description:
    - Allows for easy creation, updating and deletion of CloudFront distributions.

requirements:
  - boto3 >= 1.0.0
  - python >= 2.6

version_added: "2.5"

author:
  - Willem van Ketwich (@wilvk)
  - Will Thames (@willthames)

extends_documentation_fragment:
  - aws
  - ec2

options:

    state:
      description:
        - The desired state of the distribution
          present - creates a new distribution or updates an existing distribution.
          absent - deletes an existing distribution.
      choices: ['present', 'absent']
      default: 'present'

    distribution_id:
      description:
        - The id of the cloudfront distribution. This parameter can be exchanged with I(alias) or I(caller_reference) and is used in conjunction with I(e_tag).

    e_tag:
      description:
        - A unique identifier of a modified or existing distribution. Used in conjunction with I(distribution_id).
          Is determined automatically if not specified.

    caller_reference:
      description:
        - A unique identifier for creating and updating cloudfront distributions. Each caller reference must be unique across all distributions. e.g. a caller
          reference used in a web distribution cannot be reused in a streaming distribution. This parameter can be used instead of I(distribution_id)
          to reference an existing distribution. If not specified, this defaults to a datetime stamp of the format
          'YYYY-MM-DDTHH:MM:SS.ffffff'.

    tags:
      description:
        - Should be input as a dict() of key-value pairs.
          Note that numeric keys or values must be wrapped in quotes. e.g. "Priority:" '1'

    purge_tags:
      description:
        - Specifies whether existing tags will be removed before adding new tags. When I(purge_tags=yes), existing tags are removed and I(tags) are added, if
          specified. If no tags are specified, it removes all existing tags for the distribution. When I(purge_tags=no), existing tags are kept and I(tags)
          are added, if specified.
      default: 'no'
      type: bool

    alias:
      description:
        - The name of an alias (CNAME) that is used in a distribution. This is used to effectively reference a distribution by its alias as an alias can only
          be used by one distribution per AWS account. This variable avoids having to provide the I(distribution_id) as well as
          the I(e_tag), or I(caller_reference) of an existing distribution.

    aliases:
      description:
        - A I(list[]) of domain name aliases (CNAMEs) as strings to be used for the distribution. Each alias must be unique across all distribution for the AWS
          account.

    purge_aliases:
      description:
        - Specifies whether existing aliases will be removed before adding new aliases. When I(purge_aliases=yes), existing aliases are removed and I(aliases)
          are added.
      default: 'no'
      type: bool

    default_root_object:
      description:
        - A config element that specifies the path to request when the user requests the origin. e.g. if specified as 'index.html', this maps to
          www.example.com/index.html when www.example.com is called by the user. This prevents the entire distribution origin from being exposed at the root.

    default_origin_domain_name:
      description:
        - The domain name to use for an origin if no I(origins) have been specified. Should only be used on a first run of generating a distribution and not on
          subsequent runs. Should not be used in conjunction with I(distribution_id), I(caller_reference) or I(alias).

    default_origin_path:
      description:
        - The default origin path to specify for an origin if no I(origins) have been specified. Defaults to empty if not specified.

    origins:
      description:
        - A config element that is a I(list[]) of complex origin objects to be specified for the distribution. Used for creating and updating distributions.
          Each origin item comprises the attributes
            I(id)
            I(domain_name) (defaults to default_origin_domain_name if not specified)
            I(origin_path) (defaults to default_origin_path if not specified)
            I(custom_headers[])
              I(header_name)
              I(header_value)
            I(s3_origin_access_identity_enabled)
            I(custom_origin_config)
              I(http_port)
              I(https_port)
              I(origin_protocol_policy)
              I(origin_ssl_protocols[])
              I(origin_read_timeout)
              I(origin_keepalive_timeout)

    purge_origins:
      description: Whether to remove any origins that aren't listed in I(origins)
      default: false

    default_cache_behavior:
      description:
        - A config element that is a complex object specifying the default cache behavior of the distribution. If not specified, the I(target_origin_id) is
          defined as the I(target_origin_id) of the first valid I(cache_behavior) in I(cache_behaviors) with defaults.
          The default cache behavior comprises the attributes
            I(target_origin_id)
            I(forwarded_values)
              I(query_string)
              I(cookies)
                I(forward)
                I(whitelisted_names)
              I(headers[])
              I(query_string_cache_keys[])
              I(trusted_signers)
                I(enabled)
                I(items[])
              I(viewer_protocol_policy)
              I(min_ttl)
              I(allowed_methods)
                I(items[])
                I(cached_methods[])
              I(smooth_streaming)
              I(default_ttl)
              I(max_ttl)
              I(compress)
              I(lambda_function_associations[])
                I(lambda_function_arn)
                I(event_type)

    cache_behaviors:
      description:
        - A config element that is a I(list[]) of complex cache behavior objects to be specified for the distribution. The order
          of the list is preserved across runs unless C(purge_cache_behavior) is enabled.
          Each cache behavior comprises the attributes
            I(path_pattern)
            I(target_origin_id)
            I(forwarded_values)
              I(query_string)
              I(cookies)
              I(forward)
              I(whitelisted_names)
              I(headers[])
              I(query_string_cache_keys[])
            I(trusted_signers)
              I(enabled)
              I(items[])
            I(viewer_protocol_policy)
            I(min_ttl)
            I(allowed_methods)
              I(items[])
              I(cached_methods[])
            I(smooth_streaming)
            I(default_ttl)
            I(max_ttl)
            I(compress)
            I(lambda_function_associations[])

    purge_cache_behaviors:
      description: Whether to remove any cache behaviors that aren't listed in I(cache_behaviors). This switch
        also allows the reordering of cache_behaviors.
      default: false

    custom_error_responses:
      description:
        - A config element that is a I(list[]) of complex custom error responses to be specified for the distribution. This attribute configures custom http
          error messages returned to the user.
          Each custom error response object comprises the attributes
            I(error_code)
            I(reponse_page_path)
            I(response_code)
            I(error_caching_min_ttl)

    purge_custom_error_responses:
      description: Whether to remove any custom error responses that aren't listed in I(custom_error_responses)
      default: false

    comment:
      description:
        - A comment that describes the cloudfront distribution. If not specified, it defaults to a
          generic message that it has been created with Ansible, and a datetime stamp.

    logging:
      description:
        - A config element that is a complex object that defines logging for the distribution.
          The logging object comprises the attributes
            I(enabled)
            I(include_cookies)
            I(bucket)
            I(prefix)

    price_class:
      description:
        - A string that specifies the pricing class of the distribution. As per
          U(https://aws.amazon.com/cloudfront/pricing/)
            I(price_class=PriceClass_100) consists of the areas
              United States
              Canada
              Europe
            I(price_class=PriceClass_200) consists of the areas
              United States
              Canada
              Europe
              Hong Kong, Philippines, S. Korea, Singapore & Taiwan
              Japan
              India
            I(price_class=PriceClass_All) consists of the areas
              United States
              Canada
              Europe
              Hong Kong, Philippines, S. Korea, Singapore & Taiwan
              Japan
              India
              South America
              Australia
      choices: ['PriceClass_100', 'PriceClass_200', 'PriceClass_All']
      default: aws defaults this to 'PriceClass_All'

    enabled:
      description:
        - A boolean value that specifies whether the distribution is enabled or disabled.
      default: 'yes'
      type: bool

    viewer_certificate:
      description:
        - A config element that is a complex object that specifies the encryption details of the distribution.
          Comprises the following attributes
            I(cloudfront_default_certificate)
            I(iam_certificate_id)
            I(acm_certificate_arn)
            I(ssl_support_method)
            I(minimum_protocol_version)
            I(certificate)
            I(certificate_source)

    restrictions:
      description:
        - A config element that is a complex object that describes how a distribution should restrict it's content.
          The restriction object comprises the following attributes
            I(geo_restriction)
              I(restriction_type)
              I(items[])

    web_acl_id:
      description:
        - The id of a Web Application Firewall (WAF) Access Control List (ACL).

    http_version:
      description:
        - The version of the http protocol to use for the distribution.
      choices: [ 'http1.1', 'http2' ]
      default: aws defaults this to 'http2'

    ipv6_enabled:
      description:
        - Determines whether IPv6 support is enabled or not.
      type: bool
      default: 'no'

    wait:
      description:
        - Specifies whether the module waits until the distribution has completed processing the creation or update.
      type: bool
      default: 'no'

    wait_timeout:
      description:
        - Specifies the duration in seconds to wait for a timeout of a cloudfront create or update. Defaults to 1800 seconds (30 minutes).
      default: 1800

'''

EXAMPLES = '''

# create a basic distribution with defaults and tags

- cloudfront_distribution:
    state: present
    default_origin_domain_name: www.my-cloudfront-origin.com
    tags:
      Name: example distribution
      Project: example project
      Priority: '1'

# update a distribution comment by distribution_id

- cloudfront_distribution:
    state: present
    distribution_id: E1RP5A2MJ8073O
    comment: modified by ansible cloudfront.py

# update a distribution comment by caller_reference

- cloudfront_distribution:
    state: present
    caller_reference: my cloudfront distribution 001
    comment: modified by ansible cloudfront.py

# update a distribution's aliases and comment using the distribution_id as a reference

- cloudfront_distribution:
    state: present
    distribution_id: E1RP5A2MJ8073O
    comment: modified by cloudfront.py again
    aliases: [ 'www.my-distribution-source.com', 'zzz.aaa.io' ]

# update a distribution's aliases and comment using an alias as a reference

- cloudfront_distribution:
    state: present
    caller_reference: my test distribution
    comment: modified by cloudfront.py again
    aliases:
      - www.my-distribution-source.com
      - zzz.aaa.io

# update a distribution's comment and aliases and tags and remove existing tags

- cloudfront_distribution:
    state: present
    distribution_id: E15BU8SDCGSG57
    comment: modified by cloudfront.py again
    aliases:
      - tested.com
    tags:
      Project: distribution 1.2
    purge_tags: yes

# create a distribution with an origin, logging and default cache behavior

- cloudfront_distribution:
    state: present
    caller_reference: unique test distribution id
    origins:
        - id: 'my test origin-000111'
          domain_name: www.example.com
          origin_path: /production
          custom_headers:
            - header_name: MyCustomHeaderName
              header_value: MyCustomHeaderValue
    default_cache_behavior:
      target_origin_id: 'my test origin-000111'
      forwarded_values:
        query_string: true
        cookies:
          forward: all
        headers:
         - '*'
      viewer_protocol_policy: allow-all
      smooth_streaming: true
      compress: true
      allowed_methods:
        items:
          - GET
          - HEAD
        cached_methods:
          - GET
          - HEAD
    logging:
      enabled: true
      include_cookies: false
      bucket: mylogbucket.s3.amazonaws.com
      prefix: myprefix/
    enabled: false
    comment: this is a cloudfront distribution with logging

# delete a distribution

- cloudfront_distribution:
    state: absent
    caller_reference: replaceable distribution
'''

RETURN = '''
active_trusted_signers:
  description: Key pair IDs that CloudFront is aware of for each trusted signer
  returned: always
  type: complex
  contains:
    enabled:
      description: Whether trusted signers are in use
      returned: always
      type: bool
      sample: false
    quantity:
      description: Number of trusted signers
      returned: always
      type: int
      sample: 1
    items:
      description: Number of trusted signers
      returned: when there are trusted signers
      type: list
      sample:
      - key_pair_id
aliases:
  description: Aliases that refer to the distribution
  returned: always
  type: complex
  contains:
    items:
      description: List of aliases
      returned: always
      type: list
      sample:
      - test.example.com
    quantity:
      description: Number of aliases
      returned: always
      type: int
      sample: 1
arn:
  description: Amazon Resource Name of the distribution
  returned: always
  type: string
  sample: arn:aws:cloudfront::123456789012:distribution/E1234ABCDEFGHI
cache_behaviors:
  description: Cloudfront cache behaviors
  returned: always
  type: complex
  contains:
    items:
      description: List of cache behaviors
      returned: always
      type: complex
      contains:
        allowed_methods:
          description: Methods allowed by the cache behavior
          returned: always
          type: complex
          contains:
            cached_methods:
              description: Methods cached by the cache behavior
              returned: always
              type: complex
              contains:
                items:
                  description: List of cached methods
                  returned: always
                  type: list
                  sample:
                  - HEAD
                  - GET
                quantity:
                  description: Count of cached methods
                  returned: always
                  type: int
                  sample: 2
            items:
              description: List of methods allowed by the cache behavior
              returned: always
              type: list
              sample:
              - HEAD
              - GET
            quantity:
              description: Count of methods allowed by the cache behavior
              returned: always
              type: int
              sample: 2
        compress:
          description: Whether compression is turned on for the cache behavior
          returned: always
          type: bool
          sample: false
        default_ttl:
          description: Default Time to Live of the cache behavior
          returned: always
          type: int
          sample: 86400
        forwarded_values:
          description: Values forwarded to the origin for this cache behavior
          returned: always
          type: complex
          contains:
            cookies:
              description: Cookies to forward to the origin
              returned: always
              type: complex
              contains:
                forward:
                  description: Which cookies to forward to the origin for this cache behavior
                  returned: always
                  type: string
                  sample: none
                whitelisted_names:
                  description: The names of the cookies to forward to the origin for this cache behavior
                  returned: when I(forward) is C(whitelist)
                  type: complex
                  contains:
                    quantity:
                      description: Count of cookies to forward
                      returned: always
                      type: int
                      sample: 1
                    items:
                      description: List of cookies to forward
                      returned: when list is not empty
                      type: list
                      sample: my_cookie
            headers:
              description: Which headers are used to vary on cache retrievals
              returned: always
              type: complex
              contains:
                quantity:
                  description: Count of headers to vary on
                  returned: always
                  type: int
                  sample: 1
                items:
                  description: List of headers to vary on
                  returned: when list is not empty
                  type: list
                  sample:
                  - Host
            query_string:
              description: Whether the query string is used in cache lookups
              returned: always
              type: bool
              sample: false
            query_string_cache_keys:
              description: Which query string keys to use in cache lookups
              returned: always
              type: complex
              contains:
                quantity:
                  description: Count of query string cache keys to use in cache lookups
                  returned: always
                  type: int
                  sample: 1
                items:
                  description: List of query string cache keys to use in cache lookups
                  returned: when list is not empty
                  type: list
                  sample:
        lambda_function_associations:
          description: Lambda function associations for a cache behavior
          returned: always
          type: complex
          contains:
            quantity:
              description: Count of lambda function associations
              returned: always
              type: int
              sample: 1
            items:
              description: List of lambda function associations
              returned: when list is not empty
              type: list
              sample:
              - lambda_function_arn: arn:aws:lambda:123456789012:us-east-1/lambda/lambda-function
                event_type: viewer-response
        max_ttl:
          description: Maximum Time to Live
          returned: always
          type: int
          sample: 31536000
        min_ttl:
          description: Minimum Time to Live
          returned: always
          type: int
          sample: 0
        path_pattern:
          description: Path pattern that determines this cache behavior
          returned: always
          type: string
          sample: /path/to/files/*
        smooth_streaming:
          description: Whether smooth streaming is enabled
          returned: always
          type: bool
          sample: false
        target_origin_id:
          description: Id of origin reference by this cache behavior
          returned: always
          type: string
          sample: origin_abcd
        trusted_signers:
          description: Trusted signers
          returned: always
          type: complex
          contains:
            enabled:
              description: Whether trusted signers are enabled for this cache behavior
              returned: always
              type: bool
              sample: false
            quantity:
              description: Count of trusted signers
              returned: always
              type: int
              sample: 1
        viewer_protocol_policy:
          description: Policy of how to handle http/https
          returned: always
          type: string
          sample: redirect-to-https
    quantity:
      description: Count of cache behaviors
      returned: always
      type: int
      sample: 1

caller_reference:
  description: Idempotency reference given when creating cloudfront distribution
  returned: always
  type: string
  sample: '1484796016700'
comment:
  description: Any comments you want to include about the distribution
  returned: always
  type: string
  sample: 'my first cloudfront distribution'
custom_error_responses:
  description: Custom error responses to use for error handling
  returned: always
  type: complex
  contains:
    items:
      description: List of custom error responses
      returned: always
      type: complex
      contains:
        error_caching_min_ttl:
          description: Mininum time to cache this error response
          returned: always
          type: int
          sample: 300
        error_code:
          description: Origin response code that triggers this error response
          returned: always
          type: int
          sample: 500
        response_code:
          description: Response code to return to the requester
          returned: always
          type: string
          sample: '500'
        response_page_path:
          description: Path that contains the error page to display
          returned: always
          type: string
          sample: /errors/5xx.html
    quantity:
      description: Count of custom error response items
      returned: always
      type: int
      sample: 1
default_cache_behavior:
  description: Default cache behavior
  returned: always
  type: complex
  contains:
    allowed_methods:
      description: Methods allowed by the cache behavior
      returned: always
      type: complex
      contains:
        cached_methods:
          description: Methods cached by the cache behavior
          returned: always
          type: complex
          contains:
            items:
              description: List of cached methods
              returned: always
              type: list
              sample:
              - HEAD
              - GET
            quantity:
              description: Count of cached methods
              returned: always
              type: int
              sample: 2
        items:
          description: List of methods allowed by the cache behavior
          returned: always
          type: list
          sample:
          - HEAD
          - GET
        quantity:
          description: Count of methods allowed by the cache behavior
          returned: always
          type: int
          sample: 2
    compress:
      description: Whether compression is turned on for the cache behavior
      returned: always
      type: bool
      sample: false
    default_ttl:
      description: Default Time to Live of the cache behavior
      returned: always
      type: int
      sample: 86400
    forwarded_values:
      description: Values forwarded to the origin for this cache behavior
      returned: always
      type: complex
      contains:
        cookies:
          description: Cookies to forward to the origin
          returned: always
          type: complex
          contains:
            forward:
              description: Which cookies to forward to the origin for this cache behavior
              returned: always
              type: string
              sample: none
            whitelisted_names:
              description: The names of the cookies to forward to the origin for this cache behavior
              returned: when I(forward) is C(whitelist)
              type: complex
              contains:
                quantity:
                  description: Count of cookies to forward
                  returned: always
                  type: int
                  sample: 1
                items:
                  description: List of cookies to forward
                  returned: when list is not empty
                  type: list
                  sample: my_cookie
        headers:
          description: Which headers are used to vary on cache retrievals
          returned: always
          type: complex
          contains:
            quantity:
              description: Count of headers to vary on
              returned: always
              type: int
              sample: 1
            items:
              description: List of headers to vary on
              returned: when list is not empty
              type: list
              sample:
              - Host
        query_string:
          description: Whether the query string is used in cache lookups
          returned: always
          type: bool
          sample: false
        query_string_cache_keys:
          description: Which query string keys to use in cache lookups
          returned: always
          type: complex
          contains:
            quantity:
              description: Count of query string cache keys to use in cache lookups
              returned: always
              type: int
              sample: 1
            items:
              description: List of query string cache keys to use in cache lookups
              returned: when list is not empty
              type: list
              sample:
    lambda_function_associations:
      description: Lambda function associations for a cache behavior
      returned: always
      type: complex
      contains:
        quantity:
          description: Count of lambda function associations
          returned: always
          type: int
          sample: 1
        items:
          description: List of lambda function associations
          returned: when list is not empty
          type: list
          sample:
          - lambda_function_arn: arn:aws:lambda:123456789012:us-east-1/lambda/lambda-function
            event_type: viewer-response
    max_ttl:
      description: Maximum Time to Live
      returned: always
      type: int
      sample: 31536000
    min_ttl:
      description: Minimum Time to Live
      returned: always
      type: int
      sample: 0
    path_pattern:
      description: Path pattern that determines this cache behavior
      returned: always
      type: string
      sample: /path/to/files/*
    smooth_streaming:
      description: Whether smooth streaming is enabled
      returned: always
      type: bool
      sample: false
    target_origin_id:
      description: Id of origin reference by this cache behavior
      returned: always
      type: string
      sample: origin_abcd
    trusted_signers:
      description: Trusted signers
      returned: always
      type: complex
      contains:
        enabled:
          description: Whether trusted signers are enabled for this cache behavior
          returned: always
          type: bool
          sample: false
        quantity:
          description: Count of trusted signers
          returned: always
          type: int
          sample: 1
    viewer_protocol_policy:
      description: Policy of how to handle http/https
      returned: always
      type: string
      sample: redirect-to-https
default_root_object:
  description: The object that you want CloudFront to request from your origin (for example, index.html)
    when a viewer requests the root URL for your distribution
  returned: always
  type: string
  sample: ''
diff:
  description: Difference between previous configuration and new configuration
  returned: always
  type: dict
  sample: {}
domain_name:
  description: Domain name of cloudfront distribution
  returned: always
  type: string
  sample: d1vz8pzgurxosf.cloudfront.net
enabled:
  description: Whether the cloudfront distribution is enabled or not
  returned: always
  type: bool
  sample: true
http_version:
  description: Version of HTTP supported by the distribution
  returned: always
  type: string
  sample: http2
id:
  description: Cloudfront distribution ID
  returned: always
  type: string
  sample: E123456ABCDEFG
in_progress_invalidation_batches:
  description: The number of invalidation batches currently in progress
  returned: always
  type: int
  sample: 0
is_ipv6_enabled:
  description: Whether IPv6 is enabled
  returned: always
  type: bool
  sample: true
last_modified_time:
  description: Date and time distribution was last modified
  returned: always
  type: string
  sample: '2017-10-13T01:51:12.656000+00:00'
logging:
  description: Logging information
  returned: always
  type: complex
  contains:
    bucket:
      description: S3 bucket logging destination
      returned: always
      type: string
      sample: logs-example-com.s3.amazonaws.com
    enabled:
      description: Whether logging is enabled
      returned: always
      type: bool
      sample: true
    include_cookies:
      description: Whether to log cookies
      returned: always
      type: bool
      sample: false
    prefix:
      description: Prefix added to logging object names
      returned: always
      type: string
      sample: cloudfront/test
origins:
  description: Origins in the cloudfront distribution
  returned: always
  type: complex
  contains:
    items:
      description: List of origins
      returned: always
      type: complex
      contains:
        custom_headers:
          description: Custom headers passed to the origin
          returned: always
          type: complex
          contains:
            quantity:
              description: Count of headers
              returned: always
              type: int
              sample: 1
        custom_origin_config:
          description: Configuration of the origin
          returned: always
          type: complex
          contains:
            http_port:
              description: Port on which HTTP is listening
              returned: always
              type: int
              sample: 80
            https_port:
              description: Port on which HTTPS is listening
              returned: always
              type: int
              sample: 443
            origin_keepalive_timeout:
              description: Keep-alive timeout
              returned: always
              type: int
              sample: 5
            origin_protocol_policy:
              description: Policy of which protocols are supported
              returned: always
              type: string
              sample: https-only
            origin_read_timeout:
              description: Timeout for reads to the origin
              returned: always
              type: int
              sample: 30
            origin_ssl_protocols:
              description: SSL protocols allowed by the origin
              returned: always
              type: complex
              contains:
                items:
                  description: List of SSL protocols
                  returned: always
                  type: list
                  sample:
                  - TLSv1
                  - TLSv1.1
                  - TLSv1.2
                quantity:
                  description: Count of SSL protocols
                  returned: always
                  type: int
                  sample: 3
        domain_name:
          description: Domain name of the origin
          returned: always
          type: string
          sample: test-origin.example.com
        id:
          description: ID of the origin
          returned: always
          type: string
          sample: test-origin.example.com
        origin_path:
          description: Subdirectory to prefix the request from the S3 or HTTP origin
          returned: always
          type: string
          sample: ''
    quantity:
      description: Count of origins
      returned: always
      type: int
      sample: 1
price_class:
  description: Price class of cloudfront distribution
  returned: always
  type: string
  sample: PriceClass_All
restrictions:
  description: Restrictions in use by Cloudfront
  returned: always
  type: complex
  contains:
    geo_restriction:
      description: Controls the countries in which your content is distributed.
      returned: always
      type: complex
      contains:
        quantity:
          description: Count of restrictions
          returned: always
          type: int
          sample: 1
        items:
          description: List of country codes allowed or disallowed
          returned: always
          type: list
          sample: xy
        restriction_type:
          description: Type of restriction
          returned: always
          type: string
          sample: blacklist
status:
  description: Status of the cloudfront distribution
  returned: always
  type: string
  sample: InProgress
tags:
  description: Distribution tags
  returned: always
  type: dict
  sample:
    Hello: World
viewer_certificate:
  description: Certificate used by cloudfront distribution
  returned: always
  type: complex
  contains:
    acm_certificate_arn:
      description: ARN of ACM certificate
      returned: when certificate comes from ACM
      type: string
      sample: arn:aws:acm:us-east-1:123456789012:certificate/abcd1234-1234-1234-abcd-123456abcdef
    certificate:
      description: Reference to certificate
      returned: always
      type: string
      sample: arn:aws:acm:us-east-1:123456789012:certificate/abcd1234-1234-1234-abcd-123456abcdef
    certificate_source:
      description: Where certificate comes from
      returned: always
      type: string
      sample: acm
    minimum_protocol_version:
      description: Minimum SSL/TLS protocol supported by this distribution
      returned: always
      type: string
      sample: TLSv1
    ssl_support_method:
      description: Support for pre-SNI browsers or not
      returned: always
      type: string
      sample: sni-only
web_acl_id:
  description: ID of Web Access Control List (from WAF service)
  returned: always
  type: string
  sample: abcd1234-1234-abcd-abcd-abcd12345678
'''

from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.aws.cloudfront_facts import CloudFrontFactsServiceManager
from ansible.module_utils.ec2 import get_aws_connection_info
from ansible.module_utils.ec2 import ec2_argument_spec, boto3_conn, compare_aws_tags
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, ansible_dict_to_boto3_tag_list
from ansible.module_utils.ec2 import snake_dict_to_camel_dict, boto3_tag_list_to_ansible_dict
import datetime

try:
    from collections import OrderedDict
except ImportError:
    try:
        from ordereddict import OrderedDict
    except ImportError:
        pass  # caught by AnsibleAWSModule (as python 2.6 + boto3 => ordereddict is installed)

try:
    import botocore
except ImportError:
    pass


def change_dict_key_name(dictionary, old_key, new_key):
    if old_key in dictionary:
        dictionary[new_key] = dictionary.get(old_key)
        dictionary.pop(old_key, None)
    return dictionary


def merge_validation_into_config(config, validated_node, node_name):
    if validated_node is not None:
        if isinstance(validated_node, dict):
            config_node = config.get(node_name)
            if config_node is not None:
                config_node_items = list(config_node.items())
            else:
                config_node_items = []
            config[node_name] = dict(config_node_items + list(validated_node.items()))
        if isinstance(validated_node, list):
            config[node_name] = list(set(config.get(node_name) + validated_node))
    return config


def ansible_list_to_cloudfront_list(list_items=None, include_quantity=True):
    if list_items is None:
        list_items = []
    if not isinstance(list_items, list):
        raise ValueError('Expected a list, got a {0} with value {1}'.format(type(list_items).__name__, str(list_items)))
    result = {}
    if include_quantity:
        result['quantity'] = len(list_items)
    if len(list_items) > 0:
        result['items'] = list_items
    return result


def recursive_diff(dict1, dict2):
    left = dict((k, v) for (k, v) in dict1.items() if k not in dict2)
    right = dict((k, v) for (k, v) in dict2.items() if k not in dict1)
    for k in (set(dict1.keys()) & set(dict2.keys())):
        if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
            result = recursive_diff(dict1[k], dict2[k])
            if result:
                left[k] = result[0]
                right[k] = result[1]
        elif dict1[k] != dict2[k]:
            left[k] = dict1[k]
            right[k] = dict2[k]
    if left or right:
        return left, right
    else:
        return None


def create_distribution(client, module, config, tags):
    try:
        if not tags:
            return client.create_distribution(DistributionConfig=config)['Distribution']
        else:
            distribution_config_with_tags = {
                'DistributionConfig': config,
                'Tags': {
                    'Items': tags
                }
            }
            return client.create_distribution_with_tags(DistributionConfigWithTags=distribution_config_with_tags)['Distribution']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Error creating distribution")


def delete_distribution(client, module, distribution):
    try:
        return client.delete_distribution(Id=distribution['Distribution']['Id'], IfMatch=distribution['ETag'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Error deleting distribution %s" % to_native(distribution['Distribution']))


def update_distribution(client, module, config, distribution_id, e_tag):
    try:
        return client.update_distribution(DistributionConfig=config, Id=distribution_id, IfMatch=e_tag)['Distribution']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Error updating distribution to %s" % to_native(config))


def tag_resource(client, module, arn, tags):
    try:
        return client.tag_resource(Resource=arn, Tags=dict(Items=tags))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Error tagging resource")


def untag_resource(client, module, arn, tag_keys):
    try:
        return client.untag_resource(Resource=arn, TagKeys=dict(Items=tag_keys))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Error untagging resource")


def list_tags_for_resource(client, module, arn):
    try:
        response = client.list_tags_for_resource(Resource=arn)
        return boto3_tag_list_to_ansible_dict(response.get('Tags').get('Items'))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Error listing tags for resource")


def update_tags(client, module, existing_tags, valid_tags, purge_tags, arn):
    changed = False
    to_add, to_remove = compare_aws_tags(existing_tags, valid_tags, purge_tags)
    if to_remove:
        untag_resource(client, module, arn, to_remove)
        changed = True
    if to_add:
        tag_resource(client, module, arn, ansible_dict_to_boto3_tag_list(to_add))
        changed = True
    return changed


class CloudFrontValidationManager(object):
    """
    Manages Cloudfront validations
    """

    def __init__(self, module):
        self.__cloudfront_facts_mgr = CloudFrontFactsServiceManager(module)
        self.module = module
        self.__default_distribution_enabled = True
        self.__default_http_port = 80
        self.__default_https_port = 443
        self.__default_ipv6_enabled = False
        self.__default_origin_ssl_protocols = [
            'TLSv1',
            'TLSv1.1',
            'TLSv1.2'
        ]
        self.__default_custom_origin_protocol_policy = 'match-viewer'
        self.__default_custom_origin_read_timeout = 30
        self.__default_custom_origin_keepalive_timeout = 5
        self.__default_datetime_string = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.__default_cache_behavior_min_ttl = 0
        self.__default_cache_behavior_max_ttl = 31536000
        self.__default_cache_behavior_default_ttl = 86400
        self.__default_cache_behavior_compress = False
        self.__default_cache_behavior_viewer_protocol_policy = 'allow-all'
        self.__default_cache_behavior_smooth_streaming = False
        self.__default_cache_behavior_forwarded_values_forward_cookies = 'none'
        self.__default_cache_behavior_forwarded_values_query_string = True
        self.__default_trusted_signers_enabled = False
        self.__valid_price_classes = set([
            'PriceClass_100',
            'PriceClass_200',
            'PriceClass_All'
        ])
        self.__valid_origin_protocol_policies = set([
            'http-only',
            'match-viewer',
            'https-only'
        ])
        self.__valid_origin_ssl_protocols = set([
            'SSLv3',
            'TLSv1',
            'TLSv1.1',
            'TLSv1.2'
        ])
        self.__valid_cookie_forwarding = set([
            'none',
            'whitelist',
            'all'
        ])
        self.__valid_viewer_protocol_policies = set([
            'allow-all',
            'https-only',
            'redirect-to-https'
        ])
        self.__valid_methods = set([
            'GET',
            'HEAD',
            'POST',
            'PUT',
            'PATCH',
            'OPTIONS',
            'DELETE'
        ])
        self.__valid_methods_cached_methods = [
            set([
                'GET',
                'HEAD'
            ]),
            set([
                'GET',
                'HEAD',
                'OPTIONS'
            ])
        ]
        self.__valid_methods_allowed_methods = [
            self.__valid_methods_cached_methods[0],
            self.__valid_methods_cached_methods[1],
            self.__valid_methods
        ]
        self.__valid_lambda_function_association_event_types = set([
            'viewer-request',
            'viewer-response',
            'origin-request',
            'origin-response'
        ])
        self.__valid_viewer_certificate_ssl_support_methods = set([
            'sni-only',
            'vip'
        ])
        self.__valid_viewer_certificate_minimum_protocol_versions = set([
            'SSLv3',
            'TLSv1',
            'TLSv1_2016',
            'TLSv1.1_2016',
            'TLSv1.2_2018'
        ])
        self.__valid_viewer_certificate_certificate_sources = set([
            'cloudfront',
            'iam',
            'acm'
        ])
        self.__valid_http_versions = set([
            'http1.1',
            'http2'
        ])
        self.__s3_bucket_domain_identifier = '.s3.amazonaws.com'

    def add_missing_key(self, dict_object, key_to_set, value_to_set):
        if key_to_set not in dict_object and value_to_set is not None:
            dict_object[key_to_set] = value_to_set
        return dict_object

    def add_key_else_change_dict_key(self, dict_object, old_key, new_key, value_to_set):
        if old_key not in dict_object and value_to_set is not None:
            dict_object[new_key] = value_to_set
        else:
            dict_object = change_dict_key_name(dict_object, old_key, new_key)
        return dict_object

    def add_key_else_validate(self, dict_object, key_name, attribute_name, value_to_set, valid_values, to_aws_list=False):
        if key_name in dict_object:
            self.validate_attribute_with_allowed_values(value_to_set, attribute_name, valid_values)
        else:
            if to_aws_list:
                dict_object[key_name] = ansible_list_to_cloudfront_list(value_to_set)
            elif value_to_set is not None:
                dict_object[key_name] = value_to_set
        return dict_object

    def validate_logging(self, logging):
        try:
            if logging is None:
                return None
            valid_logging = {}
            if logging and not set(['enabled', 'include_cookies', 'bucket', 'prefix']).issubset(logging):
                self.module.fail_json(msg="The logging parameters enabled, include_cookies, bucket and prefix must be specified.")
            valid_logging['include_cookies'] = logging.get('include_cookies')
            valid_logging['enabled'] = logging.get('enabled')
            valid_logging['bucket'] = logging.get('bucket')
            valid_logging['prefix'] = logging.get('prefix')
            return valid_logging
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating distribution logging")

    def validate_is_list(self, list_to_validate, list_name):
        if not isinstance(list_to_validate, list):
            self.module.fail_json(msg='%s is of type %s. Must be a list.' % (list_name, type(list_to_validate).__name__))

    def validate_required_key(self, key_name, full_key_name, dict_object):
        if key_name not in dict_object:
            self.module.fail_json(msg="%s must be specified." % full_key_name)

    def validate_origins(self, client, config, origins, default_origin_domain_name,
                         default_origin_path, create_distribution, purge_origins=False):
        try:
            if origins is None:
                if default_origin_domain_name is None and not create_distribution:
                    if purge_origins:
                        return None
                    else:
                        return ansible_list_to_cloudfront_list(config)
                if default_origin_domain_name is not None:
                    origins = [{
                        'domain_name': default_origin_domain_name,
                        'origin_path': default_origin_path or ''
                    }]
                else:
                    origins = []
            self.validate_is_list(origins, 'origins')
            if not origins and default_origin_domain_name is None and create_distribution:
                self.module.fail_json(msg="Both origins[] and default_origin_domain_name have not been specified. Please specify at least one.")
            all_origins = OrderedDict()
            new_domains = list()
            for origin in config:
                all_origins[origin.get('domain_name')] = origin
            for origin in origins:
                origin = self.validate_origin(client, all_origins.get(origin.get('domain_name'), {}), origin, default_origin_path)
                all_origins[origin['domain_name']] = origin
                new_domains.append(origin['domain_name'])
            if purge_origins:
                for domain in list(all_origins.keys()):
                    if domain not in new_domains:
                        del(all_origins[domain])
            return ansible_list_to_cloudfront_list(list(all_origins.values()))
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating distribution origins")

    def validate_s3_origin_configuration(self, client, existing_config, origin):
        if origin['s3_origin_access_identity_enabled'] and existing_config.get('s3_origin_config', {}).get('origin_access_identity'):
            return existing_config['s3_origin_config']['origin_access_identity']
        if not origin['s3_origin_access_identity_enabled']:
            return None
        try:
            comment = "access-identity-by-ansible-%s-%s" % (origin.get('domain_name'), self.__default_datetime_string)
            cfoai_config = dict(CloudFrontOriginAccessIdentityConfig=dict(CallerReference=self.__default_datetime_string,
                                                                          Comment=comment))
            oai = client.create_cloud_front_origin_access_identity(**cfoai_config)['CloudFrontOriginAccessIdentity']['Id']
        except Exception as e:
                self.module.fail_json_aws(e, msg="Couldn't create Origin Access Identity for id %s" % origin['id'])
        return "origin-access-identity/cloudfront/%s" % oai

    def validate_origin(self, client, existing_config, origin, default_origin_path):
        try:
            origin = self.add_missing_key(origin, 'origin_path', existing_config.get('origin_path', default_origin_path or ''))
            self.validate_required_key('origin_path', 'origins[].origin_path', origin)
            origin = self.add_missing_key(origin, 'id', existing_config.get('id', self.__default_datetime_string))
            if 'custom_headers' in origin and len(origin.get('custom_headers')) > 0:
                for custom_header in origin.get('custom_headers'):
                    if 'header_name' not in custom_header or 'header_value' not in custom_header:
                        self.module.fail_json(msg="Both origins[].custom_headers.header_name and origins[].custom_headers.header_value must be specified.")
                origin['custom_headers'] = ansible_list_to_cloudfront_list(origin.get('custom_headers'))
            else:
                origin['custom_headers'] = ansible_list_to_cloudfront_list()
            if self.__s3_bucket_domain_identifier in origin.get('domain_name').lower():
                if origin.get("s3_origin_access_identity_enabled") is not None:
                    s3_origin_config = self.validate_s3_origin_configuration(client, existing_config, origin)
                    if s3_origin_config:
                        oai = s3_origin_config
                    else:
                        oai = ""
                    origin["s3_origin_config"] = dict(origin_access_identity=oai)
                    del(origin["s3_origin_access_identity_enabled"])
                    if 'custom_origin_config' in origin:
                        self.module.fail_json(msg="s3_origin_access_identity_enabled and custom_origin_config are mutually exclusive")
            else:
                origin = self.add_missing_key(origin, 'custom_origin_config', existing_config.get('custom_origin_config', {}))
                custom_origin_config = origin.get('custom_origin_config')
                custom_origin_config = self.add_key_else_validate(custom_origin_config, 'origin_protocol_policy',
                                                                  'origins[].custom_origin_config.origin_protocol_policy',
                                                                  self.__default_custom_origin_protocol_policy, self.__valid_origin_protocol_policies)
                custom_origin_config = self.add_missing_key(custom_origin_config, 'origin_read_timeout', self.__default_custom_origin_read_timeout)
                custom_origin_config = self.add_missing_key(custom_origin_config, 'origin_keepalive_timeout', self.__default_custom_origin_keepalive_timeout)
                custom_origin_config = self.add_key_else_change_dict_key(custom_origin_config, 'http_port', 'h_t_t_p_port', self.__default_http_port)
                custom_origin_config = self.add_key_else_change_dict_key(custom_origin_config, 'https_port', 'h_t_t_p_s_port', self.__default_https_port)
                if custom_origin_config.get('origin_ssl_protocols', {}).get('items'):
                    custom_origin_config['origin_ssl_protocols'] = custom_origin_config['origin_ssl_protocols']['items']
                if custom_origin_config.get('origin_ssl_protocols'):
                    self.validate_attribute_list_with_allowed_list(custom_origin_config['origin_ssl_protocols'], 'origins[].origin_ssl_protocols',
                                                                   self.__valid_origin_ssl_protocols)
                else:
                    custom_origin_config['origin_ssl_protocols'] = self.__default_origin_ssl_protocols
                custom_origin_config['origin_ssl_protocols'] = ansible_list_to_cloudfront_list(custom_origin_config['origin_ssl_protocols'])
            return origin
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error validating distribution origin")

    def validate_cache_behaviors(self, config, cache_behaviors, valid_origins, purge_cache_behaviors=False):
        try:
            if cache_behaviors is None and valid_origins is not None and purge_cache_behaviors is False:
                return ansible_list_to_cloudfront_list(config)
            all_cache_behaviors = OrderedDict()
            # cache behaviors are order dependent so we don't preserve the existing ordering when purge_cache_behaviors
            # is true (if purge_cache_behaviors is not true, we can't really know the full new order)
            if not purge_cache_behaviors:
                for behavior in config:
                    all_cache_behaviors[behavior['path_pattern']] = behavior
            for cache_behavior in cache_behaviors:
                valid_cache_behavior = self.validate_cache_behavior(all_cache_behaviors.get(cache_behavior.get('path_pattern'), {}),
                                                                    cache_behavior, valid_origins)
                all_cache_behaviors[cache_behavior['path_pattern']] = valid_cache_behavior
            if purge_cache_behaviors:
                for target_origin_id in set(all_cache_behaviors.keys()) - set([cb['path_pattern'] for cb in cache_behaviors]):
                    del(all_cache_behaviors[target_origin_id])
            return ansible_list_to_cloudfront_list(list(all_cache_behaviors.values()))
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating distribution cache behaviors")

    def validate_cache_behavior(self, config, cache_behavior, valid_origins, is_default_cache=False):
        if is_default_cache and cache_behavior is None:
            cache_behavior = {}
        if cache_behavior is None and valid_origins is not None:
            return config
        cache_behavior = self.validate_cache_behavior_first_level_keys(config, cache_behavior, valid_origins, is_default_cache)
        cache_behavior = self.validate_forwarded_values(config, cache_behavior.get('forwarded_values'), cache_behavior)
        cache_behavior = self.validate_allowed_methods(config, cache_behavior.get('allowed_methods'), cache_behavior)
        cache_behavior = self.validate_lambda_function_associations(config, cache_behavior.get('lambda_function_associations'), cache_behavior)
        cache_behavior = self.validate_trusted_signers(config, cache_behavior.get('trusted_signers'), cache_behavior)
        return cache_behavior

    def validate_cache_behavior_first_level_keys(self, config, cache_behavior, valid_origins, is_default_cache):
        try:
            cache_behavior = self.add_key_else_change_dict_key(cache_behavior, 'min_ttl', 'min_t_t_l',
                                                               config.get('min_t_t_l', self.__default_cache_behavior_min_ttl))
            cache_behavior = self.add_key_else_change_dict_key(cache_behavior, 'max_ttl', 'max_t_t_l',
                                                               config.get('max_t_t_l', self.__default_cache_behavior_max_ttl))
            cache_behavior = self.add_key_else_change_dict_key(cache_behavior, 'default_ttl', 'default_t_t_l',
                                                               config.get('default_t_t_l', self.__default_cache_behavior_default_ttl))
            cache_behavior = self.add_missing_key(cache_behavior, 'compress', config.get('compress', self.__default_cache_behavior_compress))
            target_origin_id = cache_behavior.get('target_origin_id', config.get('target_origin_id'))
            if not target_origin_id:
                target_origin_id = self.get_first_origin_id_for_default_cache_behavior(valid_origins)
            if target_origin_id not in [origin['id'] for origin in valid_origins.get('items', [])]:
                if is_default_cache:
                    cache_behavior_name = 'Default cache behavior'
                else:
                    cache_behavior_name = 'Cache behavior for path %s' % cache_behavior['path_pattern']
                self.module.fail_json(msg="%s has target_origin_id pointing to an origin that does not exist." %
                                      cache_behavior_name)
            cache_behavior['target_origin_id'] = target_origin_id
            cache_behavior = self.add_key_else_validate(cache_behavior, 'viewer_protocol_policy', 'cache_behavior.viewer_protocol_policy',
                                                        config.get('viewer_protocol_policy',
                                                                   self.__default_cache_behavior_viewer_protocol_policy),
                                                        self.__valid_viewer_protocol_policies)
            cache_behavior = self.add_missing_key(cache_behavior, 'smooth_streaming',
                                                  config.get('smooth_streaming', self.__default_cache_behavior_smooth_streaming))
            return cache_behavior
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating distribution cache behavior first level keys")

    def validate_forwarded_values(self, config, forwarded_values, cache_behavior):
        try:
            if not forwarded_values:
                forwarded_values = dict()
            existing_config = config.get('forwarded_values', {})
            headers = forwarded_values.get('headers', existing_config.get('headers', {}).get('items'))
            if headers:
                headers.sort()
            forwarded_values['headers'] = ansible_list_to_cloudfront_list(headers)
            if 'cookies' not in forwarded_values:
                forward = existing_config.get('cookies', {}).get('forward', self.__default_cache_behavior_forwarded_values_forward_cookies)
                forwarded_values['cookies'] = {'forward': forward}
            else:
                existing_whitelist = existing_config.get('cookies', {}).get('whitelisted_names', {}).get('items')
                whitelist = forwarded_values.get('cookies').get('whitelisted_names', existing_whitelist)
                if whitelist:
                    self.validate_is_list(whitelist, 'forwarded_values.whitelisted_names')
                    forwarded_values['cookies']['whitelisted_names'] = ansible_list_to_cloudfront_list(whitelist)
                cookie_forwarding = forwarded_values.get('cookies').get('forward', existing_config.get('cookies', {}).get('forward'))
                self.validate_attribute_with_allowed_values(cookie_forwarding, 'cache_behavior.forwarded_values.cookies.forward',
                                                            self.__valid_cookie_forwarding)
                forwarded_values['cookies']['forward'] = cookie_forwarding
            query_string_cache_keys = forwarded_values.get('query_string_cache_keys', existing_config.get('query_string_cache_keys', {}).get('items', []))
            self.validate_is_list(query_string_cache_keys, 'forwarded_values.query_string_cache_keys')
            forwarded_values['query_string_cache_keys'] = ansible_list_to_cloudfront_list(query_string_cache_keys)
            forwarded_values = self.add_missing_key(forwarded_values, 'query_string',
                                                    existing_config.get('query_string', self.__default_cache_behavior_forwarded_values_query_string))
            cache_behavior['forwarded_values'] = forwarded_values
            return cache_behavior
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating forwarded values")

    def validate_lambda_function_associations(self, config, lambda_function_associations, cache_behavior):
        try:
            if lambda_function_associations is not None:
                self.validate_is_list(lambda_function_associations, 'lambda_function_associations')
                for association in lambda_function_associations:
                    association = change_dict_key_name(association, 'lambda_function_arn', 'lambda_function_a_r_n')
                    self.validate_attribute_with_allowed_values(association.get('event_type'), 'cache_behaviors[].lambda_function_associations.event_type',
                                                                self.__valid_lambda_function_association_event_types)
                cache_behavior['lambda_function_associations'] = ansible_list_to_cloudfront_list(lambda_function_associations)
            else:
                if 'lambda_function_associations' in config:
                    cache_behavior['lambda_function_associations'] = config.get('lambda_function_associations')
                else:
                    cache_behavior['lambda_function_associations'] = ansible_list_to_cloudfront_list([])
            return cache_behavior
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating lambda function associations")

    def validate_allowed_methods(self, config, allowed_methods, cache_behavior):
        try:
            if allowed_methods is not None:
                self.validate_required_key('items', 'cache_behavior.allowed_methods.items[]', allowed_methods)
                temp_allowed_items = allowed_methods.get('items')
                self.validate_is_list(temp_allowed_items, 'cache_behavior.allowed_methods.items')
                self.validate_attribute_list_with_allowed_list(temp_allowed_items, 'cache_behavior.allowed_methods.items[]',
                                                               self.__valid_methods_allowed_methods)
                cached_items = allowed_methods.get('cached_methods')
                if 'cached_methods' in allowed_methods:
                    self.validate_is_list(cached_items, 'cache_behavior.allowed_methods.cached_methods')
                    self.validate_attribute_list_with_allowed_list(cached_items, 'cache_behavior.allowed_items.cached_methods[]',
                                                                   self.__valid_methods_cached_methods)
                # we don't care if the order of how cloudfront stores the methods differs - preserving existing
                # order reduces likelihood of making unnecessary changes
                if 'allowed_methods' in config and set(config['allowed_methods']['items']) == set(temp_allowed_items):
                    cache_behavior['allowed_methods'] = config['allowed_methods']
                else:
                    cache_behavior['allowed_methods'] = ansible_list_to_cloudfront_list(temp_allowed_items)

                if cached_items and set(cached_items) == set(config.get('allowed_methods', {}).get('cached_methods', {}).get('items', [])):
                    cache_behavior['allowed_methods']['cached_methods'] = config['allowed_methods']['cached_methods']
                else:
                    cache_behavior['allowed_methods']['cached_methods'] = ansible_list_to_cloudfront_list(cached_items)
            else:
                if 'allowed_methods' in config:
                    cache_behavior['allowed_methods'] = config.get('allowed_methods')
            return cache_behavior
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating allowed methods")

    def validate_trusted_signers(self, config, trusted_signers, cache_behavior):
        try:
            if trusted_signers is None:
                trusted_signers = {}
            if 'items' in trusted_signers:
                valid_trusted_signers = ansible_list_to_cloudfront_list(trusted_signers.get('items'))
            else:
                valid_trusted_signers = dict(quantity=config.get('quantity', 0))
                if 'items' in config:
                    valid_trusted_signers = dict(items=config['items'])
            valid_trusted_signers['enabled'] = trusted_signers.get('enabled', config.get('enabled', self.__default_trusted_signers_enabled))
            cache_behavior['trusted_signers'] = valid_trusted_signers
            return cache_behavior
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating trusted signers")

    def validate_viewer_certificate(self, viewer_certificate):
        try:
            if viewer_certificate is None:
                return None
            if viewer_certificate.get('cloudfront_default_certificate') and viewer_certificate.get('ssl_support_method') is not None:
                self.module.fail_json(msg="viewer_certificate.ssl_support_method should not be specified with viewer_certificate_cloudfront_default" +
                                      "_certificate set to true.")
            self.validate_attribute_with_allowed_values(viewer_certificate.get('ssl_support_method'), 'viewer_certificate.ssl_support_method',
                                                        self.__valid_viewer_certificate_ssl_support_methods)
            self.validate_attribute_with_allowed_values(viewer_certificate.get('minimum_protocol_version'), 'viewer_certificate.minimum_protocol_version',
                                                        self.__valid_viewer_certificate_minimum_protocol_versions)
            self.validate_attribute_with_allowed_values(viewer_certificate.get('certificate_source'), 'viewer_certificate.certificate_source',
                                                        self.__valid_viewer_certificate_certificate_sources)
            viewer_certificate = change_dict_key_name(viewer_certificate, 'cloudfront_default_certificate', 'cloud_front_default_certificate')
            viewer_certificate = change_dict_key_name(viewer_certificate, 'ssl_support_method', 's_s_l_support_method')
            viewer_certificate = change_dict_key_name(viewer_certificate, 'iam_certificate_id', 'i_a_m_certificate_id')
            viewer_certificate = change_dict_key_name(viewer_certificate, 'acm_certificate_arn', 'a_c_m_certificate_arn')
            return viewer_certificate
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating viewer certificate")

    def validate_custom_error_responses(self, config, custom_error_responses, purge_custom_error_responses):
        try:
            if custom_error_responses is None and not purge_custom_error_responses:
                return ansible_list_to_cloudfront_list(config)
            self.validate_is_list(custom_error_responses, 'custom_error_responses')
            result = list()
            existing_responses = dict((response['error_code'], response) for response in custom_error_responses)
            for custom_error_response in custom_error_responses:
                self.validate_required_key('error_code', 'custom_error_responses[].error_code', custom_error_response)
                custom_error_response = change_dict_key_name(custom_error_response, 'error_caching_min_ttl', 'error_caching_min_t_t_l')
                if 'response_code' in custom_error_response:
                    custom_error_response['response_code'] = str(custom_error_response['response_code'])
                if custom_error_response['error_code'] in existing_responses:
                    del(existing_responses[custom_error_response['error_code']])
                result.append(custom_error_response)
            if not purge_custom_error_responses:
                result.extend(existing_responses.values())

            return ansible_list_to_cloudfront_list(result)
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating custom error responses")

    def validate_restrictions(self, config, restrictions, purge_restrictions=False):
        try:
            if restrictions is None:
                if purge_restrictions:
                    return None
                else:
                    return config
            self.validate_required_key('geo_restriction', 'restrictions.geo_restriction', restrictions)
            geo_restriction = restrictions.get('geo_restriction')
            self.validate_required_key('restriction_type', 'restrictions.geo_restriction.restriction_type', geo_restriction)
            existing_restrictions = config.get('geo_restriction', {}).get(geo_restriction['restriction_type'], {}).get('items', [])
            geo_restriction_items = geo_restriction.get('items')
            if not purge_restrictions:
                geo_restriction_items.extend([rest for rest in existing_restrictions if
                                              rest not in geo_restriction_items])
            valid_restrictions = ansible_list_to_cloudfront_list(geo_restriction_items)
            valid_restrictions['restriction_type'] = geo_restriction.get('restriction_type')
            return {'geo_restriction': valid_restrictions}
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating restrictions")

    def validate_distribution_config_parameters(self, config, default_root_object, ipv6_enabled, http_version, web_acl_id):
        try:
            config['default_root_object'] = default_root_object or config.get('default_root_object', '')
            config['is_i_p_v_6_enabled'] = ipv6_enabled or config.get('i_p_v_6_enabled', self.__default_ipv6_enabled)
            if http_version is not None or config.get('http_version'):
                self.validate_attribute_with_allowed_values(http_version, 'http_version', self.__valid_http_versions)
                config['http_version'] = http_version or config.get('http_version')
            if web_acl_id or config.get('web_a_c_l_id'):
                config['web_a_c_l_id'] = web_acl_id or config.get('web_a_c_l_id')
            return config
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating distribution config parameters")

    def validate_common_distribution_parameters(self, config, enabled, aliases, logging, price_class, purge_aliases=False):
        try:
            if config is None:
                config = {}
            if aliases is not None:
                if not purge_aliases:
                    aliases.extend([alias for alias in config.get('aliases', {}).get('items', [])
                                    if alias not in aliases])
                config['aliases'] = ansible_list_to_cloudfront_list(aliases)
            if logging is not None:
                config['logging'] = self.validate_logging(logging)
            config['enabled'] = enabled or config.get('enabled', self.__default_distribution_enabled)
            if price_class is not None:
                self.validate_attribute_with_allowed_values(price_class, 'price_class', self.__valid_price_classes)
                config['price_class'] = price_class
            return config
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating common distribution parameters")

    def validate_comment(self, config, comment):
        config['comment'] = comment or config.get('comment', "Distribution created by Ansible with datetime stamp " + self.__default_datetime_string)
        return config

    def validate_caller_reference(self, caller_reference):
        return caller_reference or self.__default_datetime_string

    def get_first_origin_id_for_default_cache_behavior(self, valid_origins):
        try:
            if valid_origins is not None:
                valid_origins_list = valid_origins.get('items')
                if valid_origins_list is not None and isinstance(valid_origins_list, list) and len(valid_origins_list) > 0:
                    return str(valid_origins_list[0].get('id'))
            self.module.fail_json(msg="There are no valid origins from which to specify a target_origin_id for the default_cache_behavior configuration.")
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error getting first origin_id for default cache behavior")

    def validate_attribute_list_with_allowed_list(self, attribute_list, attribute_list_name, allowed_list):
        try:
            self.validate_is_list(attribute_list, attribute_list_name)
            if (isinstance(allowed_list, list) and set(attribute_list) not in allowed_list or
                    isinstance(allowed_list, set) and not set(allowed_list).issuperset(attribute_list)):
                self.module.fail_json(msg='The attribute list {0} must be one of [{1}]'.format(attribute_list_name, ' '.join(str(a) for a in allowed_list)))
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating attribute list with allowed value list")

    def validate_attribute_with_allowed_values(self, attribute, attribute_name, allowed_list):
        if attribute is not None and attribute not in allowed_list:
            self.module.fail_json(msg='The attribute {0} must be one of [{1}]'.format(attribute_name, ' '.join(str(a) for a in allowed_list)))

    def validate_distribution_from_caller_reference(self, caller_reference):
        try:
            distributions = self.__cloudfront_facts_mgr.list_distributions(False)
            distribution_name = 'Distribution'
            distribution_config_name = 'DistributionConfig'
            distribution_ids = [dist.get('Id') for dist in distributions]
            for distribution_id in distribution_ids:
                config = self.__cloudfront_facts_mgr.get_distribution(distribution_id)
                distribution = config.get(distribution_name)
                if distribution is not None:
                    distribution_config = distribution.get(distribution_config_name)
                    if distribution_config is not None and distribution_config.get('CallerReference') == caller_reference:
                        distribution['DistributionConfig'] = distribution_config
                        return distribution

        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating distribution from caller reference")

    def validate_distribution_from_aliases_caller_reference(self, distribution_id, aliases, caller_reference):
        try:
            if caller_reference is not None:
                return self.validate_distribution_from_caller_reference(caller_reference)
            else:
                if aliases:
                    distribution_id = self.validate_distribution_id_from_alias(aliases)
                if distribution_id:
                    return self.__cloudfront_facts_mgr.get_distribution(distribution_id)
            return None
        except Exception as e:
            self.module.fail_json_aws(e, msg="Error validating distribution_id from alias, aliases and caller reference")

    def validate_distribution_id_from_alias(self, aliases):
        distributions = self.__cloudfront_facts_mgr.list_distributions(False)
        if distributions:
            for distribution in distributions:
                distribution_aliases = distribution.get('Aliases', {}).get('Items', [])
                if set(aliases) & set(distribution_aliases):
                    return distribution['Id']
        return None

    def wait_until_processed(self, client, wait_timeout, distribution_id, caller_reference):
        if distribution_id is None:
            distribution_id = self.validate_distribution_id_from_caller_reference(caller_reference=caller_reference)

        try:
            waiter = client.get_waiter('distribution_deployed')
            attempts = 1 + int(wait_timeout / 60)
            waiter.wait(Id=distribution_id, WaiterConfig={'MaxAttempts': attempts})
        except botocore.exceptions.WaiterError as e:
            self.module.fail_json(msg="Timeout waiting for cloudfront action. Waited for {0} seconds before timeout. "
                                  "Error: {1}".format(to_text(wait_timeout), to_native(e)))

        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error getting distribution {0}".format(distribution_id))


def main():
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
        state=dict(choices=['present', 'absent'], default='present'),
        caller_reference=dict(),
        comment=dict(),
        distribution_id=dict(),
        e_tag=dict(),
        tags=dict(type='dict', default={}),
        purge_tags=dict(type='bool', default=False),
        alias=dict(),
        aliases=dict(type='list', default=[]),
        purge_aliases=dict(type='bool', default=False),
        default_root_object=dict(),
        origins=dict(type='list'),
        purge_origins=dict(type='bool', default=False),
        default_cache_behavior=dict(type='dict'),
        cache_behaviors=dict(type='list'),
        purge_cache_behaviors=dict(type='bool', default=False),
        custom_error_responses=dict(type='list'),
        purge_custom_error_responses=dict(type='bool', default=False),
        logging=dict(type='dict'),
        price_class=dict(),
        enabled=dict(type='bool'),
        viewer_certificate=dict(type='dict'),
        restrictions=dict(type='dict'),
        web_acl_id=dict(),
        http_version=dict(),
        ipv6_enabled=dict(type='bool'),
        default_origin_domain_name=dict(),
        default_origin_path=dict(),
        wait=dict(default=False, type='bool'),
        wait_timeout=dict(default=1800, type='int')
    ))

    result = {}
    changed = True

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        mutually_exclusive=[
            ['distribution_id', 'alias'],
            ['default_origin_domain_name', 'distribution_id'],
            ['default_origin_domain_name', 'alias'],
        ]
    )

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client = boto3_conn(module, conn_type='client', resource='cloudfront', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    validation_mgr = CloudFrontValidationManager(module)

    state = module.params.get('state')
    caller_reference = module.params.get('caller_reference')
    comment = module.params.get('comment')
    e_tag = module.params.get('e_tag')
    tags = module.params.get('tags')
    purge_tags = module.params.get('purge_tags')
    distribution_id = module.params.get('distribution_id')
    alias = module.params.get('alias')
    aliases = module.params.get('aliases')
    purge_aliases = module.params.get('purge_aliases')
    default_root_object = module.params.get('default_root_object')
    origins = module.params.get('origins')
    purge_origins = module.params.get('purge_origins')
    default_cache_behavior = module.params.get('default_cache_behavior')
    cache_behaviors = module.params.get('cache_behaviors')
    purge_cache_behaviors = module.params.get('purge_cache_behaviors')
    custom_error_responses = module.params.get('custom_error_responses')
    purge_custom_error_responses = module.params.get('purge_custom_error_responses')
    logging = module.params.get('logging')
    price_class = module.params.get('price_class')
    enabled = module.params.get('enabled')
    viewer_certificate = module.params.get('viewer_certificate')
    restrictions = module.params.get('restrictions')
    purge_restrictions = module.params.get('purge_restrictions')
    web_acl_id = module.params.get('web_acl_id')
    http_version = module.params.get('http_version')
    ipv6_enabled = module.params.get('ipv6_enabled')
    default_origin_domain_name = module.params.get('default_origin_domain_name')
    default_origin_path = module.params.get('default_origin_path')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    if alias and alias not in aliases:
        aliases.append(alias)

    distribution = validation_mgr.validate_distribution_from_aliases_caller_reference(distribution_id, aliases, caller_reference)

    update = state == 'present' and distribution
    create = state == 'present' and not distribution
    delete = state == 'absent' and distribution

    if not (update or create or delete):
        module.exit_json(changed=False)

    if update or delete:
        config = distribution['Distribution']['DistributionConfig']
        e_tag = distribution['ETag']
        distribution_id = distribution['Distribution']['Id']
    else:
        config = dict()
    if update:
        config = camel_dict_to_snake_dict(config, reversible=True)

    if create or update:
        config = validation_mgr.validate_common_distribution_parameters(config, enabled, aliases, logging, price_class, purge_aliases)
        config = validation_mgr.validate_distribution_config_parameters(config, default_root_object, ipv6_enabled, http_version, web_acl_id)
        config['origins'] = validation_mgr.validate_origins(client, config.get('origins', {}).get('items', []), origins, default_origin_domain_name,
                                                            default_origin_path, create, purge_origins)
        config['cache_behaviors'] = validation_mgr.validate_cache_behaviors(config.get('cache_behaviors', {}).get('items', []),
                                                                            cache_behaviors, config['origins'], purge_cache_behaviors)
        config['default_cache_behavior'] = validation_mgr.validate_cache_behavior(config.get('default_cache_behavior', {}),
                                                                                  default_cache_behavior, config['origins'], True)
        config['custom_error_responses'] = validation_mgr.validate_custom_error_responses(config.get('custom_error_responses', {}).get('items', []),
                                                                                          custom_error_responses, purge_custom_error_responses)
        valid_restrictions = validation_mgr.validate_restrictions(config.get('restrictions', {}), restrictions, purge_restrictions)
        if valid_restrictions:
            config['restrictions'] = valid_restrictions
        valid_viewer_certificate = validation_mgr.validate_viewer_certificate(viewer_certificate)
        config = merge_validation_into_config(config, valid_viewer_certificate, 'viewer_certificate')
        config = validation_mgr.validate_comment(config, comment)
        config = snake_dict_to_camel_dict(config, capitalize_first=True)

    if create:
        config['CallerReference'] = validation_mgr.validate_caller_reference(caller_reference)
        result = create_distribution(client, module, config, ansible_dict_to_boto3_tag_list(tags))
        result = camel_dict_to_snake_dict(result)
        result['tags'] = list_tags_for_resource(client, module, result['arn'])

    if delete:
        if config['Enabled']:
            config['Enabled'] = False
            result = update_distribution(client, module, config, distribution_id, e_tag)
            validation_mgr.wait_until_processed(client, wait_timeout, distribution_id, config.get('CallerReference'))
        distribution = validation_mgr.validate_distribution_from_aliases_caller_reference(distribution_id, aliases, caller_reference)
        # e_tag = distribution['ETag']
        result = delete_distribution(client, module, distribution)

    if update:
        changed = config != distribution['Distribution']['DistributionConfig']
        if changed:
            result = update_distribution(client, module, config, distribution_id, e_tag)
        else:
            result = distribution['Distribution']
        existing_tags = list_tags_for_resource(client, module, result['ARN'])
        distribution['Distribution']['DistributionConfig']['tags'] = existing_tags
        changed |= update_tags(client, module, existing_tags, tags, purge_tags, result['ARN'])
        result = camel_dict_to_snake_dict(result)
        result['distribution_config']['tags'] = config['tags'] = list_tags_for_resource(client, module, result['arn'])
        result['diff'] = dict()
        diff = recursive_diff(distribution['Distribution']['DistributionConfig'], config)
        if diff:
            result['diff']['before'] = diff[0]
            result['diff']['after'] = diff[1]

    if wait and (create or update):
        validation_mgr.wait_until_processed(client, wait_timeout, distribution_id, config.get('CallerReference'))

    if 'distribution_config' in result:
        result.update(result['distribution_config'])
        del(result['distribution_config'])

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
