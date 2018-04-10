#!/usr/bin/python
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_alertconfig
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of AlertConfig Avi RESTful Object
description:
    - This module is used to configure AlertConfig object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
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
    action_group_ref:
        description:
            - The alert config will trigger the selected alert action, which can send notifications and execute a controlscript.
            - It is a reference to an object of type actiongroupconfig.
    alert_rule:
        description:
            - List of filters matching on events or client logs used for triggering alerts.
        required: true
    autoscale_alert:
        description:
            - This alert config applies to auto scale alerts.
        type: bool
    category:
        description:
            - Determines whether an alert is raised immediately when event occurs (realtime) or after specified number of events occurs within rolling time
            - window.
            - Enum options - REALTIME, ROLLINGWINDOW, WATERMARK.
            - Default value when not specified in API or module is interpreted by Avi Controller as REALTIME.
        required: true
    description:
        description:
            - A custom description field.
    enabled:
        description:
            - Enable or disable this alert config from generating new alerts.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        type: bool
    expiry_time:
        description:
            - An alert is expired and deleted after the expiry time has elapsed.
            - The original event triggering the alert remains in the event's log.
            - Allowed values are 1-31536000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 86400.
            - Units(SEC).
    name:
        description:
            - Name of the alert configuration.
        required: true
    obj_uuid:
        description:
            - Uuid of the resource for which alert was raised.
    object_type:
        description:
            - The object type to which the alert config is associated with.
            - Valid object types are - virtual service, pool, service engine.
            - Enum options - VIRTUALSERVICE, POOL, HEALTHMONITOR, NETWORKPROFILE, APPLICATIONPROFILE, HTTPPOLICYSET, DNSPOLICY, IPADDRGROUP, STRINGGROUP,
            - SSLPROFILE, SSLKEYANDCERTIFICATE, NETWORKSECURITYPOLICY, APPLICATIONPERSISTENCEPROFILE, ANALYTICSPROFILE, VSDATASCRIPTSET, TENANT, PKIPROFILE,
            - AUTHPROFILE, CLOUD, SERVERAUTOSCALEPOLICY, AUTOSCALELAUNCHCONFIG, MICROSERVICEGROUP, IPAMPROFILE, HARDWARESECURITYMODULEGROUP, POOLGROUP,
            - PRIORITYLABELS, POOLGROUPDEPLOYMENTPOLICY, GSLBSERVICE, GSLBSERVICERUNTIME, SCHEDULER, GSLBGEODBPROFILE, GSLBAPPLICATIONPERSISTENCEPROFILE,
            - TRAFFICCLONEPROFILE, VSVIP, WAFPOLICY, WAFPROFILE, ERRORPAGEPROFILE, ERRORPAGEBODY, L4POLICYSET, SERVICEENGINE, DEBUGSERVICEENGINE,
            - DEBUGCONTROLLER, DEBUGVIRTUALSERVICE, SERVICEENGINEGROUP, SEPROPERTIES, NETWORK, CONTROLLERNODE, CONTROLLERPROPERTIES, SYSTEMCONFIGURATION,
            - VRFCONTEXT, USER, ALERTCONFIG, ALERTSYSLOGCONFIG, ALERTEMAILCONFIG, ALERTTYPECONFIG, APPLICATION, ROLE, CLOUDPROPERTIES, SNMPTRAPPROFILE,
            - ACTIONGROUPPROFILE, MICROSERVICE, ALERTPARAMS, ACTIONGROUPCONFIG, CLOUDCONNECTORUSER, GSLB, GSLBDNSUPDATE, GSLBSITEOPS, GLBMGRWARMSTART,
            - IPAMDNSRECORD, GSLBDNSGSSTATUS, GSLBDNSGEOFILEOPS, GSLBDNSGEOUPDATE, GSLBDNSGEOCLUSTEROPS, GSLBDNSCLEANUP, GSLBSITEOPSRESYNC, TCPSTATRUNTIME,
            - UDPSTATRUNTIME, IPSTATRUNTIME, ARPSTATRUNTIME, MBSTATRUNTIME, IPSTKQSTATSRUNTIME, MALLOCSTATRUNTIME, SHMALLOCSTATRUNTIME, CPUUSAGERUNTIME,
            - L7GLOBALSTATSRUNTIME, L7VIRTUALSERVICESTATSRUNTIME, SEAGENTVNICDBRUNTIME, SEAGENTGRAPHDBRUNTIME, SEAGENTSTATERUNTIME, INTERFACERUNTIME,
            - ARPTABLERUNTIME, DISPATCHERSTATRUNTIME, DISPATCHERSTATCLEARRUNTIME, DISPATCHERTABLEDUMPRUNTIME, DISPATCHERREMOTETIMERLISTDUMPRUNTIME,
            - METRICSAGENTMESSAGE, HEALTHMONITORSTATRUNTIME, METRICSENTITYRUNTIME, PERSISTENCEINTERNAL, HTTPPOLICYSETINTERNAL, DNSPOLICYINTERNAL,
            - CONNECTIONDUMPRUNTIME, SHAREDDBSTATS, SHAREDDBSTATSCLEAR, ICMPSTATRUNTIME, ROUTETABLERUNTIME, VIRTUALMACHINE, POOLSERVER, SEVSLIST,
            - MEMINFORUNTIME, RTERINGSTATRUNTIME, ALGOSTATRUNTIME, HEALTHMONITORRUNTIME, CPUSTATRUNTIME, SEVM, HOST, PORTGROUP, CLUSTER, DATACENTER, VCENTER,
            - HTTPPOLICYSETSTATS, DNSPOLICYSTATS, METRICSSESTATS, RATELIMITERSTATRUNTIME, NETWORKSECURITYPOLICYSTATS, TCPCONNRUNTIME, POOLSTATS,
            - CONNPOOLINTERNAL, CONNPOOLSTATS, VSHASHSHOWRUNTIME, SELOGSTATSRUNTIME, NETWORKSECURITYPOLICYDETAIL, LICENSERUNTIME, SERVERRUNTIME,
            - METRICSRUNTIMESUMMARY, METRICSRUNTIMEDETAIL, DISPATCHERSEHMPROBETEMPDISABLERUNTIME, POOLDEBUG, VSLOGMGRMAP, SERUMINSERTIONSTATS, HTTPCACHE,
            - HTTPCACHESTATS, SEDOSSTATRUNTIME, VSDOSSTATRUNTIME, SERVERUPDATEREQ, VSSCALEOUTLIST, SEMEMDISTRUNTIME, TCPCONNRUNTIMEDETAIL, SEUPGRADESTATUS,
            - SEUPGRADEPREVIEW, SEFAULTINJECTEXHAUSTM, SEFAULTINJECTEXHAUSTMCL, SEFAULTINJECTEXHAUSTMCLSMALL, SEFAULTINJECTEXHAUSTCONN, SEHEADLESSONLINEREQ,
            - SEUPGRADE, SEUPGRADESTATUSDETAIL, SERESERVEDVS, SERESERVEDVSCLEAR, VSCANDIDATESEHOSTLIST, SEGROUPUPGRADE, REBALANCE, SEGROUPREBALANCE,
            - SEAUTHSTATSRUNTIME, AUTOSCALESTATE, VIRTUALSERVICEAUTHSTATS, NETWORKSECURITYPOLICYDOS, KEYVALINTERNAL, KEYVALSUMMARYINTERNAL,
            - SERVERSTATEUPDATEINFO, CLTRACKINTERNAL, CLTRACKSUMMARYINTERNAL, MICROSERVICERUNTIME, SEMICROSERVICE, VIRTUALSERVICEANALYSIS, CLIENTINTERNAL,
            - CLIENTSUMMARYINTERNAL, MICROSERVICEGROUPRUNTIME, BGPRUNTIME, REQUESTQUEUERUNTIME, MIGRATEALL, MIGRATEALLSTATUSSUMMARY, MIGRATEALLSTATUSDETAIL,
            - INTERFACESUMMARYRUNTIME, INTERFACELACPRUNTIME, DNSTABLE, GSLBSERVICEDETAIL, GSLBSERVICEINTERNAL, GSLBSERVICEHMONSTAT, SETROLESREQUEST,
            - TRAFFICCLONERUNTIME, GEOLOCATIONINFO, SEVSHBSTATRUNTIME, GEODBINTERNAL, GSLBSITEINTERNAL, WAFSTATS, USERDEFINEDDATASCRIPTCOUNTERS, LLDPRUNTIME,
            - VSESSHARINGPOOL, SEVSSPLACEMENT, L4POLICYSETSTATS, L4POLICYSETINTERNAL, SERESOURCEPROTO, SECONSUMERPROTO, SECREATEPENDINGPROTO, PLACEMENTSTATS,
            - SEVIPPROTO, RMVRFPROTO, VCENTERMAP, VIMGRVCENTERRUNTIME, INTERESTEDVMS, INTERESTEDHOSTS, VCENTERSUPPORTEDCOUNTERS, ENTITYCOUNTERS,
            - TRANSACTIONSTATS, SEVMCREATEPROGRESS, PLACEMENTSTATUS, VISUBFOLDERS, VIDATASTORE, VIHOSTRESOURCES, CLOUDCONNECTOR, VINETWORKSUBNETVMS,
            - VIDATASTORECONTENTS, VIMGRVCENTERCLOUDRUNTIME, VIVCENTERPORTGROUPS, VIVCENTERDATACENTERS, VIMGRHOSTRUNTIME, PLACEMENTGLOBALS, APICCONFIGURATION,
            - CIFTABLE, APICTRANSACTION, VIRTUALSERVICESTATEDBCACHESUMMARY, POOLSTATEDBCACHESUMMARY, SERVERSTATEDBCACHESUMMARY, APICAGENTINTERNAL,
            - APICTRANSACTIONFLAP, APICGRAPHINSTANCES, APICEPGS, APICEPGEPS, APICDEVICEPKGVER, APICTENANTS, APICVMMDOMAINS, NSXCONFIGURATION, NSXSGTABLE,
            - NSXAGENTINTERNAL, NSXSGINFO, NSXSGIPS, NSXAGENTINTERNALCLI, MAXOBJECTS.
    recommendation:
        description:
            - Recommendation of alertconfig.
    rolling_window:
        description:
            - Only if the number of events is reached or exceeded within the time window will an alert be generated.
            - Allowed values are 1-31536000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 300.
            - Units(SEC).
    source:
        description:
            - Signifies system events or the type of client logsused in this alert configuration.
            - Enum options - CONN_LOGS, APP_LOGS, EVENT_LOGS, METRICS.
        required: true
    summary:
        description:
            - Summary of reason why alert is generated.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    threshold:
        description:
            - An alert is created only when the number of events meets or exceeds this number within the chosen time frame.
            - Allowed values are 1-65536.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
    throttle:
        description:
            - Alerts are suppressed (throttled) for this duration of time since the last alert was raised for this alert config.
            - Allowed values are 0-31536000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 600.
            - Units(SEC).
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Unique object identifier of the object.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create AlertConfig object
  avi_alertconfig:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_alertconfig
"""

RETURN = '''
obj:
    description: AlertConfig (api/alertconfig) object
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
        action_group_ref=dict(type='str',),
        alert_rule=dict(type='dict', required=True),
        autoscale_alert=dict(type='bool',),
        category=dict(type='str', required=True),
        description=dict(type='str',),
        enabled=dict(type='bool',),
        expiry_time=dict(type='int',),
        name=dict(type='str', required=True),
        obj_uuid=dict(type='str',),
        object_type=dict(type='str',),
        recommendation=dict(type='str',),
        rolling_window=dict(type='int',),
        source=dict(type='str', required=True),
        summary=dict(type='str',),
        tenant_ref=dict(type='str',),
        threshold=dict(type='int',),
        throttle=dict(type='int',),
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
    return avi_ansible_api(module, 'alertconfig',
                           set([]))

if __name__ == '__main__':
    main()
