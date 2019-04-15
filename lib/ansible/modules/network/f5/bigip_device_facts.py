#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# Copyright: (c) 2013, Matt Hite <mhite@hotmail.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_device_facts
short_description: Collect facts from F5 BIG-IP devices
description:
  - Collect facts from F5 BIG-IP devices.
version_added: 2.7
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts returned to a given subset.
      - Can specify a list of values to include a larger subset.
      - Values can also be used with an initial C(!) to specify that a specific subset
        should not be collected.
    type: list
    required: True
    choices:
      - all
      - monitors
      - profiles
      - asm-policy-stats
      - asm-policies
      - asm-server-technologies
      - asm-signature-sets
      - client-ssl-profiles
      - devices
      - device-groups
      - external-monitors
      - fasthttp-profiles
      - fastl4-profiles
      - gateway-icmp-monitors
      - gtm-pools
      - gtm-servers
      - gtm-wide-ips
      - gtm-a-pools
      - gtm-a-wide-ips
      - gtm-aaaa-pools
      - gtm-aaaa-wide-ips
      - gtm-cname-pools
      - gtm-cname-wide-ips
      - gtm-mx-pools
      - gtm-mx-wide-ips
      - gtm-naptr-pools
      - gtm-naptr-wide-ips
      - gtm-srv-pools
      - gtm-srv-wide-ips
      - http-monitors
      - https-monitors
      - http-profiles
      - iapp-services
      - iapplx-packages
      - icmp-monitors
      - interfaces
      - internal-data-groups
      - irules
      - ltm-pools
      - nodes
      - oneconnect-profiles
      - partitions
      - provision-info
      - self-ips
      - server-ssl-profiles
      - software-volumes
      - software-images
      - software-hotfixes
      - ssl-certs
      - ssl-keys
      - system-db
      - system-info
      - tcp-monitors
      - tcp-half-open-monitors
      - tcp-profiles
      - traffic-groups
      - trunks
      - udp-profiles
      - vcmp-guests
      - virtual-addresses
      - virtual-servers
      - vlans
      - "!all"
      - "!monitors"
      - "!profiles"
      - "!asm-policy-stats"
      - "!asm-policies"
      - "!asm-server-technologies"
      - "!asm-signature-sets"
      - "!client-ssl-profiles"
      - "!devices"
      - "!device-groups"
      - "!external-monitors"
      - "!fasthttp-profiles"
      - "!fastl4-profiles"
      - "!gateway-icmp-monitors"
      - "!gtm-pools"
      - "!gtm-servers"
      - "!gtm-wide-ips"
      - "!gtm-a-pools"
      - "!gtm-a-wide-ips"
      - "!gtm-aaaa-pools"
      - "!gtm-aaaa-wide-ips"
      - "!gtm-cname-pools"
      - "!gtm-cname-wide-ips"
      - "!gtm-mx-pools"
      - "!gtm-mx-wide-ips"
      - "!gtm-naptr-pools"
      - "!gtm-naptr-wide-ips"
      - "!gtm-srv-pools"
      - "!gtm-srv-wide-ips"
      - "!http-monitors"
      - "!https-monitors"
      - "!http-profiles"
      - "!iapp-services"
      - "!iapplx-packages"
      - "!icmp-monitors"
      - "!interfaces"
      - "!internal-data-groups"
      - "!irules"
      - "!ltm-pools"
      - "!nodes"
      - "!oneconnect-profiles"
      - "!partitions"
      - "!provision-info"
      - "!self-ips"
      - "!server-ssl-profiles"
      - "!software-volumes"
      - "!software-images"
      - "!software-hotfixes"
      - "!ssl-certs"
      - "!ssl-keys"
      - "!system-db"
      - "!system-info"
      - "!tcp-monitors"
      - "!tcp-half-open-monitors"
      - "!tcp-profiles"
      - "!traffic-groups"
      - "!trunks"
      - "!udp-profiles"
      - "!vcmp-guests"
      - "!virtual-addresses"
      - "!virtual-servers"
      - "!vlans"
    aliases: ['include']
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Collect BIG-IP facts
  bigip_device_facts:
    gather_subset:
      - interfaces
      - vlans
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Collect all BIG-IP facts
  bigip_device_facts:
    gather_subset:
      - all
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Collect all BIG-IP facts except trunks
  bigip_device_facts:
    gather_subset:
      - all
      - "!trunks"
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
asm_policy_stats:
  description: Miscellaneous ASM policy related facts.
  returned: When C(asm-policy-stats) is specified in C(gather_subset).
  type: complex
  contains:
    policies:
      description:
        - The total number of ASM policies on the device.
      returned: changed
      type: int
      sample: 3
    policies_active:
      description:
        - The number of ASM policies that are marked as active.
      returned: changed
      type: int
      sample: 3
    policies_attached:
      description:
        - The number of ASM policies that are attached to virtual servers.
      returned: changed
      type: int
      sample: 1
    policies_inactive:
      description:
        - The number of ASM policies that are marked as inactive.
      returned: changed
      type: int
      sample: 0
    policies_unattached:
      description:
        - The number of ASM policies that are not attached to a virtual server.
      returned: changed
      type: int
      sample: 3
  sample: hash/dictionary of values
asm_policies:
  description: Detailed facts for ASM policies present on device.
  returned: When C(asm-policies) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/foo_policy
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: foo_policy
    policy_id:
      description:
        - Generated ID of the ASM policy resource.
      returned: changed
      type: str
      sample: l0Ckxe-7yHsXp8U5tTgbFQ
    active:
      description:
        - Indicates if an ASM policy is active.
      returned: changed
      type: bool
      sample: yes
    protocol_independent:
      description:
        - Indicates if the ASM policy differentiates between HTTP/WS and HTTPS/WSS URLs.
      returned: changed
      type: bool
      sample: no
    has_parent:
      description:
        - Indicates if the ASM policy is a child of another ASM policy.
      returned: changed
      type: bool
      sample: no
    type:
      description:
        - The type of policy, can be C(Security) or C(Parent).
      returned: changed
      type: str
      sample: security
    virtual_servers:
      description:
        - Virtual server or servers which have this policy assigned to them.
      returned: changed
      type: list
      sample: ['/Common/foo_VS/']
    allowed_response_codes:
      description:
        - Lists the response status codes between 400 and 599 that the security profile considers legal.
      returned: changed
      type: list
      sample: ['400', '404']
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: Significant Policy Description
    learning_mode:
      description:
        - Determine how the policy is built.
      returned: changed
      type: str
      sample: manual
    enforcement_mode:
      description:
        - Specifies whether blocking is active or inactive for the ASM policy.
      returned: changed
      type: str
      sample: blocking
    trust_xff:
      description:
        - Indicates the system has confidence in an XFF (X-Forwarded-For) header in the request.
      returned: changed
      type: bool
      sample: yes
    custom_xff_headers:
      description:
        - List of custom XFF headers trusted by the system.
      returned: changed
      type: str
      sample: asm-proxy1
    case_insensitive:
      description:
        - Indicates if the ASM policy treats file types, URLs, and parameters as case sensitive.
      returned: changed
      type: bool
      sample: yes
    signature_staging:
      description:
        - Specifies if the staging feature is active on the ASM policy.
      returned: changed
      type: bool
      sample: yes
    place_signatures_in_staging:
      description:
        - Specifies if the system places new or updated signatures in staging
          for the number of days specified in the enforcement readiness period.
      returned: changed
      type: bool
      sample: no
    enforcement_readiness_period:
      description:
        - Period in days both security policy entities and attack signatures
          remain in staging mode before the system suggests to enforce them.
      returned: changed
      type: int
      sample: 8
    path_parameter_handling:
      description:
        - Specifies how the system handles path parameters that are attached to path segments in URIs.
      returned: changed
      type: str
      sample: ignore
    trigger_asm_irule_event:
      description:
        - Indicates if iRule event is enabled.
      returned: changed
      type: str
      sample: disabled
    inspect_http_uploads:
      description:
        - Specify if the system should inspect all http uploads.
      returned: changed
      type: bool
      sample: yes
    mask_credit_card_numbers_in_request:
      description:
        - Indicates if the system masks credit card numbers.
      returned: changed
      type: bool
      sample: no
    maximum_http_header_length:
      description:
        - Maximum length of an HTTP header name and value that the system processes.
      returned: changed
      type: int
      sample: 8192
    use_dynamic_session_id_in_url:
      description:
        - Specifies how the security policy processes URLs that use dynamic sessions.
      returned: changed
      type: bool
      sample: no
    maximum_cookie_header_length:
      description:
        - Maximum length of a cookie header name and value that the system processes.
      returned: changed
      type: int
      sample: 8192
    application_language:
      description:
        - The language encoding for the web application.
      returned: changed
      type: str
      sample: utf-8
    disallowed_geolocations:
      description:
        - Displays countries that may not access the web application.
      returned: changed
      type: str
      sample: Argentina
    csrf_protection_enabled:
      description:
        - Specifies if CSRF protection is active on the ASM policy.
      returned: changed
      type: bool
      sample: yes
    csrf_protection_ssl_only:
      description:
        - Specifies that only HTTPS URLs will be checked for CSRF protection.
      returned: changed
      type: bool
      sample: yes
    csrf_protection_expiration_time_in_seconds:
      description:
        - Specifies how long, in seconds, a configured CSRF token is valid before it expires.
      returned: changed
      type: int
      sample: 600
    csrf_urls:
      description:
        - Specifies a list of URLs for CSRF token verification.
        - In version 13.0.0 and above this has become a sub-collection and a list of dictionaries.
        - In version 12.x this is a list of simple strings.
      returned: changed
      type: complex
      contains:
        csrf_url_required_parameters:
          description:
            - Indicates whether to ignore or require one of the specified parameters is present
              in a request when checking if the URL entry matches the request.
          returned: changed
          type: str
          sample: ignore
        csrf_url_parameters_list:
          description:
            - List of parameters to look for in a request when checking if the URL entry matches the request.
          returned: changed
          type: list
          sample: ['fooparam']
        csrf_url:
          description:
            - Specifies an URL to protect.
          returned: changed
          type: str
          sample: ['/foo.html']
        csrf_url_method:
          description:
            - Method for the specified URL.
          returned: changed
          type: str
          sample: POST
        csrf_url_enforcement_action:
          description:
            - Indicates the action specified for the system to take when the URL entry matches.
          returned: changed
          type: str
          sample: none
        csrf_url_id:
          description:
            - Specified the generated ID for the configured CSRF url resource.
          returned: changed
          type: str
          sample: l0Ckxe-7yHsXp8U5tTgbFQ
        csrf_url_wildcard_order:
          description:
            - Specified the order in which the wildcard URLs are enforced.
          returned: changed
          type: str
          sample: 1
  sample: hash/dictionary of values
asm_server_technologies:
  description: Detailed facts for ASM server technologies present on device.
  returned: When C(asm-server-technologies) is specified in C(gather_subset).
  type: complex
  contains:
    id:
      description:
        - Displays the generated ID for the server technology resource.
      returned: changed
      type: str
      sample: l0Ckxe-7yHsXp8U5tTgbFQ
    server_technology_name:
      description:
        - Human friendly name of the server technology resource.
      returned: changed
      type: str
      sample: Wordpress
    server_technology_references:
      description:
        - List of dictionaries containing API self links of the associated technology resources.
      returned: changed
      type: complex
      contains:
        link:
          description:
            - A self link to an associated server technology.
      sample: https://localhost/mgmt/tm/asm/server-technologies/NQG7CT02OBC2cQWbnP7T-A?ver=13.1.0
  sample: hash/dictionary of values
asm_signature_sets:
  description: Detailed facts for ASM signature sets present on device.
  returned: When C(asm-signature-sets) is specified in C(gather_subset).
  type: complex
  contains:
    name:
      description:
        - Name of the signature set
      returned: changed
      type: str
      sample: WebSphere signatures
    id:
      description:
        - Displays the generated ID for the signature set resource.
      returned: changed
      type: str
      sample: l0Ckxe-7yHsXp8U5tTgbFQ
    type:
      description:
        - The method used to select signatures to be a part of the signature set.
      returned: changed
      type: str
      sample: filter-based
    category:
      description:
        - Displays the category of the signature set.
      returned: changed
      type: str
      sample: filter-based
    is_user_defined:
      description:
        - Specifies that this signature set was added by a user.
      returned: changed
      type: bool
      sample: no
    assign_to_policy_by_default:
      description:
        - Indicates whether the system assigns this signature set to a new created security policy by default.
      returned: changed
      type: bool
      sample: yes
    default_alarm:
      description:
        - Displays whether the security policy logs the request data in the Statistics
          screen if a request matches a signature that is included in the signature set
      returned: changed
      type: bool
      sample: yes
    default_block:
      description:
        - Displays, when the security policy's enforcement mode is Blocking,
          how the system treats requests that match a signature included in the signature set.
      returned: changed
      type: bool
      sample: yes
    default_learn:
      description:
        - Displays whether the security policy learns all requests that match a signature
          that is included in the signature set.
      returned: changed
      type: bool
      sample: yes
  sample: hash/dictionary of values
client_ssl_profiles:
  description: Client SSL Profile related facts.
  returned: When C(client-ssl-profiles) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/bigip02.internal
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: bigip02.internal
    alert_timeout:
      description:
        - Maximum time period in seconds to keep the SSL session active after alert
          message is sent, or indefinite.
      returned: changed
      type: int
      sample: 0
    allow_non_ssl:
      description:
        - Enables or disables non-SSL connections.
      returned: changed
      type: bool
      sample: yes
    authenticate_depth:
      description:
        - Specifies the authenticate depth. This is the client certificate chain maximum traversal depth.
      returned: changed
      type: int
      sample: 9
    authenticate_frequency:
      description:
        - Specifies how often the system authenticates a user.
      returned: changed
      type: str
      sample: once
    ca_file:
      description:
        - Specifies the certificate authority (CA) file name.
      returned: changed
      type: str
      sample: /Common/default-ca.crt
    cache_size:
      description:
        - Specifies the SSL session cache size.
      returned: changed
      type: int
      sample: 262144
    cache_timeout:
      description:
        - Specifies the SSL session cache timeout value.
      returned: changed
      type: int
      sample: 3600
    certificate_file:
      description:
        - Specifies the name of the certificate installed on the traffic
          management system for the purpose of terminating or initiating
          an SSL connection.
      returned: changed
      type: str
      sample: /Common/default.crt
    chain_file:
      description:
        - Specifies or builds a certificate chain file that a client can
          use to authenticate the profile.
      returned: changed
      type: str
      sample: /Common/ca-chain.crt
    ciphers:
      description:
        - Specifies a list of cipher names.
      returned: changed
      type: str
      sample: ['DEFAULT']
    crl_file:
      description:
        - Specifies the certificate revocation list file name.
      returned: changed
      type: str
      sample: /Common/default.crl
    parent:
      description:
        - Parent of the profile
      returned: changed
      type: str
      sample: /Common/clientssl
    description:
      description:
        - Description of the profile.
      returned: changed
      type: str
      sample: My profile
    modssl_methods:
      description:
        - Enables or disables ModSSL method emulation.
      returned: changed
      type: bool
      sample: no
    peer_certification_mode:
      description:
        - Specifies the peer certificate mode.
      returned: changed
      type: str
      sample: ignore
    sni_require:
      description:
        - When this option is C(yes), a client connection that does not
          specify a known server name or does not support SNI extension will
          be rejected.
      returned: changed
      type: bool
      sample: no
    sni_default:
      description:
        - When C(yes), this profile is the default SSL profile when the server
          name in a client connection does not match any configured server
          names, or a client connection does not specify any server name at
          all.
      returned: changed
      type: bool
      sample: yes
    strict_resume:
      description:
        - Enables or disables strict-resume.
      returned: changed
      type: bool
      sample: yes
    profile_mode_enabled:
      description:
        - Specifies the profile mode, which enables or disables SSL
          processing.
      returned: changed
      type: bool
      sample: yes
    renegotiation_maximum_record_delay:
      description:
        - Maximum number of SSL records that the traffic
          management system can receive before it renegotiates an SSL
          session.
      returned: changed
      type: int
      sample: 0
    renegotiation_period:
      description:
        - Number of seconds required to renegotiate an SSL
          session.
      returned: changed
      type: int
      sample: 0
    renegotiation:
      description:
        - Specifies whether renegotiations are enabled.
      returned: changed
      type: bool
      sample: yes
    server_name:
      description:
        - Specifies the server names to be matched with SNI (server name
          indication) extension information in ClientHello from a client
          connection.
      returned: changed
      type: str
      sample: bigip01
    session_ticket:
      description:
        - Enables or disables session-ticket.
      returned: changed
      type: bool
      sample: no
    unclean_shutdown:
      description:
        - Whether to force the SSL profile to perform a clean shutdown of all SSL
          connections or not
      returned: changed
      type: bool
      sample: no
    retain_certificate:
      description:
        - APM module requires storing certificate in SSL session. When
          C(no), certificate will not be stored in SSL session.
      returned: changed
      type: bool
      sample: yes
    secure_renegotiation_mode:
      description:
        - Specifies the secure renegotiation mode.
      returned: changed
      type: str
      sample: require
    handshake_timeout:
      description:
        - Specifies the handshake timeout in seconds.
      returned: changed
      type: int
      sample: 10
    forward_proxy_certificate_extension_include:
      description:
        - Specifies the extensions of the web server certificates to be
          included in the generated certificates using SSL Forward Proxy.
      returned: changed
      type: list
      sample: ["basic-constraints", "subject-alternative-name"]
    forward_proxy_certificate_lifespan:
      description:
        - Specifies the lifespan of the certificate generated using the SSL
          forward proxy feature.
      returned: changed
      type: int
      sample: 30
    forward_proxy_lookup_by_ipaddr_port:
      description:
        - Specifies whether to perform certificate look up by IP address and
          port number.
      returned: changed
      type: bool
      sample: no
    forward_proxy_enabled:
      description:
        - Enables or disables SSL forward proxy feature.
      returned: changed
      type: bool
      sample: yes
    forward_proxy_ca_passphrase:
      description:
        - Specifies the passphrase of the key file that is used as the
          certification authority key when SSL forward proxy feature is
          enabled.
      returned: changed
      type: str
    forward_proxy_ca_certificate_file:
      description:
        - Specifies the name of the certificate file that is used as the
          certification authority certificate when SSL forward proxy feature
          is enabled.
      returned: changed
      type: str
    forward_proxy_ca_key_file:
      description:
        - Specifies the name of the key file that is used as the
          certification authority key when SSL forward proxy feature is
          enabled.
      returned: changed
      type: str
  sample: hash/dictionary of values
devices:
  description: Device related facts.
  returned: When C(devices) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/bigip02.internal
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: bigip02.internal
    active_modules:
      description:
        - The currently licensed and provisioned modules on the device.
      returned: changed
      type: list
      sample: ["DNS Services (LAB)", "PSM, VE"]
    base_mac_address:
      description:
        - Media Access Control address (MAC address) of the device.
      returned: changed
      type: str
      sample: "fa:16:3e:c3:42:6f"
    build:
      description:
        - The minor version information of the total product version.
      returned: changed
      type: str
      sample: 0.0.1
    chassis_id:
      description:
        - Serial number of the device.
      returned: changed
      type: str
      sample: 11111111-2222-3333-444444444444
    chassis_type:
      description:
        - Displays the chassis type. The possible values are C(individual) and C(viprion).
      returned: changed
      type: str
      sample: individual
    comment:
      description:
        - User comments about the device.
      returned: changed
      type: str
      sample: My device
    configsync_address:
      description:
        - IP address used for configuration synchronization.
      returned: changed
      type: str
      sample: 10.10.10.10
    contact:
      description:
        - Administrator contact information.
      returned: changed
      type: str
      sample: The User
    description:
      description:
        - Description of the device.
      returned: changed
      type: str
      sample: My device
    edition:
      description:
        - Displays the software edition.
      returned: changed
      type: str
      sample: Point Release 7
    failover_state:
      description:
        - Device failover state.
      returned: changed
      type: str
      sample: active
    hostname:
      description:
        - Device hostname
      returned: changed
      type: str
      sample: bigip02.internal
    location:
      description:
        - Specifies the physical location of the device.
      returned: changed
      type: str
      sample: London
    management_address:
      description:
        - IP address of the management interface.
      returned: changed
      type: str
      sample: 3.3.3.3
    marketing_name:
      description:
        - Marketing name of the device platform.
      returned: changed
      type: str
      sample: BIG-IP Virtual Edition
    multicast_address:
      description:
        - Specifies the multicast IP address used for failover.
      returned: changed
      type: str
      sample: 4.4.4.4
    optional_modules:
      description:
        - Modules that are available for the current platform, but are not currently licensed.
      returned: changed
      type: list
      sample: ["App Mode (TMSH Only, No Root/Bash)", "BIG-IP VE, Multicast Routing"]
    platform_id:
      description:
        - Displays the device platform identifier.
      returned: changed
      type: str
      sample: Z100
    primary_mirror_address:
      description:
        - Specifies the IP address used for state mirroring.
      returned: changed
      type: str
      sample: 5.5.5.5
    product:
      description:
        - Displays the software product name.
      returned: changed
      type: str
      sample: BIG-IP
    secondary_mirror_address:
      description:
        - Secondary IP address used for state mirroring.
      returned: changed
      type: str
      sample: 2.2.2.2
    self:
      description:
        - Whether this device is the one that was queried for facts, or not.
      returned: changed
      type: bool
      sample: yes
    software_version:
      description:
        - Displays the software version number.
      returned: changed
      type: str
      sample: 13.1.0.7
    timelimited_modules:
      description:
        - Displays the licensed modules that are time-limited.
      returned: changed
      type: list
      sample: ["IP Intelligence, 3Yr, ...", "PEM URL Filtering, 3Yr, ..."]
    timezone:
      description:
        - Displays the time zone configured on the device.
      returned: changed
      type: str
      sample: UTC
    unicast_addresses:
      description:
        - Specifies the entire set of unicast addresses used for failover.
      returned: changed
      type: complex
      contains:
        effective_ip:
          description:
            - The IP address that peers can use to reach this unicast address IP.
          returned: changed
          type: str
          sample: 5.4.3.5
        effective_port:
          description:
            - The port that peers can use to reach this unicast address.
          returned: changed
          type: int
          sample: 1026
        ip:
          description:
            - The IP address that the failover daemon will listen on for packets from its peers.
          returned: changed
          type: str
          sample: 5.4.3.5
        port:
          description:
            - The IP port that the failover daemon uses to accept packets from its peers.
          returned: changed
          type: int
          sample: 1026
  sample: hash/dictionary of values
device_groups:
  description: Device group related facts.
  returned: When C(device-groups) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/fasthttp
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: fasthttp
    autosync_enabled:
      description:
        - Whether the device group automatically synchronizes configuration data to its members.
      returned: changed
      type: bool
      sample: no
    description:
      description:
        - Description of the device group.
      returned: changed
      type: str
      sample: My device group
    devices:
      description:
        - List of devices that are in the group. Devices are listed by their C(full_path).
      returned: changed
      type: list
      sample: [/Common/bigip02.internal]
    full_load_on_sync:
      description:
        - Specifies that the entire configuration for a device group is sent when configuration
          synchronization is performed.
      returned: changed
      type: bool
      sample: yes
    incremental_config_sync_size_maximum:
      description:
        - Specifies the maximum size (in KB) to devote to incremental config sync cached transactions.
      returned: changed
      type: int
      sample: 1024
    network_failover_enabled:
      description:
        - Specifies whether network failover is used.
      returned: changed
      type: bool
      sample: yes
    type:
      description:
        - Specifies the type of device group.
      returned: changed
      type: str
      sample: sync-only
    asm_sync_enabled:
      description:
        - Specifies whether to synchronize ASM configurations of device group members.
      returned: changed
      type: bool
      sample: yes
  sample: hash/dictionary of values
external_monitors:
  description: External monitor related facts.
  returned: When C(external-monitors) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/external
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: external
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: external
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My monitor
    destination:
      description:
        - Specifies the IP address and service port of the resource that is
          the destination of this monitor.
      type: str
      sample: "*:*"
    args:
      description:
        - Specifies any command-line arguments that the script requires.
      type: str
      sample: arg1 arg2 arg3
    external_program:
      description:
        - Specifies the name of the file for the monitor to use.
      type: str
      sample: /Common/arg_example
    variables:
      description:
        - Specifies any variables that the script requires.
      type: complex
      sample: { "key1": "val", "key_2": "val 2" }
    interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when either the resource is down or the status
          of the resource is unknown.
      type: int
      sample: 5
    manual_resume:
      description:
        - Specifies whether the system automatically changes the status of a
          resource to up at the next successful monitor check.
      type: bool
      sample: yes
    time_until_up:
      description:
        - Specifies the amount of time, in seconds, after the first
          successful response before a node is marked up.
      type: int
      sample: 0
    timeout:
      description:
        - Specifies the number of seconds the target has in which to respond
          to the monitor request.
      type: int
      sample: 16
    up_interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when the resource is up.
      type: int
      sample: 0
  sample: hash/dictionary of values
fasthttp_profiles:
  description: FastHTTP profile related facts.
  returned: When C(fasthttp-profiles) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/fasthttp
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: fasthttp
    client_close_timeout:
      description:
        - Number of seconds after which the system closes a client connection, when
          the system either receives a client FIN packet or sends a FIN packet to the client.
      returned: changed
      type: int
      sample: 5
    oneconnect_idle_timeout_override:
      description:
        - Number of seconds after which a server-side connection in a OneConnect pool
          is eligible for deletion, when the connection has no traffic.
      returned: changed
      type: int
      sample: 0
    oneconnect_maximum_reuse:
      description:
        - Maximum number of times that the system can re-use a current connection.
      returned: changed
      type: int
      sample: 0
    oneconnect_maximum_pool_size:
      description:
        - Maximum number of connections to a load balancing pool.
      returned: changed
      type: int
      sample: 2048
    oneconnect_minimum_pool_size:
      description:
        - Minimum number of connections to a load balancing pool.
      returned: changed
      type: int
      sample: 0
    oneconnect_replenish':
      description:
        - Specifies, when C(yes), that the system will not keep a steady-state maximum of
          connections to the back-end unless the number of connections to the pool have
          dropped beneath the C(minimum_pool_size) specified in the profile.
      returned: changed
      type: bool
      sample: yes
    oneconnect_ramp_up_increment:
      description:
        - The increment in which the system makes additional connections available, when
          all available connections are in use.
      returned: changed
      type: int
      sample: 4
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: fasthttp
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My profile
    force_http_1_0_response:
      description:
        - Specifies, when C(yes), that the server sends responses to clients in the HTTP/1.0
          format.
      returned: changed
      type: bool
      sample: no
    request_header_insert:
      description:
        - A string that the system inserts as a header in an HTTP request. If the header
          exists already, the system does not replace it.
      returned: changed
      type: str
      sample: "X-F5-Authentication: foo"
    http_1_1_close_workarounds:
      description:
        - Specifies, when C(yes), that the server uses workarounds for HTTP 1.1 close issues.
      returned: changed
      type: bool
      sample: no
    idle_timeout:
      description:
        - Length of time that a connection is idle (has no traffic) before the connection
          is eligible for deletion.
      returned: changed
      type: int
      sample: 300
    insert_x_forwarded_for:
      description:
        - Whether the system inserts the X-Forwarded-For header in an HTTP request with the
          client IP address, to use with connection pooling.
      returned: changed
      type: bool
      sample: no
    maximum_header_size:
      description:
        - Maximum amount of HTTP header data that the system buffers before making a load
          balancing decision.
      returned: changed
      type: int
      sample: 32768
    maximum_requests:
      description:
        - Maximum number of requests that the system can receive on a client-side connection,
          before the system closes the connection.
      returned: changed
      type: int
      sample: 0
    maximum_segment_size_override:
      description:
        - Maximum segment size (MSS) override for server-side connections.
      returned: changed
      type: int
      sample: 0
    receive_window_size:
      description:
        - Amount of data the BIG-IP system can accept without acknowledging the server.
      returned: changed
      type: int
      sample: 0
    reset_on_timeout:
      description:
        - Specifies, when C(yes), that the system sends a reset packet (RST) in addition to
          deleting the connection, when a connection exceeds the idle timeout value.
      returned: changed
      type: bool
      sample: yes
    server_close_timeout:
      description:
        - Number of seconds after which the system closes a client connection, when the system
          either receives a server FIN packet or sends a FIN packet to the server.
      returned: changed
      type: int
      sample: 5
    server_sack:
      description:
        - Whether the BIG-IP system processes Selective ACK (Sack) packets in cookie responses
          from the server.
      returned: changed
      type: bool
      sample: no
    server_timestamp:
      description:
        - Whether the BIG-IP system processes timestamp request packets in cookie responses
          from the server.
      returned: changed
      type: bool
      sample: no
    unclean_shutdown:
      description:
        - How the system handles closing connections. Values provided may be C(enabled), C(disabled),
          or C(fast).
      returned: changed
      type: str
      sample: enabled
  sample: hash/dictionary of values
fastl4_profiles:
  description: FastL4 profile related facts.
  returned: When C(fastl4-profiles) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/fastl4
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: fastl4
    client_timeout:
      description:
        - Specifies late binding client timeout in seconds.
        - This is the number of seconds allowed for a client to transmit enough data to
          select a server pool.
        - If this timeout expires, the timeout-recovery option dictates whether
          to drop the connection or fallback to the normal FastL4 load-balancing method
          to pick a server pool.
      returned: changed
      type: int
      sample: 30
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: fastl4
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My profile
    explicit_flow_migration:
      description:
        - Specifies whether to have the iRule code determine exactly when
          the FIX stream drops down to the ePVA hardware.
      returned: changed
      type: bool
      sample: yes
    hardware_syn_cookie:
      description:
        - Enables or disables hardware SYN cookie support when PVA10 is present on the system.
        - This option is deprecated in version 13.0.0 and is replaced by C(syn-cookie-enable).
      returned: changed
      type: bool
      sample: no
    idle_timeout:
      description:
        - Specifies the number of seconds that a connection is idle before the connection is
          eligible for deletion.
        - Values will be in the range of 0 to 4294967295 (inclusive).
        - C(0) is equivalent to the TMUI value "immediate".
        - C(4294967295) is equivalent to the TMUI value "indefinite".
      returned: changed
      type: int
      sample: 300
    dont_fragment_flag:
      description:
        - Describes the Don't Fragment (DF) bit setting in the IP Header of
          the outgoing TCP packet.
        - When C(pmtu), sets the outgoing IP Header DF bit based on IP pmtu
          setting(tm.pathmtudiscovery).
        - When C(preserve), sets the outgoing Packet's IP Header DF bit to be same as incoming
          IP Header DF bit.
        - When C(set), sets the outgoing packet's IP Header DF bit.
        - When C(clear), clears the outgoing packet's IP Header DF bit.
      returned: changed
      type: str
      sample: pmtu
    ip_tos_to_client:
      description:
        - Specifies an IP Type of Service (ToS) number for the client-side.
        - This option specifies the ToS level that the traffic management
          system assigns to IP packets when sending them to clients.
      returned: changed
      type: str or int
      sample: 200
    ip_tos_to_server:
      description:
        - Specifies an IP ToS number for the server side.
        - This option specifies the ToS level that the traffic management system assigns
          to IP packets when sending them to servers.
      returned: changed
      type: str or int
      sample: pass-through
    ttl_mode:
      description:
        - Describe the outgoing TCP packet's IP Header TTL mode.
        - When C(proxy), sets the outgoing IP Header TTL value to 255/64 for ipv4/ipv6
          respectively.
        - When C(preserve), sets the outgoing IP Header TTL value to be same as the
          incoming IP Header TTL value.
        - When C(decrement), sets the outgoing IP Header TTL value to be one less than
          the incoming TTL value.
        - When C(set), sets the outgoing IP Header TTL value to a specific value(as
          specified by C(ttl_v4) or C(ttl_v6).
      returned: changed
      type: str
      sample: preserve
    ttl_v4:
      description:
        - Specify the outgoing packet's IP Header TTL value for IPv4 traffic.
        - Maximum value that can be specified is 255.
      returned: changed
      type: int
      sample: 200
    ttl_v6:
      description:
        - Specify the outgoing packet's IP Header TTL value for IPv6
          traffic.
        - Maximum value that can be specified is 255.
      returned: changed
      type: int
      sample: 300
    keep_alive_interval:
      description:
        - Specifies the keep-alive probe interval, in seconds.
        - A value of 0 indicates keep-alive is disabled.
      returned: changed
      type: int
      sample: 10
    late_binding:
      description:
        - Specifies whether to enable or disable intelligent selection of a
          back-end server pool.
      returned: changed
      type: bool
      sample: yes
    link_qos_to_client:
      description:
        - Specifies a Link Quality of Service (QoS) (VLAN priority) number
          for the client side.
        - This option specifies the QoS level that the system assigns to packets
          when sending them to clients.
      returned: changed
      type: int or string
      sample: 7
    link_qos_to_server:
      description:
        - Specifies a Link QoS (VLAN priority) number for the server side.
        - This option specifies the QoS level that the system assigns to
          packets when sending them to servers.
      returned: changed
      type: int or string
      sample: 5
    loose_close:
      description:
        - Specifies that the system closes a loosely-initiated connection
          when the system receives the first FIN packet from either the
          client or the server.
      returned: changed
      type: bool
      sample: no
    loose_init:
      description:
        - Specifies that the system initializes a connection when it
          receives any Transmission Control Protocol (TCP) packet, rather
          than requiring a SYN packet for connection initiation.
      returned: changed
      type: bool
      sample: yes
    mss_override:
      description:
        - Specifies a maximum segment size (MSS) override for server
          connections. Note that this is also the MSS advertised to a client
          when a client first connects.
        - C(0) (zero), means the option is disabled. Otherwise, the value will be
          between 256 and 9162.
      returned: changed
      type: int
      sample: 500
    priority_to_client:
      description:
        - Specifies internal packet priority for the client side.
        - This option specifies the internal packet priority that the system
          assigns to packets when sending them to clients.
      returned: changed
      type: int or string
      sample: 300
    priority_to_server:
      description:
        - Specifies internal packet priority for the server side.
        - This option specifies the internal packet priority that the system
          assigns to packets when sending them to servers.
      returned: changed
      type: int or string
      sample: 200
    pva_acceleration:
      description:
        - Specifies the Packet Velocity(r) ASIC acceleration policy.
      returned: changed
      type: str
      sample: full
    pva_dynamic_client_packets:
      description:
        - Specifies the number of client packets before dynamic ePVA
          hardware re-offloading occurs.
        - Values will be between 0 and 10.
      returned: changed
      type: int
      sample: 8
    pva_dynamic_server_packets:
      description:
        - Specifies the number of server packets before dynamic ePVA
          hardware re-offloading occurs.
        - Values will be between 0 and 10.
      returned: changed
      type: int
      sample: 5
    pva_flow_aging:
      description:
        - Specifies if automatic aging from ePVA flow cache is enabled or not.
      returned: changed
      type: bool
      sample: yes
    pva_flow_evict:
      description:
        - Specifies if this flow can be evicted upon hash collision with a
          new flow learn snoop request.
      returned: changed
      type: bool
      sample: no
    pva_offload_dynamic:
      description:
        - Specifies whether PVA flow dynamic offloading is enabled or not.
      returned: changed
      type: bool
      sample: yes
    pva_offload_state:
      description:
        - Specifies at what stage the ePVA performs hardware offload.
        - When C(embryonic), implies at TCP CSYN or the first client UDP packet.
        - When C(establish), implies TCP 3WAY handshaking or UDP CS round trip are
          confirmed.
      returned: changed
      type: str
      sample: embryonic
    reassemble_fragments:
      description:
        - Specifies whether to reassemble fragments.
      returned: changed
      type: bool
      sample: yes
    receive_window:
      description:
        - Specifies the window size to use, in bytes.
        - The maximum is 2^31 for window scale enabling.
      returned: changed
      type: int
      sample: 1000
    reset_on_timeout:
      description:
        - Specifies whether you want to reset connections on timeout.
      returned: changed
      type: bool
      sample: yes
    rtt_from_client:
      description:
        - Enables or disables the TCP timestamp options to measure the round
          trip time to the client.
      returned: changed
      type: bool
      sample: no
    rtt_from_server:
      description:
        - Enables or disables the TCP timestamp options to measure the round
          trip time to the server.
      returned: changed
      type: bool
      sample: yes
    server_sack:
      description:
        - Specifies whether to support server sack option in cookie response
          by default.
      returned: changed
      type: bool
      sample: no
    server_timestamp:
      description:
        - Specifies whether to support server timestamp option in cookie
          response by default.
      returned: changed
      type: bool
      sample: yes
    software_syn_cookie:
      description:
        - Enables or disables software SYN cookie support when PVA10 is not present
          on the system.
        - This option is deprecated in version 13.0.0 and is replaced by
          C(syn_cookie_enabled).
      returned: changed
      type: bool
      sample: yes
    syn_cookie_enabled:
      description:
        - Enables syn-cookies capability on this virtual server.
      returned: changed
      type: bool
      sample: no
    syn_cookie_mss:
      description:
        - Specifies a maximum segment size (MSS) for server connections when
          SYN Cookie is enabled.
      returned: changed
      type: int
      sample: 2000
    syn_cookie_whitelist:
      description:
        - Specifies whether or not to use a SYN Cookie WhiteList when doing
          software SYN Cookies.
      returned: changed
      type: bool
      sample: no
    tcp_close_timeout:
      description:
        - Specifies a TCP close timeout in seconds.
      returned: changed
      type: int
      sample: 100
    generate_init_seq_number:
      description:
        - Specifies whether you want to generate TCP sequence numbers on all
          SYNs that conform with RFC1948, and allow timestamp recycling.
      returned: changed
      type: bool
      sample: yes
    tcp_handshake_timeout:
      description:
        - Specifies a TCP handshake timeout in seconds.
      returned: changed
      type: int
      sample: 5
    strip_sack:
      description:
        - Specifies whether you want to block the TCP SackOK option from
          passing to the server on an initiating SYN.
      returned: changed
      type: bool
      sample: yes
    tcp_time_wait_timeout:
      description:
        - Specifies a TCP time_wait timeout in milliseconds.
      returned: changed
      type: int
      sample: 60
    tcp_timestamp_mode:
      description:
        - Specifies how you want to handle the TCP timestamp.
      returned: changed
      type: str
      sample: preserve
    tcp_window_scale_mode:
      description:
        - Specifies how you want to handle the TCP window scale.
      returned: changed
      type: str
      sample: preserve
    timeout_recovery:
      description:
        - Specifies late binding timeout recovery mode. This is the action
          to take when late binding timeout occurs on a connection.
        - When C(disconnect), only the L7 iRule actions are acceptable to
          pick a server.
        - When C(fallback), the normal FastL4 load-balancing methods are acceptable
          to pick a server.
      returned: changed
      type: str
      sample: fallback
  sample: hash/dictionary of values
gateway_icmp_monitors:
  description: Gateway ICMP monitor related facts.
  returned: When C(gateway-icmp-monitors) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/gateway_icmp
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: gateway_icmp
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: gateway_icmp
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My monitor
    adaptive:
      description:
        - Whether adaptive response time monitoring is enabled for this monitor.
      type: bool
      sample: no
    adaptive_divergence_type:
      description:
        - Specifies whether the adaptive-divergence-value is C(relative) or
          C(absolute).
      type: str
      sample: relative
    adaptive_divergence_value:
      description:
        - Specifies how far from mean latency each monitor probe is allowed
          to be.
      type: int
      sample: 25
    adaptive_limit:
      description:
        - Specifies the hard limit, in milliseconds, which the probe is not
          allowed to exceed, regardless of the divergence value.
      type: int
      sample: 200
    adaptive_sampling_timespan:
      description:
        - Specifies the size of the sliding window, in seconds, which
          records probe history.
      type: int
      sample: 300
    destination:
      description:
        - Specifies the IP address and service port of the resource that is
          the destination of this monitor.
      type: str
      sample: "*:*"
    interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when either the resource is down or the status
          of the resource is unknown.
      type: int
      sample: 5
    manual_resume:
      description:
        - Specifies whether the system automatically changes the status of a
          resource to up at the next successful monitor check.
      type: bool
      sample: yes
    time_until_up:
      description:
        - Specifies the amount of time, in seconds, after the first
          successful response before a node is marked up.
      type: int
      sample: 0
    timeout:
      description:
        - Specifies the number of seconds the target has in which to respond
          to the monitor request.
      type: int
      sample: 16
    transparent:
      description:
        - Specifies whether the monitor operates in transparent mode.
      type: bool
      sample: no
    up_interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when the resource is up.
      type: int
      sample: 0
  sample: hash/dictionary of values
gtm_pools:
  description:
    - GTM pool related facts.
    - Every "type" of pool has the exact same list of possible facts. Therefore,
      the list of facts here is presented once instead of 6 times.
  returned: When any of C(gtm-pools) or C(gtm-*-pools) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/pool1
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: pool1
    alternate_mode:
      description:
        - The load balancing mode that the system uses to load balance name resolution
          requests among the members of the pool.
      type: str
      sample: drop-packet
    dynamic_ratio:
      description:
        - Whether or not the dynamic ratio load balancing algorithm is enabled for this
          pool.
      type: bool
      sample: yes
    enabled:
      description:
        - Is the pool enabled.
      type: bool
    disabled:
      description:
        - Is the pool disabled
      type: bool
    fallback_mode:
      description:
        - Specifies the load balancing mode that the system uses to load balance
          name resolution amongst the pool members if the preferred and alternate
          modes are unsuccessful in picking a pool.
      type: str
    load_balancing_mode:
      description:
        - Specifies the preferred load balancing mode that the system uses to load
          balance requests across pool members.
      type: str
    manual_resume:
      description:
        - Whether manual resume is enabled for this pool
      type: bool
    max_answers_returned:
      description:
        - Maximum number of available virtual servers that the system lists in a
          response.
      type: int
    members:
      description:
        - Lists of members (and their configurations) in the pool.
      type: complex
    partition:
      description:
        - Partition the pool exists on.
    qos_hit_ratio:
      description:
        - Weight of the Hit Ratio performance factor for the QoS dynamic load
          balancing method
      type: int
    qos_hops:
      description:
        - Weight of the Hops performance factor when load balancing mode or fallback mode
          is QoS.
      type: int
    qos_kilobytes_second:
      description:
        - Weight assigned to Kilobytes per Second performance factor when load balancing
          option is QoS.
      type: int
    qos_lcs:
      description:
        - Weight assign to the Link Capacity performance factor when load balacing option
          is QoS.
      type: int
    qos_packet_rate:
      description:
        - Weight assign to the Packet Rate performance factor when load balacing option
          is QoS.
      type: int
    qos_rtt:
      description:
        - Weight assign to the Round Trip Time performance factor when load balacing option
          is QoS.
      type: int
    qos_topology:
      description:
        - Weight assign to the Topology performance factor when load balacing option
          is QoS.
      type: int
    qos_vs_capacity:
      description:
        - Weight assign to the Virtual Server performance factor when load balacing option
          is QoS.
      type: int
    qos_vs_score:
      description:
        - Weight assign to the Virtual Server Score performance factor when load balacing
          option is QoS.
      type: int
    ttl:
      description:
        - Number of seconds that the IP address, once found, is valid.
      type: int
    verify_member_availability:
      description:
        - Whether or not the system verifies the availability of the members before
          sending a connection to them.
      type: bool
  sample: hash/dictionary of values
gtm_servers:
  description:
    - GTM server related facts.
  returned: When C(gtm-servers) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/server1
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: server1
    datacenter:
      description:
        - Full name of the datacenter this server belongs to.
      type: str
    enabled:
      description:
        - Whether the server is enabled.
      type: bool
    disabled:
      description:
        - Whether the server is disabled.
      type: bool
    expose_route_domains:
      description:
        - Allow the GTM server to auto-discover the LTM virtual servers from all
          route domains.
      type: bool
    iq_allow_path:
      description:
        - Whether the GTM uses this BIG-IP system to conduct a path probe before
          delegating traffic to it.
      type: bool
    iq_allow_service_check:
      description:
        - Whether the GTM uses this BIG-IP system to conduct a service check probe
          before delegating traffic to it.
      type: bool
    iq_allow_snmp:
      description:
        - Whether the GTM uses this BIG-IP system to conduct an SNMP probe
          before delegating traffic to it.
      type: bool
    limit_cpu_usage:
      description:
        - For a server configured as a generic host, specifies the percent of CPU
          usage, otherwise has no effect.
    limit_cpu_usage_status:
      description:
        - Whether C(limit_cpu_usage) is enabled for this server.
      type: bool
    limit_max_bps:
      description:
        - Maximum allowable data throughput rate in bits per second for this server.
    limit_max_bps_status:
      description:
        - Whether C(limit_max_bps) is enabled for this server.
      type: bool
    limit_max_connections:
      description:
        - Maximum number of concurrent connections, combind, for this server.
    limit_max_connections_status:
      description:
        - Whether C(limit_max_connections) is enabled for this server.
      type: bool
    limit_max_pps:
      description:
        - Maximum allowable data transfer rate, in packets per second, for this server.
    limit_max_pps_status:
      description:
        - Whether C(limit_max_pps) is enabled for this server.
      type: bool
    limit_mem_available:
      description:
        - For a server configured as a generic host, specifies the available memory
          required by the virtual servers on the server.
        - If available memory falls below this limit, the system marks the server as
          unavailable.
    limit_mem_available_status:
      description:
        - Whether C(limit_mem_available) is enabled for this server.
      type: bool
    link_discovery:
      description:
        - Specifies whether the system auto-discovers the links for this server.
      type: str
    monitors:
      description:
        - Specifies health monitors that the system uses to determine whether this
          server is available for load balancing.
      returned: changed
      type: list
      sample: ['/Common/https_443', '/Common/icmp']
    monitor_type:
      description:
        - Whether one or monitors need to pass, or all monitors need to pass.
      returned: changed
      type: str
      sample: and_list
    product:
      description:
        - Specifies the server type.
    prober_fallback:
      description:
        - The type of prober to use to monitor this servers resources when the
          preferred type is not available.
    prober_preference:
      description:
        - Specifies the type of prober to use to monitor this servers resources.
    virtual_server_discovery:
      description:
        - Whether the system auto-discovers the virtual servers for this server.
      type: str
    addresses:
      description:
        - Specifies the server IP addresses for the server.
      type: complex
    devices:
      description:
        - Specifies the names of the devies that represent this server.
      type: complex.
    virtual_servers:
      description:
        - Virtual servers that are resources for this server.
      type: complex
  sample: hash/dictionary of values
gtm_wide_ips:
  description:
    - GTM Wide IP related facts.
    - Every "type" of wide-ip has the exact same list of possible facts. Therefore,
      the list of facts here is presented once instead of 6 times.
  returned: When any of C(gtm-wide-ips) or C(gtm-*-wide-ips) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/wide1
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: wide1
    description:
      description:
        - Description of the wide ip.
    enabled:
      description:
        - Whether the Wide IP is enabled.
      type: bool
    disabled:
      description:
        - Whether the Wide IP is disabled.
      type: bool
    failure_rcode:
      description:
        - Specifies the DNS RCODE used when C(failure_rcode_response) is C(yes).
    failure_rcode_response:
      description:
        - When C(yes), specifies that the system returns a RCODE response to
          Wide IP requests after exhausting all load-balancing methods.
      type: bool
    failure_rcode_ttl:
      description:
        - Specifies the negative caching TTL of the SOA for the RCODE response.
    last_resort_pool:
      description:
        - Specifies which pool, as listed in Pool List, for the system to use as
          the last resort pool for the wide IP.
    minimal_response:
      description:
        - Specifies that the system forms the smallest allowable DNS response to
          a query.
    persist_cidr_ipv4:
      description:
        - Specifies the number of bits the system uses to identify IPv4 addresses
          when persistence is enabled.
    persist_cidr_ipv6:
      description:
        - Specifies the number of bits the system uses to identify IPv6 addresses
          when persistence is enabled.
    pool_lb_mode:
      description:
        - Specifies the load balancing method used to select a pool in this wide IP.
    ttl_persistence:
      description:
        - Specifies, in seconds, the length of time for which the persistence
          entry is valid.
    pools:
      description:
        - Specifies the pools that this wide IP uses for load balancing.
      type: complex
  sample: hash/dictionary of values
http_monitors:
  description: HTTP monitor related facts.
  returned: When C(http-monitors) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/http
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: http
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: http
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My monitor
    adaptive:
      description:
        - Whether adaptive response time monitoring is enabled for this monitor.
      type: bool
      sample: no
    adaptive_divergence_type:
      description:
        - Specifies whether the adaptive-divergence-value is C(relative) or
          C(absolute).
      type: str
      sample: relative
    adaptive_divergence_value:
      description:
        - Specifies how far from mean latency each monitor probe is allowed
          to be.
      type: int
      sample: 25
    adaptive_limit:
      description:
        - Specifies the hard limit, in milliseconds, which the probe is not
          allowed to exceed, regardless of the divergence value.
      type: int
      sample: 200
    adaptive_sampling_timespan:
      description:
        - Specifies the size of the sliding window, in seconds, which
          records probe history.
      type: int
      sample: 300
    destination:
      description:
        - Specifies the IP address and service port of the resource that is
          the destination of this monitor.
      type: str
      sample: "*:*"
    interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when either the resource is down or the status
          of the resource is unknown.
      type: int
      sample: 5
    ip_dscp:
      description:
        - Specifies the differentiated services code point (DSCP).
      type: int
      sample: 0
    manual_resume:
      description:
        - Specifies whether the system automatically changes the status of a
          resource to up at the next successful monitor check.
      type: bool
      sample: yes
    receive_string:
      description:
        - Specifies the text string that the monitor looks for in the
          returned resource.
      type: str
      sample: check string
    receive_disable_string:
      description:
        - Specifies a text string that the monitor looks for in the returned
          resource. If the text string is matched in the returned resource,
          the corresponding node or pool member is marked session disabled.
      type: str
      sample: check disable string
    reverse:
      description:
        - Specifies whether the monitor operates in reverse mode. When the
          monitor is in reverse mode, a successful check marks the monitored
          object down instead of up.
      type: bool
      sample: no
    send_string:
      description:
        - Specifies the text string that the monitor sends to the target
          object.
      type: str
      sample: "GET /\\r\\n"
    time_until_up:
      description:
        - Specifies the amount of time, in seconds, after the first
          successful response before a node is marked up.
      type: int
      sample: 0
    timeout:
      description:
        - Specifies the number of seconds the target has in which to respond
          to the monitor request.
      type: int
      sample: 16
    transparent:
      description:
        - Specifies whether the monitor operates in transparent mode.
      type: bool
      sample: no
    up_interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when the resource is up.
      type: int
      sample: 0
    username:
      description:
        - Specifies the username, if the monitored target requires
          authentication.
      type: str
      sample: user1
  sample: hash/dictionary of values
https_monitors:
  description: HTTPS monitor related facts.
  returned: When C(https-monitors) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/http
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: http
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: http
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My monitor
    adaptive:
      description:
        - Whether adaptive response time monitoring is enabled for this monitor.
      type: bool
      sample: no
    adaptive_divergence_type:
      description:
        - Specifies whether the adaptive-divergence-value is C(relative) or
          C(absolute).
      type: str
      sample: relative
    adaptive_divergence_value:
      description:
        - Specifies how far from mean latency each monitor probe is allowed
          to be.
      type: int
      sample: 25
    adaptive_limit:
      description:
        - Specifies the hard limit, in milliseconds, which the probe is not
          allowed to exceed, regardless of the divergence value.
      type: int
      sample: 200
    adaptive_sampling_timespan:
      description:
        - Specifies the size of the sliding window, in seconds, which
          records probe history.
      type: int
      sample: 300
    destination:
      description:
        - Specifies the IP address and service port of the resource that is
          the destination of this monitor.
      type: str
      sample: "*:*"
    interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when either the resource is down or the status
          of the resource is unknown.
      type: int
      sample: 5
    ip_dscp:
      description:
        - Specifies the differentiated services code point (DSCP).
      type: int
      sample: 0
    manual_resume:
      description:
        - Specifies whether the system automatically changes the status of a
          resource to up at the next successful monitor check.
      type: bool
      sample: yes
    receive_string:
      description:
        - Specifies the text string that the monitor looks for in the
          returned resource.
      type: str
      sample: check string
    receive_disable_string:
      description:
        - Specifies a text string that the monitor looks for in the returned
          resource. If the text string is matched in the returned resource,
          the corresponding node or pool member is marked session disabled.
      type: str
      sample: check disable string
    reverse:
      description:
        - Specifies whether the monitor operates in reverse mode. When the
          monitor is in reverse mode, a successful check marks the monitored
          object down instead of up.
      type: bool
      sample: no
    send_string:
      description:
        - Specifies the text string that the monitor sends to the target
          object.
      type: str
      sample: "GET /\\r\\n"
    ssl_profile:
      description:
        - Specifies the SSL profile to use for the HTTPS monitor.
      type: str
      sample: /Common/serverssl
    time_until_up:
      description:
        - Specifies the amount of time, in seconds, after the first
          successful response before a node is marked up.
      type: int
      sample: 0
    timeout:
      description:
        - Specifies the number of seconds the target has in which to respond
          to the monitor request.
      type: int
      sample: 16
    transparent:
      description:
        - Specifies whether the monitor operates in transparent mode.
      type: bool
      sample: no
    up_interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when the resource is up.
      type: int
      sample: 0
    username:
      description:
        - Specifies the username, if the monitored target requires
          authentication.
      type: str
      sample: user1
  sample: hash/dictionary of values
http_profiles:
  description: HTTP profile related facts.
  returned: When C(http-profiles) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/http
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: http
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: http
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My profile
    accept_xff:
      description:
        - Enables or disables trusting the client IP address, and statistics
          from the client IP address, based on the request's X-Forwarded-For
          (XFF) headers, if they exist.
      returned: changed
      type: bool
      sample: yes
    allow_truncated_redirects:
      description:
        - Specifies the pass-through behavior when a redirect lacking the
          trailing carriage-return and line feed pair at the end of the headers
          is parsed.
        - When C(no), will silently drop the invalid HTTP.
      returned: changed
      type: bool
      sample: no
    excess_client_headers:
      description:
        - Specifies the pass-through behavior when C(max_header_count) value is
          exceeded by the client.
        - When C(reject), rejects the connection.
      returned: changed
      type: str
      sample: reject
    excess_server_headers:
      description:
        - Specifies the pass-through behavior when C(max_header_count) value is
          exceeded by the server.
        - When C(reject), rejects the connection.
      returned: changed
      type: str
      sample: reject
    known_methods:
      description:
        - Optimizes the behavior of a known HTTP method in the list.
        - The default methods include the following HTTP/1.1 methods. CONNECT,
          DELETE, GET, HEAD, LOCK, OPTIONS, POST, PROPFIND, PUT, TRACE, UNLOCK.
        - If a known method is deleted from the C(known_methods) list, the
          BIG-IP system applies the C(unknown_method) setting to manage that traffic.
      returned: changed
      type: list
      sample: ['CONNECT', 'DELETE', ...]
    max_header_count:
      description:
        - Specifies the maximum number of headers the system supports.
      returned: changed
      type: int
      sample: 64
    max_header_size:
      description:
        - Specifies the maximum size in bytes the system allows for all HTTP
          request headers combined, including the request line.
      returned: changed
      type: int
      sample: 32768
    max_requests:
      description:
        - Specifies the number of requests that the system accepts on a per-connection
          basis.
      returned: changed
      type: int
      sample: 0
    oversize_client_headers:
      description:
        - Specifies the pass-through behavior when the C(max_header_size) value
          is exceeded by the client.
      returned: changed
      type: str
      sample: reject
    oversize_server_headers:
      description:
        - Specifies the pass-through behavior when the C(max_header_size) value
          is exceeded by the server.
      returned: changed
      type: str
      sample: reject
    pipeline_action:
      description:
        - Enables or disables HTTP/1.1 pipelining.
      returned: changed
      type: str
      sample: allow
    unknown_method:
      description:
        - Specifies the behavior (allow, reject, or pass through) when an unknown
          HTTP method is parsed.
      returned: changed
      type: str
      sample: allow
    default_connect_handling:
      description:
        - Specifies the behavior of the proxy service when handling outbound requests.
      returned: changed
      type: str
      sample: deny
    hsts_include_subdomains:
      description:
        - When C(yes), applies the HSTS policy to the HSTS host and its subdomains.
      returned: changed
      type: bool
      sample: yes
    hsts_enabled:
      description:
        - When C(yes), enables the HTTP Strict Transport Security settings.
      returned: changed
      type: bool
      sample: yes
    insert_x_forwarded_for:
      description:
        - When C(yes), specifies that the system inserts an X-Forwarded-For header in
          an HTTP request with the client IP address, to use with connection pooling.
      returned: changed
      type: bool
      sample: no
    lws_max_columns:
      description:
        - Specifies the maximum column width for any given line, when inserting an HTTP
          header in an HTTP request.
      returned: changed
      type: int
      sample: 80
    onconnect_transformations:
      description:
        - When C(yes), specifies, that the system performs HTTP header transformations
          for the purpose of keeping connections open.
      returned: changed
      type: bool
      sample: yes
    proxy_mode:
      description:
        - Specifies the proxy mode for this profile. Either reverse, explicit, or transparent.
      returned: changed
      type: str
      sample: reverse
    redirect_rewrite:
      description:
        - Specifies whether the system rewrites the URIs that are part of HTTP
          redirect (3XX) responses
      returned: changed
      type: str
      sample: none
    request_chunking:
      description:
        - Specifies how the system handles HTTP content that is chunked by a client.
      returned: changed
      type: str
      sample: preserve
    response_chunking:
      description:
        - Specifies how the system handles HTTP content that is chunked by a server.
      returned: changed
      type: str
      sample: selective
    server_agent_name:
      description:
        - Specifies the string used as the server name in traffic generated by LTM.
      returned: changed
      type: str
      sample: BigIP
    sflow_poll_interval:
      description:
        - The maximum interval in seconds between two pollings.
      returned: changed
      type: int
      sample: 0
    sflow_sampling_rate:
      description:
        - Specifies the ratio of packets observed to the samples generated.
      returned: changed
      type: int
      sample: 0
    via_request:
      description:
        - Specifies whether to Remove, Preserve, or Append Via headers included in
          a client request to an origin web server.
      returned: changed
      type: str
      sample: preserve
    via_response:
      description:
        - Specifies whether to Remove, Preserve, or Append Via headers included in
          an origin web server response to a client.
      returned: changed
      type: str
      sample: preserve
  sample: hash/dictionary of values
iapp_services:
  description: iApp v1 service related facts.
  returned: When C(iapp-services) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/service1
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: service1
    device_group:
      description:
        - The device group the iApp service is part of.
      returned: changed
      type: str
      sample: /Common/dg1
    inherited_device_group:
      description:
        - Whether the device group is inherited or not.
      returned: changed
      type: bool
      sample: yes
    inherited_traffic_group:
      description:
        - Whether the traffic group is inherited or not.
      returned: changed
      type: bool
      sample: yes
    strict_updates:
      description:
        - Whether strict updates are enabled or not.
      returned: changed
      type: bool
      sample: yes
    template_modified:
      description:
        - Whether template that the service is based on is modified from its
          default value, or not.
      returned: changed
      type: bool
      sample: yes
    traffic_group:
      description:
        - Traffic group the service is a part of.
      returned: changed
      type: str
      sample: /Common/tg
    tables:
      description:
        - List of the tabular data used to create the service.
      returned: changed
      type: complex
      sample: [{"name": "basic__snatpool_members"},...]
    variables:
      description:
        - List of the variable data used to create the service.
      returned: changed
      type: complex
      sample: [{"name": "afm__policy"},{"encrypted": "no"},{"value": "/#no_not_use#"},...]
    metadata:
      description:
        - List of the metadata data used to create the service..
      returned: changed
      type: complex
      sample: [{"name": "var1"},{"persist": "true"},...]
    lists:
      description:
        - List of the lists data used to create the service.
      returned: changed
      type: complex
      sample: [{"name": "irules__irules"},{"value": []},...]
    description:
      description:
        - Description of the service
      returned: changed
      type: str
      sample: My service
  sample: hash/dictionary of values
icmp_monitors:
  description: ICMP monitor related facts.
  returned: When C(icmp-monitors) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/icmp
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: icmp
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: icmp
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My monitor
    adaptive:
      description:
        - Whether adaptive response time monitoring is enabled for this monitor.
      type: bool
      sample: no
    adaptive_divergence_type:
      description:
        - Specifies whether the adaptive-divergence-value is C(relative) or
          C(absolute).
      type: str
      sample: relative
    adaptive_divergence_value:
      description:
        - Specifies how far from mean latency each monitor probe is allowed
          to be.
      type: int
      sample: 25
    adaptive_limit:
      description:
        - Specifies the hard limit, in milliseconds, which the probe is not
          allowed to exceed, regardless of the divergence value.
      type: int
      sample: 200
    adaptive_sampling_timespan:
      description:
        - Specifies the size of the sliding window, in seconds, which
          records probe history.
      type: int
      sample: 300
    destination:
      description:
        - Specifies the IP address and service port of the resource that is
          the destination of this monitor.
      type: str
      sample: "*:*"
    interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when either the resource is down or the status
          of the resource is unknown.
      type: int
      sample: 5
    manual_resume:
      description:
        - Specifies whether the system automatically changes the status of a
          resource to up at the next successful monitor check.
      type: bool
      sample: yes
    time_until_up:
      description:
        - Specifies the amount of time, in seconds, after the first
          successful response before a node is marked up.
      type: int
      sample: 0
    timeout:
      description:
        - Specifies the number of seconds the target has in which to respond
          to the monitor request.
      type: int
      sample: 16
    transparent:
      description:
        - Specifies whether the monitor operates in transparent mode.
      type: bool
      sample: no
    up_interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when the resource is up.
      type: int
      sample: 0
  sample: hash/dictionary of values
interfaces:
  description: Interface related facts.
  returned: When C(interfaces) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/irul1
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: irule1
    active_media_type:
      description:
        - Displays the current media setting for the interface.
      returned: changed
      type: str
      sample: 100TX-FD
    flow_control:
      description:
        - Specifies how the system controls the sending of PAUSE frames for
          flow control.
      returned: changed
      type: str
      sample: tx-rx
    description:
      description:
        - Description of the interface
      returned: changed
      type: str
      sample: My interface
    bundle:
      description:
        - The bundle capability on the port.
      returned: changed
      type: str
      sample: not-supported
    bundle_speed:
      description:
        - The bundle-speed on the port when bundle capability is
          enabled.
      returned: changed
      type: str
      sample: 100G
    enabled:
      description:
        - Whether the interface is enabled or not
      returned: changed
      type: bool
      sample: yes
    if_index:
      description:
        - The index assigned to this interface.
      returned: changed
      type: int
      sample: 32
    mac_address:
      description:
        - Displays the 6-byte ethernet address in non-case-sensitive
          hexadecimal colon notation.
      returned: changed
      type: str
      sample: "00:0b:09:88:00:9a"
    media_sfp:
      description:
        - The settings for an SFP (pluggable) interface.
      returned: changed
      type: str
      sample: auto
    lldp_admin:
      description:
        - Sets the sending or receiving of LLDP packets on that interface.
          Should be one of C(disable), C(txonly), C(rxonly) or C(txrx).
      returned: changed
      type: str
      sample: txonly
    mtu:
      description:
        - Displays the Maximum Transmission Unit (MTU) of the interface,
          which is the maximum number of bytes in a frame without IP
          fragmentation.
      returned: changed
      type: int
      sample: 1500
    prefer_port:
      description:
        - Indicates which side of a combo port the interface uses, if both
          sides of the port have the potential for external links.
      returned: changed
      type: str
      sample: sfp
    sflow_poll_interval:
      description:
        - Specifies the maximum interval in seconds between two
          pollings.
      returned: changed
      type: int
      sample: 0
    sflow_poll_interval_global:
      description:
        - Specifies whether the global interface poll-interval setting
          overrides the object-level poll-interval setting.
      returned: changed
      type: bool
      sample: yes
    stp_auto_edge_port:
      description:
        - STP edge port detection.
      returned: changed
      type: bool
      sample: yes
    stp_enabled:
      description:
        - Whether STP is enabled or not.
      returned: changed
      type: bool
      sample: no
    stp_link_type:
      description:
        - Specifies the STP link type for the interface.
      returned: changed
      type: str
      sample: auto
  sample: hash/dictionary of values
irules:
  description: iRule related facts.
  returned: When C(irules) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/irul1
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: irule1
    ignore_verification:
      description:
        - Whether the verification of the iRule should be ignored or not.
      returned: changed
      type: bool
      sample: no
    checksum:
      description:
        - Checksum of the iRule as calculated by BIG-IP.
      returned: changed
      type: str
      sample: d41d8cd98f00b204e9800998ecf8427e
    definition:
      description:
        - The actual definition of the iRule.
      returned: changed
      type: str
      sample: when HTTP_REQUEST ...
    signature:
      description:
        - The calculated signature of the iRule.
      returned: changed
      type: str
      sample: WsYy2M6xMqvosIKIEH/FSsvhtWMe6xKOA6i7f...
  sample: hash/dictionary of values
ltm_pools:
  description: List of LTM (Local Traffic Manager) pools.
  returned: When C(ltm-pools) is specified in C(gather_subset).
  type: complex
  contains:
    active_member_count:
      description:
        - The number of active pool members in the pool.
      returned: changed
      type: int
      sample: 3
    all_avg_queue_entry_age:
      description:
        - Average queue entry age, for both the pool and its members.
      returned: changed
      type: int
      sample: 5
    all_max_queue_entry_age_ever:
      description:
        - Maximum queue entry age ever, for both the pool and its members.
      returned: changed
      type: int
      sample: 2
    all_max_queue_entry_age_recently:
      description:
        - Maximum queue entry age recently, for both the pool and its members.
      returned: changed
      type: int
      sample: 5
    all_num_connections_queued_now:
      description:
        - Number of connections queued now, for both the pool and its members.
      returned: changed
      type: int
      sample: 20
    all_num_connections_serviced:
      description:
        - Number of connections serviced, for both the pool and its members.
      returned: changed
      type: int
      sample: 15
    all_queue_head_entry_age:
      description:
        - Queue head entry age, for both the pool and its members.
      returned: changed
      type: int
      sample: 4
    available_member_count:
      description:
        - The number of available pool members in the pool.
      returned: changed
      type: int
      sample: 4
    availability_status:
      description:
        - The availability of the pool.
      returned: changed
      type: str
      sample: offline
    allow_nat:
      description:
        - Whether NATs are automatically enabled or disabled for any connections using this pool.
      returned: changed
      type: bool
      sample: yes
    allow_snat:
      description:
        - Whether SNATs are automatically enabled or disabled for any connections using this pool.
      returned: changed
      type: bool
      sample: yes
    client_ip_tos:
      description:
        - Whether the system sets a Type of Service (ToS) level within a packet sent to the client,
          based on the targeted pool.
        - Values can range from C(0) to C(255), or be set to C(pass-through) or C(mimic).
      returned: changed
      type: str
      sample: pass-through
    client_link_qos:
      description:
        - Whether the system sets a Quality of Service (QoS) level within a packet sent to the client,
          based on the targeted pool.
        - Values can range from C(0) to C(7), or be set to C(pass-through).
      returned: changed
      type: str
      sample: pass-through
    current_sessions:
      descriptions:
        - Current sessions.
      returned: changed
      type: int
      sample: 2
    description:
      description:
        - Description of the pool.
      returned: changed
      type: str
      sample: my pool
    enabled_status:
      description:
        - The enabled-ness of the pool.
      returned: changed
      type: str
      sample: enabled
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/pool1
    ignore_persisted_weight:
      description:
        - Do not count the weight of persisted connections on pool members when making load balancing decisions.
      returned: changed
      type: bool
      sample: no
    lb_method:
      description:
        - Load balancing method used by the pool.
      returned: changed
      type: str
      sample: round-robin
    member_count:
      description:
        - Total number of members in the pool.
      returned: changed
      type: int
      sample: 50
    metadata:
      description:
        - Dictionary of arbitrary key/value pairs set on the pool.
      returned: changed
      type: complex
      sample: hash/dictionary of values
    minimum_active_members:
      description:
        - Whether the system load balances traffic according to the priority number assigned to the pool member.
        - This parameter is identical to C(priority_group_activation) and is just an alias for it.
      returned: changed
      type: int
      sample: 2
    minimum_up_members:
      description:
        - The minimum number of pool members that must be up.
      returned: changed
      type: int
      sample: 1
    minimum_up_members_action:
      description:
        - The action to take if the C(minimum_up_members_checking) is enabled and the number of active pool
          members falls below the number specified in C(minimum_up_members).
      returned: changed
      type: str
      sample: failover
    minimum_up_members_checking:
      description:
        - Enables or disables the C(minimum_up_members) feature.
      returned: changed
      type: bool
      sample: no
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: pool1
    pool_avg_queue_entry_age:
      description:
        - Average queue entry age, for the pool only.
      returned: changed
      type: int
      sample: 5
    pool_max_queue_entry_age_ever:
      description:
        - Maximum queue entry age ever, for the pool only.
      returned: changed
      type: int
      sample: 2
    pool_max_queue_entry_age_recently:
      description:
        - Maximum queue entry age recently, for the pool only.
      returned: changed
      type: int
      sample: 5
    pool_num_connections_queued_now:
      description:
        - Number of connections queued now, for the pool only.
      returned: changed
      type: int
      sample: 20
    pool_num_connections_serviced:
      description:
        - Number of connections serviced, for the pool only.
      returned: changed
      type: int
      sample: 15
    pool_queue_head_entry_age:
      description:
        - Queue head entry age, for the pool only.
      returned: changed
      type: int
      sample: 4
    priority_group_activation:
      description:
        - Whether the system load balances traffic according to the priority number assigned to the pool member.
        - This parameter is identical to C(minimum_active_members) and is just an alias for it.
      returned: changed
      type: int
      sample: 2
    queue_depth_limit:
      description:
        - The maximum number of connections that may simultaneously be queued to go to any member of this pool.
      returned: changed
      type: int
      sample: 3
    queue_on_connection_limit:
      description:
        - Enable or disable queuing connections when pool member or node connection limits are reached.
      returned: changed
      type: bool
      sample: yes
    queue_time_limit:
      description:
        - Specifies the maximum time, in milliseconds, a connection will remain enqueued.
      returned: changed
      type: int
      sample: 0
    real_session:
      description:
        - The actual REST API value for the C(session) attribute.
        - This is different from the C(state) return value, insofar as the return value
          can be considered a generalization of all available sessions, instead of the
          specific value of the session.
      returned: changed
      type: str
      sample: monitor-enabled
    real_state:
      description:
        - The actual REST API value for the C(state) attribute.
        - This is different from the C(state) return value, insofar as the return value
          can be considered a generalization of all available states, instead of the
          specific value of the state.
      returned: changed
      type: str
      sample: up
    reselect_tries:
      description:
        - The number of times the system tries to contact a pool member after a passive failure.
      returned: changed
      type: int
      sample: 0
    server_ip_tos:
      description:
        - The Type of Service (ToS) level to use when sending packets to a server.
      returned: changed
      type: str
      sample: pass-through
    server_link_qos:
      description:
        - The Quality of Service (QoS) level to use when sending packets to a server.
      returned: changed
      type: str
      sample: pass-through
    service_down_action:
      description:
        - The action to take if the service specified in the pool is marked down.
      returned: changed
      type: str
      sample: none
    server_side_bits_in:
      description:
        - Number of server-side ingress bits.
      returned: changed
      type: int
      sample: 1000
    server_side_bits_out:
      description:
        - Number of server-side egress bits.
      returned: changed
      type: int
      sample: 200
    server_side_current_connections:
      description:
        - Number of current connections server-side.
      returned: changed
      type: int
      sample: 300
    server_side_max_connections:
      description:
        - Maximum number of connections server-side.
      returned: changed
      type: int
      sample: 40
    server_side_pkts_in:
      description:
        - Number of server-side ingress packets.
      returned: changed
      type: int
      sample: 1098384
    server_side_pkts_out:
      description:
        - Number of server-side egress packets.
      returned: changed
      type: int
      sample: 3484734
    server_side_total_connections:
      description:
        - Total number of connections.
      returned: changed
      type: int
      sample: 24
    slow_ramp_time:
      description:
        - The ramp time for the pool.
        - This provides the ability to cause a pool member that has just been enabled,
          or marked up, to receive proportionally less traffic than other members in the pool.
      returned: changed
      type: int
      sample: 10
    status_reason:
      description:
        - If there is a problem with the status of the pool, that problem is reported here.
      returned: changed
      type: str
      sample: The children pool member(s) are down.
    members:
      description: List of LTM (Local Traffic Manager) pools.
      returned: when members exist in the pool.
      type: complex
      contains:
        address:
          description: IP address of the pool member.
          returned: changed
          type: str
          sample: 1.1.1.1
        connection_limit:
          description: The maximum number of concurrent connections allowed for a pool member.
          returned: changed
          type: int
          sample: 0
        description:
          description: The description of the pool member.
          returned: changed
          type: str
          sample: pool member 1
        dynamic_ratio:
          description:
            - A range of numbers that you want the system to use in conjunction with the ratio load balancing method.
          returned: changed
          type: int
          sample: 1
        ephemeral:
          description:
            - Whether the node backing the pool member is ephemeral or not.
          returned: changed
          type: bool
          sample: yes
        fqdn_autopopulate:
          description:
            - Whether the node should scale to the IP address set returned by DNS.
          returned: changed
          type: bool
          sample: yes
        full_path:
          description:
            - Full name of the resource as known to BIG-IP.
            - Includes the port in the name
          returned: changed
          type: str
          sample: "/Common/member:80"
        inherit_profile:
          description:
            - Whether the pool member inherits the encapsulation profile from the parent pool.
          returned: changed
          type: bool
          sample: no
        logging:
          description:
            - Whether the monitor applied should log its actions.
          returned: changed
          type: bool
          sample: no
        monitors:
          description:
            - Monitors active on the pool member. Monitor names are in their "full_path" form.
          returned: changed
          type: list
          sample: ['/Common/http']
        name:
          description:
            - Relative name of the resource in BIG-IP.
          returned: changed
          type: str
          sample: "member:80"
        partition:
          description:
            - Partition that the member exists on.
          returned: changed
          type: str
          sample: Common
        priority_group:
          description:
            - The priority group within the pool for this pool member.
          returned: changed
          type: int
          sample: 0
        encapsulation_profile:
          description:
            - The encapsulation profile to use for the pool member.
          returned: changed
          type: str
          sample: ip4ip4
        rate_limit:
          description:
            - The maximum number of connections per second allowed for a pool member.
          returned: changed
          type: bool
          sample: no
        ratio:
          description:
            - The weight of the pool for load balancing purposes.
          returned: changed
          type: int
          sample: 1
        session:
          description:
            - Enables or disables the pool member for new sessions.
          returned: changed
          type: str
          sample: monitor-enabled
        state:
          description:
            - Controls the state of the pool member, overriding any monitors.
          returned: changed
          type: str
          sample: down
    total_requests:
      description:
        - Total requests.
      returned: changed
      type: int
      sample: 8
  sample: hash/dictionary of values
nodes:
  description: Node related facts.
  returned: When C(nodes) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/5.6.7.8
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: 5.6.7.8
    ratio:
      description:
        - Fixed size ratio used for node during C(Ratio) load balancing.
      returned: changed
      type: int
      sample: 10
    description:
      description:
        - Description of the node.
      returned: changed
      type: str
      sample: My node
    connection_limit:
      description:
        - Maximum number of connections that node can handle.
      returned: changed
      type: int
      sample: 100
    address:
      description:
        - IP address of the node.
      returned: changed
      type: str
      sample: 2.3.4.5
    dynamic_ratio:
      description:
        - Dynamic ratio number for the node used when doing C(Dynamic Ratio) load balancing.
      returned: changed
      type: int
      sample: 200
    rate_limit:
      description:
        - Maximum number of connections per second allowed for node.
      returned: changed
      type: int
      sample: 1000
    monitor_status:
      description:
        - Status of the node as reported by the monitor(s) associated with it.
        - This value is also used in determining node C(state).
      returned: changed
      type: str
      sample: down
    session_status:
      description:
        - This value is also used in determining node C(state).
      returned: changed
      type: str
      sample: enabled
    availability_status:
      description:
        - The availability of the node.
      returned: changed
      type: str
      sample: offline
    enabled_status:
      description:
        - The enabled-ness of the node.
      returned: changed
      type: str
      sample: enabled
    status_reason:
      description:
        - If there is a problem with the status of the node, that problem is reported here.
      returned: changed
      type: str
      sample: /Common/https_443 No successful responses received...
    monitor_rule:
      description:
        - A string representation of the full monitor rule.
      returned: changed
      type: str
      sample: /Common/https_443 and /Common/icmp
    monitors:
      description:
        - A list of the monitors identified in the C(monitor_rule).
      returned: changed
      type: list
      sample: ['/Common/https_443', '/Common/icmp']
    monitor_type:
      description:
        - The C(monitor_type) field related to the C(bigip_node) module, for this nodes
          monitors.
      returned: changed
      type: str
      sample: and_list
  sample: hash/dictionary of values
oneconnect_profiles:
  description: OneConnect profile related facts.
  returned: When C(oneconnect-profiles) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/oneconnect
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: oneconnect
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: oneconnect
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My profile
    idle_timeout_override:
      description:
        - Specifies the number of seconds that a connection is idle before
          the connection flow is eligible for deletion.
      returned: changed
      type: int
      sample: 1000
    limit_type:
      description:
        - When C(none), simultaneous in-flight requests and responses over TCP
          connections to a pool member are counted toward the limit.
        - When C(idle), idle connections will be dropped as the TCP connection
          limit is reached.
        - When C(strict), the TCP connection limit is honored with no
          exceptions. This means that idle connections will prevent new TCP
          connections from being made until they expire, even if they could
          otherwise be reused.
      returned: changed
      type: str
      sample: idle
    max_age:
      description:
        - Specifies the maximum age, in number of seconds, of a connection
          in the connection reuse pool.
      returned: changed
      type: int
      sample: 100
    max_reuse:
      description:
        - Specifies the maximum number of times that a server connection can
          be reused.
      returned: changed
      type: int
      sample: 1000
    max_size:
      description:
        - Specifies the maximum number of connections that the system holds
          in the connection reuse pool.
        - If the pool is already full, then the server connection closes after
          the response is completed.
      returned: changed
      type: int
      sample: 1000
    share_pools:
      description:
        - Indicates that connections may be shared not only within a virtual
          server, but also among similar virtual servers.
      returned: changed
      type: bool
      sample: yes
    source_mask:
      description:
        - Specifies a source IP mask.
        - If no mask is provided, the value C(any6) is used.
      returned: changed
      type: str
      sample: 255.255.255.0
  sample: hash/dictionary of values
partitions:
  description: Partition related information.
  returned: When C(partitions) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: Common
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: Common
    description:
      description:
        - Description of the partition.
      returned: changed
      type: str
      sample: Tenant 1
    default_route_domain:
      description:
        - ID of the route domain that is associated with the IP addresses that reside
          in the partition.
      returned: changed
      type: int
      sample: 0
  sample: hash/dictionary of values
provision_info:
  description: Module provisioning related information.
  returned: When C(provision-info) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: asm
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: asm
    cpu_ratio:
      description:
        - Ratio of CPU allocated to this module.
        - Only relevant if C(level) was specified as C(custom). Otherwise, this value
          will be reported as C(0).
      returned: changed
      type: int
      sample: 0
    disk_ratio:
      description:
        - Ratio of disk allocated to this module.
        - Only relevant if C(level) was specified as C(custom). Otherwise, this value
          will be reported as C(0).
      returned: changed
      type: int
      sample: 0
    memory_ratio:
      description:
        - Ratio of memory allocated to this module.
        - Only relevant if C(level) was specified as C(custom). Otherwise, this value
          will be reported as C(0).
      returned: changed
      type: int
      sample: 0
    level:
      description:
        - Provisioned level of the module on BIG-IP.
        - Valid return values can include C(none), C(minimum), C(nominal), C(dedicated)
          and C(custom).
      returned: changed
      type: int
      sample: 0
  sample: hash/dictionary of values
self_ips:
  description: Self-IP related facts.
  returned: When C(self-ips) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/self1
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: self1
    description:
      description:
        - Description of the Self-IP.
      returned: changed
      type: str
      sample: My self-ip
    netmask:
      description:
        - Netmask portion of the IP address. In dotted notation.
      returned: changed
      type: str
      sample: 255.255.255.0
    netmask_cidr:
      description:
        - Netmask portion of the IP address. In CIDR notation.
      returned: changed
      type: int
      sample: 24
    floating:
      description:
        - Whether the Self-IP is a floating address or not.
      returned: changed
      type: bool
      sample: yes
    traffic_group:
      description:
        - Traffic group the Self-IP is associated with.
      returned: changed
      type: str
      sample: /Common/traffic-group-local-only
    service_policy:
      description:
        - Service policy assigned to the Self-IP.
      returned: changed
      type: str
      sample: /Common/service1
    vlan:
      description:
        - VLAN associated with the Self-IP.
      returned: changed
      type: str
      sample: /Common/vlan1
    allow_access_list:
      description:
        - List of protocols and optionally their ports that are allowed to access the
          Self-IP. Also known as port-lockdown in the web interface.
        - Items in the list are in the format of "protocol:port". Some items may not
          have a port associated with them and in those cases the port is C(0).
      returned: changed
      type: list
      sample: ['tcp:80', 'egp:0']
    traffic_group_inherited:
      description:
        - Whether or not the traffic group is inherited.
      returned: changed
      type: bool
      sample: no
  sample: hash/dictionary of values
server_ssl_profiles:
  description: Server SSL related facts.
  returned: When C(server-ssl-profiles) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: serverssl
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: serverssl
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My profile
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: serverssl
    alert_timeout:
      description:
        - Maximum time period in seconds to keep the SSL
          session active after alert message is sent, or indefinite.
      returned: changed
      type: str
      sample: 100
    allow_expired_crl:
      description:
        - Use the specified CRL file even if it has expired.
      returned: changed
      type: bool
      sample: yes
    authentication_frequency:
      description:
        - Specifies the frequency of authentication.
      returned: changed
      type: str
      sample: once
    authenticate_depth:
      description:
        - The client certificate chain maximum traversal depth
      returned: changed
      type: int
      sample: 9
    authenticate_name:
      description:
        - Common Name (CN) that is embedded in a server certificate.
        - The system authenticates a server based on the specified CN.
      returned: changed
      type: str
      sample: foo
    bypass_on_client_cert_fail:
      description:
        - Enables or disables SSL forward proxy bypass on failing to get
          client certificate that server asks for.
      type: bool
      sample: yes
    bypass_on_handshake_alert:
      description:
        - Enables or disables SSL forward proxy bypass on receiving
          handshake_failure, protocol_version or unsupported_extension alert
          message during the serverside SSL handshake.
      type: bool
      sample: no
    c3d_ca_cert:
      description:
        - Name of the certificate file that is used as the
          certification authority certificate when SSL client certificate
          constrained delegation is enabled.
      type: str
      sample: /Common/cacert.crt
    c3d_ca_key:
      description:
        - Name of the key file that is used as the
          certification authority key when SSL client certificate
          constrained delegation is enabled.
      type: str
      sample: /Common/default.key
    c3d_cert_extension_includes:
      description:
        - Extensions of the client certificates to be included
          in the generated certificates using SSL client certificate
          constrained delegation.
      type: list
      sample: [ "basic-constraints", "extended-key-usage", ... ]
    c3d_cert_lifespan:
      description:
        - Lifespan of the certificate generated using the SSL
          client certificate constrained delegation.
      type: int
      sample: 24
    ca_file:
      description:
        - Certificate authority file name.
      type: str
      sample: default.crt
    cache_size:
      description:
        - The SSL session cache size.
      type: int
      sample: 262144
    cache_timeout:
      description:
        - The SSL session cache timeout value, which is the usable
          lifetime seconds of negotiated SSL session IDs.
      type: int
      sample: 86400
    cert:
      description:
        - The name of the certificate installed on the traffic
          management system for the purpose of terminating or initiating an
          SSL connection.
      type: str
      sample: /Common/default.crt
    chain:
      description:
        - Specifies or builds a certificate chain file that a client can use
          to authenticate the profile.
      type: str
      sample: /Common/default.crt
    cipher_group:
      description:
        - Specifies a cipher group.
      type: str
    ciphers:
      description:
        - Specifies a cipher name
      type: str
      sample: DEFAULT
    crl_file:
      description:
        - Specifies the certificate revocation list file name.
      type: str
    expire_cert_response_control:
      description:
        - Specifies the BIGIP action when the server certificate has
          expired.
      type: str
      sample: drop
    handshake_timeout:
      description:
        - Specifies the handshake timeout in seconds.
      type: str
      sample: 10
    key:
      description:
        - Specifies the key file name. Specifies the name of the key
          installed on the traffic management system for the purpose of
          terminating or initiating an SSL connection.
      type: str
      sample: /Common/default.key
    max_active_handshakes:
      description:
        - Specifies the maximum number allowed SSL active handshakes.
      type: str
      sample: 100
    mod_ssl_methods:
      description:
        - Enables or disables ModSSL methods.
      type: bool
      sample: yes
    mode:
      description:
        - Enables or disables SSL processing.
      type: bool
      sample: no
    ocsp:
      description:
        - Specifies the name of ocsp profile for purpose of validating
          status of server certificate.
      type: str
    options:
      description:
        - Enables options, including some industry-related workarounds.
      type: list
      sample: [ "netscape-reuse-cipher-change-bug", "dont-insert-empty-fragments" ]
    peer_cert_mode:
      description:
        - Specifies the peer certificate mode.
      type: str
      sample: ignore
    proxy_ssl:
      description:
        - Allows further modification of application traffic within
          an SSL tunnel while still allowing the server to perform necessary
          authorization, authentication, auditing steps.
      type: bool
      sample: yes
    proxy_ssl_passthrough:
      description:
        - Allows Proxy SSL to passthrough the traffic when ciphersuite negotiated
          between the client and server is not supported.
      type: bool
      sample: yes
    renegotiate_period:
      description:
        - Number of seconds from the initial connect time
          after which the system renegotiates an SSL session.
      type: str
      sample: indefinite
    renegotiate_size:
      description:
        - Specifies a throughput size, in megabytes, of SSL renegotiation.
      type: str
      sample: indefinite
    renegotiation:
      description:
        - Whether renegotiations are enabled.
      type: bool
      sample: yes
    retain_certificate:
      description:
        - APM module requires storing certificate in SSL session. When C(no),
          certificate will not be stored in SSL session.
      type: bool
      sample: no
    generic_alert:
      description:
        - Enables or disables generic-alert.
      type: bool
      sample: yes
    secure_renegotiation:
      description:
        - Specifies the secure renegotiation mode.
      type: str
      sample: require
    server_name:
      description:
        - Server name to be included in SNI (server name
          indication) extension during SSL handshake in ClientHello.
      type: str
    session_mirroring:
      description:
        - Enables or disables the mirroring of sessions to high availability
          peer.
      type: bool
      sample: yes
    session_ticket:
      description:
        - Enables or disables session-ticket.
      type: bool
      sample: no
    sni_default:
      description:
        - When C(yes), this profile is the default SSL profile when the server
          name in a client connection does not match any configured server
          names, or a client connection does not specify any server name at
          all.
      type: bool
      sample: yes
    sni_require:
      description:
        - When C(yes), connections to a server that does not support SNI
          extension will be rejected.
      type: bool
      sample: no
    ssl_c3d:
      description:
        - Enables or disables SSL Client certificate constrained delegation.
      type: bool
      sample: yes
    ssl_forward_proxy_enabled:
      description:
        - Enables or disables ssl-forward-proxy feature.
      type: bool
      sample: no
    ssl_sign_hash:
      description:
        - Specifies SSL sign hash algorithm which is used to sign and verify
          SSL Server Key Exchange and Certificate Verify messages for the
          specified SSL profiles.
      type: str
      sample: sha1
    ssl_forward_proxy_bypass:
      description:
        - Enables or disables ssl-forward-proxy-bypass feature.
      type: bool
      sample: yes
    strict_resume:
      description:
        - Enables or disables the resumption of SSL sessions after an
          unclean shutdown.
      type: bool
      sample: no
    unclean_shutdown:
      description:
        - Specifies, when C(yes), that the SSL profile performs unclean
          shutdowns of all SSL connections, which means that underlying TCP
          connections are closed without exchanging the required SSL
          shutdown alerts.
      type: bool
      sample: yes
    untrusted_cert_response_control:
      description:
        - Specifies the BIGIP action when the server certificate has
          untrusted CA.
      type: str
      sample: drop
  sample: hash/dictionary of values
software_hotfixes:
  description: List of software hotfixes.
  returned: When C(software-hotfixes) is specified in C(gather_subset).
  type: complex
  contains:
    name:
      description:
        - Name of the image.
      returned: changed
      type: str
      sample: Hotfix-BIGIP-13.0.0.3.0.1679-HF3.iso
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: Hotfix-BIGIP-13.0.0.3.0.1679-HF3.iso
    build:
      description:
        - Build number of the image.
        - This is usually a sub-string of the C(name).
      returned: changed
      type: str
      sample: 3.0.1679
    checksum:
      description:
        - MD5 checksum of the image.
        - Note that this is the checksum that is stored inside the ISO. It is not
          the actual checksum of the ISO.
      returned: changed
      type: str
      sample: df1ec715d2089d0fa54c0c4284656a98
    product:
      description:
        - Product contained in the ISO.
      returned: changed
      type: str
      sample: BIG-IP
    id:
      description:
        - ID component of the image.
        - This is usually a sub-string of the C(name).
      returned: changed
      type: str
      sample: HF3
    title:
      description:
        - Human friendly name of the image.
      returned: changed
      type: str
      sample: Hotfix Version 3.0.1679
    verified:
      description:
        - Whether or not the system has verified this image.
      returned: changed
      type: bool
      sample: yes
    version:
      description:
        - Version of software contained in the image.
        - This is a sub-string of the C(name).
      returned: changed
      type: str
      sample: 13.0.0
  sample: hash/dictionary of values
software_images:
  description: List of software images.
  returned: When C(software-images) is specified in C(gather_subset).
  type: complex
  contains:
    name:
      description:
        - Name of the image.
      returned: changed
      type: str
      sample: BIGIP-13.1.0.7-0.0.1.iso
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: BIGIP-13.1.0.7-0.0.1.iso
    build:
      description:
        - Build number of the image.
        - This is usually a sub-string of the C(name).
      returned: changed
      type: str
      sample: 0.0.1
    build_date:
      description:
        - Date of the build.
      returned: changed
      type: str
      sample: "2018-05-05T15:26:30"
    checksum:
      description:
        - MD5 checksum of the image.
        - Note that this is the checksum that is stored inside the ISO. It is not
          the actual checksum of the ISO.
      returned: changed
      type: str
      sample: df1ec715d2089d0fa54c0c4284656a98
    file_size:
      description:
        - Size, in megabytes, of the image.
      returned: changed
      type: int
      sample: 1938
    last_modified:
      description:
        - Last modified date of the ISO.
      returned: changed
      type: str
      sample: "2018-05-05T15:26:30"
    product:
      description:
        - Product contained in the ISO.
      returned: changed
      type: str
      sample: BIG-IP
    verified:
      description:
        - Whether or not the system has verified this image.
      returned: changed
      type: bool
      sample: yes
    version:
      description:
        - Version of software contained in the image.
        - This is a sub-string of the C(name).
      returned: changed
      type: str
      sample: 13.1.0.7
  sample: hash/dictionary of values
software_volumes:
  description: List of software volumes.
  returned: When C(software-volumes) is specified in C(gather_subset).
  type: complex
  contains:
    active:
      description:
        - Whether the volume is currently active or not.
        - An active volume contains the currently running version of software.
      returned: changed
      type: bool
      sample: yes
    base_build:
      description:
        - Base build version of the software installed in the volume.
        - When a hotfix is installed, this refers to the base version of software
          that the hotfix requires.
      returned: changed
      type: str
      sample: 0.0.6
    build:
      description:
        - Build version of the software installed in the volume.
      returned: changed
      type: str
      sample: 0.0.6
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: HD1.1
    default_boot_location:
      description:
        - Whether this volume is the default boot location or not.
      returned: changed
      type: bool
      sample: yes
    name:
      description:
        - Relative name of the resource in BIG-IP.
        - This usually matches the C(full_name).
      returned: changed
      type: str
      sample: HD1.1
    product:
      description:
        - The F5 product installed in this slot.
        - This should always be BIG-IP.
      returned: changed
      type: str
      sample: BIG-IP
    status:
      description:
        - Status of the software installed, or being installed, in the volume.
        - When C(complete), indicates that the software has completed installing.
      returned: changed
      type: str
      sample: complete
    version:
      description:
        - Version of software installed in the volume, excluding the C(build) number.
      returned: changed
      type: str
      sample: 13.1.0.4
  sample: hash/dictionary of values
ssl_certs:
  description: SSL certificate related facts.
  returned: When C(ssl-certs) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/cert1
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: cert1
    key_type:
      description:
        - Specifies the type of cryptographic key associated with this certificate.
      returned: changed
      type: str
      sample: rsa-private
    key_size:
      description:
        - Specifies the size (in bytes) of the file associated with this file object.
      returned: changed
      type: int
      sample: 2048
    system_path:
      description:
        - Path on the BIG-IP where the cert can be found.
      returned: changed
      type: str
      sample: /config/ssl/ssl.crt/f5-irule.crt
    sha1_checksum:
      description:
        - SHA1 checksum of the certificate.
      returned: changed
      type: str
      sample: 1306e84e1e6a2da53816cefe1f684b80d6be1e3e
    subject:
      description:
        - Specifies X509 information of the certificate's subject.
      returned: changed
      type: str
      sample: "emailAddress=support@f5.com,CN=..."
    last_update_time:
      description:
        - Specifies the last time at which the file-object was
          updated/modified.
      returned: changed
      type: str
      sample: "2018-05-15T21:11:15Z"
    issuer:
      description:
        - Specifies X509 information of the certificate's issuer.
      returned: changed
      type: str
      sample: "emailAddress=support@f5.com,...CN=support.f5.com,"
    is_bundle:
      description:
        - Specifies whether the certificate file is a bundle (that is,
          whether it contains more than one certificate).
      returned: changed
      type: bool
      sample: no
    fingerprint:
      description:
        - Displays the SHA-256 fingerprint of the certificate.
      returned: changed
      type: str
      sample: "SHA256/88:A3:05:...:59:01:EA:5D:B0"
    expiration_date:
      description:
        - Specifies a string representation of the expiration date of the
          certificate.
      returned: changed
      type: str
      sample: "Aug 13 21:21:29 2031 GMT"
    expiration_timestamp:
      description:
        - Specifies the date at which this certificate expires. Stored as a
          POSIX time.
      returned: changed
      type: int
      sample: 1944422489
    create_time:
      description:
        - Specifies the time at which the file-object was created.
      returned: changed
      type: str
      sample: "2018-05-15T21:11:15Z"
  sample: hash/dictionary of values
ssl_keys:
  description: SSL certificate related facts.
  returned: When C(ssl-certs) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/key1
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: key1
    key_type:
      description:
        - Specifies the cryptographic type of the key in question. That is,
          which algorithm this key is compatible with.
      returned: changed
      type: str
      sample: rsa-private
    key_size:
      description:
        - Specifies the size of the cryptographic key associated with this
          file object, in bits.
      returned: changed
      type: int
      sample: 2048
    security_type:
      description:
        - Specifies the type of security used to handle or store the key.
      returned: changed
      type: str
      sample: normal
    system_path:
      description:
        - The path on the filesystem where the key is stored.
      returned: changed
      type: str
      sample: /config/ssl/ssl.key/default.key
    sha1_checksum:
      description:
        - The SHA1 checksum of the key.
      returned: changed
      type: str
      sample: 1fcf7de3dd8e834d613099d8e10b2060cd9ecc9f
  sample: hash/dictionary of values
system_db:
  description: System DB related facts.
  returned: When C(system-db) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: vendor.wwwurl
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: vendor.wwwurl
    default:
      description:
        - Default value of the key.
      returned: changed
      type: str
      sample: www.f5.com
    scf_config:
      description:
        - Whether the database key would be found in an SCF config or not.
      returned: changed
      type: str
      sample: false
    value:
      description:
        - The value of the key
      returned: changed
      type: str
      sample: www.f5.com
    value_range:
      description:
        - The accepted range of values for the key
      returned: changed
      type: str
      sample: string
  sample: hash/dictionary of values
system_info:
  description: Traffic group related facts.
  returned: When C(traffic-groups) is specified in C(gather_subset).
  type: complex
  contains:
    base_mac_address:
      description:
        - Media Access Control address (MAC address) of the device.
      returned: changed
      type: str
      sample: "fa:16:3e:c3:42:6f"
    marketing_name:
      description:
        - Marketing name of the device platform.
      returned: changed
      type: str
      sample: BIG-IP Virtual Edition
    time:
      description:
        - Mapping of the current time information to specific time-named keys.
      returned: changed
      type: complex
      contains:
        day:
          description:
            - The current day of the month, in numeric form.
          returned: changed
          type: int
          sample: 7
        hour:
          description:
            - The current hour of the day in 24-hour form.
          returned: changed
          type: int
          sample: 18
        minute:
          description:
            - The current minute of the hour.
          returned: changed
          type: int
          sample: 16
        month:
          description:
            - The current month, in numeric form.
          returned: changed
          type: int
          sample: 6
        second:
          description:
            - The current second of the minute.
          returned: changed
          type: int
          sample: 51
        year:
          description:
            - The current year in 4-digit form.
          returned: changed
          type: int
          sample: 2018
    hardware_information:
      description:
        - Information related to the hardware (drives and CPUs) of the system.
      type: complex
      returned: changed
      contains:
        model:
          description:
            - The model of the hardware.
          type: str
          sample: Virtual Disk
        name:
          description:
            - The name of the hardware.
          type: str
          sample: HD1
        type:
          description:
            - The type of hardware.
          type: str
          sample: physical-disk
        versions:
          description:
            - Hardware specific properties
          type: complex
          contains:
            name:
              description:
                - Name of the property
              type: str
              sample: Size
            version:
              description:
                - Value of the property
              type: str
              sample: 154.00G
    package_edition:
      description:
        - Displays the software edition.
      returned: changed
      type: str
      sample: Point Release 7
    package_version:
      description:
        - A string combining the C(product_build) and C(product_build_date).
      type: str
      sample: "Build 0.0.1 - Tue May 15 15:26:30 PDT 2018"
    product_code:
      description:
        - Code identifying the product.
      type: str
      sample: BIG-IP
    product_build:
      description:
        - Build version of the release version.
      type: str
      sample: 0.0.1
    product_version:
      description:
        - Major product version of the running software.
      type: str
      sample: 13.1.0.7
    product_built:
      description:
        - Unix timestamp of when the product was built.
      type: int
      sample: 180515152630
    product_build_date:
      description:
        - Human readable build date.
      type: str
      sample: "Tue May 15 15:26:30 PDT 2018"
    product_changelist:
      description:
        - Changelist that product branches from.
      type: int
      sample: 2557198
    product_jobid:
      description:
        - ID of the job that built the product version.
      type: int
      sample: 1012030
    chassis_serial:
      description:
        - Serial of the chassis
      type: str
      sample: 11111111-2222-3333-444444444444
    host_board_part_revision:
      description:
        - Revision of the host board.
      type: str
    host_board_serial:
      description:
        - Serial of the host board.
      type: str
    platform:
      description:
        - Platform identifier.
      type: str
      sample: Z100
    switch_board_part_revision:
      description:
        - Switch board revision.
      type: str
    switch_board_serial:
      description:
        - Serial of the switch board.
      type: str
    uptime:
      description:
        - Time, in seconds, since the system booted.
      type: int
      sample: 603202
  sample: hash/dictionary of values
tcp_monitors:
  description: TCP monitor related facts.
  returned: When C(tcp-monitors) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/tcp
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: tcp
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: tcp
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My monitor
    adaptive:
      description:
        - Whether adaptive response time monitoring is enabled for this monitor.
      type: bool
      sample: no
    adaptive_divergence_type:
      description:
        - Specifies whether the adaptive-divergence-value is C(relative) or
          C(absolute).
      type: str
      sample: relative
    adaptive_divergence_value:
      description:
        - Specifies how far from mean latency each monitor probe is allowed
          to be.
      type: int
      sample: 25
    adaptive_limit:
      description:
        - Specifies the hard limit, in milliseconds, which the probe is not
          allowed to exceed, regardless of the divergence value.
      type: int
      sample: 200
    adaptive_sampling_timespan:
      description:
        - Specifies the size of the sliding window, in seconds, which
          records probe history.
      type: int
      sample: 300
    destination:
      description:
        - Specifies the IP address and service port of the resource that is
          the destination of this monitor.
      type: str
      sample: "*:*"
    interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when either the resource is down or the status
          of the resource is unknown.
      type: int
      sample: 5
    ip_dscp:
      description:
        - Specifies the differentiated services code point (DSCP).
      type: int
      sample: 0
    manual_resume:
      description:
        - Specifies whether the system automatically changes the status of a
          resource to up at the next successful monitor check.
      type: bool
      sample: yes
    reverse:
      description:
        - Specifies whether the monitor operates in reverse mode. When the
          monitor is in reverse mode, a successful check marks the monitored
          object down instead of up.
      type: bool
      sample: no
    time_until_up:
      description:
        - Specifies the amount of time, in seconds, after the first
          successful response before a node is marked up.
      type: int
      sample: 0
    timeout:
      description:
        - Specifies the number of seconds the target has in which to respond
          to the monitor request.
      type: int
      sample: 16
    transparent:
      description:
        - Specifies whether the monitor operates in transparent mode.
      type: bool
      sample: no
    up_interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when the resource is up.
      type: int
      sample: 0
  sample: hash/dictionary of values
tcp_half_open_monitors:
  description: TCP Half-open monitor related facts.
  returned: When C(tcp-half-open-monitors) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/tcp
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: tcp
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: tcp
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My monitor
    destination:
      description:
        - Specifies the IP address and service port of the resource that is
          the destination of this monitor.
      type: str
      sample: "*:*"
    interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when either the resource is down or the status
          of the resource is unknown.
      type: int
      sample: 5
    manual_resume:
      description:
        - Specifies whether the system automatically changes the status of a
          resource to up at the next successful monitor check.
      type: bool
      sample: yes
    time_until_up:
      description:
        - Specifies the amount of time, in seconds, after the first
          successful response before a node is marked up.
      type: int
      sample: 0
    timeout:
      description:
        - Specifies the number of seconds the target has in which to respond
          to the monitor request.
      type: int
      sample: 16
    transparent:
      description:
        - Specifies whether the monitor operates in transparent mode.
      type: bool
      sample: no
    up_interval:
      description:
        - Specifies, in seconds, the frequency at which the system issues
          the monitor check when the resource is up.
      type: int
      sample: 0
  sample: hash/dictionary of values
tcp_profiles:
  description: TCP profile related facts.
  returned: When C(tcp-profiles) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: tcp
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: /Common/tcp
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: tcp
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My profile
    abc:
      description:
        - Appropriate Byte Counting (RFC 3465)
        - When C(yes), increases the congestion window by basing the increase
          amount on the number of previously unacknowledged bytes that each ACK covers.
      type: bool
      sample: yes
    ack_on_push:
      description:
        - Specifies, when C(yes), significantly improved performance to Microsoft
          Windows and MacOS peers who are writing out on a very small send buffer.
      type: bool
      sample: no
    auto_proxy_buffer:
      description:
        - Specifies, C(yes), that the system uses the network measurements to set
          the optimal proxy buffer size.
      type: bool
      sample: yes
    auto_receive_window:
      description:
        - Specifies, when C(yes), that the system uses the network measurements to
          set the optimal receive window size.
      type: bool
      sample: no
    auto_send_buffer:
      description:
        - Specifies, when C(yes), that the system uses the network measurements to
          set the optimal send buffer size.
      type: bool
      sample: yes
    close_wait:
      description:
        - Specifies the length of time that a TCP connection remains in the LAST-ACK
          state before quitting.
        - In addition to a numeric value, the value of this fact may also be one of
          C(immediate) or C(indefinite).
        - When C(immediate), specifies that the TCP connection closes immediately
          after entering the LAST-ACK state.
        - When C(indefinite), specifies that TCP connections in the LAST-ACK state
          do not close until they meet the maximum retransmissions timeout.
      type: str
      sample: indefinite
    congestion_metrics_cache:
      description:
        - Specifies, when C(yes), that the system uses a cache for storing congestion
          metrics.
        - Subsequently, because these metrics are already known and cached, the initial
          slow-start ramp for previously-encountered peers improves.
      type: bool
      sample: yes
    congestion_metrics_cache_timeout:
      description:
        - Specifies the number of seconds for which entries in the congestion metrics
          cache are valid.
      type: int
      sample: 0
    congestion_control:
      description:
        - Specifies the algorithm to use to share network resources among competing
          users to reduce congestion.
        - Return values may include, C(high-speed), C(cdg), C(chd), C(none), C(cubic),
          C(illinois), C(new-reno), C(reno), C(scalable), C(vegas), C(westwood), and
          C(woodside).
      type: str
      sample: high-speed
    deferred_accept:
      description:
        - Specifies, when C(yes), that the system defers allocation of the connection
          chain context until the system has received the payload from the client.
        - Enabling this setting is useful in dealing with 3-way handshake denial-of-service
          attacks.
      type: bool
      sample: yes
    delay_window_control:
      description:
        - Specifies that the system uses an estimate of queuing delay as a measure of
          congestion to control, in addition to the normal loss-based control, the amount
          of data sent.
      type: bool
      sample: yes
    delayed_acks:
      description:
        - Specifies, when checked (enabled), that the system can send fewer than one ACK
          (acknowledgment) segment per data segment received.
      type: bool
      sample: yes
    dsack:
      description:
        - D-SACK (RFC 2883)
        - Specifies, when C(yes), the use of the selective ACK (SACK) option to acknowledge
          duplicate segments.
      type: bool
      sample: yes
    early_retransmit:
      description:
        - Specifies, when C(yes), that the system uses early retransmit (as specified in
          RFC 5827) to reduce the recovery time for connections that are receive- buffer
          or user-data limited.
      type: bool
      sample: yes
    explicit_congestion_notification:
      description:
        - Specifies, when C(yes), that the system uses the TCP flags CWR (congestion window
          reduction) and ECE (ECN-Echo) to notify its peer of congestion and congestion
          counter-measures.
      type: bool
      sample: yes
    enhanced_loss_recovery:
      description:
        - Specifies whether the system uses enhanced loss recovery to recover from random
          packet losses more effectively.
      type: bool
      sample: yes
    fast_open:
      description:
        - Specifies, when C(yes), that the system supports TCP Fast Open, which reduces
          latency by allowing a client to include the first packet of data with the SYN
      type: bool
      sample: yes
    fast_open_cookie_expiration:
      description:
        - Specifies the number of seconds that a Fast Open Cookie delivered to a client
          is valid for SYN packets from that client.
      type: int
      sample: 1000
    fin_wait_1:
      description:
        - Specifies the length of time that a TCP connection is in the FIN-WAIT-1 or
          CLOSING state before quitting.
      type: str
      sample: indefinite
    fin_wait_2:
      description:
        - Specifies the length of time that a TCP connection is in the FIN-WAIT-2 state
          before quitting.
      type: str
      sample: 100
    idle_timeout:
      description:
        - Specifies the length of time that a connection is idle (has no traffic) before
          the connection is eligible for deletion.
      type: str
      sample: 300
    initial_congestion_window_size:
      description:
        - Specifies the initial congestion window size for connections to this destination.
      type: int
      sample: 3
    initial_receive_window_size:
      description:
        - Specifies the initial receive window size for connections to this destination.
      type: int
      sample: 5
    dont_fragment_flag:
      description:
        - Specifies the Don't Fragment (DF) bit setting in the IP Header of the outgoing
          TCP packet.
      type: str
      sample: pmtu
    ip_tos:
      description:
        - Specifies the L3 Type of Service (ToS) level that the system inserts in TCP
          packets destined for clients.
      type: str
      sample: mimic
    time_to_live:
      description:
        - Specifies the outgoing TCP packet's IP Header TTL mode.
      type: str
      sample: proxy
    time_to_live_v4:
      description:
        - Specifies the outgoing packet's IP Header TTL value for IPv4 traffic.
      type: int
      sample: 255
    time_to_live_v6:
      description:
        - Specifies the outgoing packet's IP Header TTL value for IPv6 traffic.
      type: int
      sample: 64
    keep_alive_interval:
      description:
        - Specifies how frequently the system sends data over an idle TCP
          connection, to determine whether the connection is still valid.
      type: str
      sample: 50
    limited_transmit_recovery:
      description:
        - Specifies, when C(yes), that the system uses limited transmit recovery
          revisions for fast retransmits (as specified in RFC 3042) to reduce
          the recovery time for connections on a lossy network.
      type: bool
      sample: yes
    link_qos:
      description:
        - Specifies the L2 Quality of Service (QoS) level that the system inserts
          in TCP packets destined for clients.
      type: str
      sample: 200
    max_segment_retrans:
      description:
        - Specifies the maximum number of times that the system resends data segments.
      type: int
      sample: 8
    max_syn_retrans:
      description:
        - Specifies the maximum number of times that the system resends a SYN
          packet when it does not receive a corresponding SYN-ACK.
      type: int
      sample: 3
    max_segment_size:
      description:
        - Specifies the largest amount of data that the system can receive in a
          single TCP segment, not including the TCP and IP headers.
      type: int
      sample: 1460
    md5_signature:
      description:
        - Specifies, when C(yes), to use RFC2385 TCP-MD5 signatures to protect
          TCP traffic against intermediate tampering.
      type: bool
      sample: yes
    minimum_rto:
      description:
        - Specifies the minimum length of time the system waits for
          acknowledgements of data sent before resending the data.
      type: int
      sample: 1000
    multipath_tcp:
      description:
        - Specifies, when C(yes), that the system accepts Multipath TCP (MPTCP)
          connections, which allow multiple client-side flows to connect to a
          single server-side flow.
      type: bool
      sample: yes
    mptcp_checksum:
      description:
        - Specifies, when C(yes), that the system calculates the checksum for
          MPTCP connections.
      type: bool
      sample: no
    mptcp_checksum_verify:
      description:
        - Specifies, when C(yes), that the system verifies the checksum for
          MPTCP connections.
      type: bool
      sample: no
    mptcp_fallback:
      description:
        - Specifies an action on fallback, that is, when MPTCP transitions
          to regular TCP, because something prevents MPTCP from working correctly.
      type: str
      sample: reset
    mptcp_fast_join:
      description:
        - Specifies, when C(yes), a FAST join, allowing data to be sent on the
          MP_JOIN_SYN, which can allow a server response to occur in parallel
          with the JOIN.
      type: bool
      sample: no
    mptcp_idle_timeout:
      description:
        - Specifies the number of seconds that an MPTCP connection is idle
          before the connection is eligible for deletion.
      type: int
      sample: 300
    mptcp_join_max:
      description:
        - Specifies the highest number of MPTCP connections that can join to
          a given connection.
      type: int
      sample: 5
    mptcp_make_after_break:
      description:
        - Specifies that make-after-break functionality is supported, allowing
          for long-lived MPTCP sessions.
      type: bool
      sample: no
    mptcp_no_join_dss_ack:
      description:
        - Specifies, when checked (enabled), that no DSS option is sent on the
          JOIN ACK.
      type: bool
      sample: no
    mptcp_rto_max:
      decription:
        - Specifies the number of RTOs (retransmission timeouts) before declaring
          the subflow dead.
      type: int
      sample: 5
    mptcp_retransmit_min:
      description:
        - Specifies the minimum value (in msec) of the retransmission timer for
          these MPTCP flows.
      type: int
      sample: 1000
    mptcp_subflow_max:
      description:
        - Specifies the maximum number of MPTCP subflows for a single flow.
      type: int
      sample: 6
    mptcp_timeout:
      description:
        - Specifies, in seconds, the timeout value to discard long-lived sessions
          that do not have an active flow.
      type: int
      sample: 3600
    nagle_algorithm:
      description:
        - Specifies whether the system applies Nagle's algorithm to reduce the
          number of short segments on the network.
      type: bool
      sample: no
    pkt_loss_ignore_burst:
      description:
        - Specifies the probability of performing congestion control when
          multiple packets are lost, even if the Packet Loss Ignore Rate was
          not exceeded.
      type: int
      sample: 0
    pkt_loss_ignore_rate:
      description:
        - Specifies the threshold of packets lost per million at which the
          system performs congestion control.
      type: int
      sample: 0
    proxy_buffer_high:
      description:
        - Specifies the proxy buffer level, in bytes, at which the receive window
          is closed.
      type: int
      sample: 49152
    proxy_buffer_low:
      description:
        - Specifies the proxy buffer level, in bytes, at which the receive window
          is opened.
      type: int
      sample: 32768
    proxy_max_segment:
      description:
        - Specifies, when C(yes), that the system attempts to advertise the same
          maximum segment size (MSS) to the server-side connection as that of the
          client-side connection.
      type: bool
      sample: yes
    proxy_options:
      description:
        - Specifies, when C(yes), that the system advertises an option (such as
          time stamps) to the server only when the option is negotiated with the
          client.
      type: bool
      sample: no
    push_flag:
      description:
        - Specifies how the BIG-IP system receives ACKs.
      type: str
      sample: default
    rate_pace:
      description:
        - Specifies, when C(yes), that the system paces the egress packets to
          avoid dropping packets, allowing for optimum goodput.
      type: bool
      sample: yes
    rate_pace_max_rate:
      description:
        - Specifies the maximum rate in bytes per second to which the system
          paces TCP data transmission.
      type: int
      sample: 0
    receive_window:
      description:
        - Specifies the maximum advertised RECEIVE window size.
      type: int
      sample: 65535
    reset_on_timeout:
      description:
        - Specifies, when C(yes), that the system sends a reset packet (RST)
          in addition to deleting the connection, when a connection exceeds
          the idle timeout value.
      type: bool
      sample: yes
    retransmit_threshold:
      description:
        - Specifies the number of duplicate ACKs (retransmit threshold) to start
          fast recovery.
      type: int
      sample: 3
    selective_acks:
      description:
        - Specifies, when C(yes), that the system processes data using
          selective ACKs (SACKs) whenever possible, to improve system performance.
      type: bool
      sample: yes
    selective_nack:
      description:
        - Specifies, when C(yes), that the system processes data using a selective
          negative acknowledgment (SNACK) whenever possible, to improve system
          performance.
      type: bool
      sample: yes
    send_buffer:
      description:
        - Specifies the SEND window size.
      type: int
      sample: 65535
    slow_start:
      description:
        - Specifies, when C(yes), that the system uses Slow-Start Congestion
          Avoidance as described in RFC3390 in order to ramp up traffic without
          causing excessive congestion on the link.
      type: bool
      sample: yes
    syn_cookie_enable:
      description:
        - Specifies the default (if no DoS profile is associated) number of
          embryonic connections that are allowed on any virtual server,
          before SYN Cookie challenges are enabled for that virtual server.
      type: bool
      sample: yes
    syn_cookie_white_list:
      description:
        - Specifies whether or not to use a SYN Cookie WhiteList when doing
          software SYN Cookies.
      type: bool
      sample: no
    syn_retrans_to_base:
      description:
        - Specifies the initial RTO (Retransmission TimeOut) base multiplier
          for SYN retransmissions.
      type: int
      sample: 3000
    tail_loss_probe:
      description:
        - Specifies, when C(yes), that the system uses Tail Loss Probe to
          reduce the number of retransmission timeouts.
      type: bool
      sample: yes
    time_wait_recycle:
      description:
        - Specifies, when C(yes), that connections in a TIME-WAIT state are
          reused when the system receives a SYN packet, indicating a request
          for a new connection.
      type: bool
      sample: yes
    time_wait:
      description:
        - Specifies the length of time that a TCP connection remains in the
          TIME-WAIT state before entering the CLOSED state.
      type: str
      sample: 2000
    timestamps:
      description:
        - Specifies, when C(yes), that the system uses the timestamps extension
          for TCP (as specified in RFC 1323) to enhance high-speed network performance.
      type: bool
      sample: yes
    verified_accept:
      description:
        - Specifies, when C(yes), that the system can actually communicate with
          the server before establishing a client connection.
      type: bool
      sample: yes
    zero_window_timeout:
      description:
        - Specifies the timeout in milliseconds for terminating a connection
          with an effective zero length TCP transmit window.
      type: str
      sample: 2000
  sample: hash/dictionary of values
traffic_groups:
  description: Traffic group related facts.
  returned: When C(traffic-groups) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/tg1
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: tg1
    description:
      description:
        - Description of the traffic group.
      returned: changed
      type: str
      sample: My traffic group
    auto_failback_enabled:
      description:
        - Specifies whether the traffic group fails back to the default
          device.
      returned: changed
      type: bool
      sample: yes
    auto_failback_time:
      description:
        - Specifies the time required to fail back.
      returned: changed
      type: int
      sample: 60
    ha_load_factor:
      description:
        - Specifies a number for this traffic group that represents the load
          this traffic group presents to the system relative to other
          traffic groups.
      returned: changed
      type: int
      sample: 1
    ha_order:
      description:
        - This list of devices specifies the order in which the devices will
          become active for the traffic group when a failure occurs.
      returned: changed
      type: list
      sample: ['/Common/device1', '/Common/device2']
    is_floating:
      description:
        - Indicates whether the traffic group can fail over to other devices
          in the device group.
      returned: changed
      type: bool
      sample: no
    mac_masquerade_address:
      description:
        - Specifies a MAC address for the traffic group.
      returned: changed
      type: str
      sample: "00:98:76:54:32:10"
  sample: hash/dictionary of values
trunks:
  description: Trunk related facts.
  returned: When C(trunks) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/trunk1
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: trunk1
    description:
      description:
        - Description of the Trunk.
      returned: changed
      type: str
      sample: My trunk
    media_speed:
      description:
        - Speed of the media attached to the trunk.
      returned: changed
      type: int
      sample: 10000
    lacp_mode:
      description:
        - The operation mode for LACP.
      returned: changed
      type: str
      sample: passive
    lacp_enabled:
      description:
        - Whether LACP is enabled or not.
      returned: changed
      type: bool
      sample: yes
    stp_enabled:
      description:
        - Whether Spanning Tree Protocol (STP) is enabled or not.
      returned: changed
      type: bool
      sample: yes
    operational_member_count:
      description:
        - Number of working members associated with the trunk.
      returned: changed
      type: int
      sample: 1
    media_status:
      description:
        - Whether the media that is part of the trunk is up or not.
      returned: changed
      type: bool
      sample: yes
    link_selection_policy:
      description:
        - The LACP policy that the trunk uses to determine which member link can handle
          new traffic.
      returned: changed
      type: str
      sample: maximum-bandwidth
    lacp_timeout:
      description:
        - The rate at which the system sends the LACP control packets.
      returned: changed
      type: int
      sample: 10
    interfaces:
      description:
        - The list of interfaces that are part of the trunk.
      returned: changed
      type: list
      sample: ['1.2', '1.3']
    distribution_hash:
      description:
        - The basis for the has that the system uses as the frame distribution algorithm.
        - The system uses this hash to determine which interface to use for forwarding
          traffic.
      returned: changed
      type: str
      sample: src-dst-ipport
    configured_member_count:
      description:
        - The number of configured members that are associated with the trunk.
      returned: changed
      type: int
      sample: 1
  sample: hash/dictionary of values
udp_profiles:
  description: UDP profile related facts.
  returned: When C(udp-profiles) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: udp
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: /Common/udp
    parent:
      description:
        - Profile from which this profile inherits settings.
      returned: changed
      type: str
      sample: udp
    description:
      description:
        - Description of the resource.
      returned: changed
      type: str
      sample: My profile
    allow_no_payload:
      description:
        - Allow the passage of datagrams that contain header information, but no essential data.
      returned: changed
      type: bool
      sample: yes
    buffer_max_bytes:
      description:
        - Ingress buffer byte limit. Maximum allowed value is 16777215.
      returned: changed
      type: int
      sample: 655350
    buffer_max_packets:
      description:
        - Ingress buffer packet limit. Maximum allowed value is 255.
      returned: changed
      type: int
      sample: 0
    datagram_load_balancing:
      description:
        - Load balance UDP datagram by datagram
      returned: changed
      type: bool
      sample: yes
    idle_timeout:
      description:
        - Number of seconds that a connection is idle before
          the connection is eligible for deletion.
        - In addition to a number, may be one of the values C(indefinite), or
          C(immediate).
      returned: changed
      type: bool
      sample: 200
    ip_df_mode:
      description:
        - Describes the Don't Fragment (DF) bit setting in the outgoing UDP
          packet.
        - May be one of C(pmtu), C(preserve), C(set), or C(clear).
        - When C(pmtu), sets the outgoing UDP packet DF big based on the ip
          pmtu setting.
        - When C(preserve), preserves the incoming UDP packet Don't Fragment bit.
        - When C(set), sets the outgoing UDP packet DF bit.
        - When C(clear), clears the outgoing UDP packet DF bit.
      returned: changed
      type: str
      sample: pmtu
    ip_tos_to_client:
      description:
        - The Type of Service level that the traffic management
          system assigns to UDP packets when sending them to clients.
        - May be numeric, or the values C(pass-through) or C(mimic).
      returned: changed
      type: str
      sample: mimic
    ip_ttl_mode:
      description:
        - The outgoing UDP packet's TTL mode.
        - Valid modes are C(proxy), C(preserve), C(decrement), and C(set).
        - When C(proxy), set the IP TTL of ipv4 to the default value of 255 and
          ipv6 to the default value of 64.
        - When C(preserve), set the IP TTL to the original packet TTL value.
        - When C(decrement), set the IP TTL to the original packet TTL value minus 1.
        - When C(set), set the IP TTL with the specified values in C(ip_ttl_v4) and
          C(ip_ttl_v6) values in the same profile.
      returned: changed
      type: str
      sample: proxy
    ip_ttl_v4:
      description:
        - IPv4 TTL.
      returned: changed
      type: int
      sample: 10
    ip_ttl_v6:
      description:
        - IPv6 TTL.
      returned: changed
      type: int
      sample: 100
    link_qos_to_client:
      description:
        - The Quality of Service level that the system assigns to
          UDP packets when sending them to clients.
        - May be either numberic, or the value C(pass-through).
      returned: changed
      type: str
      sample: pass-through
    no_checksum:
      description:
        - Whether the checksum processing is enabled or disabled.
        - Note that if the datagram is IPv6, the system always performs
          checksum processing.
      returned: changed
      type: bool
      sample: yes
    proxy_mss:
      description:
        - When C(yes), specifies that the system advertises the same mss
          to the server as was negotiated with the client.
      returned: changed
      type: bool
      sample: yes
  sample: hash/dictionary of values
vcmp_guests:
  description: vCMP related facts.
  returned: When C(vcmp-guests) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: guest1
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: guest1
    allowed_slots:
      description:
        - List of slots that the guest is allowed to be assigned to.
      returned: changed
      type: list
      sample: [0, 1, 3]
    assigned_slots:
      description:
        - Slots that the guest is assigned to.
      returned: changed
      type: list
      sample: [0]
    boot_priority:
      description:
        - Specifies boot priority of the guest. Lower number means earlier to boot.
      returned: changed
      type: int
      sample: 65535
    cores_per_slot:
      description:
        - Number of cores that the system allocates to the guest.
      returned: changed
      type: int
      sample: 2
    hostname:
      description:
        - FQDN assigned to the guest.
      returned: changed
      type: str
      sample: guest1.localdomain
    hotfix_image:
      description:
        - hotfix image to install onto any of this guest's newly created virtual disks.
      returned: changed
      type: str
      sample: Hotfix-BIGIP-12.1.3.4-0.0.2-hf1.iso
    initial_image:
      description:
        - Software image to install onto any of this guest's newly created virtual disks.
      returned: changed
      type: str
      sample: BIGIP-12.1.3.4-0.0.2.iso
    mgmt_route:
      description:
        - Management gateway IP address for the guest.
      returned: changed
      type: str
      sample: 2.2.2.1
    mgmt_address:
      description:
        - Management IP address configuration for the guest.
      returned: changed
      type: str
      sample: 2.3.2.3
    mgmt_network:
      description:
        - Accessibility of this vCMP guest's management network.
      returned: changed
      type: str
      sample: bridged
    min_number_of_slots:
      description:
        - Specifies the minimum number of slots that the guest must be assigned to.
      returned: changed
      type: int
      sample: 2
    number_of_slots:
      description:
        - Specifies the number of slots the guest should be assigned to.
        - This number is always greater than, or equal to, C(min_number_of_slots).
      returned: changed
      type: int
      sample: 2
    ssl_mode:
      description:
        - The SSL hardware allocation mode for the guest.
      returned: changed
      type: str
      sample: shared
    state:
      description:
        - Specifies the state of the guest.
        - May be one of C(configured), C(provisioned), or C(deployed).
        - Each state implies the actions of all states before it.
      returned: changed
      type: str
      sample: provisioned
    virtual_disk:
      description:
        - The filename of the virtual disk to use for this guest.
      returned: changed
      type: str
      sample: guest1.img
  sample: hash/dictionary of values
virtual_addresses:
  description: Virtual address related facts.
  returned: When C(virtual-addresses) is specified in C(gather_subset).
  type: complex
  contains:
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/2.3.4.5
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: 2.3.4.5
    address:
      description:
        - The virtual IP address.
      returned: changed
      type: str
      sample: 2.3.4.5
    arp_enabled:
      description:
        - Whether or not ARP is enabled for the specified virtual address.
      returned: changed
      type: bool
      sample: yes
    auto_delete_enabled:
      description:
        - Indicates if the virtual address will be deleted automatically on
          deletion of the last associated virtual server or not.
      returned: changed
      type: bool
      sample: no
    connection_limit:
      description:
        - Concurrent connection limit for one or more virtual
          servers.
      returned: changed
      type: int
      sample: 0
    description:
      description:
        - The description of the virtual address.
      returned: changed
      type: str
      sample: My virtual address
    enabled:
      description:
        - Whether the virtual address is enabled or not.
      returned: changed
      type: bool
      sample: yes
    icmp_echo:
      description:
        - Whether the virtual address should reply to ICMP echo requests.
      returned: changed
      type: bool
      sample: yes
    floating:
      description:
        - Property derived from traffic-group. A floating virtual
          address is a virtual address for a VLAN that serves as a shared
          address by all devices of a BIG-IP traffic-group.
      returned: changed
      type: bool
      sample: yes
    netmask:
      description:
        - Netmask of the virtual address.
      returned: changed
      type: str
      sample: 255.255.255.255
    route_advertisement:
      description:
        - Specifies the route advertisement setting for the virtual address.
      returned: changed
      type: bool
      sample: no
    traffic_group:
      description:
        - Traffic group on which the virtual address is active.
      returned: changed
      type: str
      sample: /Common/traffic-group-1
    spanning:
      description:
        - Whether or not spanning is enabled for the specified virtual address.
      returned: changed
      type: bool
      sample: no
    inherited_traffic_group:
      description:
        - Indicates if the traffic-group is inherited from the parent folder.
      returned: changed
      type: bool
      sample: no
  sample: hash/dictionary of values
virtual_servers:
  description: Virtual address related facts.
  returned: When C(virtual-addresses) is specified in C(gather_subset).
  type: complex
  contains:
    availability_status:
      description:
        - The availability of the virtual server.
      returned: changed
      type: str
      sample: offline
    full_path:
      description:
        - Full name of the resource as known to BIG-IP.
      returned: changed
      type: str
      sample: /Common/2.3.4.5
    name:
      description:
        - Relative name of the resource in BIG-IP.
      returned: changed
      type: str
      sample: 2.3.4.5
    auto_lasthop:
      description:
        - When enabled, allows the system to send return traffic to the MAC address
          that transmitted the request, even if the routing table points to a different
          network or interface.
      returned: changed
      type: str
      sample: default
    bw_controller_policy:
      description:
        - The bandwidth controller for the system to use to enforce a throughput policy
          for incoming network traffic.
      returned: changed
      type: str
      sample: /Common/bw1
    client_side_bits_in:
      description:
        - Number of client-side ingress bits.
      returned: changed
      type: int
      sample: 1000
    client_side_bits_out:
      description:
        - Number of client-side egress bits.
      returned: changed
      type: int
      sample: 200
    client_side_current_connections:
      description:
        - Number of current connections client-side.
      returned: changed
      type: int
      sample: 300
    client_side_evicted_connections:
      description:
        - Number of evicted connections client-side.
      returned: changed
      type: int
      sample: 100
    client_side_max_connections:
      description:
        - Maximum number of connections client-side.
      returned: changed
      type: int
      sample: 40
    client_side_pkts_in:
      description:
        - Number of client-side ingress packets.
      returned: changed
      type: int
      sample: 1098384
    client_side_pkts_out:
      description:
        - Number of client-side egress packets.
      returned: changed
      type: int
      sample: 3484734
    client_side_slow_killed:
      description:
        - Number of slow connections killed, client-side.
      returned: changed
      type: int
      sample: 234
    client_side_total_connections:
      description:
        - Total number of connections.
      returned: changed
      type: int
      sample: 24
    cmp_enabled:
      description:
        - Whether or not clustered multi-processor (CMP) acceleration is enabled.
      returned: changed
      type: bool
      sample: yes
    cmp_mode:
      description:
        - The clustered-multiprocessing mode.
      returned: changed
      type: str
      sample: all-cpus
    connection_limit:
      description:
        - Maximum number of concurrent connections you want to allow for the virtual server.
      returned: changed
      type: int
      sample: 100
    description:
      description:
        - The description of the virtual server.
      returned: changed
      type: str
      sample: My virtual
    enabled:
      description:
        - Whether or not the virtual is enabled.
      returned: changed
      type: bool
      sample: yes
    ephemeral_bits_in:
      description:
        - Number of ephemeral ingress bits.
      returned: changed
      type: int
      sample: 1000
    ephemeral_bits_out:
      description:
        - Number of ephemeral egress bits.
      returned: changed
      type: int
      sample: 200
    ephemeral_current_connections:
      description:
        - Number of ephemeral current connections.
      returned: changed
      type: int
      sample: 300
    ephemeral_evicted_connections:
      description:
        - Number of ephemeral evicted connections.
      returned: changed
      type: int
      sample: 100
    ephemeral_max_connections:
      description:
        - Maximum number of ephemeral connections.
      returned: changed
      type: int
      sample: 40
    ephemeral_pkts_in:
      description:
        - Number of ephemeral ingress packets.
      returned: changed
      type: int
      sample: 1098384
    ephemeral_pkts_out:
      description:
        - Number of ephemeral egress packets.
      returned: changed
      type: int
      sample: 3484734
    ephemeral_slow_killed:
      description:
        - Number of ephemeral slow connections killed.
      returned: changed
      type: int
      sample: 234
    ephemeral_total_connections:
      description:
        - Total number of ephemeral connections.
      returned: changed
      type: int
      sample: 24
    total_software_accepted_syn_cookies:
      description:
        - SYN Cookies Total Software Accepted.
      returned: changed
      type: int
      sample: 0
    total_hardware_accepted_syn_cookies:
      description:
        - SYN Cookies Total Hardware Accepted.
      returned: changed
      type: int
      sample: 0
    total_hardware_syn_cookies:
      description:
        - SYN Cookies Total Hardware
      returned: changed
      type: int
      sample: 0
    hardware_syn_cookie_instances:
      description:
        - Hardware SYN Cookie Instances
      returned: changed
      type: int
      sample: 0
    total_software_rejected_syn_cookies:
      description:
        - Total Software Rejected
      returned: changed
      type: int
      sample: 0
    software_syn_cookie_instances:
      description:
        - Software SYN Cookie Instances
      returned: changed
      type: int
      sample: 0
    current_syn_cache:
      description:
        - Current SYN Cache
      returned: changed
      type: int
      sample: 0
    max_conn_duration:
      description:
        - Max Conn Duration/msec
      returned: changed
      type: int
      sample: 0
    mean_conn_duration:
      description:
        - Mean Conn Duration/msec
      returned: changed
      type: int
      sample: 0
    min_conn_duration:
      description:
        - Min Conn Duration/msec
      returned: changed
      type: int
      sample: 0
    cpu_usage_ratio_last_5_min:
      description:
        - CPU Usage Ratio (%) Last 5 Minutes
      returned: changed
      type: int
      sample: 0
    cpu_usage_ratio_last_5_sec:
      description:
        - CPU Usage Ratio (%) Last 5 Seconds
      returned: changed
      type: int
      sample: 0
    cpu_usage_ratio_last_1_min:
      description:
        - CPU Usage Ratio (%) Last 1 Minute
      returned: changed
      type: int
      sample: 0
    syn_cache_overflow:
      description:
        - SYN Cache Overflow
      returned: changed
      type: int
      sample: 0
    total_software_syn_cookies:
      description:
        - Total Software
      returned: changed
      type: int
      sample: 0
    syn_cookies_status:
      description:
        - SYN Cookies Status
      returned: changed
      type: str
      sample: not-activated
    fallback_persistence_profile:
      description:
        - Fallback persistence profile for the virtual server to use
          when the default persistence profile is not available.
      returned: changed
      type: str
      sample: /Common/fallback1
    persistence_profile:
      description:
        - The persistence profile you want the system to use as the default
          for this virtual server.
      returned: changed
      type: str
      sample: /Common/persist1
    translate_port:
      description:
        - Enables or disables port translation.
      returned: changed
      type: bool
      sample: yes
    translate_address:
      description:
        - Enables or disables address translation for the virtual server.
      returned: changed
      type: bool
      sample: yes
    vlans:
      description:
        - List of VLANs on which the virtual server is either enabled or disabled.
      returned: changed
      type: list
      sample: ['/Common/vlan1', '/Common/vlan2']
    destination:
      description:
        - Name of the virtual address and service on which the virtual server
          listens for connections.
      returned: changed
      type: str
      sample: /Common/2.2.3.3%1:76
    last_hop_pool:
      description:
        - Name of the last hop pool that you want the virtual
          server to use to direct reply traffic to the last hop router.
      returned: changed
      type: str
      sample: /Common/pool1
    nat64_enabled:
      description:
        - Whether or not NAT64 is enabled.
      returned: changed
      type: bool
      sample: yes
    source_port_behavior:
      description:
        - Specifies whether the system preserves the source port of the connection.
      returned: changed
      type: str
      sample: preserve
    ip_intelligence_policy:
      description:
        - IP Intelligence policy assigned to the virtual
      returned: changed
      type: str
      sample: /Common/ip1
    protocol:
      description:
        - IP protocol for which you want the virtual server to direct traffic.
      returned: changed
      type: str
      sample: tcp
    default_pool:
      description:
        - Pool name that you want the virtual server to use as the default pool.
      returned: changed
      type: str
      sample: /Common/pool1
    rate_limit_mode:
      description:
        - Indicates whether the rate limit is applied per virtual object,
          per source address, per destination address, or some combination
          thereof.
      returned: changed
      type: str
      sample: object
    rate_limit_source_mask:
      description:
        - Specifies a mask, in bits, to be applied to the source address as
          part of the rate limiting.
      returned: changed
      type: int
      sample: 0
    rate_limit:
      description:
        - Maximum number of connections per second allowed for a virtual server.
      returned: changed
      type: int
      sample: 34
    snat_type:
      description:
        - Specifies the type of source address translation associated
          with the specified virtual server.
      returned: changed
      type: str
      sample: none
    snat_pool:
      description:
        - Specifies the name of a LSN or SNAT pool used by the specified virtual server.
      returned: changed
      type: str
      sample: /Common/pool1
    status_reason:
      description:
        - If there is a problem with the status of the virtual, that problem is reported here.
      returned: changed
      type: str
      sample: The children pool member(s) either don't have service checking...
    gtm_score:
      description:
        - Specifies a score that is associated with the virtual server.
      returned: changed
      type: int
      sample: 0
    rate_class:
      description:
        - Name of an existing rate class that you want the
          virtual server to use to enforce a throughput policy for incoming
          network traffic.
      returned: changed
      type: str
    rate_limit_destination_mask:
      description:
        - Specifies a mask, in bits, to be applied to the destination
          address as part of the rate limiting.
      returned: changed
      type: int
      sample: 32
    source_address:
      description:
        - Specifies an IP address or network from which the virtual server
          will accept traffic.
      returned: changed
      type: str
      sample: 0.0.0./0
    authentication_profile:
      description:
        - Specifies a list of authentication profile names, separated by
          spaces, that the virtual server uses to manage authentication.
      returned: changed
      type: list
      sample: ['/Common/ssl_drldp']
    connection_mirror_enabled:
      description:
        - Whether or not connection mirroring is enabled.
      returned: changed
      type: bool
      sample: yes
    irules:
      description:
        - List of iRules that customize the virtual server to direct and manage traffic.
      returned: changed
      type: list
      sample: ['/Common/rule1', /Common/rule2']
    security_log_profiles:
      description:
        - Specifies the log profile applied to the virtual server.
      returned: changed
      type: list
      sample: ['/Common/global-network', '/Common/local-dos']
    type:
      description:
        - Virtual server type.
      returned: changed
      type: str
      sample: standard
    destination_address:
      description:
        - Address portion of the C(destination).
      returned: changed
      type: str
      sample: 2.3.3.2
    destination_port:
      description:
        - Port potion of the C(destination).
      returned: changed
      type: int
      sample: 80
    profiles:
      description:
        - List of the profiles attached to the virtual.
      type: complex
      contains:
        context:
          description:
            - Which side of the connection the profile affects; either C(all),
              C(client-side) or C(server-side).
          returned: changed
          type: str
          sample: client-side
        full_path:
          description:
            - Full name of the resource as known to BIG-IP.
          returned: changed
          type: str
          sample: /Common/tcp
        name:
          description:
            - Relative name of the resource in BIG-IP.
          returned: changed
          type: str
          sample: tcp
    total_requests:
      description:
        - Total requests.
      returned: changed
      type: int
      sample: 8
  sample: hash/dictionary of values
vlans:
  description: List of VLAN facts.
  returned: When C(vlans) is specified in C(gather_subset).
  type: complex
  contains:
    auto_lasthop:
      description:
        - Allows the system to send return traffic to the MAC address that transmitted the
          request, even if the routing table points to a different network or interface.
      returned: changed
      type: str
      sample: enabled
    cmp_hash_algorithm:
      description:
        - Specifies how the traffic on the VLAN will be disaggregated.
      returned: changed
      type: str
      sample: default
    description:
      description:
        - Description of the VLAN.
      returned: changed
      type: str
      sample: My vlan
    failsafe_action:
      description:
        - Action for the system to take when the fail-safe mechanism is triggered.
      returned: changed
      type: str
      sample: reboot
    failsafe_enabled:
      description:
        - Whether failsafe is enabled or not.
      returned: changed
      type: bool
      sample: yes
    failsafe_timeout:
      description:
        - Number of seconds that an active unit can run without detecting network traffic
          on this VLAN before it starts a failover.
      returned: changed
      type: int
      sample: 90
    if_index:
      description:
        - Index assigned to this VLAN. It is a unique identifier assigned for all objects
          displayed in the SNMP IF-MIB.
      returned: changed
      type: int
      sample: 176
    learning_mode:
      description:
        - Whether switch ports placed in the VLAN are configured for switch learning,
          forwarding only, or dropped.
      returned: changed
      type: str
      sample: enable-forward
    interfaces:
      description:
        - List of tagged or untagged interfaces and trunks that you want to configure for the VLAN.
      returned: changed
      type: complex
      contains:
        full_path:
          description:
            - Full name of the resource as known to BIG-IP.
          returned: changed
          type: str
          sample: 1.3
        name:
          description:
            - Relative name of the resource in BIG-IP.
          returned: changed
          type: str
          sample: 1.3
        tagged:
          description:
            - Whether the interface is tagged or not.
          returned: changed
          type: bool
          sample: no
    mtu:
      description:
        - Specific maximum transition unit (MTU) for the VLAN.
      returned: changed
      type: int
      sample: 1500
    sflow_poll_interval:
      description:
        - Maximum interval in seconds between two pollings.
      returned: changed
      type: int
      sample: 0
    sflow_poll_interval_global:
      description:
        - Whether the global VLAN poll-interval setting, overrides the object-level
          poll-interval setting.
      returned: changed
      type: bool
      sample: no
    sflow_sampling_rate:
      description:
        - Ratio of packets observed to the samples generated.
      returned: changed
      type: int
      sample: 0
    sflow_sampling_rate_global:
      description:
        - Whether the global VLAN sampling-rate setting, overrides the object-level
          sampling-rate setting.
      returned: changed
      type: bool
      sample: yes
    source_check_enabled:
      description:
        - Specifies that only connections that have a return route in the routing table are accepted.
      returned: changed
      type: bool
      sample: yes
    true_mac_address:
      description:
        - Media access control (MAC) address for the lowest-numbered interface assigned to this VLAN.
      returned: changed
      type: str
      sample: "fa:16:3e:10:da:ff"
    tag:
      description:
        - Tag number for the VLAN.
      returned: changed
      type: int
      sample: 30
  sample: hash/dictionary of values
'''

import datetime
import math
import re
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import to_netmask
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE
from ansible.module_utils.six import iteritems
from ansible.module_utils.six import string_types
from collections import namedtuple
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.icontrol import modules_provisioned
    from library.module_utils.network.f5.icontrol import tmos_version
    from library.module_utils.network.f5.urls import parseStats
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.icontrol import modules_provisioned
    from ansible.module_utils.network.f5.icontrol import tmos_version
    from ansible.module_utils.network.f5.urls import parseStats


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs

        # A list of modules currently provisioned on the device.
        #
        # This list is used by different fact managers to check to see
        # if they should even attempt to gather facts. If the module is
        # not provisioned, then it is likely that the REST API will not
        # return valid data.
        #
        # For example, ASM (at the time of this writing 13.x/14.x) will
        # raise an exception if you attempt to query its APIs if it is
        # not provisioned. An example error message is shown below.
        #
        #  {
        #    "code": 400,
        #    "message": "java.net.ConnectException: Connection refused (Connection refused)",
        #    "referer": "172.18.43.40",
        #    "restOperationId": 18164160,
        #    "kind": ":resterrorresponse"
        #  }
        #
        # This list is provided to the specific fact manager by the
        # master ModuleManager of this module.
        self.provisioned_modules = []

    def exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        return results


class Parameters(AnsibleF5Parameters):
    @property
    def gather_subset(self):
        if isinstance(self._values['gather_subset'], string_types):
            self._values['gather_subset'] = [self._values['gather_subset']]
        elif not isinstance(self._values['gather_subset'], list):
            raise F5ModuleError(
                "The specified gather_subset must be a list."
            )
        tmp = list(set(self._values['gather_subset']))
        tmp.sort()
        self._values['gather_subset'] = tmp

        return self._values['gather_subset']


class BaseParameters(Parameters):
    @property
    def enabled(self):
        return flatten_boolean(self._values['enabled'])

    @property
    def disabled(self):
        return flatten_boolean(self._values['disabled'])

    def _remove_internal_keywords(self, resource):
        resource.pop('kind', None)
        resource.pop('generation', None)
        resource.pop('selfLink', None)
        resource.pop('isSubcollection', None)
        resource.pop('fullPath', None)

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result


class AsmPolicyStatsParameters(BaseParameters):
    api_map = {

    }

    returnables = [
        'policies',
        'policies_active',
        'policies_attached',
        'policies_inactive',
        'policies_unattached',
    ]

    @property
    def policies(self):
        if self._values['policies'] is None or len(self._values['policies']) == 0:
            return None
        return len(self._values['policies'])

    @property
    def policies_active(self):
        if self._values['policies'] is None or len(self._values['policies']) == 0:
            return None
        return len([x for x in self._values['policies'] if x['active'] is True])

    @property
    def policies_inactive(self):
        if self._values['policies'] is None or len(self._values['policies']) == 0:
            return None
        return len([x for x in self._values['policies'] if x['active'] is not True])

    @property
    def policies_attached(self):
        if self._values['policies'] is None or len(self._values['policies']) == 0:
            return None
        return len([x for x in self._values['policies'] if x['active'] is True and len(x['virtualServers']) > 0])

    @property
    def policies_unattached(self):
        if self._values['policies'] is None or len(self._values['policies']) == 0:
            return None
        return len([x for x in self._values['policies'] if x['active'] is True and len(x['virtualServers']) == 0])


class AsmPolicyStatsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(AsmPolicyStatsFactManager, self).__init__(**kwargs)
        self.want = AsmPolicyStatsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(asm_policy_stats=facts)
        return result

    def _exec_module(self):
        if 'asm' not in self.provisioned_modules:
            return []
        facts = self.read_facts()
        results = facts.to_return()
        return results

    def read_facts(self):
        collection = self.read_collection_from_device()
        params = AsmPolicyStatsParameters(params=collection)
        return params

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/asm/policies".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return dict(
            policies=response['items']
        )


class AsmPolicyFactParameters(BaseParameters):
    api_map = {
        'hasParent': 'has_parent',
        'protocolIndependent': 'protocol_independent',
        'virtualServers': 'virtual_servers',
        'allowedResponseCodes': 'allowed_response_codes',
        'learningMode': 'learning_mode',
        'enforcementMode': 'enforcement_mode',
        'customXffHeaders': 'custom_xff_headers',
        'caseInsensitive': 'case_insensitive',
        'stagingSettings': 'staging_settings',
        'applicationLanguage': 'application_language',
        'trustXff': 'trust_xff',
        'geolocation-enforcement': 'geolocation_enforcement',
        'disallowedLocations': 'disallowed_locations',
        'signature-settings': 'signature_settings',
        'header-settings': 'header_settings',
        'cookie-settings': 'cookie_settings',
        'policy-builder': 'policy_builder',
        'disallowed-geolocations': 'disallowed_geolocations',
        'whitelist-ips': 'whitelist_ips',
        'fullPath': 'full_path',
        'csrf-protection': 'csrf_protection',
    }

    returnables = [
        'full_path',
        'name',
        'policy_id',
        'active',
        'protocol_independent',
        'has_parent',
        'type',
        'virtual_servers',
        'allowed_response_codes',
        'description',
        'learning_mode',
        'enforcement_mode',
        'custom_xff_headers',
        'case_insensitive',
        'signature_staging',
        'place_signatures_in_staging',
        'enforcement_readiness_period',
        'path_parameter_handling',
        'trigger_asm_irule_event',
        'inspect_http_uploads',
        'mask_credit_card_numbers_in_request',
        'maximum_http_header_length',
        'use_dynamic_session_id_in_url',
        'maximum_cookie_header_length',
        'application_language',
        'trust_xff',
        'disallowed_geolocations',
        'csrf_urls',
        'csrf_protection_enabled',
        'csrf_protection_ssl_only',
        'csrf_protection_expiration_time_in_seconds',
    ]

    def _morph_keys(self, key_map, item):
        for k, v in iteritems(key_map):
            item[v] = item.pop(k, None)
        result = self._filter_params(item)
        return result

    @property
    def active(self):
        return flatten_boolean(self._values['active'])

    @property
    def case_insensitive(self):
        return flatten_boolean(self._values['case_insensitive'])

    @property
    def has_parent(self):
        return flatten_boolean(self._values['has_parent'])

    @property
    def policy_id(self):
        if self._values['id'] is None:
            return None
        return self._values['id']

    @property
    def signature_staging(self):
        if 'staging_settings' in self._values:
            if self._values['staging_settings'] is None:
                return None
            if 'signatureStaging' in self._values['staging_settings']:
                return flatten_boolean(self._values['staging_settings']['signatureStaging'])
        if 'signature_settings' in self._values:
            if self._values['signature_settings'] is None:
                return None
            if 'signatureStaging' in self._values['signature_settings']:
                return flatten_boolean(self._values['signature_settings']['signatureStaging'])

    @property
    def place_signatures_in_staging(self):
        if 'staging_settings' in self._values:
            if self._values['staging_settings'] is None:
                return None
            if 'placeSignaturesInStaging' in self._values['staging_settings']:
                return flatten_boolean(self._values['staging_settings']['placeSignaturesInStaging'])
        if 'signature_settings' in self._values:
            if self._values['signature_settings'] is None:
                return None
            if 'signatureStaging' in self._values['signature_settings']:
                return flatten_boolean(self._values['signature_settings']['placeSignaturesInStaging'])

    @property
    def enforcement_readiness_period(self):
        if 'staging_settings' in self._values:
            if self._values['staging_settings'] is None:
                return None
            if 'enforcementReadinessPeriod' in self._values['staging_settings']:
                return self._values['staging_settings']['enforcementReadinessPeriod']
        if 'general' in self._values:
            if self._values['general'] is None:
                return None
            if 'signatureStaging' in self._values['general']:
                return self._values['general']['enforcementReadinessPeriod']

    @property
    def path_parameter_handling(self):
        if 'attributes' in self._values:
            if self._values['attributes'] is None:
                return None
            if 'pathParameterHandling' in self._values['attributes']:
                return self._values['attributes']['pathParameterHandling']
        if 'general' in self._values:
            if self._values['general'] is None:
                return None
            if 'pathParameterHandling' in self._values['general']:
                return self._values['general']['pathParameterHandling']

    @property
    def trigger_asm_irule_event(self):
        if 'attributes' in self._values:
            if self._values['attributes'] is None:
                return None
            if 'triggerAsmIruleEvent' in self._values['attributes']:
                return self._values['attributes']['triggerAsmIruleEvent']
        if 'general' in self._values:
            if self._values['general'] is None:
                return None
            if 'triggerAsmIruleEvent' in self._values['general']:
                return self._values['general']['triggerAsmIruleEvent']

    @property
    def inspect_http_uploads(self):
        if 'attributes' in self._values:
            if self._values['attributes'] is None:
                return None
            if 'inspectHttpUploads' in self._values['attributes']:
                return flatten_boolean(self._values['attributes']['inspectHttpUploads'])
        if 'antivirus' in self._values:
            if self._values['antivirus'] is None:
                return None
            if 'inspectHttpUploads' in self._values['antivirus']:
                return flatten_boolean(self._values['antivirus']['inspectHttpUploads'])

    @property
    def mask_credit_card_numbers_in_request(self):
        if 'attributes' in self._values:
            if self._values['attributes'] is None:
                return None
            if 'maskCreditCardNumbersInRequest' in self._values['attributes']:
                return flatten_boolean(self._values['attributes']['maskCreditCardNumbersInRequest'])
        if 'general' in self._values:
            if self._values['general'] is None:
                return None
            if 'maskCreditCardNumbersInRequest' in self._values['general']:
                return flatten_boolean(self._values['general']['maskCreditCardNumbersInRequest'])

    @property
    def maximum_http_header_length(self):
        if 'attributes' in self._values:
            if self._values['attributes'] is None:
                return None
            if 'maximumHttpHeaderLength' in self._values['attributes']:
                if self._values['attributes']['maximumHttpHeaderLength'] == 'any':
                    return 'any'
                return int(self._values['attributes']['maximumHttpHeaderLength'])

        if 'header_settings' in self._values:
            if self._values['header_settings'] is None:
                return None
            if 'maximumHttpHeaderLength' in self._values['header_settings']:
                if self._values['header_settings']['maximumHttpHeaderLength'] == 'any':
                    return 'any'
                return int(self._values['header_settings']['maximumHttpHeaderLength'])

    @property
    def use_dynamic_session_id_in_url(self):
        if 'attributes' in self._values:
            if self._values['attributes'] is None:
                return None
            if 'useDynamicSessionIdInUrl' in self._values['attributes']:
                return flatten_boolean(self._values['attributes']['useDynamicSessionIdInUrl'])
        if 'general' in self._values:
            if self._values['general'] is None:
                return None
            if 'useDynamicSessionIdInUrl' in self._values['general']:
                return flatten_boolean(self._values['general']['useDynamicSessionIdInUrl'])

    @property
    def maximum_cookie_header_length(self):
        if 'attributes' in self._values:
            if self._values['attributes'] is None:
                return None
            if 'maximumCookieHeaderLength' in self._values['attributes']:
                if self._values['attributes']['maximumCookieHeaderLength'] == 'any':
                    return 'any'
                return int(self._values['attributes']['maximumCookieHeaderLength'])
        if 'cookie_settings' in self._values:
            if self._values['cookie_settings'] is None:
                return None
            if 'maximumCookieHeaderLength' in self._values['cookie_settings']:
                if self._values['cookie_settings']['maximumCookieHeaderLength'] == 'any':
                    return 'any'
                return int(self._values['cookie_settings']['maximumCookieHeaderLength'])

    @property
    def trust_xff(self):
        if 'trust_xff' in self._values:
            if self._values['trust_xff'] is None:
                return None
            return flatten_boolean(self._values['trust_xff'])
        if 'general' in self._values:
            if self._values['general'] is None:
                return None
            if 'trustXff' in self._values['general']:
                return flatten_boolean(self._values['general']['trustXff'])

    @property
    def custom_xff_headers(self):
        if 'custom_xff_headers' in self._values:
            if self._values['custom_xff_headers'] is None:
                return None
            return self._values['custom_xff_headers']
        if 'general' in self._values:
            if self._values['general'] is None:
                return None
            if 'customXffHeaders' in self._values['general']:
                return self._values['general']['customXffHeaders']

    @property
    def allowed_response_codes(self):
        if 'allowed_response_codes' in self._values:
            if self._values['allowed_response_codes'] is None:
                return None
            return self._values['allowed_response_codes']
        if 'general' in self._values:
            if self._values['general'] is None:
                return None
            if 'allowedResponseCodes' in self._values['general']:
                return self._values['general']['allowedResponseCodes']

    @property
    def learning_mode(self):
        if 'policy_builder' in self._values:
            if self._values['policy_builder'] is None:
                return None
            if 'learningMode' in self._values['policy_builder']:
                return self._values['policy_builder']['learningMode']

    @property
    def disallowed_locations(self):
        if 'geolocation_enforcement' in self._values:
            if self._values['geolocation_enforcement'] is None:
                return None
            return self._values['geolocation_enforcement']['disallowedLocations']

    @property
    def disallowed_geolocations(self):
        if 'disallowed_geolocations' in self._values:
            if self._values['disallowed_geolocations'] is None:
                return None
            return self._values['disallowed_geolocations']

    @property
    def csrf_protection_enabled(self):
        if 'csrf_protection' in self._values:
            return flatten_boolean(self._values['csrf_protection']['enabled'])

    @property
    def csrf_protection_ssl_only(self):
        if 'csrf_protection' in self._values:
            if 'sslOnly' in self._values['csrf_protection']:
                return flatten_boolean(self._values['csrf_protection']['sslOnly'])

    @property
    def csrf_protection_expiration_time_in_seconds(self):
        if 'csrf_protection' in self._values:
            if 'expirationTimeInSeconds' in self._values['csrf_protection']:
                if self._values['csrf_protection']['expirationTimeInSeconds'] is None:
                    return None
                if self._values['csrf_protection']['expirationTimeInSeconds'] == 'disabled':
                    return 'disabled'
                return int(self._values['csrf_protection']['expirationTimeInSeconds'])

    def format_csrf_collection(self, items):
        result = list()
        key_map = {
            'requiredParameters': 'csrf_url_required_parameters',
            'url': 'csrf_url',
            'method': 'csrf_url_method',
            'enforcementAction': 'csrf_url_enforcement_action',
            'id': 'csrf_url_id',
            'wildcardOrder': 'csrf_url_wildcard_order',
            'parametersList': 'csrf_url_parameters_list'
        }
        for item in items:
            self._remove_internal_keywords(item)
            item.pop('lastUpdateMicros')
            output = self._morph_keys(key_map, item)
            result.append(output)
        return result

    @property
    def csrf_urls(self):
        if 'csrfUrls' in self._values:
            if self._values['csrfUrls'] is None:
                return None
            return self._values['csrfUrls']
        if 'csrf-urls' in self._values:
            if self._values['csrf-urls'] is None:
                return None
            return self.format_csrf_collection(self._values['csrf-urls'])

    @property
    def protocol_independent(self):
        return flatten_boolean(self._values['protocol_independent'])


# TODO include: web-scraping,ip-intelligence,session-tracking,
# TODO login-enforcement,data-guard,redirection-protection,vulnerability-assessment, parentPolicyReference


class AsmPolicyFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(AsmPolicyFactManager, self).__init__(**kwargs)
        self.want = AsmPolicyFactParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(asm_policies=facts)
        return result

    def _exec_module(self):
        if 'asm' not in self.provisioned_modules:
            return []
        manager = self.get_manager()
        return manager._exec_module()

    def get_manager(self):
        if self.version_is_less_than_13():
            return AsmPolicyFactManagerV12(**self.kwargs)
        else:
            return AsmPolicyFactManagerV13(**self.kwargs)

    def version_is_less_than_13(self):
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('13.0.0'):
            return True
        else:
            return False

    def read_facts(self):
        results = []
        collection = self.increment_read()
        for resource in collection:
            params = AsmPolicyFactParameters(params=resource)
            results.append(params)
        return results

    def increment_read(self):
        n = 0
        result = []
        while True:
            items = self.read_collection_from_device(skip=n)
            if not items:
                break
            result.extend(items)
            n = n + 10
        return result


class AsmPolicyFactManagerV12(AsmPolicyFactManager):
    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_collection_from_device(self, skip=0):
        uri = "https://{0}:{1}/mgmt/tm/asm/policies".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )

        to_expand = 'policy-builder,geolocation-enforcement,csrf-protection'
        query = '?$top=10&$skip={0}&$expand={1}'.format(skip, to_expand)

        resp = self.client.api.get(uri + query)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        if 'items' not in response:
            return None
        return response['items']


class AsmPolicyFactManagerV13(AsmPolicyFactManager):
    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_collection_from_device(self, skip=0):
        uri = "https://{0}:{1}/mgmt/tm/asm/policies".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        to_expand = 'general,signature-settings,header-settings,cookie-settings,antivirus,' \
                    'policy-builder,csrf-protection,csrf-urls'
        query = '?$top=10&$skip={0}&$expand={1}'.format(skip, to_expand)
        resp = self.client.api.get(uri + query)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        if 'items' not in response:
            return None

        return response['items']


class AsmServerTechnologyFactParameters(BaseParameters):
    api_map = {
        'serverTechnologyName': 'server_technology_name',
        'serverTechnologyReferences': 'server_technology_references',
    }

    returnables = [
        'id',
        'server_technology_name',
        'server_technology_references',
    ]


class AsmServerTechnologyFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(AsmServerTechnologyFactManager, self).__init__(**kwargs)
        self.want = AsmServerTechnologyFactParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(asm_server_technologies=facts)
        return result

    def _exec_module(self):
        results = []
        if 'asm' not in self.provisioned_modules:
            return results
        if self.version_is_less_than_13():
            return results
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['server_technology_name'])
        return results

    def version_is_less_than_13(self):
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('13.0.0'):
            return True
        else:
            return False

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = AsmServerTechnologyFactParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/asm/server-technologies".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class AsmSignatureSetsFactParameters(BaseParameters):
    api_map = {
        'isUserDefined': 'is_user_defined',
        'assignToPolicyByDefault': 'assign_to_policy_by_default',
        'defaultAlarm': 'default_alarm',
        'defaultBlock': 'default_block',
        'defaultLearn': 'default_learn',
    }

    returnables = [
        'name',
        'id',
        'type',
        'category',
        'is_user_defined',
        'assign_to_policy_by_default',
        'default_alarm',
        'default_block',
        'default_learn',
    ]

    @property
    def is_user_defined(self):
        return flatten_boolean(self._values['is_user_defined'])

    @property
    def assign_to_policy_by_default(self):
        return flatten_boolean(self._values['assign_to_policy_by_default'])

    @property
    def default_alarm(self):
        return flatten_boolean(self._values['default_alarm'])

    @property
    def default_block(self):
        return flatten_boolean(self._values['default_block'])

    @property
    def default_learn(self):
        return flatten_boolean(self._values['default_learn'])

# TODO: add the following: filter, systems, signatureReferences


class AsmSignatureSetsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(AsmSignatureSetsFactManager, self).__init__(**kwargs)
        self.want = AsmSignatureSetsFactParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(asm_signature_sets=facts)
        return result

    def _exec_module(self):
        results = []
        if 'asm' not in self.provisioned_modules:
            return results
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['name'])
        return results

    def read_facts(self):
        results = []
        collection = self.increment_read()
        for resource in collection:
            params = AsmSignatureSetsFactParameters(params=resource)
            results.append(params)
        return results

    def increment_read(self):
        n = 0
        result = []
        while True:
            items = self.read_collection_from_device(skip=n)
            if not items:
                break
            result.extend(items)
            n = n + 5
        return result

    def read_collection_from_device(self, skip=0):
        uri = "https://{0}:{1}/mgmt/tm/asm/signature-sets".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        query = '?$top=5&$skip={0}'.format(skip)
        resp = self.client.api.get(uri + query)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        if 'items' not in response:
            return None

        return response['items']


class ClientSslProfilesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'alertTimeout': 'alert_timeout',
        'allowNonSsl': 'allow_non_ssl',
        'authenticateDepth': 'authenticate_depth',
        'authenticate': 'authenticate_frequency',
        'caFile': 'ca_file',
        'cacheSize': 'cache_size',
        'cacheTimeout': 'cache_timeout',
        'cert': 'certificate_file',
        'chain': 'chain_file',
        'crlFile': 'crl_file',
        'defaultsFrom': 'parent',
        'modSslMethods': 'modssl_methods',
        'peerCertMode': 'peer_certification_mode',
        'sniRequire': 'sni_require',
        'strictResume': 'strict_resume',
        'mode': 'profile_mode_enabled',
        'renegotiateMaxRecordDelay': 'renegotiation_maximum_record_delay',
        'renegotiatePeriod': 'renegotiation_period',
        'serverName': 'server_name',
        'sessionTicket': 'session_ticket',
        'sniDefault': 'sni_default',
        'uncleanShutdown': 'unclean_shutdown',
        'retainCertificate': 'retain_certificate',
        'secureRenegotiation': 'secure_renegotiation_mode',
        'handshakeTimeout': 'handshake_timeout',
        'certExtensionIncludes': 'forward_proxy_certificate_extension_include',
        'certLifespan': 'forward_proxy_certificate_lifespan',
        'certLookupByIpaddrPort': 'forward_proxy_lookup_by_ipaddr_port',
        'sslForwardProxy': 'forward_proxy_enabled',
        'proxyCaPassphrase': 'forward_proxy_ca_passphrase',
        'proxyCaCert': 'forward_proxy_ca_certificate_file',
        'proxyCaKey': 'forward_proxy_ca_key_file'
    }

    returnables = [
        'full_path',
        'name',
        'alert_timeout',
        'allow_non_ssl',
        'authenticate_depth',
        'authenticate_frequency',
        'ca_file',
        'cache_size',
        'cache_timeout',
        'certificate_file',
        'chain_file',
        'ciphers',
        'crl_file',
        'parent',
        'description',
        'modssl_methods',
        'peer_certification_mode',
        'sni_require',
        'sni_default',
        'strict_resume',
        'profile_mode_enabled',
        'renegotiation_maximum_record_delay',
        'renegotiation_period',
        'renegotiation',
        'server_name',
        'session_ticket',
        'unclean_shutdown',
        'retain_certificate',
        'secure_renegotiation_mode',
        'handshake_timeout',
        'forward_proxy_certificate_extension_include',
        'forward_proxy_certificate_lifespan',
        'forward_proxy_lookup_by_ipaddr_port',
        'forward_proxy_enabled',
        'forward_proxy_ca_passphrase',
        'forward_proxy_ca_certificate_file',
        'forward_proxy_ca_key_file'
    ]

    @property
    def alert_timeout(self):
        if self._values['alert_timeout'] is None:
            return None
        if self._values['alert_timeout'] == 'indefinite':
            return 0
        return int(self._values['alert_timeout'])

    @property
    def renegotiation_maximum_record_delay(self):
        if self._values['renegotiation_maximum_record_delay'] is None:
            return None
        if self._values['renegotiation_maximum_record_delay'] == 'indefinite':
            return 0
        return int(self._values['renegotiation_maximum_record_delay'])

    @property
    def renegotiation_period(self):
        if self._values['renegotiation_period'] is None:
            return None
        if self._values['renegotiation_period'] == 'indefinite':
            return 0
        return int(self._values['renegotiation_period'])

    @property
    def handshake_timeout(self):
        if self._values['handshake_timeout'] is None:
            return None
        if self._values['handshake_timeout'] == 'indefinite':
            return 0
        return int(self._values['handshake_timeout'])

    @property
    def allow_non_ssl(self):
        if self._values['allow_non_ssl'] is None:
            return None
        if self._values['allow_non_ssl'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def forward_proxy_enabled(self):
        if self._values['forward_proxy_enabled'] is None:
            return None
        if self._values['forward_proxy_enabled'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def renegotiation(self):
        if self._values['renegotiation'] is None:
            return None
        if self._values['renegotiation'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def forward_proxy_lookup_by_ipaddr_port(self):
        if self._values['forward_proxy_lookup_by_ipaddr_port'] is None:
            return None
        if self._values['forward_proxy_lookup_by_ipaddr_port'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def unclean_shutdown(self):
        if self._values['unclean_shutdown'] is None:
            return None
        if self._values['unclean_shutdown'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def session_ticket(self):
        if self._values['session_ticket'] is None:
            return None
        if self._values['session_ticket'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def retain_certificate(self):
        if self._values['retain_certificate'] is None:
            return None
        if self._values['retain_certificate'] == 'true':
            return 'yes'
        return 'no'

    @property
    def server_name(self):
        if self._values['server_name'] in [None, 'none']:
            return None
        return self._values['server_name']

    @property
    def forward_proxy_ca_certificate_file(self):
        if self._values['forward_proxy_ca_certificate_file'] in [None, 'none']:
            return None
        return self._values['forward_proxy_ca_certificate_file']

    @property
    def forward_proxy_ca_key_file(self):
        if self._values['forward_proxy_ca_key_file'] in [None, 'none']:
            return None
        return self._values['forward_proxy_ca_key_file']

    @property
    def authenticate_frequency(self):
        if self._values['authenticate_frequency'] is None:
            return None
        return self._values['authenticate_frequency']

    @property
    def ca_file(self):
        if self._values['ca_file'] in [None, 'none']:
            return None
        return self._values['ca_file']

    @property
    def certificate_file(self):
        if self._values['certificate_file'] in [None, 'none']:
            return None
        return self._values['certificate_file']

    @property
    def chain_file(self):
        if self._values['chain_file'] in [None, 'none']:
            return None
        return self._values['chain_file']

    @property
    def crl_file(self):
        if self._values['crl_file'] in [None, 'none']:
            return None
        return self._values['crl_file']

    @property
    def ciphers(self):
        if self._values['ciphers'] in [None, 'none']:
            return None
        return self._values['ciphers'].split(' ')

    @property
    def modssl_methods(self):
        if self._values['modssl_methods'] is None:
            return None
        if self._values['modssl_methods'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def strict_resume(self):
        if self._values['strict_resume'] is None:
            return None
        if self._values['strict_resume'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def profile_mode_enabled(self):
        if self._values['profile_mode_enabled'] is None:
            return None
        if self._values['profile_mode_enabled'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def sni_require(self):
        if self._values['sni_require'] is None:
            return None
        if self._values['sni_require'] == 'false':
            return 'no'
        return 'yes'

    @property
    def sni_default(self):
        if self._values['sni_default'] is None:
            return None
        if self._values['sni_default'] == 'false':
            return 'no'
        return 'yes'


class ClientSslProfilesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(ClientSslProfilesFactManager, self).__init__(**kwargs)
        self.want = ClientSslProfilesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(client_ssl_profiles=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = ClientSslProfilesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/client-ssl".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class DeviceGroupsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'autoSync': 'autosync_enabled',
        'asmSync': 'asm_sync_enabled',
        'devicesReference': 'devices',
        'fullLoadOnSync': 'full_load_on_sync',
        'incrementalConfigSyncSizeMax': 'incremental_config_sync_size_maximum',
        'networkFailover': 'network_failover_enabled'
    }

    returnables = [
        'full_path',
        'name',
        'autosync_enabled',
        'description',
        'devices',
        'full_load_on_sync',
        'incremental_config_sync_size_maximum',
        'network_failover_enabled',
        'type',
        'asm_sync_enabled'
    ]

    @property
    def network_failover_enabled(self):
        if self._values['network_failover_enabled'] is None:
            return None
        if self._values['network_failover_enabled'] == 'enabled':
            return 'yes'
        return 'no'

    @property
    def asm_sync_enabled(self):
        if self._values['asm_sync_enabled'] is None:
            return None
        if self._values['asm_sync_enabled'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def autosync_enabled(self):
        if self._values['autosync_enabled'] is None:
            return None
        if self._values['autosync_enabled'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def full_load_on_sync(self):
        if self._values['full_load_on_sync'] is None:
            return None
        if self._values['full_load_on_sync'] == 'true':
            return 'yes'
        return 'no'

    @property
    def devices(self):
        if self._values['devices'] is None or 'items' not in self._values['devices']:
            return None
        result = [x['fullPath'] for x in self._values['devices']['items']]
        result.sort()
        return result


class DeviceGroupsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(DeviceGroupsFactManager, self).__init__(**kwargs)
        self.want = DeviceGroupsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(device_groups=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = DeviceGroupsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/cm/device-group/?expandSubcollections=true".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class DevicesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'activeModules': 'active_modules',
        'baseMac': 'base_mac_address',
        'chassisId': 'chassis_id',
        'chassisType': 'chassis_type',
        'configsyncIp': 'configsync_address',
        'failoverState': 'failover_state',
        'managementIp': 'management_address',
        'marketingName': 'marketing_name',
        'multicastIp': 'multicast_address',
        'optionalModules': 'optional_modules',
        'platformId': 'platform_id',
        'mirrorIp': 'primary_mirror_address',
        'mirrorSecondaryIp': 'secondary_mirror_address',
        'version': 'software_version',
        'timeLimitedModules': 'timelimited_modules',
        'timeZone': 'timezone',
        'unicastAddress': 'unicast_addresses',
        'selfDevice': 'self'
    }

    returnables = [
        'full_path',
        'name',
        'active_modules',
        'base_mac_address',
        'build',
        'chassis_id',
        'chassis_type',
        'comment',
        'configsync_address',
        'contact',
        'description',
        'edition',
        'failover_state',
        'hostname',
        'location',
        'management_address',
        'marketing_name',
        'multicast_address',
        'optional_modules',
        'platform_id',
        'primary_mirror_address',
        'product',
        'secondary_mirror_address',
        'self',
        'software_version',
        'timelimited_modules',
        'timezone',
        'unicast_addresses',
    ]

    @property
    def active_modules(self):
        if self._values['active_modules'] is None:
            return None
        result = []
        for x in self._values['active_modules']:
            parts = x.split('|')
            result += parts[2:]
        return list(set(result))

    @property
    def self(self):
        result = flatten_boolean(self._values['self'])
        return result

    @property
    def configsync_address(self):
        if self._values['configsync_address'] in [None, 'none']:
            return None
        return self._values['configsync_address']

    @property
    def primary_mirror_address(self):
        if self._values['primary_mirror_address'] in [None, 'any6']:
            return None
        return self._values['primary_mirror_address']

    @property
    def secondary_mirror_address(self):
        if self._values['secondary_mirror_address'] in [None, 'any6']:
            return None
        return self._values['secondary_mirror_address']

    @property
    def unicast_addresses(self):
        if self._values['unicast_addresses'] is None:
            return None
        result = []

        for addr in self._values['unicast_addresses']:
            tmp = {}
            for key in ['effectiveIp', 'effectivePort', 'ip', 'port']:
                if key in addr:
                    renamed_key = self.convert(key)
                    tmp[renamed_key] = addr.get(key, None)
            if tmp:
                result.append(tmp)
        if result:
            return result

    def convert(self, name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class DevicesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(DevicesFactManager, self).__init__(**kwargs)
        self.want = DevicesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(devices=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = DevicesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/cm/device".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class ExternalMonitorsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'defaultsFrom': 'parent',
        'adaptiveDivergenceType': 'adaptive_divergence_type',
        'adaptiveDivergenceValue': 'adaptive_divergence_value',
        'adaptiveLimit': 'adaptive_limit',
        'adaptiveSamplingTimespan': 'adaptive_sampling_timespan',
        'manualResume': 'manual_resume',
        'timeUntilUp': 'time_until_up',
        'upInterval': 'up_interval',
        'run': 'external_program',
        'apiRawValues': 'variables',
    }

    returnables = [
        'full_path',
        'name',
        'parent',
        'description',
        'args',
        'destination',
        'external_program',
        'interval',
        'manual_resume',
        'time_until_up',
        'timeout',
        'up_interval',
        'variables',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def manual_resume(self):
        return flatten_boolean(self._values['manual_resume'])

    @property
    def variables(self):
        if self._values['variables'] is None:
            return None
        result = {}
        for k, v in iteritems(self._values['variables']):
            k = k.replace('userDefined ', '').strip()
            result[k] = v
        return result


class ExternalMonitorsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(ExternalMonitorsFactManager, self).__init__(**kwargs)
        self.want = ExternalMonitorsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(external_monitors=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = ExternalMonitorsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/external".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class FastHttpProfilesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'clientCloseTimeout': 'client_close_timeout',
        'connpoolIdleTimeoutOverride': 'oneconnect_idle_timeout_override',
        'connpoolMaxReuse': 'oneconnect_maximum_reuse',
        'connpoolMaxSize': 'oneconnect_maximum_pool_size',
        'connpoolMinSize': 'oneconnect_minimum_pool_size',
        'connpoolReplenish': 'oneconnect_replenish',
        'connpoolStep': 'oneconnect_ramp_up_increment',
        'defaultsFrom': 'parent',
        'forceHttp_10Response': 'force_http_1_0_response',
        'headerInsert': 'request_header_insert',
        'http_11CloseWorkarounds': 'http_1_1_close_workarounds',
        'idleTimeout': 'idle_timeout',
        'insertXforwardedFor': 'insert_x_forwarded_for',
        'maxHeaderSize': 'maximum_header_size',
        'maxRequests': 'maximum_requests',
        'mssOverride': 'maximum_segment_size_override',
        'receiveWindowSize': 'receive_window_size',
        'resetOnTimeout': 'reset_on_timeout',
        'serverCloseTimeout': 'server_close_timeout',
        'serverSack': 'server_sack',
        'serverTimestamp': 'server_timestamp',
        'uncleanShutdown': 'unclean_shutdown'
    }

    returnables = [
        'full_path',
        'name',
        'client_close_timeout',
        'oneconnect_idle_timeout_override',
        'oneconnect_maximum_reuse',
        'oneconnect_maximum_pool_size',
        'oneconnect_minimum_pool_size',
        'oneconnect_replenish',
        'oneconnect_ramp_up_increment',
        'parent',
        'description',
        'force_http_1_0_response',
        'request_header_insert',
        'http_1_1_close_workarounds',
        'idle_timeout',
        'insert_x_forwarded_for',
        'maximum_header_size',
        'maximum_requests',
        'maximum_segment_size_override',
        'receive_window_size',
        'reset_on_timeout',
        'server_close_timeout',
        'server_sack',
        'server_timestamp',
        'unclean_shutdown'
    ]

    @property
    def request_header_insert(self):
        if self._values['request_header_insert'] in [None, 'none']:
            return None
        return self._values['request_header_insert']

    @property
    def server_timestamp(self):
        return flatten_boolean(self._values['server_timestamp'])

    @property
    def server_sack(self):
        return flatten_boolean(self._values['server_sack'])

    @property
    def reset_on_timeout(self):
        return flatten_boolean(self._values['reset_on_timeout'])

    @property
    def insert_x_forwarded_for(self):
        return flatten_boolean(self._values['insert_x_forwarded_for'])

    @property
    def http_1_1_close_workarounds(self):
        return flatten_boolean(self._values['http_1_1_close_workarounds'])

    @property
    def force_http_1_0_response(self):
        return flatten_boolean(self._values['force_http_1_0_response'])

    @property
    def oneconnect_replenish(self):
        return flatten_boolean(self._values['oneconnect_replenish'])

    @property
    def idle_timeout(self):
        if self._values['idle_timeout'] is None:
            return None
        elif self._values['idle_timeout'] == 'immediate':
            return 0
        elif self._values['idle_timeout'] == 'indefinite':
            return 4294967295
        return int(self._values['idle_timeout'])


class FastHttpProfilesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(FastHttpProfilesFactManager, self).__init__(**kwargs)
        self.want = FastHttpProfilesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(fasthttp_profiles=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = FastHttpProfilesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/fasthttp".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class FastL4ProfilesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'clientTimeout': 'client_timeout',
        'defaultsFrom': 'parent',
        'explicitFlowMigration': 'explicit_flow_migration',
        'hardwareSynCookie': 'hardware_syn_cookie',
        'idleTimeout': 'idle_timeout',
        'ipDfMode': 'dont_fragment_flag',
        'ipTosToClient': 'ip_tos_to_client',
        'ipTosToServer': 'ip_tos_to_server',
        'ipTtlMode': 'ttl_mode',
        'ipTtlV4': 'ttl_v4',
        'ipTtlV6': 'ttl_v6',
        'keepAliveInterval': 'keep_alive_interval',
        'lateBinding': 'late_binding',
        'linkQosToClient': 'link_qos_to_client',
        'linkQosToServer': 'link_qos_to_server',
        'looseClose': 'loose_close',
        'looseInitialization': 'loose_init',
        'mssOverride': 'mss_override',
        'priorityToClient': 'priority_to_client',
        'priorityToServer': 'priority_to_server',
        'pvaAcceleration': 'pva_acceleration',
        'pvaDynamicClientPackets': 'pva_dynamic_client_packets',
        'pvaDynamicServerPackets': 'pva_dynamic_server_packets',
        'pvaFlowAging': 'pva_flow_aging',
        'pvaFlowEvict': 'pva_flow_evict',
        'pvaOffloadDynamic': 'pva_offload_dynamic',
        'pvaOffloadState': 'pva_offload_state',
        'reassembleFragments': 'reassemble_fragments',
        'receiveWindowSize': 'receive_window',
        'resetOnTimeout': 'reset_on_timeout',
        'rttFromClient': 'rtt_from_client',
        'rttFromServer': 'rtt_from_server',
        'serverSack': 'server_sack',
        'serverTimestamp': 'server_timestamp',
        'softwareSynCookie': 'software_syn_cookie',
        'synCookieEnable': 'syn_cookie_enabled',
        'synCookieMss': 'syn_cookie_mss',
        'synCookieWhitelist': 'syn_cookie_whitelist',
        'tcpCloseTimeout': 'tcp_close_timeout',
        'tcpGenerateIsn': 'generate_init_seq_number',
        'tcpHandshakeTimeout': 'tcp_handshake_timeout',
        'tcpStripSack': 'strip_sack',
        'tcpTimeWaitTimeout': 'tcp_time_wait_timeout',
        'tcpTimestampMode': 'tcp_timestamp_mode',
        'tcpWscaleMode': 'tcp_window_scale_mode',
        'timeoutRecovery': 'timeout_recovery',
    }

    returnables = [
        'full_path',
        'name',
        'client_timeout',
        'parent',
        'description',
        'explicit_flow_migration',
        'hardware_syn_cookie',
        'idle_timeout',
        'dont_fragment_flag',
        'ip_tos_to_client',
        'ip_tos_to_server',
        'ttl_mode',
        'ttl_v4',
        'ttl_v6',
        'keep_alive_interval',
        'late_binding',
        'link_qos_to_client',
        'link_qos_to_server',
        'loose_close',
        'loose_init',
        'mss_override',  # Maximum Segment Size Override
        'priority_to_client',
        'priority_to_server',
        'pva_acceleration',
        'pva_dynamic_client_packets',
        'pva_dynamic_server_packets',
        'pva_flow_aging',
        'pva_flow_evict',
        'pva_offload_dynamic',
        'pva_offload_state',
        'reassemble_fragments',
        'receive_window',
        'reset_on_timeout',
        'rtt_from_client',
        'rtt_from_server',
        'server_sack',
        'server_timestamp',
        'software_syn_cookie',
        'syn_cookie_enabled',
        'syn_cookie_mss',
        'syn_cookie_whitelist',
        'tcp_close_timeout',
        'generate_init_seq_number',
        'tcp_handshake_timeout',
        'strip_sack',
        'tcp_time_wait_timeout',
        'tcp_timestamp_mode',
        'tcp_window_scale_mode',
        'timeout_recovery',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def strip_sack(self):
        return flatten_boolean(self._values['strip_sack'])

    @property
    def generate_init_seq_number(self):
        return flatten_boolean(self._values['generate_init_seq_number'])

    @property
    def syn_cookie_whitelist(self):
        return flatten_boolean(self._values['syn_cookie_whitelist'])

    @property
    def syn_cookie_enabled(self):
        return flatten_boolean(self._values['syn_cookie_enabled'])

    @property
    def software_syn_cookie(self):
        return flatten_boolean(self._values['software_syn_cookie'])

    @property
    def server_timestamp(self):
        return flatten_boolean(self._values['server_timestamp'])

    @property
    def server_sack(self):
        return flatten_boolean(self._values['server_sack'])

    @property
    def rtt_from_server(self):
        return flatten_boolean(self._values['rtt_from_server'])

    @property
    def rtt_from_client(self):
        return flatten_boolean(self._values['rtt_from_client'])

    @property
    def reset_on_timeout(self):
        return flatten_boolean(self._values['reset_on_timeout'])

    @property
    def explicit_flow_migration(self):
        return flatten_boolean(self._values['explicit_flow_migration'])

    @property
    def reassemble_fragments(self):
        return flatten_boolean(self._values['reassemble_fragments'])

    @property
    def pva_flow_aging(self):
        return flatten_boolean(self._values['pva_flow_aging'])

    @property
    def pva_flow_evict(self):
        return flatten_boolean(self._values['pva_flow_evict'])

    @property
    def pva_offload_dynamic(self):
        return flatten_boolean(self._values['pva_offload_dynamic'])

    @property
    def hardware_syn_cookie(self):
        return flatten_boolean(self._values['hardware_syn_cookie'])

    @property
    def loose_close(self):
        return flatten_boolean(self._values['loose_close'])

    @property
    def loose_init(self):
        return flatten_boolean(self._values['loose_init'])

    @property
    def late_binding(self):
        return flatten_boolean(self._values['late_binding'])

    @property
    def tcp_handshake_timeout(self):
        if self._values['tcp_handshake_timeout'] is None:
            return None
        elif self._values['tcp_handshake_timeout'] == 'immediate':
            return 0
        elif self._values['tcp_handshake_timeout'] == 'indefinite':
            return 4294967295
        return int(self._values['tcp_handshake_timeout'])

    @property
    def idle_timeout(self):
        if self._values['idle_timeout'] is None:
            return None
        elif self._values['idle_timeout'] == 'immediate':
            return 0
        elif self._values['idle_timeout'] == 'indefinite':
            return 4294967295
        return int(self._values['idle_timeout'])

    @property
    def tcp_close_timeout(self):
        if self._values['tcp_close_timeout'] is None:
            return None
        elif self._values['tcp_close_timeout'] == 'immediate':
            return 0
        elif self._values['tcp_close_timeout'] == 'indefinite':
            return 4294967295
        return int(self._values['tcp_close_timeout'])

    @property
    def keep_alive_interval(self):
        if self._values['keep_alive_interval'] is None:
            return None
        elif self._values['keep_alive_interval'] == 'disabled':
            return 0
        return int(self._values['keep_alive_interval'])

    @property
    def ip_tos_to_client(self):
        if self._values['ip_tos_to_client'] is None:
            return None
        try:
            return int(self._values['ip_tos_to_client'])
        except ValueError:
            return self._values['ip_tos_to_client']

    @property
    def ip_tos_to_server(self):
        if self._values['ip_tos_to_server'] is None:
            return None
        try:
            return int(self._values['ip_tos_to_server'])
        except ValueError:
            return self._values['ip_tos_to_server']

    @property
    def link_qos_to_client(self):
        if self._values['link_qos_to_client'] is None:
            return None
        try:
            return int(self._values['link_qos_to_client'])
        except ValueError:
            return self._values['link_qos_to_client']

    @property
    def link_qos_to_server(self):
        if self._values['link_qos_to_server'] is None:
            return None
        try:
            return int(self._values['link_qos_to_server'])
        except ValueError:
            return self._values['link_qos_to_server']

    @property
    def priority_to_client(self):
        if self._values['priority_to_client'] is None:
            return None
        try:
            return int(self._values['priority_to_client'])
        except ValueError:
            return self._values['priority_to_client']

    @property
    def priority_to_server(self):
        if self._values['priority_to_server'] is None:
            return None
        try:
            return int(self._values['priority_to_server'])
        except ValueError:
            return self._values['priority_to_server']


class FastL4ProfilesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(FastL4ProfilesFactManager, self).__init__(**kwargs)
        self.want = FastL4ProfilesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(fastl4_profiles=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = FastL4ProfilesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/fastl4".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GatewayIcmpMonitorsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'defaultsFrom': 'parent',
        'adaptiveDivergenceType': 'adaptive_divergence_type',
        'adaptiveDivergenceValue': 'adaptive_divergence_value',
        'adaptiveLimit': 'adaptive_limit',
        'adaptiveSamplingTimespan': 'adaptive_sampling_timespan',
        'manualResume': 'manual_resume',
        'timeUntilUp': 'time_until_up',
        'upInterval': 'up_interval',
    }

    returnables = [
        'full_path',
        'name',
        'parent',
        'description',
        'adaptive',
        'adaptive_divergence_type',
        'adaptive_divergence_value',
        'adaptive_limit',
        'adaptive_sampling_timespan',
        'destination',
        'interval',
        'manual_resume',
        'time_until_up',
        'timeout',
        'transparent',
        'up_interval',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def transparent(self):
        return flatten_boolean(self._values['transparent'])

    @property
    def manual_resume(self):
        return flatten_boolean(self._values['manual_resume'])

    @property
    def adaptive(self):
        return flatten_boolean(self._values['adaptive'])


class GatewayIcmpMonitorsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GatewayIcmpMonitorsFactManager, self).__init__(**kwargs)
        self.want = GatewayIcmpMonitorsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gateway_icmp_monitors=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GatewayIcmpMonitorsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/gateway-icmp".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmXPoolsParameters(BaseParameters):
    api_map = {
        'alternateMode': 'alternate_mode',
        'dynamicRatio': 'dynamic_ratio',
        'fallbackMode': 'fallback_mode',
        'fullPath': 'full_path',
        'loadBalancingMode': 'load_balancing_mode',
        'manualResume': 'manual_resume',
        'maxAnswersReturned': 'max_answers_returned',
        'qosHitRatio': 'qos_hit_ratio',
        'qosHops': 'qos_hops',
        'qosKilobytesSecond': 'qos_kilobytes_second',
        'qosLcs': 'qos_lcs',
        'qosPacketRate': 'qos_packet_rate',
        'qosRtt': 'qos_rtt',
        'qosTopology': 'qos_topology',
        'qosVsCapacity': 'qos_vs_capacity',
        'qosVsScore': 'qos_vs_score',
        'verifyMemberAvailability': 'verify_member_availability',
        'membersReference': 'members'
    }

    returnables = [
        'alternate_mode',
        'dynamic_ratio',
        'enabled',
        'disabled',
        'fallback_mode',
        'full_path',
        'load_balancing_mode',
        'manual_resume',
        'max_answers_returned',
        'members',
        'name',
        'partition',
        'qos_hit_ratio',
        'qos_hops',
        'qos_kilobytes_second',
        'qos_lcs',
        'qos_packet_rate',
        'qos_rtt',
        'qos_topology',
        'qos_vs_capacity',
        'qos_vs_score',
        'ttl',
        'verify_member_availability',
    ]

    @property
    def verify_member_availability(self):
        return flatten_boolean(self._values['verify_member_availability'])

    @property
    def dynamic_ratio(self):
        return flatten_boolean(self._values['dynamic_ratio'])

    @property
    def max_answers_returned(self):
        if self._values['max_answers_returned'] is None:
            return None
        return int(self._values['max_answers_returned'])

    @property
    def members(self):
        result = []
        if self._values['members'] is None or 'items' not in self._values['members']:
            return result
        for item in self._values['members']['items']:
            self._remove_internal_keywords(item)
            if 'disabled' in item:
                item['disabled'] = flatten_boolean(item['disabled'])
                item['enabled'] = flatten_boolean(not item['disabled'])
            if 'enabled' in item:
                item['enabled'] = flatten_boolean(item['enabled'])
                item['disabled'] = flatten_boolean(not item['enabled'])
            if 'fullPath' in item:
                item['full_path'] = item.pop('fullPath')
            if 'memberOrder' in item:
                item['member_order'] = int(item.pop('memberOrder'))
            # Cast some attributes to integer
            for x in ['order', 'preference', 'ratio', 'service']:
                if x in item:
                    item[x] = int(item[x])
            result.append(item)
        return result

    @property
    def qos_hit_ratio(self):
        if self._values['qos_hit_ratio'] is None:
            return None
        return int(self._values['qos_hit_ratio'])

    @property
    def qos_hops(self):
        if self._values['qos_hops'] is None:
            return None
        return int(self._values['qos_hops'])

    @property
    def qos_kilobytes_second(self):
        if self._values['qos_kilobytes_second'] is None:
            return None
        return int(self._values['qos_kilobytes_second'])

    @property
    def qos_lcs(self):
        if self._values['qos_lcs'] is None:
            return None
        return int(self._values['qos_lcs'])

    @property
    def qos_packet_rate(self):
        if self._values['qos_packet_rate'] is None:
            return None
        return int(self._values['qos_packet_rate'])

    @property
    def qos_rtt(self):
        if self._values['qos_rtt'] is None:
            return None
        return int(self._values['qos_rtt'])

    @property
    def qos_topology(self):
        if self._values['qos_topology'] is None:
            return None
        return int(self._values['qos_topology'])

    @property
    def qos_vs_capacity(self):
        if self._values['qos_vs_capacity'] is None:
            return None
        return int(self._values['qos_vs_capacity'])

    @property
    def qos_vs_score(self):
        if self._values['qos_vs_score'] is None:
            return None
        return int(self._values['qos_vs_score'])

    @property
    def availability_state(self):
        if self._values['stats'] is None:
            return None
        try:
            result = self._values['stats']['status']['availabilityState']
            return result['description']
        except AttributeError:
            return None

    @property
    def enabled_state(self):
        if self._values['stats'] is None:
            return None
        try:
            result = self._values['stats']['status']['enabledState']
            return result['description']
        except AttributeError:
            return None

    @property
    def availability_status(self):
        # This fact is a combination of the availability_state and enabled_state
        #
        # The purpose of the fact is to give a higher-level view of the availability
        # of the pool, that can be used in playbooks. If you need further detail,
        # consider using the following facts together.
        #
        # - availability_state
        # - enabled_state
        #
        if self.enabled_state == 'enabled':
            if self.availability_state == 'offline':
                return 'red'
            elif self.availability_state == 'available':
                return 'green'
            elif self.availability_state == 'unknown':
                return 'blue'
            else:
                return 'none'
        else:
            # disabled
            return 'black'

    @property
    def manual_resume(self):
        return flatten_boolean(self._values['manual_resume'])


class GtmAPoolsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmAPoolsFactManager, self).__init__(**kwargs)
        self.want = GtmXPoolsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_a_pools=facts)
        return result

    def _exec_module(self):
        if 'gtm' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmXPoolsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/pool/a".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        query = "?expandSubcollections=true"
        resp = self.client.api.get(uri + query)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmAaaaPoolsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmAaaaPoolsFactManager, self).__init__(**kwargs)
        self.want = GtmXPoolsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_aaaa_pools=facts)
        return result

    def _exec_module(self):
        if 'gtm' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmXPoolsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/pool/aaaa".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        query = "?expandSubcollections=true"
        resp = self.client.api.get(uri + query)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmCnamePoolsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmCnamePoolsFactManager, self).__init__(**kwargs)
        self.want = GtmXPoolsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_cname_pools=facts)
        return result

    def _exec_module(self):
        if 'gtm' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmXPoolsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/pool/cname".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        query = "?expandSubcollections=true"
        resp = self.client.api.get(uri + query)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmMxPoolsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmMxPoolsFactManager, self).__init__(**kwargs)
        self.want = GtmXPoolsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_mx_pools=facts)
        return result

    def _exec_module(self):
        if 'gtm' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmXPoolsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/pool/mx".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        query = "?expandSubcollections=true"
        resp = self.client.api.get(uri + query)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmNaptrPoolsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmNaptrPoolsFactManager, self).__init__(**kwargs)
        self.want = GtmXPoolsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_naptr_pools=facts)
        return result

    def _exec_module(self):
        if 'gtm' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmXPoolsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/pool/naptr".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        query = "?expandSubcollections=true"
        resp = self.client.api.get(uri + query)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmSrvPoolsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmSrvPoolsFactManager, self).__init__(**kwargs)
        self.want = GtmXPoolsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_srv_pools=facts)
        return result

    def _exec_module(self):
        if 'gtm' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmXPoolsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/pool/srv".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        query = "?expandSubcollections=true"
        resp = self.client.api.get(uri + query)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmServersParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'exposeRouteDomains': 'expose_route_domains',
        'iqAllowPath': 'iq_allow_path',
        'iqAllowServiceCheck': 'iq_allow_service_check',
        'iqAllowSnmp': 'iq_allow_snmp',
        'limitCpuUsage': 'limit_cpu_usage',
        'limitCpuUsageStatus': 'limit_cpu_usage_status',
        'limitMaxBps': 'limit_max_bps',
        'limitMaxBpsStatus': 'limit_max_bps_status',
        'limitMaxConnections': 'limit_max_connections',
        'limitMaxConnectionsStatus': 'limit_max_connections_status',
        'limitMaxPps': 'limit_max_pps',
        'limitMaxPpsStatus': 'limit_max_pps_status',
        'limitMemAvail': 'limit_mem_available',
        'limitMemAvailStatus': 'limit_mem_available_status',
        'linkDiscovery': 'link_discovery',
        'proberFallback': 'prober_fallback',
        'proberPreference': 'prober_preference',
        'virtualServerDiscovery': 'virtual_server_discovery',
        'devicesReference': 'devices',
        'virtualServersReference': 'virtual_servers',
        'monitor': 'monitors',
    }

    returnables = [
        'datacenter',
        'enabled',
        'disabled',
        'expose_route_domains',
        'iq_allow_path',
        'full_path',
        'iq_allow_service_check',
        'iq_allow_snmp',
        'limit_cpu_usage',
        'limit_cpu_usage_status',
        'limit_max_bps',
        'limit_max_bps_status',
        'limit_max_connections',
        'limit_max_connections_status',
        'limit_max_pps',
        'limit_max_pps_status',
        'limit_mem_available',
        'limit_mem_available_status',
        'link_discovery',
        'monitors',
        'monitor_type',
        'name',
        'product',
        'prober_fallback',
        'prober_preference',
        'virtual_server_discovery',
        'addresses',
        'devices',
        'virtual_servers',
    ]

    @property
    def monitors(self):
        if self._values['monitors'] is None:
            return []
        try:
            result = re.findall(r'/\w+/[^\s}]+', self._values['monitors'])
            return result
        except Exception:
            return [self._values['monitors']]

    @property
    def monitor_type(self):
        if self._values['monitors'] is None:
            return None
        pattern = r'min\s+\d+\s+of'
        matches = re.search(pattern, self._values['monitors'])
        if matches:
            return 'm_of_n'
        else:
            return 'and_list'

    @property
    def limit_mem_available_status(self):
        return flatten_boolean(self._values['limit_mem_available_status'])

    @property
    def limit_max_pps_status(self):
        return flatten_boolean(self._values['limit_max_pps_status'])

    @property
    def limit_max_connections_status(self):
        return flatten_boolean(self._values['limit_max_connections_status'])

    @property
    def limit_max_bps_status(self):
        return flatten_boolean(self._values['limit_max_bps_status'])

    @property
    def limit_cpu_usage_status(self):
        return flatten_boolean(self._values['limit_cpu_usage_status'])

    @property
    def iq_allow_service_check(self):
        return flatten_boolean(self._values['iq_allow_service_check'])

    @property
    def iq_allow_snmp(self):
        return flatten_boolean(self._values['iq_allow_snmp'])

    @property
    def expose_route_domains(self):
        return flatten_boolean(self._values['expose_route_domains'])

    @property
    def iq_allow_path(self):
        return flatten_boolean(self._values['iq_allow_path'])

    @property
    def product(self):
        if self._values['product'] is None:
            return None
        if self._values['product'] in ['single-bigip', 'redundant-bigip']:
            return 'bigip'
        return self._values['product']

    @property
    def devices(self):
        result = []
        if self._values['devices'] is None or 'items' not in self._values['devices']:
            return result
        for item in self._values['devices']['items']:
            self._remove_internal_keywords(item)
            if 'fullPath' in item:
                item['full_path'] = item.pop('fullPath')
            result.append(item)
        return result

    @property
    def virtual_servers(self):
        result = []
        if self._values['virtual_servers'] is None or 'items' not in self._values['virtual_servers']:
            return result
        for item in self._values['virtual_servers']['items']:
            self._remove_internal_keywords(item)
            if 'disabled' in item:
                if item['disabled'] in BOOLEANS_TRUE:
                    item['disabled'] = flatten_boolean(item['disabled'])
                    item['enabled'] = flatten_boolean(not item['disabled'])
            if 'enabled' in item:
                if item['enabled'] in BOOLEANS_TRUE:
                    item['enabled'] = flatten_boolean(item['enabled'])
                    item['disabled'] = flatten_boolean(not item['enabled'])
            if 'fullPath' in item:
                item['full_path'] = item.pop('fullPath')
            if 'limitMaxBps' in item:
                item['limit_max_bps'] = int(item.pop('limitMaxBps'))
            if 'limitMaxBpsStatus' in item:
                item['limit_max_bps_status'] = item.pop('limitMaxBpsStatus')
            if 'limitMaxConnections' in item:
                item['limit_max_connections'] = int(item.pop('limitMaxConnections'))
            if 'limitMaxConnectionsStatus' in item:
                item['limit_max_connections_status'] = item.pop('limitMaxConnectionsStatus')
            if 'limitMaxPps' in item:
                item['limit_max_pps'] = int(item.pop('limitMaxPps'))
            if 'limitMaxPpsStatus' in item:
                item['limit_max_pps_status'] = item.pop('limitMaxPpsStatus')
            if 'translationAddress' in item:
                item['translation_address'] = item.pop('translationAddress')
            if 'translationPort' in item:
                item['translation_port'] = int(item.pop('translationPort'))
            result.append(item)
        return result

    @property
    def limit_cpu_usage(self):
        if self._values['limit_cpu_usage'] is None:
            return None
        return int(self._values['limit_cpu_usage'])

    @property
    def limit_max_bps(self):
        if self._values['limit_max_bps'] is None:
            return None
        return int(self._values['limit_max_bps'])

    @property
    def limit_max_connections(self):
        if self._values['limit_max_connections'] is None:
            return None
        return int(self._values['limit_max_connections'])

    @property
    def limit_max_pps(self):
        if self._values['limit_max_pps'] is None:
            return None
        return int(self._values['limit_max_pps'])

    @property
    def limit_mem_available(self):
        if self._values['limit_mem_available'] is None:
            return None
        return int(self._values['limit_mem_available'])


class GtmServersFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmServersFactManager, self).__init__(**kwargs)
        self.want = GtmServersParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_servers=facts)
        return result

    def _exec_module(self):
        if 'gtm' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmServersParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/server".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmXWideIpsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'failureRcode': 'failure_rcode',
        'failureRcodeResponse': 'failure_rcode_response',
        'failureRcodeTtl': 'failure_rcode_ttl',
        'lastResortPool': 'last_resort_pool',
        'minimalResponse': 'minimal_response',
        'persistCidrIpv4': 'persist_cidr_ipv4',
        'persistCidrIpv6': 'persist_cidr_ipv6',
        'poolLbMode': 'pool_lb_mode',
        'ttlPersistence': 'ttl_persistence'
    }

    returnables = [
        'full_path',
        'description',
        'enabled',
        'disabled',
        'failure_rcode',
        'failure_rcode_response',
        'failure_rcode_ttl',
        'last_resort_pool',
        'minimal_response',
        'name',
        'persist_cidr_ipv4',
        'persist_cidr_ipv6',
        'pool_lb_mode',
        'ttl_persistence',
        'pools',
    ]

    @property
    def pools(self):
        result = []
        if self._values['pools'] is None:
            return []
        for pool in self._values['pools']:
            del pool['nameReference']
            for x in ['order', 'ratio']:
                if x in pool:
                    pool[x] = int(pool[x])
            result.append(pool)
        return result

    @property
    def failure_rcode_response(self):
        return flatten_boolean(self._values['failure_rcode_response'])

    @property
    def failure_rcode_ttl(self):
        if self._values['failure_rcode_ttl'] is None:
            return None
        return int(self._values['failure_rcode_ttl'])

    @property
    def persist_cidr_ipv4(self):
        if self._values['persist_cidr_ipv4'] is None:
            return None
        return int(self._values['persist_cidr_ipv4'])

    @property
    def persist_cidr_ipv6(self):
        if self._values['persist_cidr_ipv6'] is None:
            return None
        return int(self._values['persist_cidr_ipv6'])

    @property
    def ttl_persistence(self):
        if self._values['ttl_persistence'] is None:
            return None
        return int(self._values['ttl_persistence'])


class GtmAWideIpsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmAWideIpsFactManager, self).__init__(**kwargs)
        self.want = GtmXWideIpsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_a_wide_ips=facts)
        return result

    def _exec_module(self):
        if 'gtm' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmXWideIpsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/wideip/a".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmAaaaWideIpsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmAaaaWideIpsFactManager, self).__init__(**kwargs)
        self.want = GtmXWideIpsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_aaaa_wide_ips=facts)
        return result

    def _exec_module(self):
        if 'gtm' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmXWideIpsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/wideip/aaaa".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmCnameWideIpsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmCnameWideIpsFactManager, self).__init__(**kwargs)
        self.want = GtmXWideIpsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_cname_wide_ips=facts)
        return result

    def _exec_module(self):
        if 'gtm' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmXWideIpsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/wideip/cname".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmMxWideIpsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmMxWideIpsFactManager, self).__init__(**kwargs)
        self.want = GtmXWideIpsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_mx_wide_ips=facts)
        return result

    def _exec_module(self):
        if 'gtm' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmXWideIpsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/wideip/mx".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmNaptrWideIpsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmNaptrWideIpsFactManager, self).__init__(**kwargs)
        self.want = GtmXWideIpsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_naptr_wide_ips=facts)
        return result

    def _exec_module(self):
        results = []
        if 'gtm' not in self.provisioned_modules:
            return []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmXWideIpsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/wideip/naptr".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class GtmSrvWideIpsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(GtmSrvWideIpsFactManager, self).__init__(**kwargs)
        self.want = GtmXWideIpsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(gtm_srv_wide_ips=facts)
        return result

    def _exec_module(self):
        if 'gtm' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = GtmXWideIpsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/wideip/srv".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class HttpMonitorsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'defaultsFrom': 'parent',
        'adaptiveDivergenceType': 'adaptive_divergence_type',
        'adaptiveDivergenceValue': 'adaptive_divergence_value',
        'adaptiveLimit': 'adaptive_limit',
        'adaptiveSamplingTimespan': 'adaptive_sampling_timespan',
        'ipDscp': 'ip_dscp',
        'manualResume': 'manual_resume',
        'recv': 'receive_string',
        'recvDisable': 'receive_disable_string',
        'send': 'send_string',
        'timeUntilUp': 'time_until_up',
        'upInterval': 'up_interval',
    }

    returnables = [
        'full_path',
        'name',
        'parent',
        'description',
        'adaptive',
        'adaptive_divergence_type',
        'adaptive_divergence_value',
        'adaptive_limit',
        'adaptive_sampling_timespan',
        'destination',
        'interval',
        'ip_dscp',
        'manual_resume',
        'receive_string',
        'receive_disable_string',
        'reverse',
        'send_string',
        'time_until_up',
        'timeout',
        'transparent',
        'up_interval',
        'username',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def transparent(self):
        return flatten_boolean(self._values['transparent'])

    @property
    def reverse(self):
        return flatten_boolean(self._values['reverse'])

    @property
    def manual_resume(self):
        return flatten_boolean(self._values['manual_resume'])

    @property
    def adaptive(self):
        return flatten_boolean(self._values['adaptive'])


class HttpMonitorsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(HttpMonitorsFactManager, self).__init__(**kwargs)
        self.want = HttpMonitorsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(http_monitors=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = HttpMonitorsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/http".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = response['items']
        return result


class HttpsMonitorsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'defaultsFrom': 'parent',
        'adaptiveDivergenceType': 'adaptive_divergence_type',
        'adaptiveDivergenceValue': 'adaptive_divergence_value',
        'adaptiveLimit': 'adaptive_limit',
        'adaptiveSamplingTimespan': 'adaptive_sampling_timespan',
        'ipDscp': 'ip_dscp',
        'manualResume': 'manual_resume',
        'recv': 'receive_string',
        'recvDisable': 'receive_disable_string',
        'send': 'send_string',
        'sslProfile': 'ssl_profile',
        'timeUntilUp': 'time_until_up',
        'upInterval': 'up_interval',
    }

    returnables = [
        'full_path',
        'name',
        'parent',
        'description',
        'adaptive',
        'adaptive_divergence_type',
        'adaptive_divergence_value',
        'adaptive_limit',
        'adaptive_sampling_timespan',
        'destination',
        'interval',
        'ip_dscp',
        'manual_resume',
        'receive_string',
        'receive_disable_string',
        'reverse',
        'send_string',
        'ssl_profile',
        'time_until_up',
        'timeout',
        'transparent',
        'up_interval',
        'username',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def transparent(self):
        return flatten_boolean(self._values['transparent'])

    @property
    def reverse(self):
        return flatten_boolean(self._values['reverse'])

    @property
    def manual_resume(self):
        return flatten_boolean(self._values['manual_resume'])

    @property
    def adaptive(self):
        return flatten_boolean(self._values['adaptive'])


class HttpsMonitorsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(HttpsMonitorsFactManager, self).__init__(**kwargs)
        self.want = HttpsMonitorsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(https_monitors=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = HttpsMonitorsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/https".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = response['items']
        return result


class HttpProfilesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'defaultsFrom': 'parent',
        'acceptXff': 'accept_xff',
        'explicitProxy': 'explicit_proxy',
        'insertXforwardedFor': 'insert_x_forwarded_for',
        'lwsWidth': 'lws_max_columns',
        'oneconnectTransformations': 'onconnect_transformations',
        'proxyType': 'proxy_mode',
        'redirectRewrite': 'redirect_rewrite',
        'requestChunking': 'request_chunking',
        'responseChunking': 'response_chunking',
        'serverAgentName': 'server_agent_name',
        'viaRequest': 'via_request',
        'viaResponse': 'via_response',
        'pipeline': 'pipeline_action',
    }

    returnables = [
        'full_path',
        'name',
        'parent',
        'description',
        'accept_xff',
        'allow_truncated_redirects',
        'excess_client_headers',
        'excess_server_headers',
        'known_methods',
        'max_header_count',
        'max_header_size',
        'max_requests',
        'oversize_client_headers',
        'oversize_server_headers',
        'pipeline_action',
        'unknown_method',
        'default_connect_handling',
        'hsts_include_subdomains',
        'hsts_enabled',
        'insert_x_forwarded_for',
        'lws_max_columns',
        'onconnect_transformations',
        'proxy_mode',
        'redirect_rewrite',
        'request_chunking',
        'response_chunking',
        'server_agent_name',
        'sflow_poll_interval',
        'sflow_sampling_rate',
        'via_request',
        'via_response',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def accept_xff(self):
        return flatten_boolean(self._values['accept_xff'])

    @property
    def excess_client_headers(self):
        if self._values['enforcement'] is None:
            return None
        if self._values['enforcement']['excessClientHeaders'] is None:
            return None
        return self._values['enforcement']['excessClientHeaders']

    @property
    def excess_server_headers(self):
        if self._values['enforcement'] is None:
            return None
        if self._values['enforcement']['excessServerHeaders'] is None:
            return None
        return self._values['enforcement']['excessServerHeaders']

    @property
    def known_methods(self):
        if self._values['enforcement'] is None:
            return None
        if self._values['enforcement']['knownMethods'] is None:
            return None
        return self._values['enforcement']['knownMethods']

    @property
    def max_header_count(self):
        if self._values['enforcement'] is None:
            return None
        if self._values['enforcement']['maxHeaderCount'] is None:
            return None
        return self._values['enforcement']['maxHeaderCount']

    @property
    def max_header_size(self):
        if self._values['enforcement'] is None:
            return None
        if self._values['enforcement']['maxHeaderSize'] is None:
            return None
        return self._values['enforcement']['maxHeaderSize']

    @property
    def max_requests(self):
        if self._values['enforcement'] is None:
            return None
        if self._values['enforcement']['maxRequests'] is None:
            return None
        return self._values['enforcement']['maxRequests']

    @property
    def oversize_client_headers(self):
        if self._values['enforcement'] is None:
            return None
        if self._values['enforcement']['oversizeClientHeaders'] is None:
            return None
        return self._values['enforcement']['oversizeClientHeaders']

    @property
    def oversize_server_headers(self):
        if self._values['enforcement'] is None:
            return None
        if self._values['enforcement']['oversizeServerHeaders'] is None:
            return None
        return self._values['enforcement']['oversizeServerHeaders']

    @property
    def allow_truncated_redirects(self):
        if self._values['enforcement'] is None:
            return None
        if self._values['enforcement']['truncatedRedirects'] is None:
            return None
        return flatten_boolean(self._values['enforcement']['truncatedRedirects'])

    @property
    def unknown_method(self):
        if self._values['enforcement'] is None:
            return None
        if self._values['enforcement']['unknownMethod'] is None:
            return None
        return self._values['enforcement']['unknownMethod']

    @property
    def default_connect_handling(self):
        if self._values['explicit_proxy'] is None:
            return None
        if self._values['explicit_proxy']['defaultConnectHandling'] is None:
            return None
        return self._values['explicit_proxy']['defaultConnectHandling']

    @property
    def hsts_include_subdomains(self):
        if self._values['hsts'] is None:
            return None
        if self._values['hsts']['includeSubdomains'] is None:
            return None
        return flatten_boolean(self._values['hsts']['includeSubdomains'])

    @property
    def hsts_enabled(self):
        if self._values['hsts'] is None:
            return None
        if self._values['hsts']['mode'] is None:
            return None
        return flatten_boolean(self._values['hsts']['mode'])

    @property
    def hsts_max_age(self):
        if self._values['hsts'] is None:
            return None
        if self._values['hsts']['mode'] is None:
            return None
        return self._values['hsts']['maximumAge']

    @property
    def insert_x_forwarded_for(self):
        if self._values['insert_x_forwarded_for'] is None:
            return None
        return flatten_boolean(self._values['insert_x_forwarded_for'])

    @property
    def onconnect_transformations(self):
        if self._values['onconnect_transformations'] is None:
            return None
        return flatten_boolean(self._values['onconnect_transformations'])

    @property
    def sflow_poll_interval(self):
        if self._values['sflow'] is None:
            return None
        if self._values['sflow']['pollInterval'] is None:
            return None
        return self._values['sflow']['pollInterval']

    @property
    def sflow_sampling_rate(self):
        if self._values['sflow'] is None:
            return None
        if self._values['sflow']['samplingRate'] is None:
            return None
        return self._values['sflow']['samplingRate']


class HttpProfilesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(HttpProfilesFactManager, self).__init__(**kwargs)
        self.want = HttpProfilesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(http_profiles=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = HttpProfilesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class IappServicesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'deviceGroup': 'device_group',
        'inheritedDevicegroup': 'inherited_device_group',
        'inheritedTrafficGroup': 'inherited_traffic_group',
        'strictUpdates': 'strict_updates',
        'templateModified': 'template_modified',
        'trafficGroup': 'traffic_group',
    }

    returnables = [
        'full_path',
        'name',
        'device_group',
        'inherited_device_group',
        'inherited_traffic_group',
        'strict_updates',
        'template_modified',
        'traffic_group',
        'tables',
        'variables',
        'metadata',
        'lists',
        'description',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def inherited_device_group(self):
        return flatten_boolean(self._values['inherited_device_group'])

    @property
    def inherited_traffic_group(self):
        return flatten_boolean(self._values['inherited_traffic_group'])

    @property
    def strict_updates(self):
        return flatten_boolean(self._values['strict_updates'])

    @property
    def template_modified(self):
        return flatten_boolean(self._values['template_modified'])


class IappServicesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(IappServicesFactManager, self).__init__(**kwargs)
        self.want = IappServicesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(iapp_services=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = IappServicesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/application/service".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class IapplxPackagesParameters(BaseParameters):
    api_map = {
        'packageName': 'package_name',
    }

    returnables = [
        'name',
        'version',
        'release',
        'arch',
        'package_name',
        'tags',
    ]


class IapplxPackagesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(IapplxPackagesFactManager, self).__init__(**kwargs)
        self.want = IapplxPackagesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(iapplx_packages=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['name'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = IapplxPackagesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        params = dict(operation='QUERY')
        uri = "https://{0}:{1}/mgmt/shared/iapp/package-management-tasks".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        status = self.wait_for_task(response['id'])
        if status == 'FINISHED':
            uri = "https://{0}:{1}/mgmt/shared/iapp/package-management-tasks/{2}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                response['id']
            )
            resp = self.client.api.get(uri)
            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))
            if 'code' in response and response['code'] == 400:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp.content)
        else:
            raise F5ModuleError(
                "An error occurred querying iAppLX packages."
            )
        result = response['queryResponse']
        return result

    def wait_for_task(self, task_id):
        uri = "https://{0}:{1}/mgmt/shared/iapp/package-management-tasks/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            task_id
        )
        for x in range(0, 60):
            resp = self.client.api.get(uri)
            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))
            if 'code' in response and response['code'] == 400:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp.content)
            if response['status'] in ['FINISHED', 'FAILED']:
                return response['status']
            time.sleep(1)
        return response['status']


class IcmpMonitorsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'defaultsFrom': 'parent',
        'adaptiveDivergenceType': 'adaptive_divergence_type',
        'adaptiveDivergenceValue': 'adaptive_divergence_value',
        'adaptiveLimit': 'adaptive_limit',
        'adaptiveSamplingTimespan': 'adaptive_sampling_timespan',
        'manualResume': 'manual_resume',
        'timeUntilUp': 'time_until_up',
        'upInterval': 'up_interval',
    }

    returnables = [
        'full_path',
        'name',
        'parent',
        'description',
        'adaptive',
        'adaptive_divergence_type',
        'adaptive_divergence_value',
        'adaptive_limit',
        'adaptive_sampling_timespan',
        'destination',
        'interval',
        'manual_resume',
        'time_until_up',
        'timeout',
        'transparent',
        'up_interval',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def transparent(self):
        return flatten_boolean(self._values['transparent'])

    @property
    def manual_resume(self):
        return flatten_boolean(self._values['manual_resume'])

    @property
    def adaptive(self):
        return flatten_boolean(self._values['adaptive'])


class IcmpMonitorsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(IcmpMonitorsFactManager, self).__init__(**kwargs)
        self.want = IcmpMonitorsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(icmp_monitors=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = IcmpMonitorsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/icmp".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class InterfacesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'mediaActive': 'active_media_type',
        'flowControl': 'flow_control',
        'bundleSpeed': 'bundle_speed',
        'ifIndex': 'if_index',
        'macAddress': 'mac_address',
        'mediaSfp': 'media_sfp',
        'lldpAdmin': 'lldp_admin',
        'preferPort': 'prefer_port',
        'stpAutoEdgePort': 'stp_auto_edge_port',
        'stp': 'stp_enabled',
        'stpLinkType': 'stp_link_type'
    }

    returnables = [
        'full_path',
        'name',
        'active_media_type',
        'flow_control',
        'description',
        'bundle',
        'bundle_speed',
        'enabled',
        'if_index',
        'mac_address',
        'media_sfp',
        'lldp_admin',
        'mtu',
        'prefer_port',
        'sflow_poll_interval',
        'sflow_poll_interval_global',
        'stp_auto_edge_port',
        'stp_enabled',
        'stp_link_type'
    ]

    @property
    def stp_auto_edge_port(self):
        return flatten_boolean(self._values['stp_auto_edge_port'])

    @property
    def stp_enabled(self):
        return flatten_boolean(self._values['stp_enabled'])

    @property
    def sflow_poll_interval_global(self):
        if self._values['sflow'] is None:
            return None
        if 'pollIntervalGlobal' in self._values['sflow']:
            return self._values['sflow']['pollIntervalGlobal']

    @property
    def sflow_poll_interval(self):
        if self._values['sflow'] is None:
            return None
        if 'pollInterval' in self._values['sflow']:
            return self._values['sflow']['pollInterval']

    @property
    def mac_address(self):
        if self._values['mac_address'] in [None, 'none']:
            return None
        return self._values['mac_address']

    @property
    def enabled(self):
        return flatten_boolean(self._values['enabled'])


class InterfacesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(InterfacesFactManager, self).__init__(**kwargs)
        self.want = InterfacesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(interfaces=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = InterfacesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/interface".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class InternalDataGroupsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path'
    }

    returnables = [
        'full_path',
        'name',
        'type',
        'records'
    ]


class InternalDataGroupsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(InternalDataGroupsFactManager, self).__init__(**kwargs)
        self.want = InternalDataGroupsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(internal_data_groups=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = InternalDataGroupsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/data-group/internal".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class IrulesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'ignoreVerification': 'ignore_verification',
    }

    returnables = [
        'full_path',
        'name',
        'ignore_verification',
        'checksum',
        'definition',
        'signature'
    ]

    @property
    def checksum(self):
        if self._values['apiAnonymous'] is None:
            return None
        pattern = r'definition-checksum\s(?P<checksum>\w+)'
        matches = re.search(pattern, self._values['apiAnonymous'])
        if matches:
            return matches.group('checksum')

    @property
    def definition(self):
        if self._values['apiAnonymous'] is None:
            return None
        pattern = r'(definition-(checksum|signature)\s[\w=\/+]+)'
        result = re.sub(pattern, '', self._values['apiAnonymous']).strip()
        if result:
            return result

    @property
    def signature(self):
        if self._values['apiAnonymous'] is None:
            return None
        pattern = r'definition-signature\s(?P<signature>[\w=\/+]+)'
        matches = re.search(pattern, self._values['apiAnonymous'])
        if matches:
            return matches.group('signature')

    @property
    def ignore_verification(self):
        if self._values['ignore_verification'] is None:
            return 'no'
        return 'yes'


class IrulesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(IrulesFactManager, self).__init__(**kwargs)
        self.want = IrulesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(irules=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = IrulesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/rule".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class LtmPoolsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'allowNat': 'allow_nat',
        'allowSnat': 'allow_snat',
        'ignorePersistedWeight': 'ignore_persisted_weight',
        'ipTosToClient': 'client_ip_tos',
        'ipTosToServer': 'server_ip_tos',
        'linkQosToClient': 'client_link_qos',
        'linkQosToServer': 'server_link_qos',
        'loadBalancingMode': 'lb_method',
        'minActiveMembers': 'minimum_active_members',
        'minUpMembers': 'minimum_up_members',
        'minUpMembersAction': 'minimum_up_members_action',
        'minUpMembersChecking': 'minimum_up_members_checking',
        'queueDepthLimit': 'queue_depth_limit',
        'queueOnConnectionLimit': 'queue_on_connection_limit',
        'queueTimeLimit': 'queue_time_limit',
        'reselectTries': 'reselect_tries',
        'serviceDownAction': 'service_down_action',
        'slowRampTime': 'slow_ramp_time',
        'monitor': 'monitors',
    }

    returnables = [
        'full_path',
        'name',
        'allow_nat',
        'allow_snat',
        'description',
        'ignore_persisted_weight',
        'client_ip_tos',
        'server_ip_tos',
        'client_link_qos',
        'server_link_qos',
        'lb_method',
        'minimum_active_members',
        'minimum_up_members',
        'minimum_up_members_action',
        'minimum_up_members_checking',
        'monitors',
        'queue_depth_limit',
        'queue_on_connection_limit',
        'queue_time_limit',
        'reselect_tries',
        'service_down_action',
        'slow_ramp_time',
        'priority_group_activation',
        'members',
        'metadata',
        'active_member_count',
        'available_member_count',
        'availability_status',
        'enabled_status',
        'status_reason',
        'all_max_queue_entry_age_ever',
        'all_avg_queue_entry_age',
        'all_queue_head_entry_age',
        'all_max_queue_entry_age_recently',
        'all_num_connections_queued_now',
        'all_num_connections_serviced',
        'pool_max_queue_entry_age_ever',
        'pool_avg_queue_entry_age',
        'pool_queue_head_entry_age',
        'pool_max_queue_entry_age_recently',
        'pool_num_connections_queued_now',
        'pool_num_connections_serviced',
        'current_sessions',
        'member_count',
        'total_requests',
        'server_side_bits_in',
        'server_side_bits_out',
        'server_side_current_connections',
        'server_side_max_connections',
        'server_side_pkts_in',
        'server_side_pkts_out',
        'server_side_total_connections',
    ]

    @property
    def active_member_count(self):
        if 'availableMemberCnt' in self._values['stats']:
            return int(self._values['stats']['activeMemberCnt'])
        return None

    @property
    def available_member_count(self):
        if 'availableMemberCnt' in self._values['stats']:
            return int(self._values['stats']['availableMemberCnt'])
        return None

    @property
    def all_max_queue_entry_age_ever(self):
        return self._values['stats']['connqAll']['ageEdm']

    @property
    def all_avg_queue_entry_age(self):
        return self._values['stats']['connqAll']['ageEma']

    @property
    def all_queue_head_entry_age(self):
        return self._values['stats']['connqAll']['ageHead']

    @property
    def all_max_queue_entry_age_recently(self):
        return self._values['stats']['connqAll']['ageMax']

    @property
    def all_num_connections_queued_now(self):
        return self._values['stats']['connqAll']['depth']

    @property
    def all_num_connections_serviced(self):
        return self._values['stats']['connqAll']['serviced']

    @property
    def availability_status(self):
        return self._values['stats']['status']['availabilityState']

    @property
    def enabled_status(self):
        return self._values['stats']['status']['enabledState']

    @property
    def status_reason(self):
        return self._values['stats']['status']['statusReason']

    @property
    def pool_max_queue_entry_age_ever(self):
        return self._values['stats']['connq']['ageEdm']

    @property
    def pool_avg_queue_entry_age(self):
        return self._values['stats']['connq']['ageEma']

    @property
    def pool_queue_head_entry_age(self):
        return self._values['stats']['connq']['ageHead']

    @property
    def pool_max_queue_entry_age_recently(self):
        return self._values['stats']['connq']['ageMax']

    @property
    def pool_num_connections_queued_now(self):
        return self._values['stats']['connq']['depth']

    @property
    def pool_num_connections_serviced(self):
        return self._values['stats']['connq']['serviced']

    @property
    def current_sessions(self):
        return self._values['stats']['curSessions']

    @property
    def member_count(self):
        if 'memberCnt' in self._values['stats']:
            return self._values['stats']['memberCnt']
        return None

    @property
    def total_requests(self):
        return self._values['stats']['totRequests']

    @property
    def server_side_bits_in(self):
        return self._values['stats']['serverside']['bitsIn']

    @property
    def server_side_bits_out(self):
        return self._values['stats']['serverside']['bitsOut']

    @property
    def server_side_current_connections(self):
        return self._values['stats']['serverside']['curConns']

    @property
    def server_side_max_connections(self):
        return self._values['stats']['serverside']['maxConns']

    @property
    def server_side_pkts_in(self):
        return self._values['stats']['serverside']['pktsIn']

    @property
    def server_side_pkts_out(self):
        return self._values['stats']['serverside']['pktsOut']

    @property
    def server_side_total_connections(self):
        return self._values['stats']['serverside']['totConns']

    @property
    def ignore_persisted_weight(self):
        return flatten_boolean(self._values['ignore_persisted_weight'])

    @property
    def minimum_up_members_checking(self):
        return flatten_boolean(self._values['minimum_up_members_checking'])

    @property
    def queue_on_connection_limit(self):
        return flatten_boolean(self._values['queue_on_connection_limit'])

    @property
    def priority_group_activation(self):
        """Returns the TMUI value for "Priority Group Activation"

        This value is identified as ``minActiveMembers`` in the REST API, so this
        is just a convenience key for users of Ansible (where the ``bigip_virtual_server``
        parameter is called ``priority_group_activation``.

        Returns:
            int: Priority number assigned to the pool members.
        """
        return self._values['minimum_active_members']

    @property
    def metadata(self):
        """Returns metadata associated with a pool

        An arbitrary amount of metadata may be associated with a pool. You typically
        see this used in situations where the user wants to annotate a resource, maybe
        in cases where an automation system is responsible for creating the resource.

        The metadata in the API is always stored as a list of dictionaries. We change
        this to be a simple dictionary before it is returned to the user.

        Returns:
            dict: A dictionary of key/value pairs where the key is the metadata name
                  and the value is the metadata value.
        """
        if self._values['metadata'] is None:
            return None
        result = dict([(k['name'], k['value']) for k in self._values['metadata']])
        return result

    @property
    def members(self):
        if not self._values['members']:
            return None
        result = []
        for member in self._values['members']:
            member['connection_limit'] = member.pop('connectionLimit', None)
            member['dynamic_ratio'] = member.pop('dynamicRatio', None)
            member['full_path'] = member.pop('fullPath', None)
            member['inherit_profile'] = member.pop('inheritProfile', None)
            member['priority_group'] = member.pop('priorityGroup', None)
            member['rate_limit'] = member.pop('rateLimit', None)

            if 'fqdn' in member and 'autopopulate' in member['fqdn']:
                if member['fqdn']['autopopulate'] == 'enabled':
                    member['fqdn_autopopulate'] = 'yes'
                elif member['fqdn']['autopopulate'] == 'disabled':
                    member['fqdn_autopopulate'] = 'no'
                del member['fqdn']

            for key in ['ephemeral', 'inherit_profile', 'logging', 'rate_limit']:
                tmp = flatten_boolean(member[key])
                member[key] = tmp

            if 'profiles' in member:
                # Even though the ``profiles`` is a list, there is only ever 1
                member['encapsulation_profile'] = [x['name'] for x in member['profiles']][0]
                del member['profiles']

            if 'monitor' in member:
                monitors = member.pop('monitor')
                if monitors is not None:
                    try:
                        member['monitors'] = re.findall(r'/[\w-]+/[^\s}]+', monitors)
                    except Exception:
                        member['monitors'] = [monitors.strip()]

            session = member.pop('session')
            state = member.pop('state')

            member['real_session'] = session
            member['real_state'] = state

            if state in ['user-up', 'unchecked', 'fqdn-up-no-addr', 'fqdn-up'] and session in ['user-enabled']:
                member['state'] = 'present'
            elif state in ['user-down'] and session in ['user-disabled']:
                member['state'] = 'forced_offline'
            elif state in ['up', 'checking'] and session in ['monitor-enabled']:
                member['state'] = 'present'
            elif state in ['down'] and session in ['monitor-enabled']:
                member['state'] = 'offline'
            else:
                member['state'] = 'disabled'
            self._remove_internal_keywords(member)
            member = dict([(k, v) for k, v in iteritems(member) if v is not None])
            result.append(member)
        return result

    @property
    def monitors(self):
        if self._values['monitors'] is None:
            return None
        try:
            result = re.findall(r'/[\w-]+/[^\s}]+', self._values['monitors'])
            return result
        except Exception:
            return [self._values['monitors'].strip()]


class LtmPoolsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(LtmPoolsFactManager, self).__init__(**kwargs)
        self.want = LtmPoolsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(ltm_pools=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            attrs = resource
            members = self.read_member_from_device(attrs['fullPath'])
            attrs['members'] = members
            attrs['stats'] = self.read_stats_from_device(attrs['fullPath'])
            params = LtmPoolsParameters(params=attrs)
            results.append(params)
        return results

    def read_collection_from_device(self):
        """Read the LTM pools collection from the device

        Note that sub-collection expansion does not work with LTM pools. Therefore,
        one needs to query the ``members`` endpoint separately and add that to the
        list of ``attrs`` before the full set of attributes is sent to the ``Parameters``
        class.

        Returns:
             list: List of ``Pool`` objects
        """
        uri = "https://{0}:{1}/mgmt/tm/ltm/pool".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result

    def read_member_from_device(self, full_path):
        uri = "https://{0}:{1}/mgmt/tm/ltm/pool/{2}/members".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=full_path)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result

    def read_stats_from_device(self, full_path):
        uri = "https://{0}:{1}/mgmt/tm/ltm/pool/{2}/stats".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=full_path)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        try:
            return result['stats']
        except KeyError:
            return {}


class NodesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'connectionLimit': 'connection_limit',
        'dynamicRatio': 'dynamic_ratio',
        'rateLimit': 'rate_limit',
        'monitor': 'monitors'
    }

    returnables = [
        'full_path',
        'name',
        'ratio',
        'description',
        'connection_limit',
        'address',
        'dynamic_ratio',
        'rate_limit',
        'monitor_status',
        'session_status',
        'availability_status',
        'enabled_status',
        'status_reason',
        'monitor_rule',
        'monitors',
        'monitor_type'
    ]

    @property
    def monitors(self):
        if self._values['monitors'] is None:
            return []
        try:
            result = re.findall(r'/\w+/[^\s}]+', self._values['monitors'])
            return result
        except Exception:
            return [self._values['monitors']]

    @property
    def monitor_type(self):
        if self._values['monitors'] is None:
            return None
        pattern = r'min\s+\d+\s+of'
        matches = re.search(pattern, self._values['monitors'])
        if matches:
            return 'm_of_n'
        else:
            return 'and_list'

    @property
    def rate_limit(self):
        if self._values['rate_limit'] is None:
            return None
        elif self._values['rate_limit'] == 'disabled':
            return 0
        else:
            return int(self._values['rate_limit'])

    @property
    def monitor_status(self):
        return self._values['stats']['monitorStatus']

    @property
    def session_status(self):
        return self._values['stats']['sessionStatus']

    @property
    def availability_status(self):
        return self._values['stats']['status']['availabilityState']

    @property
    def enabled_status(self):
        return self._values['stats']['status']['enabledState']

    @property
    def status_reason(self):
        return self._values['stats']['status']['statusReason']

    @property
    def monitor_rule(self):
        return self._values['stats']['monitorRule']


class NodesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(NodesFactManager, self).__init__(**kwargs)
        self.want = NodesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(nodes=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            attrs = resource
            attrs['stats'] = self.read_stats_from_device(attrs['fullPath'])
            params = NodesParameters(params=attrs)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/node".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result

    def read_stats_from_device(self, full_path):
        uri = "https://{0}:{1}/mgmt/tm/ltm/node/{2}/stats".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=full_path)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        try:
            return result['stats']
        except KeyError:
            return {}


class OneConnectProfilesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'clientTimeout': 'client_timeout',
        'defaultsFrom': 'parent',
        'idleTimeoutOverride': 'idle_timeout_override',
        'limitType': 'limit_type',
        'maxAge': 'max_age',
        'maxReuse': 'max_reuse',
        'maxSize': 'max_size',
        'sharePools': 'share_pools',
        'sourceMask': 'source_mask',
    }

    returnables = [
        'full_path',
        'name',
        'parent',
        'description',
        'idle_timeout_override',
        'limit_type',
        'max_age',
        'max_reuse',
        'max_size',
        'share_pools',
        'source_mask',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def idle_timeout_override(self):
        if self._values['idle_timeout_override'] is None:
            return None
        elif self._values['idle_timeout_override'] == 'disabled':
            return 0
        elif self._values['idle_timeout_override'] == 'indefinite':
            return 4294967295
        return int(self._values['idle_timeout_override'])

    @property
    def share_pools(self):
        return flatten_boolean(self._values['share_pools'])


class OneConnectProfilesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(OneConnectProfilesFactManager, self).__init__(**kwargs)
        self.want = OneConnectProfilesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(oneconnect_profiles=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = OneConnectProfilesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/one-connect".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class PartitionParameters(BaseParameters):
    api_map = {
        'defaultRouteDomain': 'default_route_domain',
        'fullPath': 'full_path',
    }

    returnables = [
        'name',
        'full_path',
        'description',
        'default_route_domain'
    ]


class PartitionFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(PartitionFactManager, self).__init__(**kwargs)
        self.want = PartitionParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(partitions=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = PartitionParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/partition".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class ProvisionInfoParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'cpuRatio': 'cpu_ratio',
        'diskRatio': 'disk_ratio',
        'memoryRatio': 'memory_ratio',
    }

    returnables = [
        'full_path',
        'name',
        'cpu_ratio',
        'disk_ratio',
        'memory_ratio',
        'level'
    ]


class ProvisionInfoFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(ProvisionInfoFactManager, self).__init__(**kwargs)
        self.want = ProvisionInfoParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(provision_info=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = ProvisionInfoParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/provision".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class RouteDomainParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'bwcPolicy': 'bandwidth_controller_policy',
        'connectionLimit': 'connection_limit',
        'flowEvictionPolicy': 'flow_eviction_policy',
        'servicePolicy': 'service_policy',
        'routingProtocol': 'routing_protocol'
    }

    returnables = [
        'name',
        'id',
        'full_path',
        'parent',
        'bandwidth_controller_policy',
        'connection_limit',
        'description',
        'flow_eviction_policy',
        'service_policy',
        'strict',
        'routing_protocol',
        'vlans'
    ]

    @property
    def strict(self):
        return flatten_boolean(self._values['strict'])

    @property
    def connection_limit(self):
        if self._values['connection_limit'] is None:
            return None
        return int(self._values['connection_limit'])


class RouteDomainFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(RouteDomainFactManager, self).__init__(**kwargs)
        self.want = RouteDomainParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(route_domains=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = RouteDomainParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/route-domain".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class SelfIpsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'trafficGroup': 'traffic_group',
        'servicePolicy': 'service_policy',
        'allowService': 'allow_access_list',
        'inheritedTrafficGroup': 'traffic_group_inherited'
    }

    returnables = [
        'full_path',
        'name',
        'address',
        'description',
        'netmask',
        'netmask_cidr',
        'floating',
        'traffic_group',
        'service_policy',
        'vlan',
        'allow_access_list',
        'traffic_group_inherited'
    ]

    @property
    def address(self):
        parts = self._values['address'].split('/')
        return parts[0]

    @property
    def netmask(self):
        parts = self._values['address'].split('/')
        return to_netmask(parts[1])

    @property
    def netmask_cidr(self):
        parts = self._values['address'].split('/')
        return int(parts[1])

    @property
    def traffic_group_inherited(self):
        if self._values['traffic_group_inherited'] is None:
            return None
        elif self._values['traffic_group_inherited'] in [False, 'false']:
            # BIG-IP appears to store this as a string. This is a bug, so we handle both
            # cases here.
            return 'no'
        else:
            return 'yes'

    @property
    def floating(self):
        if self._values['floating'] is None:
            return None
        elif self._values['floating'] == 'disabled':
            return 'no'
        else:
            return 'yes'


class SelfIpsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(SelfIpsFactManager, self).__init__(**kwargs)
        self.want = SelfIpsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(self_ips=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = SelfIpsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/self".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class ServerSslProfilesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'alertTimeout': 'alert_timeout',
        'allowExpiredCrl': 'allow_expired_crl',
        'authenticate': 'authentication_frequency',
        'authenticateDepth': 'authenticate_depth',
        'authenticateName': 'authenticate_name',
        'bypassOnClientCertFail': 'bypass_on_client_cert_fail',
        'bypassOnHandshakeAlert': 'bypass_on_handshake_alert',
        'c3dCaCert': 'c3d_ca_cert',
        'c3dCaKey': 'c3d_ca_key',
        'c3dCertExtensionIncludes': 'c3d_cert_extension_includes',
        'c3dCertLifespan': 'c3d_cert_lifespan',
        'caFile': 'ca_file',
        'cacheSize': 'cache_size',
        'cacheTimeout': 'cache_timeout',
        'cipherGroup': 'cipher_group',
        'crlFile': 'crl_file',
        'expireCertResponseControl': 'expire_cert_response_control',
        'genericAlert': 'generic_alert',
        'handshakeTimeout': 'handshake_timeout',
        'maxActiveHandshakes': 'max_active_handshakes',
        'modSslMethods': 'mod_ssl_methods',
        'tmOptions': 'options',
        'peerCertMode': 'peer_cert_mode',
        'proxySsl': 'proxy_ssl',
        'proxySslPassthrough': 'proxy_ssl_passthrough',
        'renegotiatePeriod': 'renegotiate_period',
        'renegotiateSize': 'renegotiate_size',
        'retainCertificate': 'retain_certificate',
        'secureRenegotiation': 'secure_renegotiation',
        'serverName': 'server_name',
        'sessionMirroring': 'session_mirroring',
        'sessionTicket': 'session_ticket',
        'sniDefault': 'sni_default',
        'sniRequire': 'sni_require',
        'sslC3d': 'ssl_c3d',
        'sslForwardProxy': 'ssl_forward_proxy_enabled',
        'sslForwardProxyBypass': 'ssl_forward_proxy_bypass',
        'sslSignHash': 'ssl_sign_hash',
        'strictResume': 'strict_resume',
        'uncleanShutdown': 'unclean_shutdown',
        'untrustedCertResponseControl': 'untrusted_cert_response_control'
    }

    returnables = [
        'full_path',
        'name',
        'parent',
        'description',
        'unclean_shutdown',
        'strict_resume',
        'ssl_forward_proxy_enabled',
        'ssl_forward_proxy_bypass',
        'sni_default',
        'sni_require',
        'ssl_c3d',
        'session_mirroring',
        'session_ticket',
        'mod_ssl_methods',
        'allow_expired_crl',
        'retain_certificate',
        'mode',
        'bypass_on_client_cert_fail',
        'bypass_on_handshake_alert',
        'generic_alert',
        'renegotiation',
        'proxy_ssl',
        'proxy_ssl_passthrough',
        'peer_cert_mode',
        'untrusted_cert_response_control',
        'ssl_sign_hash',
        'server_name',
        'secure_renegotiation',
        'renegotiate_size',
        'renegotiate_period',
        'options',
        'ocsp',
        'max_active_handshakes',
        'key',
        'handshake_timeout',
        'expire_cert_response_control',
        'cert',
        'chain',
        'authentication_frequency',
        'ciphers',
        'cipher_group',
        'crl_file',
        'cache_timeout',
        'cache_size',
        'ca_file',
        'c3d_cert_lifespan',
        'alert_timeout',
        'c3d_ca_key',
        'authenticate_depth',
        'authenticate_name',
        'c3d_ca_cert',
        'c3d_cert_extension_includes',
    ]

    @property
    def c3d_cert_extension_includes(self):
        if self._values['c3d_cert_extension_includes'] is None:
            return None
        if len(self._values['c3d_cert_extension_includes']) == 0:
            return None
        self._values['c3d_cert_extension_includes'].sort()
        return self._values['c3d_cert_extension_includes']

    @property
    def options(self):
        if self._values['options'] is None:
            return None
        if len(self._values['options']) == 0:
            return None
        self._values['options'].sort()
        return self._values['options']

    @property
    def c3d_ca_cert(self):
        if self._values['c3d_ca_cert'] in [None, 'none']:
            return None
        return self._values['c3d_ca_cert']

    @property
    def ocsp(self):
        if self._values['ocsp'] in [None, 'none']:
            return None
        return self._values['ocsp']

    @property
    def server_name(self):
        if self._values['server_name'] in [None, 'none']:
            return None
        return self._values['server_name']

    @property
    def cipher_group(self):
        if self._values['cipher_group'] in [None, 'none']:
            return None
        return self._values['cipher_group']

    @property
    def authenticate_name(self):
        if self._values['authenticate_name'] in [None, 'none']:
            return None
        return self._values['authenticate_name']

    @property
    def c3d_ca_key(self):
        if self._values['c3d_ca_key'] in [None, 'none']:
            return None
        return self._values['c3d_ca_key']

    @property
    def ca_file(self):
        if self._values['ca_file'] in [None, 'none']:
            return None
        return self._values['ca_file']

    @property
    def crl_file(self):
        if self._values['crl_file'] in [None, 'none']:
            return None
        return self._values['crl_file']

    @property
    def authentication_frequency(self):
        if self._values['authentication_frequency'] in [None, 'none']:
            return None
        return self._values['authentication_frequency']

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def proxy_ssl_passthrough(self):
        return flatten_boolean(self._values['proxy_ssl_passthrough'])

    @property
    def proxy_ssl(self):
        return flatten_boolean(self._values['proxy_ssl'])

    @property
    def generic_alert(self):
        return flatten_boolean(self._values['generic_alert'])

    @property
    def renegotiation(self):
        return flatten_boolean(self._values['renegotiation'])

    @property
    def bypass_on_handshake_alert(self):
        return flatten_boolean(self._values['bypass_on_handshake_alert'])

    @property
    def bypass_on_client_cert_fail(self):
        return flatten_boolean(self._values['bypass_on_client_cert_fail'])

    @property
    def mode(self):
        return flatten_boolean(self._values['mode'])

    @property
    def retain_certificate(self):
        return flatten_boolean(self._values['retain_certificate'])

    @property
    def allow_expired_crl(self):
        return flatten_boolean(self._values['allow_expired_crl'])

    @property
    def mod_ssl_methods(self):
        return flatten_boolean(self._values['mod_ssl_methods'])

    @property
    def session_ticket(self):
        return flatten_boolean(self._values['session_ticket'])

    @property
    def session_mirroring(self):
        return flatten_boolean(self._values['session_mirroring'])

    @property
    def unclean_shutdown(self):
        return flatten_boolean(self._values['unclean_shutdown'])

    @property
    def strict_resume(self):
        return flatten_boolean(self._values['strict_resume'])

    @property
    def ssl_forward_proxy_enabled(self):
        return flatten_boolean(self._values['ssl_forward_proxy_enabled'])

    @property
    def ssl_forward_proxy_bypass(self):
        return flatten_boolean(self._values['ssl_forward_proxy_bypass'])

    @property
    def sni_default(self):
        return flatten_boolean(self._values['sni_default'])

    @property
    def sni_require(self):
        return flatten_boolean(self._values['sni_require'])

    @property
    def ssl_c3d(self):
        return flatten_boolean(self._values['ssl_c3d'])


class ServerSslProfilesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(ServerSslProfilesFactManager, self).__init__(**kwargs)
        self.want = ServerSslProfilesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(server_ssl_profiles=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = ServerSslProfilesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/server-ssl".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class SoftwareVolumesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'basebuild': 'base_build',
    }

    returnables = [
        'full_path',
        'name',
        'active',
        'base_build',
        'build',
        'product',
        'status',
        'version',
        'install_volume',
        'default_boot_location'
    ]

    @property
    def install_volume(self):
        if self._values['media'] is None:
            return None
        return self._values['media'].get('name', None)

    @property
    def default_boot_location(self):
        if self._values['media'] is None:
            return None
        return flatten_boolean(self._values['media'].get('defaultBootLocation', None))

    @property
    def active(self):
        if self._values['active'] is True:
            return 'yes'
        return 'no'


class SoftwareVolumesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(SoftwareVolumesFactManager, self).__init__(**kwargs)
        self.want = SoftwareVolumesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(software_volumes=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = SoftwareVolumesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/software/volume".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class SoftwareHotfixesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
    }

    returnables = [
        'name',
        'full_path',
        'build',
        'checksum',
        'id',
        'product',
        'title',
        'verified',
        'version',
    ]


class SoftwareHotfixesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(SoftwareHotfixesFactManager, self).__init__(**kwargs)
        self.want = SoftwareHotfixesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(software_hotfixes=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = SoftwareHotfixesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/software/hotfix".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class SoftwareImagesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'buildDate': 'build_date',
        'fileSize': 'file_size',
        'lastModified': 'last_modified',
    }

    returnables = [
        'name',
        'full_path',
        'build',
        'build_date',
        'checksum',
        'file_size',
        'last_modified',
        'product',
        'verified',
        'version',
    ]

    @property
    def file_size(self):
        if self._values['file_size'] is None:
            return None
        matches = re.match(r'\d+', self._values['file_size'])
        if matches:
            return int(matches.group(0))

    @property
    def build_date(self):
        """Normalizes the build_date string

        The ISOs usually ship with a broken format

        ex: Tue May 15 15 26 30 PDT 2018

        This will re-format that time so that it looks like ISO 8601 without
        microseconds

        ex: 2018-05-15T15:26:30

        :return:
        """
        if self._values['build_date'] is None:
            return None

        d = self._values['build_date'].split(' ')

        # This removes the timezone portion from the string. This is done
        # because Python has awfule tz parsing and strptime doesnt work with
        # all timezones in %Z; it only uses the timezones found in time.tzname
        d.pop(6)

        result = datetime.datetime.strptime(' '.join(d), '%a %b %d %H %M %S %Y').isoformat()
        return result

    @property
    def last_modified(self):
        """Normalizes the last_modified string

        The strings that the system reports look like the following

        ex: Tue May 15 15:26:30 2018

        This property normalizes this value to be isoformat

        ex: 2018-05-15T15:26:30

        :return:
        """
        if self._values['last_modified'] is None:
            return None
        result = datetime.datetime.strptime(self._values['last_modified'], '%a %b %d %H:%M:%S %Y').isoformat()
        return result


class SoftwareImagesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(SoftwareImagesFactManager, self).__init__(**kwargs)
        self.want = SoftwareImagesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(software_images=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = SoftwareImagesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/software/image".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class SslCertificatesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'keyType': 'key_type',
        'certificateKeySize': 'key_size',
        'systemPath': 'system_path',
        'checksum': 'sha1_checksum',
        'lastUpdateTime': 'last_update_time',
        'isBundle': 'is_bundle',
        'expirationString': 'expiration_date',
        'expirationDate': 'expiration_timestamp',
        'createTime': 'create_time'
    }

    returnables = [
        'full_path',
        'name',
        'key_type',
        'key_size',
        'system_path',
        'sha1_checksum',
        'subject',
        'last_update_time',
        'issuer',
        'is_bundle',
        'fingerprint',
        'expiration_date',
        'expiration_timestamp',
        'create_time',
    ]

    @property
    def sha1_checksum(self):
        if self._values['sha1_checksum'] is None:
            return None
        parts = self._values['sha1_checksum'].split(':')
        return parts[2]

    @property
    def is_bundle(self):
        if self._values['sha1_checksum'] is None:
            return None
        if self._values['is_bundle'] in BOOLEANS_TRUE:
            return 'yes'
        return 'no'


class SslCertificatesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(SslCertificatesFactManager, self).__init__(**kwargs)
        self.want = SslCertificatesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(ssl_certs=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = SslCertificatesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/ssl-cert".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class SslKeysParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'keyType': 'key_type',
        'keySize': 'key_size',
        'securityType': 'security_type',
        'systemPath': 'system_path',
        'checksum': 'sha1_checksum'
    }

    returnables = [
        'full_path',
        'name',
        'key_type',
        'key_size',
        'security_type',
        'system_path',
        'sha1_checksum'
    ]

    @property
    def sha1_checksum(self):
        if self._values['sha1_checksum'] is None:
            return None
        parts = self._values['sha1_checksum'].split(':')
        return parts[2]


class SslKeysFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(SslKeysFactManager, self).__init__(**kwargs)
        self.want = SslKeysParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(ssl_keys=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = SslKeysParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/ssl-key".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class SystemDbParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'defaultValue': 'default',
        'scfConfig': 'scf_config',
        'valueRange': 'value_range'
    }

    returnables = [
        'name',
        'full_path',
        'default',
        'scf_config',
        'value',
        'value_range'
    ]


class SystemDbFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(SystemDbFactManager, self).__init__(**kwargs)
        self.want = SystemInfoParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(system_db=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = SystemDbParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/db".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class SystemInfoParameters(BaseParameters):
    api_map = {

    }

    returnables = [
        'base_mac_address',
        'marketing_name',
        'time',
        'hardware_information',
        'product_information',
        'package_edition',
        'package_version',
        'product_code',
        'product_build',
        'product_built',
        'product_build_date',
        'product_changelist',
        'product_jobid',
        'product_version',
        'uptime',
        'chassis_serial',
        'host_board_part_revision',
        'host_board_serial',
        'platform',
        'switch_board_part_revision',
        'switch_board_serial'
    ]

    @property
    def chassis_serial(self):
        if self._values['system-info'] is None:
            return None
        if 'bigipChassisSerialNum' not in self._values['system-info'][0]:
            return None
        return self._values['system-info'][0]['bigipChassisSerialNum']

    @property
    def switch_board_serial(self):
        if self._values['system-info'] is None:
            return None
        if 'switchBoardSerialNum' not in self._values['system-info'][0]:
            return None
        if self._values['system-info'][0]['switchBoardSerialNum'].strip() == '':
            return None
        return self._values['system-info'][0]['switchBoardSerialNum']

    @property
    def switch_board_part_revision(self):
        if self._values['system-info'] is None:
            return None
        if 'switchBoardPartRevNum' not in self._values['system-info'][0]:
            return None
        if self._values['system-info'][0]['switchBoardPartRevNum'].strip() == '':
            return None
        return self._values['system-info'][0]['switchBoardPartRevNum']

    @property
    def platform(self):
        if self._values['system-info'] is None:
            return None
        return self._values['system-info'][0]['platform']

    @property
    def host_board_serial(self):
        if self._values['system-info'] is None:
            return None
        if 'hostBoardSerialNum' not in self._values['system-info'][0]:
            return None
        if self._values['system-info'][0]['hostBoardSerialNum'].strip() == '':
            return None
        return self._values['system-info'][0]['hostBoardSerialNum']

    @property
    def host_board_part_revision(self):
        if self._values['system-info'] is None:
            return None
        if 'hostBoardPartRevNum' not in self._values['system-info'][0]:
            return None
        if self._values['system-info'][0]['hostBoardPartRevNum'].strip() == '':
            return None
        return self._values['system-info'][0]['hostBoardPartRevNum']

    @property
    def package_edition(self):
        return self._values['Edition']

    @property
    def package_version(self):
        return 'Build {0} - {1}'.format(self._values['Build'], self._values['Date'])

    @property
    def product_build(self):
        return self._values['Build']

    @property
    def product_build_date(self):
        return self._values['Date']

    @property
    def product_built(self):
        if 'Built' in self._values['version_info']:
            return int(self._values['version_info']['Built'])

    @property
    def product_changelist(self):
        if 'Changelist' in self._values['version_info']:
            return int(self._values['version_info']['Changelist'])

    @property
    def product_jobid(self):
        if 'JobID' in self._values['version_info']:
            return int(self._values['version_info']['JobID'])

    @property
    def product_code(self):
        return self._values['Product']

    @property
    def product_version(self):
        return self._values['Version']

    @property
    def hardware_information(self):
        if self._values['hardware-version'] is None:
            return None
        self._transform_name_attribute(self._values['hardware-version'])
        result = [v for k, v in iteritems(self._values['hardware-version'])]
        return result

    def _transform_name_attribute(self, entry):
        if isinstance(entry, dict):
            for k, v in iteritems(entry):
                if k == 'tmName':
                    entry['name'] = entry.pop('tmName')
                self._transform_name_attribute(v)
        elif isinstance(entry, list):
            for k in entry:
                if k == 'tmName':
                    entry['name'] = entry.pop('tmName')
                self._transform_name_attribute(k)
        else:
            return

    @property
    def time(self):
        if self._values['fullDate'] is None:
            return None
        date = datetime.datetime.strptime(self._values['fullDate'], "%Y-%m-%dT%H:%M:%SZ")
        result = dict(
            day=date.day,
            hour=date.hour,
            minute=date.minute,
            month=date.month,
            second=date.second,
            year=date.year
        )
        return result

    @property
    def marketing_name(self):
        if self._values['platform'] is None:
            return None
        return self._values['platform'][0]['marketingName']

    @property
    def base_mac_address(self):
        if self._values['platform'] is None:
            return None
        return self._values['platform'][0]['baseMac']


class SystemInfoFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(SystemInfoFactManager, self).__init__(**kwargs)
        self.want = SystemInfoParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(system_info=facts)
        return result

    def _exec_module(self):
        facts = self.read_facts()
        results = facts.to_return()
        return results

    def read_facts(self):
        collection = self.read_collection_from_device()
        params = SystemInfoParameters(params=collection)
        return params

    def read_collection_from_device(self):
        result = dict()
        tmp = self.read_hardware_info_from_device()
        if tmp:
            result.update(tmp)

        tmp = self.read_clock_info_from_device()
        if tmp:
            result.update(tmp)

        tmp = self.read_version_info_from_device()
        if tmp:
            result.update(tmp)

        tmp = self.read_uptime_info_from_device()
        if tmp:
            result.update(tmp)

        tmp = self.read_version_file_info_from_device()
        if tmp:
            result.update(tmp)

        return result

    def read_version_file_info_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        args = dict(
            command='run',
            utilCmdArgs='-c "cat /VERSION"'
        )
        resp = self.client.api.post(uri, json=args)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        try:
            pattern = r'^(?P<key>(Product|Build|Sequence|BaseBuild|Edition|Date|Built|Changelist|JobID))\:(?P<value>.*)'
            result = response['commandResult'].strip()
        except KeyError:
            return None

        if 'No such file or directory' in result:
            return None

        lines = response['commandResult'].split("\n")
        result = dict()
        for line in lines:
            if not line:
                continue
            matches = re.match(pattern, line)
            if matches:
                result[matches.group('key')] = matches.group('value').strip()

        if result:
            return dict(
                version_info=result
            )

    def read_uptime_info_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        args = dict(
            command='run',
            utilCmdArgs='-c "cat /proc/uptime"'
        )
        resp = self.client.api.post(uri, json=args)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        try:
            parts = response['commandResult'].strip().split(' ')
            return dict(
                uptime=math.floor(float(parts[0]))
            )
        except KeyError:
            pass

    def read_hardware_info_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/hardware".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        return result

    def read_clock_info_from_device(self):
        """Parses clock info from the REST API

        The clock stat returned from the REST API (at the time of 13.1.0.7)
        is similar to the following.

        {
            "kind": "tm:sys:clock:clockstats",
            "selfLink": "https://localhost/mgmt/tm/sys/clock?ver=13.1.0.4",
            "entries": {
                "https://localhost/mgmt/tm/sys/clock/0": {
                    "nestedStats": {
                        "entries": {
                            "fullDate": {
                                "description": "2018-06-05T13:38:33Z"
                            }
                        }
                    }
                }
            }
        }

        Parsing this data using the ``parseStats`` method, yields a list of
        the clock stats in a format resembling that below.

        [{'fullDate': '2018-06-05T13:41:05Z'}]

        Therefore, this method cherry-picks the first entry from this list
        and returns it. There can be no other items in this list.

        Returns:
            A dict mapping keys to the corresponding clock stats. For
            example:

            {'fullDate': '2018-06-05T13:41:05Z'}

            There should never not be a clock stat, unless by chance it
            is removed from the API in the future, or changed to a different
            API endpoint.

        Raises:
            F5ModuleError: A non-successful HTTP code was returned or a JSON
                           response was not found.
        """
        uri = "https://{0}:{1}/mgmt/tm/sys/clock".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        return result[0]

    def read_version_info_from_device(self):
        """Parses version info from the REST API

        The version stat returned from the REST API (at the time of 13.1.0.7)
        is similar to the following.

        {
            "kind": "tm:sys:version:versionstats",
            "selfLink": "https://localhost/mgmt/tm/sys/version?ver=13.1.0.4",
            "entries": {
                "https://localhost/mgmt/tm/sys/version/0": {
                    "nestedStats": {
                        "entries": {
                            "Build": {
                                "description": "0.0.6"
                            },
                            "Date": {
                                "description": "Tue Mar 13 20:10:42 PDT 2018"
                            },
                            "Edition": {
                                "description": "Point Release 4"
                            },
                            "Product": {
                                "description": "BIG-IP"
                            },
                            "Title": {
                                "description": "Main Package"
                            },
                            "Version": {
                                "description": "13.1.0.4"
                            }
                        }
                    }
                }
            }
        }

        Parsing this data using the ``parseStats`` method, yields a list of
        the clock stats in a format resembling that below.

        [{'Build': '0.0.6', 'Date': 'Tue Mar 13 20:10:42 PDT 2018',
          'Edition': 'Point Release 4', 'Product': 'BIG-IP', 'Title': 'Main Package',
          'Version': '13.1.0.4'}]

        Therefore, this method cherry-picks the first entry from this list
        and returns it. There can be no other items in this list.

        Returns:
            A dict mapping keys to the corresponding clock stats. For
            example:

            {'Build': '0.0.6', 'Date': 'Tue Mar 13 20:10:42 PDT 2018',
             'Edition': 'Point Release 4', 'Product': 'BIG-IP', 'Title': 'Main Package',
             'Version': '13.1.0.4'}

            There should never not be a version stat, unless by chance it
            is removed from the API in the future, or changed to a different
            API endpoint.

        Raises:
            F5ModuleError: A non-successful HTTP code was returned or a JSON
                           response was not found.
        """
        uri = "https://{0}:{1}/mgmt/tm/sys/version".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        return result[0]


class TcpMonitorsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'defaultsFrom': 'parent',
        'adaptiveDivergenceType': 'adaptive_divergence_type',
        'adaptiveDivergenceValue': 'adaptive_divergence_value',
        'adaptiveLimit': 'adaptive_limit',
        'adaptiveSamplingTimespan': 'adaptive_sampling_timespan',
        'ipDscp': 'ip_dscp',
        'manualResume': 'manual_resume',
        'timeUntilUp': 'time_until_up',
        'upInterval': 'up_interval',
    }

    returnables = [
        'full_path',
        'name',
        'parent',
        'description',
        'adaptive',
        'adaptive_divergence_type',
        'adaptive_divergence_value',
        'adaptive_limit',
        'adaptive_sampling_timespan',
        'destination',
        'interval',
        'ip_dscp',
        'manual_resume',
        'reverse',
        'time_until_up',
        'timeout',
        'transparent',
        'up_interval',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def transparent(self):
        return flatten_boolean(self._values['transparent'])

    @property
    def manual_resume(self):
        return flatten_boolean(self._values['manual_resume'])

    @property
    def adaptive(self):
        return flatten_boolean(self._values['adaptive'])

    @property
    def reverse(self):
        return flatten_boolean(self._values['reverse'])


class TcpMonitorsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(TcpMonitorsFactManager, self).__init__(**kwargs)
        self.want = TcpMonitorsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(tcp_monitors=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = TcpMonitorsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/tcp".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class TcpHalfOpenMonitorsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'defaultsFrom': 'parent',
        'manualResume': 'manual_resume',
        'timeUntilUp': 'time_until_up',
        'upInterval': 'up_interval',
    }

    returnables = [
        'full_path',
        'name',
        'parent',
        'description',
        'destination',
        'interval',
        'manual_resume',
        'time_until_up',
        'timeout',
        'transparent',
        'up_interval',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def transparent(self):
        return flatten_boolean(self._values['transparent'])

    @property
    def manual_resume(self):
        return flatten_boolean(self._values['manual_resume'])


class TcpHalfOpenMonitorsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(TcpHalfOpenMonitorsFactManager, self).__init__(**kwargs)
        self.want = TcpHalfOpenMonitorsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(tcp_half_open_monitors=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = TcpHalfOpenMonitorsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/tcp-half-open".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class TcpProfilesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'defaultsFrom': 'parent',
        'ackOnPush': 'ack_on_push',
        'autoProxyBufferSize': 'auto_proxy_buffer',
        'autoReceiveWindowSize': 'auto_receive_window',
        'autoSendBufferSize': 'auto_send_buffer',
        'closeWaitTimeout': 'close_wait',
        'cmetricsCache': 'congestion_metrics_cache',
        'cmetricsCacheTimeout': 'congestion_metrics_cache_timeout',
        'congestionControl': 'congestion_control',
        'deferredAccept': 'deferred_accept',
        'delayWindowControl': 'delay_window_control',
        'delayedAcks': 'delayed_acks',
        'earlyRetransmit': 'early_retransmit',
        'ecn': 'explicit_congestion_notification',
        'enhancedLossRecovery': 'enhanced_loss_recovery',
        'fastOpen': 'fast_open',
        'fastOpenCookieExpiration': 'fast_open_cookie_expiration',
        'finWaitTimeout': 'fin_wait_1',
        'finWait_2Timeout': 'fin_wait_2',
        'idleTimeout': 'idle_timeout',
        'initCwnd': 'initial_congestion_window_size',
        'initRwnd': 'initial_receive_window_size',
        'ipDfMode': 'dont_fragment_flag',
        'ipTosToClient': 'ip_tos',
        'ipTtlMode': 'time_to_live',
        'ipTtlV4': 'time_to_live_v4',
        'ipTtlV6': 'time_to_live_v6',
        'keepAliveInterval': 'keep_alive_interval',
        'limitedTransmit': 'limited_transmit_recovery',
        'linkQosToClient': 'link_qos',
        'maxRetrans': 'max_segment_retrans',
        'synMaxRetrans': 'max_syn_retrans',
        'rexmtThresh': 'retransmit_threshold',
        'maxSegmentSize': 'max_segment_size',
        'md5Signature': 'md5_signature',
        'minimumRto': 'minimum_rto',
        'mptcp': 'multipath_tcp',
        'mptcpCsum': 'mptcp_checksum',
        'mptcpCsumVerify': 'mptcp_checksum_verify',
        'mptcpFallback': 'mptcp_fallback',
        'mptcpFastjoin': 'mptcp_fast_join',
        'mptcpIdleTimeout': 'mptcp_idle_timeout',
        'mptcpJoinMax': 'mptcp_join_max',
        'mptcpMakeafterbreak': 'mptcp_make_after_break',
        'mptcpNojoindssack': 'mptcp_no_join_dss_ack',
        'mptcpRtomax': 'mptcp_rto_max',
        'mptcpRxmitmin': 'mptcp_retransmit_min',
        'mptcpSubflowmax': 'mptcp_subflow_max',
        'mptcpTimeout': 'mptcp_timeout',
        'nagle': 'nagle_algorithm',
        'pktLossIgnoreBurst': 'pkt_loss_ignore_burst',
        'pktLossIgnoreRate': 'pkt_loss_ignore_rate',
        'proxyBufferHigh': 'proxy_buffer_high',
        'proxyBufferLow': 'proxy_buffer_low',
        'proxyMss': 'proxy_max_segment',
        'proxyOptions': 'proxy_options',
        'pushFlag': 'push_flag',
        'ratePace': 'rate_pace',
        'ratePaceMaxRate': 'rate_pace_max_rate',
        'receiveWindowSize': 'receive_window',
        'resetOnTimeout': 'reset_on_timeout',
        'selectiveAcks': 'selective_acks',
        'selectiveNack': 'selective_nack',
        'sendBufferSize': 'send_buffer',
        'slowStart': 'slow_start',
        'synCookieEnable': 'syn_cookie_enable',
        'synCookieWhitelist': 'syn_cookie_white_list',
        'synRtoBase': 'syn_retrans_to_base',
        'tailLossProbe': 'tail_loss_probe',
        'timeWaitRecycle': 'time_wait_recycle',
        'timeWaitTimeout': 'time_wait',
        'verifiedAccept': 'verified_accept',
        'zeroWindowTimeout': 'zero_window_timeout',
    }

    returnables = [
        'full_path',
        'name',
        'parent',
        'description',
        'abc',
        'ack_on_push',
        'auto_proxy_buffer',
        'auto_receive_window',
        'auto_send_buffer',
        'close_wait',
        'congestion_metrics_cache',
        'congestion_metrics_cache_timeout',
        'congestion_control',
        'deferred_accept',
        'delay_window_control',
        'delayed_acks',
        'dsack',
        'early_retransmit',
        'explicit_congestion_notification',
        'enhanced_loss_recovery',
        'fast_open',
        'fast_open_cookie_expiration',
        'fin_wait_1',
        'fin_wait_2',
        'idle_timeout',
        'initial_congestion_window_size',
        'initial_receive_window_size',
        'dont_fragment_flag',
        'ip_tos',
        'time_to_live',
        'time_to_live_v4',
        'time_to_live_v6',
        'keep_alive_interval',
        'limited_transmit_recovery',
        'link_qos',
        'max_segment_retrans',
        'max_syn_retrans',
        'max_segment_size',
        'md5_signature',
        'minimum_rto',
        'multipath_tcp',
        'mptcp_checksum',
        'mptcp_checksum_verify',
        'mptcp_fallback',
        'mptcp_fast_join',
        'mptcp_idle_timeout',
        'mptcp_join_max',
        'mptcp_make_after_break',
        'mptcp_no_join_dss_ack',
        'mptcp_rto_max',
        'mptcp_retransmit_min',
        'mptcp_subflow_max',
        'mptcp_timeout',
        'nagle_algorithm',
        'pkt_loss_ignore_burst',
        'pkt_loss_ignore_rate',
        'proxy_buffer_high',
        'proxy_buffer_low',
        'proxy_max_segment',
        'proxy_options',
        'push_flag',
        'rate_pace',
        'rate_pace_max_rate',
        'receive_window',
        'reset_on_timeout',
        'retransmit_threshold',
        'selective_acks',
        'selective_nack',
        'send_buffer',
        'slow_start',
        'syn_cookie_enable',
        'syn_cookie_white_list',
        'syn_retrans_to_base',
        'tail_loss_probe',
        'time_wait_recycle',
        'time_wait',
        'timestamps',
        'verified_accept',
        'zero_window_timeout',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def time_wait(self):
        if self._values['time_wait'] is None:
            return None
        if self._values['time_wait'] == 0:
            return "immediate"
        if self._values['time_wait'] == 4294967295:
            return 'indefinite'
        return self._values['time_wait']

    @property
    def close_wait(self):
        if self._values['close_wait'] is None:
            return None
        if self._values['close_wait'] == 0:
            return "immediate"
        if self._values['close_wait'] == 4294967295:
            return 'indefinite'
        return self._values['close_wait']

    @property
    def fin_wait_1(self):
        if self._values['fin_wait_1'] is None:
            return None
        if self._values['fin_wait_1'] == 0:
            return "immediate"
        if self._values['fin_wait_1'] == 4294967295:
            return 'indefinite'
        return self._values['fin_wait_1']

    @property
    def fin_wait_2(self):
        if self._values['fin_wait_2'] is None:
            return None
        if self._values['fin_wait_2'] == 0:
            return "immediate"
        if self._values['fin_wait_2'] == 4294967295:
            return 'indefinite'
        return self._values['fin_wait_2']

    @property
    def zero_window_timeout(self):
        if self._values['zero_window_timeout'] is None:
            return None
        if self._values['zero_window_timeout'] == 4294967295:
            return 'indefinite'
        return self._values['zero_window_timeout']

    @property
    def idle_timeout(self):
        if self._values['idle_timeout'] is None:
            return None
        if self._values['idle_timeout'] == 4294967295:
            return 'indefinite'
        return self._values['idle_timeout']

    @property
    def keep_alive_interval(self):
        if self._values['keep_alive_interval'] is None:
            return None
        if self._values['keep_alive_interval'] == 4294967295:
            return 'indefinite'
        return self._values['keep_alive_interval']

    @property
    def verified_accept(self):
        return flatten_boolean(self._values['verified_accept'])

    @property
    def timestamps(self):
        return flatten_boolean(self._values['timestamps'])

    @property
    def time_wait_recycle(self):
        return flatten_boolean(self._values['time_wait_recycle'])

    @property
    def tail_loss_probe(self):
        return flatten_boolean(self._values['tail_loss_probe'])

    @property
    def syn_cookie_white_list(self):
        return flatten_boolean(self._values['syn_cookie_white_list'])

    @property
    def syn_cookie_enable(self):
        return flatten_boolean(self._values['syn_cookie_enable'])

    @property
    def slow_start(self):
        return flatten_boolean(self._values['slow_start'])

    @property
    def selective_nack(self):
        return flatten_boolean(self._values['selective_nack'])

    @property
    def selective_acks(self):
        return flatten_boolean(self._values['selective_acks'])

    @property
    def reset_on_timeout(self):
        return flatten_boolean(self._values['reset_on_timeout'])

    @property
    def rate_pace(self):
        return flatten_boolean(self._values['rate_pace'])

    @property
    def proxy_options(self):
        return flatten_boolean(self._values['proxy_options'])

    @property
    def proxy_max_segment(self):
        return flatten_boolean(self._values['proxy_max_segment'])

    @property
    def nagle_algorithm(self):
        return flatten_boolean(self._values['nagle_algorithm'])

    @property
    def mptcp_no_join_dss_ack(self):
        return flatten_boolean(self._values['mptcp_no_join_dss_ack'])

    @property
    def mptcp_make_after_break(self):
        return flatten_boolean(self._values['mptcp_make_after_break'])

    @property
    def mptcp_fast_join(self):
        return flatten_boolean(self._values['mptcp_fast_join'])

    @property
    def mptcp_checksum_verify(self):
        return flatten_boolean(self._values['mptcp_checksum_verify'])

    @property
    def mptcp_checksum(self):
        return flatten_boolean(self._values['mptcp_checksum'])

    @property
    def multipath_tcp(self):
        return flatten_boolean(self._values['multipath_tcp'])

    @property
    def md5_signature(self):
        return flatten_boolean(self._values['md5_signature'])

    @property
    def limited_transmit_recovery(self):
        return flatten_boolean(self._values['limited_transmit_recovery'])

    @property
    def fast_open(self):
        return flatten_boolean(self._values['fast_open'])

    @property
    def enhanced_loss_recovery(self):
        return flatten_boolean(self._values['enhanced_loss_recovery'])

    @property
    def explicit_congestion_notification(self):
        return flatten_boolean(self._values['explicit_congestion_notification'])

    @property
    def early_retransmit(self):
        return flatten_boolean(self._values['early_retransmit'])

    @property
    def dsack(self):
        return flatten_boolean(self._values['dsack'])

    @property
    def delayed_acks(self):
        return flatten_boolean(self._values['delayed_acks'])

    @property
    def delay_window_control(self):
        return flatten_boolean(self._values['delay_window_control'])

    @property
    def deferred_accept(self):
        return flatten_boolean(self._values['deferred_accept'])

    @property
    def congestion_metrics_cache(self):
        return flatten_boolean(self._values['congestion_metrics_cache'])

    @property
    def auto_send_buffer(self):
        return flatten_boolean(self._values['auto_send_buffer'])

    @property
    def auto_receive_window(self):
        return flatten_boolean(self._values['auto_receive_window'])

    @property
    def auto_proxy_buffer(self):
        return flatten_boolean(self._values['auto_proxy_buffer'])

    @property
    def abc(self):
        return flatten_boolean(self._values['abc'])

    @property
    def ack_on_push(self):
        return flatten_boolean(self._values['ack_on_push'])


class TcpProfilesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(TcpProfilesFactManager, self).__init__(**kwargs)
        self.want = TcpProfilesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(tcp_profiles=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = TcpProfilesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/tcp".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class TrafficGroupsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'autoFailbackEnabled': 'auto_failback_enabled',
        'autoFailbackTime': 'auto_failback_time',
        'haLoadFactor': 'ha_load_factor',
        'haOrder': 'ha_order',
        'isFloating': 'is_floating',
        'mac': 'mac_masquerade_address'
    }

    returnables = [
        'full_path',
        'name',
        'description',
        'auto_failback_enabled',
        'auto_failback_time',
        'ha_load_factor',
        'ha_order',
        'is_floating',
        'mac_masquerade_address'
    ]

    @property
    def auto_failback_time(self):
        if self._values['auto_failback_time'] is None:
            return None
        return int(self._values['auto_failback_time'])

    @property
    def auto_failback_enabled(self):
        if self._values['auto_failback_enabled'] is None:
            return None
        elif self._values['auto_failback_enabled'] == 'false':
            # Yes, the REST API stores this as a string
            return 'no'
        return 'yes'

    @property
    def is_floating(self):
        if self._values['is_floating'] is None:
            return None
        elif self._values['is_floating'] == 'true':
            # Yes, the REST API stores this as a string
            return 'yes'
        return 'no'

    @property
    def mac_masquerade_address(self):
        if self._values['mac_masquerade_address'] in [None, 'none']:
            return None
        return self._values['mac_masquerade_address']


class TrafficGroupsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(TrafficGroupsFactManager, self).__init__(**kwargs)
        self.want = TrafficGroupsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(traffic_groups=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            attrs = resource
            attrs['stats'] = self.read_stats_from_device(attrs['fullPath'])
            params = TrafficGroupsParameters(params=attrs)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/cm/traffic-group".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result

    def read_stats_from_device(self, full_path):
        uri = "https://{0}:{1}/mgmt/tm/cm/traffic-group/{2}/stats".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=full_path)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        try:
            return result['stats']
        except KeyError:
            return {}


class TrunksParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'media': 'media_speed',
        'lacpMode': 'lacp_mode',
        'lacp': 'lacp_state',
        'lacpTimeout': 'lacp_timeout',
        'stp': 'stp_enabled',
        'workingMbrCount': 'operational_member_count',
        'linkSelectPolicy': 'link_selection_policy',
        'distributionHash': 'distribution_hash',
        'cfgMbrCount': 'configured_member_count'
    }

    returnables = [
        'full_path',
        'name',
        'description',
        'media_speed',
        'lacp_mode',        # 'active' or 'passive'
        'lacp_enabled',
        'stp_enabled',
        'operational_member_count',
        'media_status',
        'link_selection_policy',
        'lacp_timeout',
        'interfaces',
        'distribution_hash',
        'configured_member_count'
    ]

    @property
    def lacp_enabled(self):
        if self._values['lacp_enabled'] is None:
            return None
        elif self._values['lacp_enabled'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def stp_enabled(self):
        if self._values['stp_enabled'] is None:
            return None
        elif self._values['stp_enabled'] == 'disabled':
            return 'no'
        return 'yes'

    @property
    def media_status(self):
        return self._values['stats']['status']


class TrunksFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(TrunksFactManager, self).__init__(**kwargs)
        self.want = TrunksParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(trunks=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            attrs = resource
            attrs['stats'] = self.read_stats_from_device(attrs['fullPath'])
            params = TrunksParameters(params=attrs)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/trunk".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result

    def read_stats_from_device(self, full_path):
        uri = "https://{0}:{1}/mgmt/tm/net/trunk/{2}/stats".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=full_path)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        try:
            return result['stats']
        except KeyError:
            return {}


class UdpProfilesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'allowNoPayload': 'allow_no_payload',
        'bufferMaxBytes': 'buffer_max_bytes',
        'bufferMaxPackets': 'buffer_max_packets',
        'datagramLoadBalancing': 'datagram_load_balancing',
        'defaultsFrom': 'parent',
        'idleTimeout': 'idle_timeout',
        'ipDfMode': 'ip_df_mode',
        'ipTosToClient': 'ip_tos_to_client',
        'ipTtlMode': 'ip_ttl_mode',
        'ipTtlV4': 'ip_ttl_v4',
        'ipTtlV6': 'ip_ttl_v6',
        'linkQosToClient': 'link_qos_to_client',
        'noChecksum': 'no_checksum',
        'proxyMss': 'proxy_mss',
    }

    returnables = [
        'full_path',
        'name',
        'parent',
        'description',
        'allow_no_payload',
        'buffer_max_bytes',
        'buffer_max_packets',
        'datagram_load_balancing',
        'idle_timeout',
        'ip_df_mode',
        'ip_tos_to_client',
        'ip_ttl_mode',
        'ip_ttl_v4',
        'ip_ttl_v6',
        'link_qos_to_client',
        'no_checksum',
        'proxy_mss',
    ]

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def allow_no_payload(self):
        return flatten_boolean(self._values['allow_no_payload'])

    @property
    def datagram_load_balancing(self):
        return flatten_boolean(self._values['datagram_load_balancing'])

    @property
    def proxy_mss(self):
        return flatten_boolean(self._values['proxy_mss'])

    @property
    def no_checksum(self):
        return flatten_boolean(self._values['no_checksum'])


class UdpProfilesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(UdpProfilesFactManager, self).__init__(**kwargs)
        self.want = UdpProfilesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(udp_profiles=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = UdpProfilesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/udp".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class VcmpGuestsParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'allowedSlots': 'allowed_slots',
        'assignedSlots': 'assigned_slots',
        'bootPriority': 'boot_priority',
        'coresPerSlot': 'cores_per_slot',
        'initialImage': 'initial_image',
        'initialHotfix': 'hotfix_image',
        'managementGw': 'mgmt_route',
        'managementIp': 'mgmt_address',
        'managementNetwork': 'mgmt_network',
        'minSlots': 'min_number_of_slots',
        'slots': 'number_of_slots',
        'sslMode': 'ssl_mode',
        'virtualDisk': 'virtual_disk'
    }

    returnables = [
        'name',
        'full_path',
        'allowed_slots',
        'assigned_slots',
        'boot_priority',
        'cores_per_slot',
        'hostname',
        'hotfix_image',
        'initial_image',
        'mgmt_route',
        'mgmt_address',
        'mgmt_network',
        'min_number_of_slots',
        'number_of_slots',
        'ssl_mode',
        'state',
        'virtual_disk',
    ]


class VcmpGuestsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(VcmpGuestsFactManager, self).__init__(**kwargs)
        self.want = VcmpGuestsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(vcmp_guests=facts)
        return result

    def _exec_module(self):
        if 'vcmp' not in self.provisioned_modules:
            return []
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = VcmpGuestsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/vcmp/guest".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class VirtualAddressesParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'arp': 'arp_enabled',
        'autoDelete': 'auto_delete_enabled',
        'connectionLimit': 'connection_limit',
        'icmpEcho': 'icmp_echo',
        'mask': 'netmask',
        'routeAdvertisement': 'route_advertisement',
        'trafficGroup': 'traffic_group',
        'inheritedTrafficGroup': 'inherited_traffic_group'
    }

    returnables = [
        'full_path',
        'name',
        'address',
        'arp_enabled',
        'auto_delete_enabled',
        'connection_limit',
        'description',
        'enabled',
        'icmp_echo',
        'floating',
        'netmask',
        'route_advertisement',
        'traffic_group',
        'spanning',
        'inherited_traffic_group'
    ]

    @property
    def spanning(self):
        return flatten_boolean(self._values['spanning'])

    @property
    def arp_enabled(self):
        return flatten_boolean(self._values['arp_enabled'])

    @property
    def route_advertisement(self):
        return flatten_boolean(self._values['route_advertisement'])

    @property
    def auto_delete_enabled(self):
        return flatten_boolean(self._values['auto_delete_enabled'])

    @property
    def inherited_traffic_group(self):
        return flatten_boolean(self._values['inherited_traffic_group'])

    @property
    def icmp_echo(self):
        return flatten_boolean(self._values['icmp_echo'])

    @property
    def floating(self):
        return flatten_boolean(self._values['floating'])

    @property
    def enabled(self):
        return flatten_boolean(self._values['enabled'])


class VirtualAddressesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(VirtualAddressesFactManager, self).__init__(**kwargs)
        self.want = VirtualAddressesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(virtual_addresses=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = VirtualAddressesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual-address".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class VirtualServersParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'autoLasthop': 'auto_lasthop',
        'bwcPolicy': 'bw_controller_policy',
        'cmpEnabled': 'cmp_enabled',
        'connectionLimit': 'connection_limit',
        'fallbackPersistence': 'fallback_persistence_profile',
        'persist': 'persistence_profile',
        'translatePort': 'translate_port',
        'translateAddress': 'translate_address',
        'lastHopPool': 'last_hop_pool',
        'nat64': 'nat64_enabled',
        'sourcePort': 'source_port_behavior',
        'ipIntelligencePolicy': 'ip_intelligence_policy',
        'ipProtocol': 'protocol',
        'pool': 'default_pool',
        'rateLimitMode': 'rate_limit_mode',
        'rateLimitSrcMask': 'rate_limit_source_mask',
        'rateLimitDstMask': 'rate_limit_destination_mask',
        'rateLimit': 'rate_limit',
        'sourceAddressTranslation': 'snat_type',
        'gtmScore': 'gtm_score',
        'rateClass': 'rate_class',
        'source': 'source_address',
        'auth': 'authentication_profile',
        'mirror': 'connection_mirror_enabled',
        'rules': 'irules',
        'securityLogProfiles': 'security_log_profiles',
        'profilesReference': 'profiles'
    }

    returnables = [
        'full_path',
        'name',
        'auto_lasthop',
        'bw_controller_policy',
        'cmp_enabled',
        'connection_limit',
        'description',
        'enabled',
        'fallback_persistence_profile',
        'persistence_profile',
        'translate_port',
        'translate_address',
        'vlans',
        'destination',
        'last_hop_pool',
        'nat64_enabled',
        'source_port_behavior',
        'ip_intelligence_policy',
        'protocol',
        'default_pool',
        'rate_limit_mode',
        'rate_limit_source_mask',
        'rate_limit',
        'snat_type',
        'snat_pool',
        'gtm_score',
        'rate_class',
        'rate_limit_destination_mask',
        'source_address',
        'authentication_profile',
        'connection_mirror_enabled',
        'irules',
        'security_log_profiles',
        'type',
        'profiles',
        'destination_address',
        'destination_port',
        'availability_status',
        'status_reason',
        'total_requests',
        'client_side_bits_in',
        'client_side_bits_out',
        'client_side_current_connections',
        'client_side_evicted_connections',
        'client_side_max_connections',
        'client_side_pkts_in',
        'client_side_pkts_out',
        'client_side_slow_killed',
        'client_side_total_connections',
        'cmp_mode',
        'ephemeral_bits_in',
        'ephemeral_bits_out',
        'ephemeral_current_connections',
        'ephemeral_evicted_connections',
        'ephemeral_max_connections',
        'ephemeral_pkts_in',
        'ephemeral_pkts_out',
        'ephemeral_slow_killed',
        'ephemeral_total_connections',
        'total_software_accepted_syn_cookies',
        'total_hardware_accepted_syn_cookies',
        'total_hardware_syn_cookies',
        'hardware_syn_cookie_instances',
        'total_software_rejected_syn_cookies',
        'software_syn_cookie_instances',
        'current_syn_cache',
        'syn_cache_overflow',
        'total_software_syn_cookies',
        'syn_cookies_status',
        'max_conn_duration',
        'mean_conn_duration',
        'min_conn_duration',
        'cpu_usage_ratio_last_5_min',
        'cpu_usage_ratio_last_5_sec',
        'cpu_usage_ratio_last_1_min',
    ]

    @property
    def max_conn_duration(self):
        return self._values['stats']['csMaxConnDur']

    @property
    def mean_conn_duration(self):
        return self._values['stats']['csMeanConnDur']

    @property
    def min_conn_duration(self):
        return self._values['stats']['csMinConnDur']

    @property
    def cpu_usage_ratio_last_5_min(self):
        return self._values['stats']['fiveMinAvgUsageRatio']

    @property
    def cpu_usage_ratio_last_5_sec(self):
        return self._values['stats']['fiveSecAvgUsageRatio']

    @property
    def cpu_usage_ratio_last_1_min(self):
        return self._values['stats']['oneMinAvgUsageRatio']

    @property
    def cmp_mode(self):
        return self._values['stats']['cmpEnableMode']

    @property
    def availability_status(self):
        return self._values['stats']['status']['availabilityState']

    @property
    def status_reason(self):
        return self._values['stats']['status']['statusReason']

    @property
    def total_requests(self):
        return self._values['stats']['totRequests']

    @property
    def ephemeral_bits_in(self):
        return self._values['stats']['ephemeral']['bitsIn']

    @property
    def ephemeral_bits_out(self):
        return self._values['stats']['ephemeral']['bitsOut']

    @property
    def ephemeral_current_connections(self):
        return self._values['stats']['ephemeral']['curConns']

    @property
    def ephemeral_evicted_connections(self):
        return self._values['stats']['ephemeral']['evictedConns']

    @property
    def ephemeral_max_connections(self):
        return self._values['stats']['ephemeral']['maxConns']

    @property
    def ephemeral_pkts_in(self):
        return self._values['stats']['ephemeral']['pktsIn']

    @property
    def ephemeral_pkts_out(self):
        return self._values['stats']['ephemeral']['pktsOut']

    @property
    def ephemeral_slow_killed(self):
        return self._values['stats']['ephemeral']['slowKilled']

    @property
    def ephemeral_total_connections(self):
        return self._values['stats']['ephemeral']['totConns']

    @property
    def client_side_bits_in(self):
        return self._values['stats']['clientside']['bitsIn']

    @property
    def client_side_bits_out(self):
        return self._values['stats']['clientside']['bitsOut']

    @property
    def client_side_current_connections(self):
        return self._values['stats']['clientside']['curConns']

    @property
    def client_side_evicted_connections(self):
        return self._values['stats']['clientside']['evictedConns']

    @property
    def client_side_max_connections(self):
        return self._values['stats']['clientside']['maxConns']

    @property
    def client_side_pkts_in(self):
        return self._values['stats']['clientside']['pktsIn']

    @property
    def client_side_pkts_out(self):
        return self._values['stats']['clientside']['pktsOut']

    @property
    def client_side_slow_killed(self):
        return self._values['stats']['clientside']['slowKilled']

    @property
    def client_side_total_connections(self):
        return self._values['stats']['clientside']['totConns']

    @property
    def total_software_accepted_syn_cookies(self):
        return self._values['stats']['syncookie']['accepts']

    @property
    def total_hardware_accepted_syn_cookies(self):
        return self._values['stats']['syncookie']['hwAccepts']

    @property
    def total_hardware_syn_cookies(self):
        return self._values['stats']['syncookie']['hwSyncookies']

    @property
    def hardware_syn_cookie_instances(self):
        return self._values['stats']['syncookie']['hwsyncookieInstance']

    @property
    def total_software_rejected_syn_cookies(self):
        return self._values['stats']['syncookie']['rejects']

    @property
    def software_syn_cookie_instances(self):
        return self._values['stats']['syncookie']['swsyncookieInstance']

    @property
    def current_syn_cache(self):
        return self._values['stats']['syncookie']['syncacheCurr']

    @property
    def syn_cache_overflow(self):
        return self._values['stats']['syncookie']['syncacheOver']

    @property
    def total_software_syn_cookies(self):
        return self._values['stats']['syncookie']['syncookies']

    @property
    def syn_cookies_status(self):
        return self._values['stats']['syncookieStatus']

    @property
    def destination_address(self):
        if self._values['destination'] is None:
            return None
        tup = self.destination_tuple
        return tup.ip

    @property
    def destination_port(self):
        if self._values['destination'] is None:
            return None
        tup = self.destination_tuple
        return tup.port

    @property
    def type(self):
        """Attempt to determine the current server type

        This check is very unscientific. It turns out that this information is not
        exactly available anywhere on a BIG-IP. Instead, we rely on a semi-reliable
        means for determining what the type of the virtual server is. Hopefully it
        always works.

        There are a handful of attributes that can be used to determine a specific
        type. There are some types though that can only be determined by looking at
        the profiles that are assigned to them. We follow that method for those
        complicated types; message-routing, fasthttp, and fastl4.

        Because type determination is an expensive operation, we cache the result
        from the operation.

        Returns:
            string: The server type.
        """
        if self._values['l2Forward'] is True:
            result = 'forwarding-l2'
        elif self._values['ipForward'] is True:
            result = 'forwarding-ip'
        elif self._values['stateless'] is True:
            result = 'stateless'
        elif self._values['reject'] is True:
            result = 'reject'
        elif self._values['dhcpRelay'] is True:
            result = 'dhcp'
        elif self._values['internal'] is True:
            result = 'internal'
        elif self.has_fasthttp_profiles:
            result = 'performance-http'
        elif self.has_fastl4_profiles:
            result = 'performance-l4'
        elif self.has_message_routing_profiles:
            result = 'message-routing'
        else:
            result = 'standard'
        return result

    @property
    def profiles(self):
        """Returns a list of profiles from the API

        The profiles are formatted so that they are usable in this module and
        are able to be compared by the Difference engine.

        Returns:
             list (:obj:`list` of :obj:`dict`): List of profiles.

             Each dictionary in the list contains the following three (3) keys.

             * name
             * context
             * fullPath

        Raises:
            F5ModuleError: If the specified context is a value other that
                ``all``, ``server-side``, or ``client-side``.
        """
        if 'items' not in self._values['profiles']:
            return None
        result = []
        for item in self._values['profiles']['items']:
            context = item['context']
            if context == 'serverside':
                context = 'server-side'
            elif context == 'clientside':
                context = 'client-side'
            name = item['name']
            if context in ['all', 'server-side', 'client-side']:
                result.append(dict(name=name, context=context, full_path=item['fullPath']))
            else:
                raise F5ModuleError(
                    "Unknown profile context found: '{0}'".format(context)
                )
        return result

    @property
    def has_message_routing_profiles(self):
        if self.profiles is None:
            return None
        current = self._read_current_message_routing_profiles_from_device()
        result = [x['name'] for x in self.profiles if x['name'] in current]
        if len(result) > 0:
            return True
        return False

    @property
    def has_fastl4_profiles(self):
        if self.profiles is None:
            return None
        current = self._read_current_fastl4_profiles_from_device()
        result = [x['name'] for x in self.profiles if x['name'] in current]
        if len(result) > 0:
            return True
        return False

    @property
    def has_fasthttp_profiles(self):
        """Check if ``fasthttp`` profile is in API profiles

        This method is used to determine the server type when doing comparisons
        in the Difference class.

        Returns:
             bool: True if server has ``fasthttp`` profiles. False otherwise.
        """
        if self.profiles is None:
            return None
        current = self._read_current_fasthttp_profiles_from_device()
        result = [x['name'] for x in self.profiles if x['name'] in current]
        if len(result) > 0:
            return True
        return False

    def _read_current_message_routing_profiles_from_device(self):
        collection1 = self.client.api.tm.ltm.profile.diameters.get_collection()
        collection2 = self.client.api.tm.ltm.profile.sips.get_collection()
        result = [x.name for x in collection1]
        result += [x.name for x in collection2]
        return result

    def _read_current_fastl4_profiles_from_device(self):
        collection = self.client.api.tm.ltm.profile.fastl4s.get_collection()
        result = [x.name for x in collection]
        return result

    def _read_current_fasthttp_profiles_from_device(self):
        collection = self.client.api.tm.ltm.profile.fasthttps.get_collection()
        result = [x.name for x in collection]
        return result

    @property
    def security_log_profiles(self):
        if self._values['security_log_profiles'] is None:
            return None
        result = list(set([x.strip('"') for x in self._values['security_log_profiles']]))
        result.sort()
        return result

    @property
    def snat_type(self):
        if self._values['snat_type'] is None:
            return None
        if 'type' in self._values['snat_type']:
            if self._values['snat_type']['type'] == 'automap':
                return 'automap'
            elif self._values['snat_type']['type'] == 'none':
                return 'none'
            elif self._values['snat_type']['type'] == 'pool':
                return 'snat'

    @property
    def connection_mirror_enabled(self):
        if self._values['connection_mirror_enabled'] is None:
            return None
        elif self._values['connection_mirror_enabled'] == 'enabled':
            return 'yes'
        return 'no'

    @property
    def rate_limit(self):
        if self._values['rate_limit'] is None:
            return None
        elif self._values['rate_limit'] == 'disabled':
            return -1
        return int(self._values['rate_limit'])

    @property
    def nat64_enabled(self):
        if self._values['nat64_enabled'] is None:
            return None
        elif self._values['nat64_enabled'] == 'enabled':
            return 'yes'
        return 'no'

    @property
    def enabled(self):
        if self._values['enabled'] is None:
            return 'no'
        elif self._values['enabled'] is True:
            return 'yes'
        return 'no'

    @property
    def translate_port(self):
        if self._values['translate_port'] is None:
            return None
        elif self._values['translate_port'] == 'enabled':
            return 'yes'
        return 'no'

    @property
    def translate_address(self):
        if self._values['translate_address'] is None:
            return None
        elif self._values['translate_address'] == 'enabled':
            return 'yes'
        return 'no'

    @property
    def persistence_profile(self):
        """Return persistence profile in a consumable form

        I don't know why the persistence profile is stored this way, but below is the
        general format of it.

            "persist": [
                {
                    "name": "msrdp",
                    "partition": "Common",
                    "tmDefault": "yes",
                    "nameReference": {
                        "link": "https://localhost/mgmt/tm/ltm/persistence/msrdp/~Common~msrdp?ver=13.1.0.4"
                    }
                }
            ],

        As you can see, this is quite different from something like the fallback
        persistence profile which is just simply

            /Common/fallback1

        This method makes the persistence profile look like the fallback profile.

        Returns:
             string: The persistence profile configured on the virtual.
        """
        if self._values['persistence_profile'] is None:
            return None
        profile = self._values['persistence_profile'][0]
        result = fq_name(profile['partition'], profile['name'])
        return result

    @property
    def destination_tuple(self):
        Destination = namedtuple('Destination', ['ip', 'port', 'route_domain'])

        # Remove the partition
        if self._values['destination'] is None:
            result = Destination(ip=None, port=None, route_domain=None)
            return result
        destination = re.sub(r'^/[a-zA-Z0-9_.-]+/', '', self._values['destination'])

        if is_valid_ip(destination):
            result = Destination(
                ip=destination,
                port=None,
                route_domain=None
            )
            return result

        # Covers the following examples
        #
        # /Common/2700:bc00:1f10:101::6%2.80
        # 2700:bc00:1f10:101::6%2.80
        # 1.1.1.1%2:80
        # /Common/1.1.1.1%2:80
        # /Common/2700:bc00:1f10:101::6%2.any
        #
        pattern = r'(?P<ip>[^%]+)%(?P<route_domain>[0-9]+)[:.](?P<port>[0-9]+|any)'
        matches = re.search(pattern, destination)
        if matches:
            try:
                port = int(matches.group('port'))
            except ValueError:
                # Can be a port of "any". This only happens with IPv6
                port = matches.group('port')
                if port == 'any':
                    port = 0
            ip = matches.group('ip')
            if not is_valid_ip(ip):
                raise F5ModuleError(
                    "The provided destination is not a valid IP address"
                )
            result = Destination(
                ip=matches.group('ip'),
                port=port,
                route_domain=int(matches.group('route_domain'))
            )
            return result

        pattern = r'(?P<ip>[^%]+)%(?P<route_domain>[0-9]+)'
        matches = re.search(pattern, destination)
        if matches:
            ip = matches.group('ip')
            if not is_valid_ip(ip):
                raise F5ModuleError(
                    "The provided destination is not a valid IP address"
                )
            result = Destination(
                ip=matches.group('ip'),
                port=None,
                route_domain=int(matches.group('route_domain'))
            )
            return result

        parts = destination.split('.')
        if len(parts) == 4:
            # IPv4
            ip, port = destination.split(':')
            if not is_valid_ip(ip):
                raise F5ModuleError(
                    "The provided destination is not a valid IP address"
                )
            result = Destination(
                ip=ip,
                port=int(port),
                route_domain=None
            )
            return result
        elif len(parts) == 2:
            # IPv6
            ip, port = destination.split('.')
            try:
                port = int(port)
            except ValueError:
                # Can be a port of "any". This only happens with IPv6
                if port == 'any':
                    port = 0
            if not is_valid_ip(ip):
                raise F5ModuleError(
                    "The provided destination is not a valid IP address"
                )
            result = Destination(
                ip=ip,
                port=port,
                route_domain=None
            )
            return result
        else:
            result = Destination(ip=None, port=None, route_domain=None)
            return result


class VirtualServersFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(VirtualServersFactManager, self).__init__(**kwargs)
        self.want = VirtualServersParameters(client=self.client, params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(virtual_servers=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            attrs = resource
            attrs['stats'] = self.read_stats_from_device(attrs['fullPath'])
            params = VirtualServersParameters(params=attrs)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual?expandSubcollections=true".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result

    def read_stats_from_device(self, full_path):
        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual/{2}/stats".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=full_path)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        try:
            return result['stats']
        except KeyError:
            return {}


class VlansParameters(BaseParameters):
    api_map = {
        'autoLasthop': 'auto_lasthop',
        'cmpHash': 'cmp_hash_algorithm',
        'failsafeAction': 'failsafe_action',
        'failsafe': 'failsafe_enabled',
        'failsafeTimeout': 'failsafe_timeout',
        'ifIndex': 'if_index',
        'learning': 'learning_mode',
        'interfacesReference': 'interfaces',
        'sourceChecking': 'source_check_enabled',
        'fullPath': 'full_path'
    }

    returnables = [
        'full_path',
        'name',
        'auto_lasthop',
        'cmp_hash_algorithm',
        'description',
        'failsafe_action',
        'failsafe_enabled',
        'failsafe_timeout',
        'if_index',
        'learning_mode',
        'interfaces',
        'mtu',
        'sflow_poll_interval',
        'sflow_poll_interval_global',
        'sflow_sampling_rate',
        'sflow_sampling_rate_global',
        'source_check_enabled',
        'true_mac_address',
        'tag',
    ]

    @property
    def interfaces(self):
        if self._values['interfaces'] is None:
            return None
        if 'items' not in self._values['interfaces']:
            return None
        result = []
        for item in self._values['interfaces']['items']:
            tmp = dict(
                name=item['name'],
                full_path=item['fullPath']
            )
            if 'tagged' in item:
                tmp['tagged'] = 'yes'
            else:
                tmp['tagged'] = 'no'
            result.append(tmp)
        return result

    @property
    def sflow_poll_interval(self):
        return int(self._values['sflow']['pollInterval'])

    @property
    def sflow_poll_interval_global(self):
        return flatten_boolean(self._values['sflow']['pollIntervalGlobal'])

    @property
    def sflow_sampling_rate(self):
        return int(self._values['sflow']['samplingRate'])

    @property
    def sflow_sampling_rate_global(self):
        return flatten_boolean(self._values['sflow']['samplingRateGlobal'])

    @property
    def source_check_state(self):
        return flatten_boolean(self._values['source_check_state'])

    @property
    def true_mac_address(self):
        # Who made this field a "description"!?
        return self._values['stats']['macTrue']

    @property
    def tag(self):
        # We can't agree on field names...SMH
        return self._values['stats']['id']

    @property
    def failsafe_enabled(self):
        return flatten_boolean(self._values['failsafe_enabled'])


class VlansFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(VlansFactManager, self).__init__(**kwargs)
        self.want = VlansParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(vlans=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            attrs = resource
            attrs['stats'] = self.read_stats_from_device(attrs['fullPath'])
            params = VlansParameters(params=attrs)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/vlan?expandSubcollections=true".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result

    def read_stats_from_device(self, full_path):
        uri = "https://{0}:{1}/mgmt/tm/net/vlan/{2}/stats".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=full_path)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        try:
            return result['stats']
        except KeyError:
            return {}


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs
        self.want = Parameters(params=self.module.params)
        self.managers = {
            'asm-policy-stats': AsmPolicyStatsFactManager,
            'asm-policies': AsmPolicyFactManager,
            'asm-server-technologies': AsmServerTechnologyFactManager,
            'asm-signature-sets': AsmSignatureSetsFactManager,
            'client-ssl-profiles': ClientSslProfilesFactManager,
            'devices': DevicesFactManager,
            'device-groups': DeviceGroupsFactManager,
            'external-monitors': ExternalMonitorsFactManager,
            'fasthttp-profiles': FastHttpProfilesFactManager,
            'fastl4-profiles': FastL4ProfilesFactManager,
            'gateway-icmp-monitors': GatewayIcmpMonitorsFactManager,
            'gtm-a-pools': GtmAPoolsFactManager,
            'gtm-servers': GtmServersFactManager,
            'gtm-a-wide-ips': GtmAWideIpsFactManager,
            'gtm-aaaa-pools': GtmAaaaPoolsFactManager,
            'gtm-aaaa-wide-ips': GtmAaaaWideIpsFactManager,
            'gtm-cname-pools': GtmCnamePoolsFactManager,
            'gtm-cname-wide-ips': GtmCnameWideIpsFactManager,
            'gtm-mx-pools': GtmMxPoolsFactManager,
            'gtm-mx-wide-ips': GtmMxWideIpsFactManager,
            'gtm-naptr-pools': GtmNaptrPoolsFactManager,
            'gtm-naptr-wide-ips': GtmNaptrWideIpsFactManager,
            'gtm-srv-pools': GtmSrvPoolsFactManager,
            'gtm-srv-wide-ips': GtmSrvWideIpsFactManager,
            'http-monitors': HttpMonitorsFactManager,
            'https-monitors': HttpsMonitorsFactManager,
            'http-profiles': HttpProfilesFactManager,
            'iapp-services': IappServicesFactManager,
            'iapplx-packages': IapplxPackagesFactManager,
            'icmp-monitors': IcmpMonitorsFactManager,
            'interfaces': InterfacesFactManager,
            'internal-data-groups': InternalDataGroupsFactManager,
            'irules': IrulesFactManager,
            'ltm-pools': LtmPoolsFactManager,
            'nodes': NodesFactManager,
            'oneconnect-profiles': OneConnectProfilesFactManager,
            'partitions': PartitionFactManager,
            'provision-info': ProvisionInfoFactManager,
            'route-domains': RouteDomainFactManager,
            'self-ips': SelfIpsFactManager,
            'server-ssl-profiles': ServerSslProfilesFactManager,
            'software-volumes': SoftwareVolumesFactManager,
            'software-images': SoftwareImagesFactManager,
            'software-hotfixes': SoftwareHotfixesFactManager,
            'ssl-certs': SslCertificatesFactManager,
            'ssl-keys': SslKeysFactManager,
            'system-db': SystemDbFactManager,
            'system-info': SystemInfoFactManager,
            'tcp-monitors': TcpMonitorsFactManager,
            'tcp-half-open-monitors': TcpHalfOpenMonitorsFactManager,
            'tcp-profiles': TcpProfilesFactManager,
            'traffic-groups': TrafficGroupsFactManager,
            'trunks': TrunksFactManager,
            'udp-profiles': UdpProfilesFactManager,
            'vcmp-guests': VcmpGuestsFactManager,
            'virtual-addresses': VirtualAddressesFactManager,
            'virtual-servers': VirtualServersFactManager,
            'vlans': VlansFactManager,
        }

    def exec_module(self):
        self.handle_all_keyword()
        self.handle_profiles_keyword()
        self.handle_monitors_keyword()
        self.handle_gtm_pools_keyword()
        self.handle_gtm_wide_ips_keyword()
        res = self.check_valid_gather_subset(self.want.gather_subset)
        if res:
            invalid = ','.join(res)
            raise F5ModuleError(
                "The specified 'gather_subset' options are invalid: {0}".format(invalid)
            )
        result = self.filter_excluded_facts()

        managers = []
        for name in result:
            manager = self.get_manager(name)
            if manager:
                managers.append(manager)

        if not managers:
            result = dict(
                changed=False
            )
            return result

        result = self.execute_managers(managers)
        if result:
            result['changed'] = True
        else:
            result['changed'] = False
        return result

    def filter_excluded_facts(self):
        # Remove the excluded entries from the list of possible facts
        exclude = [x[1:] for x in self.want.gather_subset if x[0] == '!']
        include = [x for x in self.want.gather_subset if x[0] != '!']
        result = [x for x in include if x not in exclude]
        return result

    def handle_all_keyword(self):
        if 'all' not in self.want.gather_subset:
            return
        managers = list(self.managers.keys()) + self.want.gather_subset
        managers.remove('all')
        self.want.update({'gather_subset': managers})

    def handle_profiles_keyword(self):
        if 'profiles' not in self.want.gather_subset:
            return
        managers = [x for x in self.managers.keys() if '-profiles' in x] + self.want.gather_subset
        managers.remove('profiles')
        self.want.update({'gather_subset': managers})

    def handle_monitors_keyword(self):
        if 'monitors' not in self.want.gather_subset:
            return
        managers = [x for x in self.managers.keys() if '-monitors' in x] + self.want.gather_subset
        managers.remove('monitors')
        self.want.update({'gather_subset': managers})

    def handle_gtm_pools_keyword(self):
        if 'gtm-pools' not in self.want.gather_subset:
            return
        keys = self.managers.keys()
        managers = [x for x in keys if x.startswith('gtm-') and x.endswith('-pools')]
        managers += self.want.gather_subset
        managers.remove('gtm-pools')
        self.want.update({'gather_subset': managers})

    def handle_gtm_wide_ips_keyword(self):
        if 'gtm-wide-ips' not in self.want.gather_subset:
            return
        keys = self.managers.keys()
        managers = [x for x in keys if x.startswith('gtm-') and x.endswith('-wide-ips')]
        managers += self.want.gather_subset
        managers.remove('gtm-wide-ips')
        self.want.update({'gather_subset': managers})

    def check_valid_gather_subset(self, includes):
        """Check that the specified subset is valid

        The ``gather_subset`` parameter is specified as a "raw" field which means that
        any Python type could technically be provided

        :param includes:
        :return:
        """
        keys = self.managers.keys()
        result = []
        for x in includes:
            if x not in keys:
                if x[0] == '!':
                    if x[1:] not in keys:
                        result.append(x)
                else:
                    result.append(x)
        return result

    def execute_managers(self, managers):
        results = dict()
        client = F5RestClient(**self.module.params)
        prov = modules_provisioned(client)
        for manager in managers:
            manager.provisioned_modules = prov
            result = manager.exec_module()
            results.update(result)
        return results

    def get_manager(self, which):
        result = {}
        manager = self.managers.get(which, None)
        if not manager:
            return result
        kwargs = dict()
        kwargs.update(self.kwargs)

        kwargs['client'] = F5RestClient(**self.module.params)
        result = manager(**kwargs)
        return result


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False
        argument_spec = dict(
            gather_subset=dict(
                type='list',
                required=True,
                aliases=['include'],
                choices=[
                    # Meta choices
                    'all',
                    'monitors',
                    'profiles',
                    'gtm-pools',
                    'gtm-wide-ips',

                    # Non-meta choices
                    'asm-policies',
                    'asm-policy-stats',
                    'asm-server-technologies',
                    'asm-signature-sets',
                    'client-ssl-profiles',
                    'devices',
                    'device-groups',
                    'external-monitors',
                    'fasthttp-profiles',
                    'fastl4-profiles',
                    'gateway-icmp-monitors',
                    'gtm-a-pools',
                    'gtm-servers',
                    'gtm-a-wide-ips',
                    'gtm-aaaa-pools',
                    'gtm-aaaa-wide-ips',
                    'gtm-cname-pools',
                    'gtm-cname-wide-ips',
                    'gtm-mx-pools',
                    'gtm-mx-wide-ips',
                    'gtm-naptr-pools',
                    'gtm-naptr-wide-ips',
                    'gtm-srv-pools',
                    'gtm-srv-wide-ips',
                    'http-profiles',
                    'http-monitors',
                    'https-monitors',
                    'iapp-services',
                    'iapplx-packages',
                    'icmp-monitors',
                    'interfaces',
                    'internal-data-groups',
                    'irules',
                    'ltm-pools',
                    'nodes',
                    'oneconnect-profiles',
                    'partitions',
                    'provision-info',
                    'self-ips',
                    'server-ssl-profiles',
                    'software-volumes',
                    'software-images',
                    'software-hotfixes',
                    'ssl-certs',
                    'ssl-keys',
                    'system-db',
                    'system-info',
                    'tcp-monitors',
                    'tcp-half-open-monitors',
                    'tcp-profiles',
                    'traffic-groups',
                    'trunks',
                    'udp-profiles',
                    'vcmp-guests',
                    'virtual-addresses',
                    'virtual-servers',
                    'vlans',

                    # Negations of meta choices
                    '!all',
                    "!monitors",
                    '!profiles',
                    '!gtm-pools',
                    '!gtm-wide-ips',

                    # Negations of non-meta-choices
                    '!asm-policy-stats',
                    '!asm-policies',
                    '!asm-server-technologies',
                    '!asm-signature-sets',
                    '!client-ssl-profiles',
                    '!devices',
                    '!device-groups',
                    '!external-monitors',
                    '!fasthttp-profiles',
                    '!fastl4-profiles',
                    '!gateway-icmp-monitors',
                    '!gtm-a-pools',
                    '!gtm-servers',
                    '!gtm-a-wide-ips',
                    '!gtm-aaaa-pools',
                    '!gtm-aaaa-wide-ips',
                    '!gtm-cname-pools',
                    '!gtm-cname-wide-ips',
                    '!gtm-mx-pools',
                    '!gtm-mx-wide-ips',
                    '!gtm-naptr-pools',
                    '!gtm-naptr-wide-ips',
                    '!gtm-srv-pools',
                    '!gtm-srv-wide-ips',
                    '!http-profiles',
                    '!http-monitors',
                    '!https-monitors',
                    '!iapp-services',
                    '!iapplx-packages',
                    '!icmp-monitors',
                    '!interfaces',
                    '!internal-data-groups',
                    '!irules',
                    '!ltm-pools',
                    '!nodes',
                    '!oneconnect-profiles',
                    '!partitions',
                    '!provision-info',
                    '!self-ips',
                    '!server-ssl-profiles',
                    '!software-volumes',
                    '!software-images',
                    '!software-hotfixes',
                    '!ssl-certs',
                    '!ssl-keys',
                    '!system-db',
                    '!system-info',
                    '!tcp-monitors',
                    '!tcp-half-open-monitors',
                    '!tcp-profiles',
                    '!traffic-groups',
                    '!trunks',
                    '!udp-profiles',
                    '!vcmp-guests',
                    '!virtual-addresses',
                    '!virtual-servers',
                    '!vlans',
                ]
            ),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
