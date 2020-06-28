# -*- coding:utf-8 -*-

setsmtp = {
    'interface': 'interface',
    'email': 'email',
    'primary_status': 'primaryStatus',
    'primary_ip': 'primaryServerIP',
    'primary_name': 'primaryServerName',
    'primary_port': 'primaryServerPort',
    'primary_auth': 'primaryServerAuthentication',
    'primary_username': 'primaryServerUsername',
    'primary_password': 'primaryServerPassword',
    'secondary_status': 'secondaryStatus',
    'secondary_ip': 'secondaryServerIP',
    'secondary_name': 'secondaryServerName',
    'secondary_port': 'secondaryServerPort',
    'secondary_auth': 'secondaryServerAuthentication',
    'secondary_username': 'secondaryServerUsername',
    'secondary_password': 'secondaryServerPassword',
}

setdns = {
    'dns_status': 'dns',
    'host_cfg': 'hostManual',
    'host_name': 'hostName',
    'domain_manual': 'domainManual',
    'domain_iface': 'domainIface',
    'domain_name': 'domainName',
    'dns_manual': 'dnsManual',
    'dns_iface': 'dnsIface',
    'dns_priority': 'dnsIP',
    'dns_server1': 'dnsServer1',
    'dns_server2': 'dnsServer2',
    'dns_server3': 'dnsServer3',
}

exportbioscfg = {
    'file_url': 'fileurl'
}

importbioscfg = {
    'file_url': 'fileurl'
}

collectblackbox = {
    'file_url': 'fileurl'
}

setbios = {
    'file_url': 'fileurl'
}

addldisk = {
    'info': 'Info',
    'ctrl_id': 'ctrlId',
    'level': 'rlevel',
}

adduser = {
    'role_id': 'roleid'
}

getauditlog = {
    'log_time': 'logtime',
    'audit_file': 'auditfile'
}

fancontrol = {
    'fan_speed': 'fanspeedlevel'
}

setldisk = {
    'info': 'Info',
    'ctrl_id': 'ctrlId',
    'ldisk_id': 'ldiskId'
}

setbmclogsettings = {
    'file_size': 'fileSize',
    'audit_status': 'auditLogStatus',
    'audit_type': 'auditType',
    'rotate_count': 'rotateCount',
    'server_addr': 'serverAddr',
    'server_port': 'serverPort',
    'protocol_type': 'protocolType'
}

settime = {
    'auto_date': 'autoDate',
    'ntp_time': 'ntpTime',
    'time_zone': 'timeZone',
    'server1': 'NTPServer1',
    'server2': 'NTPServer2',
    'server3': 'NTPServer3',
    'syn_cycle': 'NTPSynCycle',
}

setpriv = {
    'role_id': 'roleid'
}

setservice = {
    'service_name': 'servicename',
    'non_secure_port': 'nonsecureport',
    'secure_port': 'secureport',
}

setsnmp = {
    'snmp_status': 'snmpStatus',
    'auth_protocol': 'authProtocol',
    'auth_password': 'authPassword',
    'priv_protocol': 'privProtocol',
    'priv_password': 'privPassword',
}

setsnmptrap = {
    'event_severity': 'eventSeverity',
    'engine_id': 'engineId',
    'auth_protocol': 'authProtocol',
    'auth_password': 'authPassword',
    'priv_protocol': 'privProtocol',
    'priv_password': 'privPassword',
    'system_name': 'systemName',
    'system_id': 'systemID',
    'trap_port': 'SNMPtrapPort',
}

geteventlog = {
    'log_time': 'logtime',
    'event_file': 'eventfile'
}

getsystemlog = {
    'log_time': 'logtime',
    'system_file': 'systemfile'
}

fwupdate = {
    'over_ride': 'override',
    'has_me': 'hasme',
    'dual_image': 'dualimage'
}


def getParam(dictobj):
    param = {
        'setsmtp': setsmtp,
        'setdns': setdns,
        'exportbioscfg': exportbioscfg,
        'addldisk': addldisk,
        'adduser': adduser,
        'getauditlog': getauditlog,
        'importbioscfg': importbioscfg,
        'collectblackbox': collectblackbox,
        'setbios': setbios,
        'fancontrol': fancontrol,
        'setldisk': setldisk,
        'setbmclogsettings': setbmclogsettings,
        'settime': settime,
        'setpriv': setpriv,
        'setservice': setservice,
        'setsnmp': setsnmp,
        'setsnmptrap': setsnmptrap,
        'geteventlog': geteventlog,
        'getsystemlog': getsystemlog,
        'fwupdate': fwupdate
    }
    if 'subcommand' in dictobj:
        subcommand = dictobj['subcommand']
        obj = {}
        if subcommand in param:
            paramDict = param[subcommand]
            for k, v in dictobj.items():
                if k in paramDict:
                    k = paramDict[k]
                obj[k] = v
        else:
            obj = dictobj
        return obj
    else:
        return dictobj
