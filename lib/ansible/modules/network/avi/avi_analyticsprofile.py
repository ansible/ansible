#!/usr/bin/python
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 17.1.1
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_analyticsprofile
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

short_description: Module for setup of AnalyticsProfile Avi RESTful Object
description:
    - This module is used to configure AnalyticsProfile object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.3"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent", "present"]
    avi_api_update_method:
        description:
            - Default method for object update is HTTP PUT.
            - Setting to patch will override that behavior to use HTTP PATCH.
        version_added: "2.5"
        default: put
        choices: ["put", "patch"]
    avi_api_patch_op:
        description:
            - Patch operation to use when using avi_api_update_method as patch.
        version_added: "2.5"
        choices: ["add", "replace", "delete"]
    apdex_response_threshold:
        description:
            - If a client receives an http response in less than the satisfactory latency threshold, the request is considered satisfied.
            - It is considered tolerated if it is not satisfied and less than tolerated latency factor multiplied by the satisfactory latency threshold.
            - Greater than this number and the client's request is considered frustrated.
            - Allowed values are 1-30000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 500.
            - Units(MILLISECONDS).
    apdex_response_tolerated_factor:
        description:
            - Client tolerated response latency factor.
            - Client must receive a response within this factor times the satisfactory threshold (apdex_response_threshold) to be considered tolerated.
            - Allowed values are 1-1000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.0.
    apdex_rtt_threshold:
        description:
            - Satisfactory client to avi round trip time(rtt).
            - Allowed values are 1-2000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 250.
            - Units(MILLISECONDS).
    apdex_rtt_tolerated_factor:
        description:
            - Tolerated client to avi round trip time(rtt) factor.
            - It is a multiple of apdex_rtt_tolerated_factor.
            - Allowed values are 1-1000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.0.
    apdex_rum_threshold:
        description:
            - If a client is able to load a page in less than the satisfactory latency threshold, the pageload is considered satisfied.
            - It is considered tolerated if it is greater than satisfied but less than the tolerated latency multiplied by satisifed latency.
            - Greater than this number and the client's request is considered frustrated.
            - A pageload includes the time for dns lookup, download of all http objects, and page render time.
            - Allowed values are 1-30000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 5000.
            - Units(MILLISECONDS).
    apdex_rum_tolerated_factor:
        description:
            - Virtual service threshold factor for tolerated page load time (plt) as multiple of apdex_rum_threshold.
            - Allowed values are 1-1000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.0.
    apdex_server_response_threshold:
        description:
            - A server http response is considered satisfied if latency is less than the satisfactory latency threshold.
            - The response is considered tolerated when it is greater than satisfied but less than the tolerated latency factor * s_latency.
            - Greater than this number and the server response is considered frustrated.
            - Allowed values are 1-30000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 400.
            - Units(MILLISECONDS).
    apdex_server_response_tolerated_factor:
        description:
            - Server tolerated response latency factor.
            - Servermust response within this factor times the satisfactory threshold (apdex_server_response_threshold) to be considered tolerated.
            - Allowed values are 1-1000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.0.
    apdex_server_rtt_threshold:
        description:
            - Satisfactory client to avi round trip time(rtt).
            - Allowed values are 1-2000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 125.
            - Units(MILLISECONDS).
    apdex_server_rtt_tolerated_factor:
        description:
            - Tolerated client to avi round trip time(rtt) factor.
            - It is a multiple of apdex_rtt_tolerated_factor.
            - Allowed values are 1-1000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.0.
    client_log_config:
        description:
            - Configure which logs are sent to the avi controller from ses and how they are processed.
    client_log_streaming_config:
        description:
            - Configure to stream logs to an external server.
            - Field introduced in 17.1.1.
        version_added: "2.4"
    conn_lossy_ooo_threshold:
        description:
            - A connection between client and avi is considered lossy when more than this percentage of out of order packets are received.
            - Allowed values are 1-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 50.
            - Units(PERCENT).
    conn_lossy_timeo_rexmt_threshold:
        description:
            - A connection between client and avi is considered lossy when more than this percentage of packets are retransmitted due to timeout.
            - Allowed values are 1-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 20.
            - Units(PERCENT).
    conn_lossy_total_rexmt_threshold:
        description:
            - A connection between client and avi is considered lossy when more than this percentage of packets are retransmitted.
            - Allowed values are 1-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 50.
            - Units(PERCENT).
    conn_lossy_zero_win_size_event_threshold:
        description:
            - A client connection is considered lossy when percentage of times a packet could not be trasmitted due to tcp zero window is above this threshold.
            - Allowed values are 0-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 2.
            - Units(PERCENT).
    conn_server_lossy_ooo_threshold:
        description:
            - A connection between avi and server is considered lossy when more than this percentage of out of order packets are received.
            - Allowed values are 1-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 50.
            - Units(PERCENT).
    conn_server_lossy_timeo_rexmt_threshold:
        description:
            - A connection between avi and server is considered lossy when more than this percentage of packets are retransmitted due to timeout.
            - Allowed values are 1-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 20.
            - Units(PERCENT).
    conn_server_lossy_total_rexmt_threshold:
        description:
            - A connection between avi and server is considered lossy when more than this percentage of packets are retransmitted.
            - Allowed values are 1-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 50.
            - Units(PERCENT).
    conn_server_lossy_zero_win_size_event_threshold:
        description:
            - A server connection is considered lossy when percentage of times a packet could not be trasmitted due to tcp zero window is above this threshold.
            - Allowed values are 0-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 2.
            - Units(PERCENT).
    description:
        description:
            - User defined description for the object.
    disable_se_analytics:
        description:
            - Disable node (service engine) level analytics forvs metrics.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    disable_server_analytics:
        description:
            - Disable analytics on backend servers.
            - This may be desired in container environment when there are large number of  ephemeral servers.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    exclude_client_close_before_request_as_error:
        description:
            - Exclude client closed connection before an http request could be completed from being classified as an error.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    exclude_dns_policy_drop_as_significant:
        description:
            - Exclude dns policy drops from the list of errors.
            - Field introduced in 17.2.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.5"
        type: bool
    exclude_gs_down_as_error:
        description:
            - Exclude queries to gslb services that are operationally down from the list of errors.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    exclude_http_error_codes:
        description:
            - List of http status codes to be excluded from being classified as an error.
            - Error connections or responses impacts health score, are included as significant logs, and may be classified as part of a dos attack.
    exclude_invalid_dns_domain_as_error:
        description:
            - Exclude dns queries to domains outside the domains configured in the dns application profile from the list of errors.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    exclude_invalid_dns_query_as_error:
        description:
            - Exclude invalid dns queries from the list of errors.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    exclude_no_dns_record_as_error:
        description:
            - Exclude queries to domains that did not have configured services/records from the list of errors.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    exclude_no_valid_gs_member_as_error:
        description:
            - Exclude queries to gslb services that have no available members from the list of errors.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    exclude_persistence_change_as_error:
        description:
            - Exclude persistence server changed while load balancing' from the list of errors.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    exclude_server_dns_error_as_error:
        description:
            - Exclude server dns error response from the list of errors.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    exclude_server_tcp_reset_as_error:
        description:
            - Exclude server tcp reset from errors.
            - It is common for applications like ms exchange.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    exclude_syn_retransmit_as_error:
        description:
            - Exclude 'server unanswered syns' from the list of errors.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    exclude_tcp_reset_as_error:
        description:
            - Exclude tcp resets by client from the list of potential errors.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    exclude_unsupported_dns_query_as_error:
        description:
            - Exclude unsupported dns queries from the list of errors.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    hs_event_throttle_window:
        description:
            - Time window (in secs) within which only unique health change events should occur.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1209600.
    hs_max_anomaly_penalty:
        description:
            - Maximum penalty that may be deducted from health score for anomalies.
            - Allowed values are 0-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.
    hs_max_resources_penalty:
        description:
            - Maximum penalty that may be deducted from health score for high resource utilization.
            - Allowed values are 0-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 25.
    hs_max_security_penalty:
        description:
            - Maximum penalty that may be deducted from health score based on security assessment.
            - Allowed values are 0-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 100.
    hs_min_dos_rate:
        description:
            - Dos connection rate below which the dos security assessment will not kick in.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1000.
    hs_performance_boost:
        description:
            - Adds free performance score credits to health score.
            - It can be used for compensating health score for known slow applications.
            - Allowed values are 0-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
    hs_pscore_traffic_threshold_l4_client:
        description:
            - Threshold number of connections in 5min, below which apdexr, apdexc, rum_apdex, and other network quality metrics are not computed.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.0.
    hs_pscore_traffic_threshold_l4_server:
        description:
            - Threshold number of connections in 5min, below which apdexr, apdexc, rum_apdex, and other network quality metrics are not computed.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.0.
    hs_security_certscore_expired:
        description:
            - Score assigned when the certificate has expired.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.0.
    hs_security_certscore_gt30d:
        description:
            - Score assigned when the certificate expires in more than 30 days.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 5.0.
    hs_security_certscore_le07d:
        description:
            - Score assigned when the certificate expires in less than or equal to 7 days.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 2.0.
    hs_security_certscore_le30d:
        description:
            - Score assigned when the certificate expires in less than or equal to 30 days.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.0.
    hs_security_chain_invalidity_penalty:
        description:
            - Penalty for allowing certificates with invalid chain.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.0.
    hs_security_cipherscore_eq000b:
        description:
            - Score assigned when the minimum cipher strength is 0 bits.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.0.
    hs_security_cipherscore_ge128b:
        description:
            - Score assigned when the minimum cipher strength is greater than equal to 128 bits.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 5.0.
    hs_security_cipherscore_lt128b:
        description:
            - Score assigned when the minimum cipher strength is less than 128 bits.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 3.5.
    hs_security_encalgo_score_none:
        description:
            - Score assigned when no algorithm is used for encryption.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.0.
    hs_security_encalgo_score_rc4:
        description:
            - Score assigned when rc4 algorithm is used for encryption.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 2.5.
    hs_security_hsts_penalty:
        description:
            - Penalty for not enabling hsts.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.0.
    hs_security_nonpfs_penalty:
        description:
            - Penalty for allowing non-pfs handshakes.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.0.
    hs_security_selfsignedcert_penalty:
        description:
            - Deprecated.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.0.
    hs_security_ssl30_score:
        description:
            - Score assigned when supporting ssl3.0 encryption protocol.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 3.5.
    hs_security_tls10_score:
        description:
            - Score assigned when supporting tls1.0 encryption protocol.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 5.0.
    hs_security_tls11_score:
        description:
            - Score assigned when supporting tls1.1 encryption protocol.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 5.0.
    hs_security_tls12_score:
        description:
            - Score assigned when supporting tls1.2 encryption protocol.
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 5.0.
    hs_security_weak_signature_algo_penalty:
        description:
            - Penalty for allowing weak signature algorithm(s).
            - Allowed values are 0-5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.0.
    name:
        description:
            - The name of the analytics profile.
        required: true
    ranges:
        description:
            - List of http status code ranges to be excluded from being classified as an error.
    resp_code_block:
        description:
            - Block of http response codes to be excluded from being classified as an error.
            - Enum options - AP_HTTP_RSP_4XX, AP_HTTP_RSP_5XX.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Uuid of the analytics profile.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
  - name: Create a custom Analytics profile object
    avi_analyticsprofile:
      controller: '{{ controller }}'
      username: '{{ username }}'
      password: '{{ password }}'
      apdex_response_threshold: 500
      apdex_response_tolerated_factor: 4.0
      apdex_rtt_threshold: 250
      apdex_rtt_tolerated_factor: 4.0
      apdex_rum_threshold: 5000
      apdex_rum_tolerated_factor: 4.0
      apdex_server_response_threshold: 400
      apdex_server_response_tolerated_factor: 4.0
      apdex_server_rtt_threshold: 125
      apdex_server_rtt_tolerated_factor: 4.0
      conn_lossy_ooo_threshold: 50
      conn_lossy_timeo_rexmt_threshold: 20
      conn_lossy_total_rexmt_threshold: 50
      conn_lossy_zero_win_size_event_threshold: 2
      conn_server_lossy_ooo_threshold: 50
      conn_server_lossy_timeo_rexmt_threshold: 20
      conn_server_lossy_total_rexmt_threshold: 50
      conn_server_lossy_zero_win_size_event_threshold: 2
      disable_se_analytics: false
      disable_server_analytics: false
      exclude_client_close_before_request_as_error: false
      exclude_persistence_change_as_error: false
      exclude_server_tcp_reset_as_error: false
      exclude_syn_retransmit_as_error: false
      exclude_tcp_reset_as_error: false
      hs_event_throttle_window: 1209600
      hs_max_anomaly_penalty: 10
      hs_max_resources_penalty: 25
      hs_max_security_penalty: 100
      hs_min_dos_rate: 1000
      hs_performance_boost: 20
      hs_pscore_traffic_threshold_l4_client: 10.0
      hs_pscore_traffic_threshold_l4_server: 10.0
      hs_security_certscore_expired: 0.0
      hs_security_certscore_gt30d: 5.0
      hs_security_certscore_le07d: 2.0
      hs_security_certscore_le30d: 4.0
      hs_security_chain_invalidity_penalty: 1.0
      hs_security_cipherscore_eq000b: 0.0
      hs_security_cipherscore_ge128b: 5.0
      hs_security_cipherscore_lt128b: 3.5
      hs_security_encalgo_score_none: 0.0
      hs_security_encalgo_score_rc4: 2.5
      hs_security_hsts_penalty: 0.0
      hs_security_nonpfs_penalty: 1.0
      hs_security_selfsignedcert_penalty: 1.0
      hs_security_ssl30_score: 3.5
      hs_security_tls10_score: 5.0
      hs_security_tls11_score: 5.0
      hs_security_tls12_score: 5.0
      hs_security_weak_signature_algo_penalty: 1.0
      name: jason-analytics-profile
      tenant_ref: Demo
"""

RETURN = '''
obj:
    description: AnalyticsProfile (api/analyticsprofile) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        avi_api_update_method=dict(default='put',
                                   choices=['put', 'patch']),
        avi_api_patch_op=dict(choices=['add', 'replace', 'delete']),
        apdex_response_threshold=dict(type='int',),
        apdex_response_tolerated_factor=dict(type='float',),
        apdex_rtt_threshold=dict(type='int',),
        apdex_rtt_tolerated_factor=dict(type='float',),
        apdex_rum_threshold=dict(type='int',),
        apdex_rum_tolerated_factor=dict(type='float',),
        apdex_server_response_threshold=dict(type='int',),
        apdex_server_response_tolerated_factor=dict(type='float',),
        apdex_server_rtt_threshold=dict(type='int',),
        apdex_server_rtt_tolerated_factor=dict(type='float',),
        client_log_config=dict(type='dict',),
        client_log_streaming_config=dict(type='dict',),
        conn_lossy_ooo_threshold=dict(type='int',),
        conn_lossy_timeo_rexmt_threshold=dict(type='int',),
        conn_lossy_total_rexmt_threshold=dict(type='int',),
        conn_lossy_zero_win_size_event_threshold=dict(type='int',),
        conn_server_lossy_ooo_threshold=dict(type='int',),
        conn_server_lossy_timeo_rexmt_threshold=dict(type='int',),
        conn_server_lossy_total_rexmt_threshold=dict(type='int',),
        conn_server_lossy_zero_win_size_event_threshold=dict(type='int',),
        description=dict(type='str',),
        disable_se_analytics=dict(type='bool',),
        disable_server_analytics=dict(type='bool',),
        exclude_client_close_before_request_as_error=dict(type='bool',),
        exclude_dns_policy_drop_as_significant=dict(type='bool',),
        exclude_gs_down_as_error=dict(type='bool',),
        exclude_http_error_codes=dict(type='list',),
        exclude_invalid_dns_domain_as_error=dict(type='bool',),
        exclude_invalid_dns_query_as_error=dict(type='bool',),
        exclude_no_dns_record_as_error=dict(type='bool',),
        exclude_no_valid_gs_member_as_error=dict(type='bool',),
        exclude_persistence_change_as_error=dict(type='bool',),
        exclude_server_dns_error_as_error=dict(type='bool',),
        exclude_server_tcp_reset_as_error=dict(type='bool',),
        exclude_syn_retransmit_as_error=dict(type='bool',),
        exclude_tcp_reset_as_error=dict(type='bool',),
        exclude_unsupported_dns_query_as_error=dict(type='bool',),
        hs_event_throttle_window=dict(type='int',),
        hs_max_anomaly_penalty=dict(type='int',),
        hs_max_resources_penalty=dict(type='int',),
        hs_max_security_penalty=dict(type='int',),
        hs_min_dos_rate=dict(type='int',),
        hs_performance_boost=dict(type='int',),
        hs_pscore_traffic_threshold_l4_client=dict(type='float',),
        hs_pscore_traffic_threshold_l4_server=dict(type='float',),
        hs_security_certscore_expired=dict(type='float',),
        hs_security_certscore_gt30d=dict(type='float',),
        hs_security_certscore_le07d=dict(type='float',),
        hs_security_certscore_le30d=dict(type='float',),
        hs_security_chain_invalidity_penalty=dict(type='float',),
        hs_security_cipherscore_eq000b=dict(type='float',),
        hs_security_cipherscore_ge128b=dict(type='float',),
        hs_security_cipherscore_lt128b=dict(type='float',),
        hs_security_encalgo_score_none=dict(type='float',),
        hs_security_encalgo_score_rc4=dict(type='float',),
        hs_security_hsts_penalty=dict(type='float',),
        hs_security_nonpfs_penalty=dict(type='float',),
        hs_security_selfsignedcert_penalty=dict(type='float',),
        hs_security_ssl30_score=dict(type='float',),
        hs_security_tls10_score=dict(type='float',),
        hs_security_tls11_score=dict(type='float',),
        hs_security_tls12_score=dict(type='float',),
        hs_security_weak_signature_algo_penalty=dict(type='float',),
        name=dict(type='str', required=True),
        ranges=dict(type='list',),
        resp_code_block=dict(type='list',),
        tenant_ref=dict(type='str',),
        url=dict(type='str',),
        uuid=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'analyticsprofile',
                           set([]))


if __name__ == '__main__':
    main()
