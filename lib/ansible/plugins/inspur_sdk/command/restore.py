# -*- coding:utf-8 -*-
import json
import os
from os import path
import time
import platform
from ansible.plugins.inspur_sdk.util import RegularCheckUtil
from ansible.plugins.inspur_sdk.command import RestFunc
from ansible.plugins.inspur_sdk.interface.ResEntity import ResultBean


def getUser(client):
    responds = RestFunc.getUserByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        return result
    else:
        return None


def getGroup(client):
    groupList = []
    default = ['Administrator', 'Operator', 'User']
    responds = RestFunc.getUserGroupByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        for item in result:
            if 'GroupName' in item:
                groupList.append(item['GroupName'])
            else:
                return default
        return groupList
    else:
        return default


def checkUser(client, args, flag):
    responds = RestFunc.getUserByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']

        for item in result:
            if 'name' in item:
                name = str(item['name'])
                if flag == 'importUser':
                    if name == args.username:
                        if 'network_privilege' not in item or 'access' not in item:
                            return 'Info'
                        if item['network_privilege'] != 'administrator' or item['access'] != 1:
                            return 'No'
                        else:
                            return 'Yes'
                elif flag == 'importUserGroup':
                    if name == args.username:
                        if 'network_privilege' not in item or 'access' not in item:
                            return 'Info'
                        if item['network_privilege'] != 'administrator' or item['access'] != 1:
                            return 'No'
                        else:
                            return 'Yes'
                elif flag == 'Import':
                    if name == args['U']:
                        if 'network_privilege' not in item or 'access' not in item:
                            return 'Info'
                        if item['network_privilege'] != 'administrator' or item['access'] != 1:
                            return 'No'
                        else:
                            return 'Yes'
                else:
                    return 'No'
            else:
                return 'No'
        return 'No'

    else:
        return 'No'


def restore_user(client, args, path_user):
    flag = checkUser(client, args, 'importUser')
    if flag == 'Info':
        return 0, 'Cannot get privilege of user ' + args.username

    elif flag == 'No':
        return 0, 'User ' + args.username + ' no permission'

    CurUser = getUser(client)
    CurUserName = []
    if CurUser is None:
        return 0, 'Cannot get users information'
    else:
        for item in CurUser:
            if 'name' not in item:
                return 0, 'Cannot get users information'
            else:
                if item['name'] == '':
                    continue
                CurUserName.append(item['name'])

    f = open(path_user, 'r')
    user = f.read()
    f.close()
    dict = json.loads(user)
    FileUserName = []
    for item in dict:
        if 'name' not in item:
            return 0, 'Cannot get json user information'
        else:
            if item['name'] == '':
                continue
            FileUserName.append(item['name'])
    # print FileUserName
    addUserName = []
    setUserName = []
    delUserName = []
    for name in FileUserName:
        if name not in CurUserName:
            addUserName.append(name)
        else:
            setUserName.append(name)
    for name in CurUserName:
        if name not in FileUserName:
            delUserName.append(name)

    # get settings
    f = open(path_user, 'r')
    user = f.read()
    f.close()
    dict = json.loads(user)

    f = open(args.passpath, 'r')
    password = f.read()
    f.close()
    pwd = json.loads(password)

    for item in dict:
        if 'name' not in item:
            return 0, 'Cannot get users name'
        elif item['name'] == args.username:
            continue
        else:
            if item['name'] in delUserName or item['name'] in setUserName:
                nameFlag = False
                for User in pwd['USERS']:
                    if item['name'] == User['username']:
                        nameFlag = True
                        if User['password'] == '':
                            return 0, 'user ' + item['name'] + ' no password'

                if not nameFlag:
                    return 0, 'user ' + item['name'] + ' no password'

    # delUser
    status, info = deluser(client, args, delUserName)
    if status != 1:
        return status, info

    # setUser
    status, info = deluser(client, args, setUserName)
    if status != 1:
        return status, info

    status, info = adduser(client, args, setUserName, path_user)
    if status != 1:
        return status, info

    # addUser
    status, info = adduser(client, args, addUserName, path_user)
    if status != 1:
        return status, info
    return 1, 'ok'


def restore_group(client, args, path_userg):
    flag = checkUser(client, args, 'importUserGroup')
    if flag == 'Info':
        return 0, 'Cannot get privilege of user ' + args.username

    elif flag == 'No':
        return 0, 'User ' + args.username + ' no permission'

    CurGroupName = getGroup(client)
    # print CurUserName

    f = open(path_userg, 'r')
    user = f.read()
    f.close()
    dict = json.loads(user)
    FileGroupName = []
    for item in dict:
        if 'GroupName' not in item:
            return 0, 'Cannot get json group information'
        else:
            if item['GroupName'] == '':
                continue
            FileGroupName.append(item['GroupName'])
    # print FileUserName
    addGroupName = []
    setGroupName = []
    delGroupName = []
    defaultName = ['Administrator', 'Operator', 'User']
    for name in FileGroupName:
        if name not in CurGroupName:
            addGroupName.append(name)
        else:
            if name not in defaultName:
                setGroupName.append(name)
    for name in CurGroupName:
        if name not in FileGroupName and name not in defaultName:
            delGroupName.append(name)

    # delUser
    status, info = delusergroup(client, args, delGroupName)
    if status != 1:
        return status, info

    # setUser
    status, info = setusergroup(client, args, setGroupName, path_userg)
    if status != 1:
        return status, info

    # addUser
    status, info = addusergroup(client, args, addGroupName, path_userg)
    if status != 1:
        return status, info

    return 1, "ok"


def getLDAPgroup(client):
    responds = RestFunc.getLDAPgroupM6(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        return result
    else:
        return None


def getADgroup(client):
    responds = RestFunc.getADGroupByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        return result
    else:
        return None


def restore_LDAP(client, args, path):
    Group = getLDAPgroup(client)
    if Group is None:
        return 2, 'Cannot get LDAP group'
    else:
        CurGroupName = []
        for item in Group:
            CurGroupName.append(item['role_group_name'])

    f = open(path, 'r')
    group = f.read()
    f.close()
    dict = json.loads(group)
    FileGroupName = []
    for item in dict:
        if 'role_group_name' not in item:
            return 0, 'Cannot get json LDAP group information'
        else:
            if item['role_group_name'] == '':
                continue
            FileGroupName.append(item['role_group_name'])

    # delUser
    status, info = delldapgroup(client, args, CurGroupName)
    if status != 1:
        return status, info

    # addUser
    status, info = addldapgroup(client, args, path)
    if status != 1:
        return status, info

    return 1, "ok"


def restore_AD(client, args, path):
    Group = getADgroup(client)
    if Group is None:
        return 2, 'Cannot get AD group'
    else:
        CurGroupName = []
        for item in Group:
            CurGroupName.append(item['role_group_name'])

    f = open(path, 'r')
    group = f.read()
    f.close()
    dict = json.loads(group)
    FileGroupName = []
    for item in dict:
        if 'role_group_name' not in item:
            return 0, 'Cannot get json AD group information'
        else:
            if item['role_group_name'] == '':
                continue
            FileGroupName.append(item['role_group_name'])

    # delUser
    status, info = deladgroup(client, args, CurGroupName)
    if status != 1:
        return status, info

    # addUser
    status, info = addadgroup(client, args, path)
    if status != 1:
        return status, info

    return 1, "ok"


def restore(client, args):
    result = ResultBean
    if platform.system() == 'Linux':
        file_separator = "/"
    else:
        file_separator = "\\"
    # Windows下 -F "D:\100.2.38.46\" 最后的'\"'会被解析为'"'
    # 判断并删除
    if args.bak_file[-1] == '"':
        args.bak_file = args.bak_file[:-1] + "\\"
    if not os.path.exists(args.bak_file):
        result.State('Failure')
        result.Message(['backup file or folder(-F) is not exists'])
        return result
    if os.path.isdir(args.bak_file):
        args.passpath = os.path.join(args.bak_file, 'password.txt')
    else:
        args.passpath = os.path.join(os.path.dirname(args.bak_file), 'password.txt')
    networkFlag = False
    dnsFlag = False
    serviceFlag = False
    ntpFlag = False
    smtpFlag = False
    snmptrapFlag = False
    adFlag = False
    ldapFlag = False
    userFlag = False
    biosFlag = False
    if args.item is None or args.item == 'all':
        if not os.path.isdir(args.bak_file):
            print ('Failure: -F should be a folder')
            result.State('Failure')
            result.Message(['-F should be a folder'])
            return result
        networkFlag = True
        dnsFlag = True
        serviceFlag = True
        ntpFlag = True
        smtpFlag = True
        snmptrapFlag = True
        adFlag = True
        ldapFlag = True
        userFlag = True
        biosFlag = True
    elif args.item == 'dns':
        dnsFlag = True
    elif args.item == 'network':
        networkFlag = True
    elif args.item == 'service':
        serviceFlag = True
    elif args.item == 'ntp':
        ntpFlag = True
    elif args.item == 'smtp':
        smtpFlag = True
    elif args.item == 'snmptrap':
        snmptrapFlag = True
    elif args.item == 'ad':
        adFlag = True
    elif args.item == 'ldap':
        ldapFlag = True
    elif args.item == 'user':
        userFlag = True
    # elif args.item == 'bios':
    else:
        biosFlag = True
    infoList = []
    if ntpFlag == True:
        # NTP no
        if os.path.isfile(args.bak_file):
            path_ntp = args.bak_file
        else:
            path_ntp = os.path.join(args.bak_file, "NTP.conf")
        if not os.path.exists(path_ntp):
            print ('Failure: restore NTP settings failed. No NTP backup file.')
            infoList.append('Failure: restore NTP settings failed. No NTP backup file.')
        else:
            try:
                status, info = ntp(client, path_ntp)
            except (TypeError, KeyError):
                status = -3
                info = 'illegal backup file, please check.'
            if status == 1:
                infoList.append('Success: restore NTP settings success. ' + info)
            else:
                infoList.append('Failure: restore NTP settings failed. ' + info)
    if snmptrapFlag == True:
        # snmptrap no
        if os.path.isfile(args.bak_file):
            path_snmptrap = args.bak_file
        else:
            path_snmptrap = os.path.join(args.bak_file, "SNMPtrap.conf")
        if not os.path.exists(path_snmptrap):
            infoList.append('Failure: restore SNMP trap configure failed. No SNMPtrap backup file.')
        else:
            try:
                status, info = snmp(client, path_snmptrap)
            except (TypeError, KeyError):
                status = -3
                info = 'illegal backup file, please check.'
            if status == 1:
                infoList.append('Success: restore SNMP trap configure success. ' + info)
            else:
                infoList.append('Failure: restore SNMP trap configure failed. ' + info)
    if networkFlag == True:
        # network yes
        if os.path.isfile(args.bak_file):
            path_network = args.bak_file
        else:
            path_network = os.path.join(args.bak_file, "network.conf")
        if not os.path.exists(path_network):
            infoList.append('Failure: restore network settings failed. No network backup file')
        else:
            try:
                status, info = network(client, path_network)
            except (TypeError, KeyError):
                status = -3
                info = 'illegal backup file, please check.'
            if status == 1:
                infoList.append('Success: restore network settings success, bmc will reset, please wait for a moment')
            else:
                infoList.append('Failure: restore network settings failed. ' + info)
    if smtpFlag == True:
        # SMTP no
        if os.path.isfile(args.bak_file):
            path_smtp = args.bak_file
        else:
            path_smtp = os.path.join(args.bak_file, "SMTP.conf")
        if not os.path.exists(path_smtp):
            infoList.append('Failure: restore SMTP settings failed. No SMTP backup file')
        else:
            try:
                status, info = smtp(client, args, path_smtp)
            except (TypeError, KeyError):
                status = -3
                info = 'illegal backup file, please check.'
            if status == 1:
                infoList.append('Success: restore SMTP settings success. ' + info)
            else:
                infoList.append('Failure: restore SMTP settings failed. ' + info)
        # services
    if serviceFlag == True:
        if os.path.isfile(args.bak_file):
            path_service = args.bak_file
        else:
            path_service = os.path.join(args.bak_file, "Services.conf")
        if not os.path.exists(path_service):
            infoList.append('Failure: restore service settings failed. No service backup file.')
        else:
            try:
                status, info = service(client, path_service)
            except (TypeError, KeyError):
                status = -3
                info = 'illegal backup file, please check.'
            if status == 1:
                infoList.append('Success: restore service settings success. ' + info)
            else:
                infoList.append('Failure: restore service settings failed. ' + info)
    if biosFlag == True:
        if os.path.isfile(args.bak_file):
            path_bios = args.bak_file
        else:
            path_bios = os.path.join(args.bak_file, "Bios.conf")
        if not os.path.exists(path_bios):
            infoList.append('Failure: restore bios settings failed. no BIOS backup file.')
        else:
            status, info = bios(client, path_bios)
            if status == 1:
                infoList.append('Success: restore BIOS config success. ' + info)
            else:
                infoList.append('Failure: restore BIOS config failed.' + info)
    if userFlag == True:
        # user group
        if os.path.isfile(args.bak_file):
            infoList.append('Failure: restore user settings failed. Input the folder of user backup files(-F)')
        else:
            path_userg = os.path.join(args.bak_file, "UserGroup.conf")
            if not os.path.exists(path_userg):
                infoList.append('Failure: restore user group settings failed. No user group backup file.')
                infoList.append('Failure: restore user settings failed. Restore user group settings first.')
            else:
                try:
                    # status,info = importUserGroup.restore(client, args, path_userg)
                    status, info = restore_group(client, args, path_userg)
                except KeyError as k:
                    status = -3
                    info = 'illegal backup file, please check1.'
                    infoList.append(str(k))
                except TypeError as t:
                    status = -3
                    info = 'illegal backup file, please check2.'
                    infoList.append(str(t))
                except Exception as e:
                    status = -3
                    info = 'illegal backup file, please check3.'
                    infoList.append(str(e))
                if status == 1:
                    infoList.append('Success: restore user group settings success. ')
                    # user
                    path_user = os.path.join(args.bak_file, "User.conf")
                    if not os.path.exists(path_user):
                        infoList.append('Failure: restore user settings failed. No user backup file.')
                    else:
                        try:
                            # status,info = importUser.restore(client, args, path_user)
                            status, info = restore_user(client, args, path_user)
                        except KeyError as k:
                            status = -3
                            info = 'illegal backup file, please check1.'
                            infoList.append(str(k))
                        except TypeError as t:
                            status = -3
                            info = 'illegal backup file, please check2.'
                            infoList.append(str(t))
                        except Exception as e:
                            status = -3
                            info = 'illegal backup file, please check3.'
                            infoList.append(str(e))
                        if status == 1:
                            infoList.append('Success: restore user settings success. ')
                        else:
                            infoList.append('Failure: restore user settings failed. ' + info)
                else:
                    infoList.append('Failure: restore user group settings failed. ' + info)

    if ldapFlag == True:
        # ladp
        if os.path.isfile(args.bak_file):
            path_ldap = args.bak_file
        else:
            path_ldap = os.path.join(args.bak_file, "LDAP.conf")
        if not os.path.exists(path_ldap):
            infoList.append('Failure: restore ldap settings failed. No LDAP backup file')
        else:
            try:
                status, info = ldap(client, args, path_ldap)
            except (TypeError, KeyError):
                status = -3
                info = 'illegal backup file, please check.'
            if status == 1:
                infoList.append('Success: restore LDAP settings success')
                if os.path.isfile(args.bak_file):
                    path_ldap = os.path.join(os.path.dirname(args.bak_file), "LDAPgroup.conf")
                else:
                    path_ldap = os.path.join(args.bak_file, "LDAPgroup.conf")
                if os.path.exists(path_ldap):
                    try:
                        # status,info = importLDAPgroup.restore(client,args, path_ldap)
                        status, info = restore_LDAP(client, args, path_ldap)
                    except (TypeError, KeyError):
                        status = -3
                        info = 'illegal backup file, please check.'
                    if status == 1:
                        infoList.append('Success: restore LDAP group settings success')
                    elif status == 2:
                        infoList.append('Success: restore LDAP group settings success')
                    else:
                        infoList.append('Failure: ' + info)
            elif status == 2:
                infoList.append('Success: restore LDAP settings success')
            else:
                infoList.append('Failure: ' + info)
    if adFlag == True:
        # ad
        if os.path.isfile(args.bak_file):
            path_ad = args.bak_file
        else:
            path_ad = os.path.join(args.bak_file, "AD.conf")
        if not os.path.exists(path_ad):
            infoList.append('Failure: restore ad settings failed. No AD backup file')
        else:
            try:
                status, info = ad(client, args, path_ad)
            except (TypeError, KeyError):
                status = -3
                info = 'illegal backup file, please check.'
            if status == 1:
                infoList.append('Success: restore AD settings success')
                if os.path.isfile(args.bak_file):
                    path_ad = os.path.join(os.path.dirname(args.bak_file), "ADgroup.conf")
                else:
                    path_ad = os.path.join(args.bak_file, "ADgroup.conf")
                if os.path.exists(path_ad):
                    try:
                        status, info = restore_AD(client, args, path_ad)
                    except (TypeError, KeyError):
                        status = -3
                        info = 'illegal backup file, please check.'
                    if status == 1:
                        infoList.append('Success: restore AD group settings success')
                    elif status == 2:
                        infoList.append('Success: restore AD group settings success')
                    else:
                        infoList.append('Failure: ' + info)
            elif status == 2:
                infoList.append('Success: restore AD settings success')
            else:
                infoList.append('Failure: ' + info)
    if dnsFlag == True:
        # DNS
        if os.path.isfile(args.bak_file):
            path_dns = args.bak_file
        else:
            path_dns = os.path.join(args.bak_file, "DNS.conf")
        if not os.path.exists(path_dns):
            info = 'illegal backup file, please check.'
        else:
            try:
                status, info = dns(client, path_dns)
            except (TypeError, KeyError):
                status = -3
                info = 'illegal backup file, please check.'
            if status == 1:
                infoList.append('Success: restore DNS settings success. ' + info)
            else:
                infoList.append('Failure: restore DNS settings failed. ' + info)
        time.sleep(120)
    result = ResultBean()
    result.State('Success')
    result.Message(infoList)
    return result


def ntp(client, bak_path):
    f = open(bak_path, 'r')
    NTPInfo = f.read()
    f.close()
    NTPJson = json.loads(NTPInfo)
    flag = True
    info = ""
    now_time = time.time()
    timestamp = int(now_time) + int(480) * 60
    if str(NTPJson['auto_date']) == "2":
        autodate = 1
    else:
        autodate = NTPJson['auto_date']
    data = {
        'auto_date': autodate,
        'id': NTPJson['id'],
        'localized_timestamp': NTPJson['localized_timestamp'],
        'primary_ntp': NTPJson['primary_ntp'],
        'secondary_ntp': NTPJson['secondary_ntp'],
        'third_ntp': NTPJson['third_ntp'],
        'timestamp': timestamp,
        'timezone': "",
        'utc_minutes': NTPJson['utc_minutes']
    }
    if 'date_cycle' in NTPJson:
        data['date_cycle'] = NTPJson['date_cycle']
    responds = RestFunc.setTimeByRest(client, data)
    if responds['code'] == 0 and responds['data'] is not None:
        flag = True
        info = responds['data']
    else:
        flag = False
        info = responds['data']
    if flag:
        return 1, info
    else:
        return -1, info


def dns(client, bak_path):
    f = open(bak_path, 'r')
    DNSInfo = f.read()
    f.close()
    DNSJson = json.loads(DNSInfo)
    flag = True
    info = ""
    data = {
        'dns_iface': DNSJson['dns_iface'],
        'dns_manual': DNSJson['dns_manual'],
        'dns_priority': DNSJson['dns_priority'],
        'dns_server1': DNSJson['dns_server1'],
        'dns_server2': DNSJson['dns_server2'],
        'dns_server3': DNSJson['dns_server3'],
        'dns_status': DNSJson['dns_status'],
        'domain_iface': DNSJson['domain_iface'],
        'domain_manual': DNSJson['domain_manual'],
        'domain_name': DNSJson['domain_name'],
        'host_cfg': DNSJson['host_cfg'],
        'host_name': DNSJson['host_name']
    }
    responds = RestFunc.setDNSByRestM5(client, data)
    if responds['code'] == 0 and responds['data'] is not None:
        responds = RestFunc.setDNSRestartBMCByRest(client, data)
        if responds['code'] == 0 and responds['data'] is not None:
            flag = True
            info = 'DNS is reseting, please wait for a few minutes'
        else:
            flag = False
            info = responds['data']
    else:
        flag = False
        info = responds['data']
    if flag:
        return 1, info
    else:
        return -1, info


def snmp(client, bak_path):
    f = open(bak_path, 'r')
    NTPInfo = f.read()
    f.close()
    NTPJson = json.loads(NTPInfo)
    flag = True
    info = ""
    data = {
        'trap_version': NTPJson['trap_version'],
        'event_level': NTPJson['event_level'],
        'community': NTPJson['community'],
        'username': NTPJson['username'],
        'engine_id': NTPJson['engine_id'],
        'auth_protocol': NTPJson['auth_protocol'],
        'auth_passwd': NTPJson['auth_passwd'],
        'priv_protocol': NTPJson['priv_protocol'],
        'priv_passwd': NTPJson['priv_passwd'],
        'system_name': NTPJson['system_name'],
        'system_id': NTPJson['system_id'],
        'location': NTPJson['location'],
        'contact_name': NTPJson['contact_name'],
        'host_os': NTPJson['host_os']
    }
    responds = RestFunc.setTrapComByRest(client, data)
    if responds['code'] == 0 and responds['data'] is not None:
        info = ""
    else:
        flag = False
        info = responds['data']
    if flag:
        return 1, info
    else:
        return -1, info


def network(client, bak_path):
    # 读取

    f = open(bak_path, 'r')
    networkInfo = f.read()
    f.close()
    networkJson = json.loads(networkInfo)
    flag = True
    info = ""
    lanDict = {
        'eth0': 'eth0(shared)',
        'eth1': 'eth1(dedicated)'
    }
    for netinfo in networkJson:
        data = {
            "id": netinfo['id'],
            "interface_name": netinfo['interface_name'],
            "channel_number": netinfo['channel_number'],
            "mac_address": netinfo['mac_address'],
            "lan_enable": netinfo['lan_enable'],

            "ipv4_enable": netinfo['ipv4_enable'],
            "ipv4_dhcp_enable": netinfo['ipv4_dhcp_enable'],
            "ipv4_address": netinfo['ipv4_address'],
            "ipv4_subnet": netinfo['ipv4_subnet'],
            "ipv4_gateway": netinfo['ipv4_gateway'],

            "ipv6_enable": netinfo['ipv6_enable'],
            "ipv6_dhcp_enable": netinfo['ipv6_dhcp_enable'],
            "ipv6_address": netinfo['ipv6_address'],
            "ipv6_index": netinfo['ipv6_index'],
            "ipv6_prefix": netinfo['ipv6_prefix'],
            "ipv6_gateway": netinfo['ipv6_gateway'],

            "vlan_enable": netinfo['vlan_enable'],
            "vlan_id": netinfo['vlan_id'],
            "vlan_priority": netinfo['vlan_priority']
        }
        responds = RestFunc.setLanByRest(client, data)
        if responds['code'] == 0 and responds['data'] is not None:
            info = info + lanDict[netinfo['interface_name']] + ": set network info success. "
        else:
            flag = False
            info = info + lanDict[netinfo['interface_name']] + ": set network info failed. "
        time.sleep(120)
    if flag:
        return 1, info
    else:
        return -1, info


def smtp(client, args, bak_path):
    f = open(bak_path, 'r')
    SMTPInfo = f.read()
    f.close()
    SMTPJson = json.loads(SMTPInfo)
    flag = True
    info = ""
    lanDict = {
        'eth0': 'eth0(shared)',
        'eth1': 'eth1(dedicated)',
        'bond0': 'Bond'
    }
    for item in SMTPJson:
        data = {
            'channel_interface': item['channel_interface'],
            'email_id': item['email_id'],
            'id': item['id'],

            'primary_smtp_enable': item['primary_smtp_enable'],
            'primary_server_ip': item['primary_server_ip'],
            'primary_server_name': item['primary_server_name'],
            'primary_smtp_authentication': item['primary_smtp_authentication'],
            'primary_smtp_port': item['primary_smtp_port'],
            'primary_smtp_secure_port': item['primary_smtp_secure_port'],
            'primary_ssltls_enable': item['primary_ssltls_enable'],
            'primary_starttls_enable': item['primary_starttls_enable'],
            'primary_username': item['primary_username'],

            'secondary_smtp_enable': item['secondary_smtp_enable'],
            'secondary_server_ip': item['secondary_server_ip'],
            'secondary_server_name': item['secondary_server_name'],
            'secondary_smtp_authentication': item['secondary_smtp_authentication'],
            'secondary_smtp_port': item['secondary_smtp_port'],
            'secondary_smtp_secure_port': item['secondary_smtp_secure_port'],
            'secondary_ssltls_enable': item['secondary_ssltls_enable'],
            'secondary_starttls_enable': item['secondary_starttls_enable'],
            'secondary_username': item['secondary_username']
        }

        SMTPServerList = []
        # 是否需要密码
        primary_password_flag = False
        secondary_password_flag = False
        # 是否获取密码
        primary_password_get_flag = True
        secondary_password_get_flag = True
        if item['primary_smtp_enable'] == 1 and item['primary_smtp_authentication'] == 1:
            primary_password_flag = True
        if item['secondary_smtp_enable'] == 1 and item['secondary_smtp_authentication'] == 1:
            secondary_password_flag = True
        if primary_password_flag or secondary_password_flag:
            f = open(args.passpath, 'r')
            password_txt = f.read()
            f.close()
            password_json = json.loads(password_txt)
            SMTPServerList = password_json['SMTP']
            if SMTPServerList == []:
                flag = False
                info = info + lanDict[
                    item['channel_interface']] + ": need SMTP server user and password in password.txt. "
                break
        if primary_password_flag:
            primary_password_get_flag = False
            for up in SMTPServerList:
                if up['serverip'] == item['primary_server_ip'] and up['username'] == item['primary_username']:
                    data.update(primary_password=up['password'])
                    primary_password_get_flag = True
                    break
        if not primary_password_get_flag:
            flag = False
            info = info + lanDict[item['channel_interface']] + ": do not find password for user [" + str(
                item['primary_username']) + "] of primary SMTP server [" + str(item['primary_server_ip']) + "] "
            continue
        if secondary_password_flag:
            secondary_password_get_flag = False
            for up in SMTPServerList:
                if up['serverip'] == item['secondary_server_ip'] and up['username'] == item['secondary_username']:
                    data.update(secondary_password=up['password'])
                    secondary_password_get_flag = True
                    break
        if not secondary_password_get_flag:
            flag = False
            info = info + lanDict[item['channel_interface']] + ": do not find password for user [" + str(
                item['secondary_username']) + "] of secondary SMTP server [" + str(item['secondary_server_ip']) + "] "
            continue
        responds = RestFunc.setSMTPM5ByRest(client, item['id'], data)
        if responds['code'] == 0 and responds['data'] is not None:
            info = info + lanDict[item['channel_interface']] + ": set SMTP info success. "
        else:
            flag = False

            info = info + lanDict[item['channel_interface']] + ": set SMTP info failed. "
    if flag:
        return 1, info
    else:
        return -1, info


def service(client, path_service):
    # 读取
    f = open(path_service, 'r')
    networkInfo = f.read()
    f.close()
    networkJson = json.loads(networkInfo)
    for netinfo in networkJson:
        data = {
            'service_name': netinfo['service_name'],
            'state': netinfo['state'],
            'interface_name': netinfo['interface_name'],
            'secure_port': netinfo['secure_port'],
            'non_secure_port': netinfo['non_secure_port'],
            'time_out': netinfo['time_out']
            }
        responds = RestFunc.setServiceByRest(client, data, netinfo['id'])
        if responds['code'] == 0 and responds['data'] is not None:
            continue
        else:
            return -2, str(responds['data'])
    return 1, " "


def bios(client, path_bios):
    responds = RestFunc.exportBiosCfgByRest(client, path_bios)
    if responds['code'] == 0 and responds['data'] is not None:
        return 1, 'ok'
    else:
        return -2, 'import bios option failed. '


def delusergroup(client, args, delName):
    for item in delName:
        argsList = {}
        # 添加BMC用户名
        argsList['U'] = args.username
        # 添加子命令参数
        argsList['N'] = item
        status, info = delusergroupfun(client, argsList)
        if status != 1:
            return status, info
    return 1, 'ok'


def delusergroupfun(client, argsList):
    flag = checkUser(client, argsList, 'Import')
    if flag == 'Info':
        return 0, 'can not get privilege of user ' + str(argsList['U'])
    elif flag == 'No':
        return 0, 'user ' + str(argsList['U']) + ' no permission'

    group = []
    default = ['Administrator', 'Operator', 'User']

    Group = getUserGroup(client)
    id = 0
    if Group is None:
        return 0, 'failed to get user group'
    else:
        try:
            for item in Group:
                if item['GroupName'] == argsList['N']:
                    id = item['GroupID']

                group.append(item['GroupName'])
        except ValueError:
            return 0, 'failed to get user group'

    # 判断用户组是否存在
    if argsList['N'] not in group:
        return 0, 'no group ' + str(argsList['N'])

    # 保留用户组不能修改
    if argsList['N'] in default:
        return 0, str(argsList['N']) + ' is reserved user group '

    responds = RestFunc.delUserGroupByRest(client, id, argsList['N'])
    if responds['code'] == 0 and responds['data'] is not None:
        return 1, 'ok'
    else:
        return 0, 'failed to delete user group' + str(argsList['N'])


def setusergroupfun(client, argsList):
    flag = checkUser(client, argsList, 'Import')
    if flag == 'Info':
        return 0, 'Cannot get privilege of user ' + str(argsList['U'])
    elif flag == 'No':
        return 0, 'User ' + str(argsList['U']) + ' no permission'

    group = []
    default = ['Administrator', 'Operator', 'User']

    Group = getUserGroup(client)
    id = 0
    if Group is None:
        return 0, 'failed to get user group'
    else:
        try:
            for item in Group:
                if item['GroupName'] == argsList['N']:
                    id = item['GroupID']

                group.append(item['GroupName'])
        except ValueError:
            return 0, 'failed to get user group'
    # 判断用户组是否存在
    if argsList['N'] not in group:
        return 0, 'no group ' + argsList['N']

    # 保留用户组不能修改
    if argsList['N'] in default:
        return 0, argsList['N'] + ' is reserved user group '
    if argsList['PRI'] == 'no access':
        argsList['PRI'] = 'none'
    responds = RestFunc.setUserGroupByRest(client, id, argsList['N'], argsList['PRI'])
    if responds['code'] == 0 and responds['data'] is not None:
        return 1, 'ok'
    else:
        return 0, 'failed to set user group ' + str(argsList['N'])


def getUserGroup(client):
    responds = RestFunc.getUserGroupByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        return result
    else:
        return None


def setusergroup(client, args, setName, path_userg):
    f = open(path_userg, 'r')

    user = f.read()
    f.close()
    dict = json.loads(user)
    for item in dict:
        argsList = {}
        # 添加BMC用户名
        argsList['U'] = args.username
        # 添加子命令参数
        if 'GroupName' not in item or 'GroupPriv' not in item:
            return 0, 'Cannot get json group information'
        else:
            if item['GroupName'] in setName:
                argsList['N'] = item['GroupName']
                if item['GroupPriv'] == 'proprietary' or item['GroupPriv'] == 'Proprietary':
                    argsList['PRI'] = 'oem'
                elif item['GroupPriv'] == 'no access' or item['GroupPriv'] == 'No Access':
                    argsList['PRI'] = 'none'
                else:
                    argsList['PRI'] = str(item['GroupPriv']).lower()
                status, info = setusergroupfun(client, argsList)
                if status != 1:
                    return status, info
    return 1, 'ok'


def addusergroupfun(client, argsList):
    flag = checkUser(client, argsList, 'Import')

    if flag == 'Info':
        return 0, 'can not get privilege of user ' + str(argsList['U'])
    elif flag == 'No':
        return 0, 'user ' + str(argsList['U']) + ' no permission'

    group = []
    Group = getUserGroup(client)

    if Group is None:
        return 0, 'failed to get user group'
    else:
        try:
            for item in Group:
                group.append(item['GroupName'])
        except ValueError:
            return 0, 'failed to get user group'

    if argsList['N'] in group:
        return 0, 'group ' + str(argsList['N']) + ' already exists'
    if argsList['PRI'] == 'no access':
        argsList['PRI'] = 'none'
    responds = RestFunc.addUserGroupByRest(client, argsList['N'], argsList['PRI'])
    if responds['code'] == 0 and responds['data'] is not None:
        return 1, 'ok'
    else:
        return 0, 'failed to add user group ' + str(argsList['N'])


def addusergroup(client, args, addName, path_userg):
    f = open(path_userg, 'r')

    user = f.read()
    f.close()
    dict = json.loads(user)
    for item in dict:
        argsList = {}
        # 添加BMC用户名
        argsList['U'] = args.username
        # 添加子命令参数
        if 'GroupName' not in item or 'GroupPriv' not in item:
            return 0, 'Cannot get json group information'
        else:
            if item['GroupName'] in addName:
                argsList['N'] = item['GroupName']
                if item['GroupPriv'] == 'proprietary' or item['GroupPriv'] == 'Proprietary':
                    argsList['PRI'] = 'oem'
                elif item['GroupPriv'] == 'no access' or item['GroupPriv'] == 'No Access':
                    argsList['PRI'] = 'none'
                else:
                    argsList['PRI'] = str(item['GroupPriv']).lower()
                status, info = addusergroupfun(client, argsList)
                if status != 1:
                    return status, info
    return 1, 'ok'


def deluserfun(client, argsList):
    flag = checkUser(client, argsList, 'Import')
    if flag == 'Info':
        return 0, 'can not get privilege of usr ' + str(argsList['U'])

    elif flag == 'No':
        return 0, 'user ' + str(argsList['U']) + ' no permission'

    userID = getUserID(client, argsList, 'Import')
    if userID is None:
        return 0, 'no user ' + str(argsList['N'])

    responds = RestFunc.delUserByRest(client, str(userID), str(argsList['N']))
    if responds['code'] == 0 and responds['data'] is not None:
        return 1, 'ok'
    else:
        return 0, "failed to delete " + str(argsList['N'])


def deluser(client, args, delName):
    for item in delName:
        argsList = {}
        # 添加BMC用户名
        argsList['U'] = args.username
        # 添加子命令参数
        argsList['N'] = item
        if item == args.username:
            continue
        status, info = deluserfun(client, argsList)
        if status != 1:
            return status, info
    return 1, 'ok'


def getUserID(client, args, flag):
    responds = RestFunc.getUserByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        try:
            for item in result:
                if flag == 'delUser':
                    if item['name'] == args.uname:
                        return item['id']
                elif flag == 'Import':
                    if item['name'] == args['N']:
                        return item['id']
                else:
                    if item['name'] == args.uname:
                        return item['id']
        except ValueError:
            return None
        return None
    else:
        return None


def setuserfun(client, argsList):
    flag = checkUser(client, argsList, 'Import')
    if flag == 'Info':
        return 0, 'can not get privilege of usr ' + str(argsList['U'])

    elif flag == 'No':
        return 0, 'user ' + str(argsList['U']) + ' no permission'

    userID = getUserID(client, argsList, 'Import')
    if userID is None:
        return 0, 'no user ' + str(argsList['N'])

    responds = RestFunc.delUserByRest(client, str(userID), str(argsList['N']))
    if responds['code'] == 0 and responds['data'] is not None:
        return 1, 'ok'
    else:
        return 0, "failed to delete " + str(argsList['N'])


def setuser(client, args, delName):

    for item in delName:
        argsList = {}
        # 添加BMC用户名
        argsList['U'] = args.username
        # 添加子命令参数
        argsList['N'] = item
        if item == args.username:
            continue
        status, info = setuserfun(client, argsList)
        if status != 1:
            return status, info
    return 1, 'ok'


def adduserfun(client, argsList):
    flag = checkUser(client, argsList, 'Import')
    if flag == 'Info':
        return 0, 'can not get privilege of user ' + str(argsList['U'])
    elif flag == 'No':
        return 0, 'user ' + str(argsList['U']) + ' no permission'

    userID = getUserID(client)
    if userID is None:
        return 0, 'can not get information of user' + str(argsList['N'])
    if userID == 'no':
        return 0, 'no space to add users' + str(argsList['N'])

    if argsList['ID'] != '':
        userID = argsList['ID']

    UserOperation = 0  # add a user
    if argsList['PS'] == 'bytes_16':
        size = 16
    else:
        size = 16
    if 1 <= len(argsList['N']) <= 16:
        if not argsList['N'][0].isalpha():
            return 0, ''''name' must start with an alphabetical character'''
    else:
        return 0, ''''name' is a string of 1 to 16 alpha-numeric characters'''

    if argsList['PWD'] == '':
        return 0, 'user ' + str(argsList['N']) + ' no password'

    elif len(argsList['PWD']) < 1 or len(argsList['PWD']) > 16:
        return 0, 'password of user ' + str(argsList['N']) + ' is a string of 1 to ' \
            + str(size) + ' characters'

    if argsList['ACCESS'] == '':
        argsList['ACCESS'] = 0

    if argsList['G'] == '':
        groupName = 'Administrator'
    else:
        groupList = getGroup(client)
        if argsList['G'] not in groupList:
            return 0, 'Error in adding user ' + str(argsList['N']) + ', no group ' + str(argsList['G'])
        else:
            groupName = argsList['G']

    data = {"UserOperation": UserOperation, "password_old": "", "access": argsList['ACCESS'], "changepassword": 1,
            "confirm_password": argsList['PWD'],
            "email_format": argsList['EmailFormat'], "email_id": argsList['EmailID'], "fixed_user_count": 2, "id": userID, "kvm": argsList['KVM'],
            "name": argsList['N'],
            "group_name": groupName, "network_privilege": argsList['PRI'], "password": argsList['PWD'],
            "password_size": argsList['PS'], "privilege_limit_serial": "user", "snmp": 0, "snmp_access": "read_only",
            "snmp_authentication_protocol": "sha", "snmp_privacy_protocol": "des", "ssh_key": "Not Available",
            "ssh_status": 0, "vmedia": argsList['VM']}

    responds = RestFunc.addUserByRestM5(client, str(userID), data)
    if responds['code'] == 0 and responds['data'] is not None:
        return 1, 'ok'

    else:
        return 0, str(responds['data'])


def adduser(client, args, addName, path_user):
    f = open(path_user, 'r')
    user = f.read()
    f.close()
    dict = json.loads(user)
    f = open(args.passpath, 'r')

    password = f.read()
    f.close()
    pwd = json.loads(password)

    for item in dict:
        argsList = {}
        # 添加BMC用户名
        argsList['U'] = args.username
        # 添加子命令参数

        if 'name' not in item:
            return 0, 'Cannot get users name'
        elif item['name'] == args.username:
            continue
        else:
            if item['name'] in addName:
                argsList['PWD'] = ''
                argsList['ID'] = ''
                for User in pwd['USERS']:
                    if item['name'] == User['username']:
                        argsList['PWD'] = User['password']

                argsList['N'] = item['name']

                argsList['G'] = item['group_name']
                argsList['ACCESS'] = item['access']
                argsList['EmailFormat'] = item['email_format']
                argsList['EmailID'] = item['email_id']
                argsList['KVM'] = item['kvm']
                argsList['PRI'] = item['network_privilege']
                argsList['PS'] = 'bytes_16'
                argsList['VM'] = item['vmedia']
                argsList['ID'] = item['id']
                status, info = adduserfun(client, argsList)
                if status != 1:
                    return status, info
            else:
                continue
    return 1, 'ok'


def ldapfun(client, argsList):
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    # 启用 LDAP
    if argsList['S'] == 1:
        if argsList['E'] == '':
            argsList['E'] = 0

        if argsList['ADDR'] == '':
            return 0, 'argument ADDR is required'

        else:
            if not RegularCheckUtil.checkIP(argsList['ADDR']):
                return 0, 'invalid ADDR value'

        if argsList['PORT'] == '':
            argsList['PORT'] = 389
        else:
            if argsList['PORT'] < 1 or argsList['PORT'] > 65535:
                return 0, 'argument PORT range in 1-65535'

        if argsList['DN'] == '':
            return 0, 'argument DN is required'
        else:
            if not argsList['DN'][0].isalpha():
                return 0, 'DN must start with an alphabetical character'

            if len(argsList['DN']) < 4 or len(argsList['DN']) > 64:
                return 0, 'Bind DN is a string of 4 to 64 alpha-numeric characters'

        if argsList['PWD'] == '':
            return 0, 'password of server ' + argsList['ADDR'] + ' is required'
        else:
            if len(argsList['PWD']) < 1 or len(argsList['PWD']) > 48:
                return 0, 'password of server ' + argsList['ADDR'] + ' is a string of 1 to 48 characters'

        if argsList['BASE'] == '':
            return 0, 'search base is required'
        else:
            if not argsList['BASE'][0].isalpha():
                return 0, 'search base must start with an alphabetical character'

            if len(argsList['BASE']) < 4 or len(argsList['BASE']) > 64:
                return 0, 'Search base is a string of 4 to 64 alpha-numeric characters'

        if argsList['ATTR'] == '':
            return 0, 'Attribute of User Login is required'

        encry = {'no': 0, 'SSL': 1, 'StartTLS': 2, 0: 0, 1: 1, 2: 2}

        # 加密类型为StartTLS
        if argsList['E'] == 2:
            if argsList['CN'] == '':
                return 0, 'common name is required'
            if argsList['CA'] != '':
                if RegularCheckUtil.checkFile(argsList['CA']):
                    file1 = argsList['CA']
                    file1Base = path.basename(file1)
                else:
                    return 0, 'incorrect CA file'
            else:
                file1 = None
                file1Base = None

            if argsList['CE'] != '':
                if RegularCheckUtil.checkFile(argsList['CE']):
                    file2 = argsList['CE']
                    file2Base = path.basename(file2)
                else:
                    return 0, 'incorrect CE file'
            else:
                file2 = None
                file2Base = None

            if argsList['PK'] != '':
                if RegularCheckUtil.checkFile(argsList['PK']):
                    file3 = argsList['PK']
                    file3Base = path.basename(file3)
                else:
                    return 0, 'incorrect PK file'
            else:
                file3 = None
                file3Base = None

            data_TLS = {
                'bind_dn': argsList['DN'],
                'ca_certificate_file': file1Base,
                'certificate_file': file2Base,
                'common_name_type': argsList['CN'],
                'enable': 1,
                'encryption_type': "2",
                'id': 1,
                'password': argsList['PWD'],
                'port': argsList['PORT'],
                'private_key': file3Base,
                'search_base': argsList['BASE'],
                'server_address': argsList['ADDR'],
                'user_login_attribute': argsList['ATTR']

            }
            if file1:
                file1 = open(file1, 'rb')
            else:
                file1 = ''

            if file2:
                file2 = open(file2, 'rb')
            else:
                file2 = ''

            if file3:
                file3 = open(file3, 'rb')
            else:
                file3 = ''

            try:
                files = {
                    'ca_certificate_file': file1,
                    'certificate_file': file2,
                    'private_key': file3
                }
                # # 修改header
                # header = client.getHearder()
                # header["X-Requested-With"] = "XMLHttpRequest"
                # header["Content-Type"] = 'multipart/form-data; boundary=----WebKitFormBoundaryESySkHogY2EmvMkE'
                # header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
                #
                # r = client.request("POST", "api/settings/ldap-certificates", files=files, headers=header)
                responds = RestFunc.setLDAPFile(client, files)
                if responds['code'] != 0:
                    return 0, 'failed to set LDAP'

            except (IOError, TypeError):
                return 0, 'failed to set LDAP'

            responds = RestFunc.setLDAP(client, data_TLS)
            if responds['code'] == 0 and responds['data'] is not None:
                return 1, 'ok'
            else:
                return 0, 'failed to set LDAP'

        # 加密类型为 no 或 SSL
        else:
            data = {
                'bind_dn': argsList['DN'],
                'common_name_type': 'ip',
                'enable': 1,
                'encryption_type': argsList['E'],
                'id': 1,
                'password': argsList['PWD'],
                'port': argsList['PORT'],
                'search_base': argsList['BASE'],
                'server_address': argsList['ADDR'],
                'user_login_attribute': argsList['ATTR']
            }

            responds = RestFunc.setLDAP(client, data)
            if responds['code'] == 0 and responds['data'] is not None:
                return 1, 'ok'
            else:
                return 0, 'failed to set LDAP'
    # 禁用 LDAP
    else:
        data = {
            'bind_dn': '',
            'common_name_type': "ip",
            'enable': 0,
            'encryption_type': 0,
            'id': 1,
            'port': 389,
            'search_base': '',
            'server_address': '',
            'user_login_attribute': 'cn'
        }
        responds = RestFunc.setLDAP(client, data)
        if responds['code'] == 0 and responds['data'] is not None:
            if argsList['S'] == 0:
                return 2, 'ok'
            else:
                return 1, 'ok'
        else:
            return 0, 'failed to set LDAP'


def ldap(client, args, path_ldap):
    f = open(path_ldap, 'r')

    ladp = f.read()
    f.close()
    dict = json.loads(ladp)
    argsList = {}
    argsList['S'] = dict['enable']
    argsList['CN'] = dict['common_name_type']
    argsList['BASE'] = dict['search_base']
    argsList['E'] = dict['encryption_type']
    argsList['ADDR'] = dict['server_address']
    argsList['DN'] = dict['bind_dn']
    argsList['ATTR'] = dict['user_login_attribute']
    argsList['PORT'] = dict['port']
    argsList['PWD'] = ''
    argsList['CA'] = ''
    argsList['CE'] = ''
    argsList['PK'] = ''
    f = open(args.passpath, 'r')

    password = f.read()
    f.close()
    pwd = json.loads(password)
    try:
        for item in pwd['LDAP']:
            if argsList['ADDR'] == item['serverip']:
                argsList['PWD'] = item['password']
                argsList['CA'] = item['ca_certificate_file']
                argsList['CE'] = item['certificate_file']
                argsList['PK'] = item['private_key']
    except KeyError:
        return 0, 'incorrect password file'
    return ldapfun(client, argsList)


def delldapgroupfun(client, argsList):
    group = getLDAPgroup(client)
    if group is None:
        return 0, 'Cannot get LDAP group information'
    else:
        id = -1
        for item in group:
            if item['role_group_name'] == argsList['N']:
                id = item['id']

        if id == -1:
            return 0, 'No group ' + argsList['N']

    responds = RestFunc.delLDAPgroupM6(client, id)
    if responds['code'] == 0 and responds['data'] is not None:
        return 1, 'ok'
    else:
        return 0, 'failed to delete LDAP group'


def delldapgroup(client, args, delName):
    for item in delName:
        argsList = {}
        argsList['N'] = item

        status, info = delldapgroupfun(client, argsList)
        if status != 1:
            return status, info
    return 1, 'ok'


def addldapgroufun(client, argsList):

    if argsList['BASE'] == '':
        return 0, ''''role_group_domain' is required '''
    if argsList['PRI'] == '':
        return 0, ''''role_group_withoem_privilege' is required '''

    if argsList['KVM'] == '':
        argsList['KVM'] = 0

    if argsList['VM'] == '':
        argsList['VM'] = 0
    data = {
        'id': argsList['ID'],
        'role_group_domain': argsList['BASE'],
        'role_group_kvm_privilege': argsList['KVM'],
        'role_group_name': argsList['N'],
        'role_group_privilege': "none",
        'role_group_vmedia_privilege': argsList['VM'],
        'role_group_withoem_privilege': argsList['PRI']
    }
    responds = RestFunc.setLDAPgroupM6(client, data)
    if responds['code'] == 0 and responds['data'] is not None:
        return 1, 'ok'
    else:
        return 0, 'failed to add LDAP group'


def addldapgroup(client, args, path):
    # get settings
    f = open(path, 'r')
    group = f.read()
    f.close()
    dict = json.loads(group)
    for item in dict:
        argsList = {}
        argsList['ID'] = item['id']
        argsList['N'] = item['role_group_name']
        if argsList['N'] == '':
            continue
        argsList['BASE'] = item['role_group_domain']
        argsList['PRI'] = item['role_group_withoem_privilege']
        argsList['KVM'] = item['role_group_kvm_privilege']
        argsList['VM'] = item['role_group_vmedia_privilege']
        status, info = addldapgroup(client, argsList)
        if status != 1:
            return status, info
    return 1, 'ok'


def adfun(client, argsList):

    if argsList['S'] == '':
        return 0, ''''enable' is required'''

    if argsList['S'] == 1:
        if argsList['N'] == '':
            return 0, ''''secret_username' is required'''
        else:
            name = argsList['N']
            if not name[0].isalpha():
                return 0, ''''secret_username' must start with an alphabetical character'''
            if len(argsList['N']) < 1 or len(argsList['N']) > 16:
                return 0, ''''secret_username' is a string of 1 to 16 alpha-numeric characters'''

        if argsList['PWD'] == '':
            return 0, 'password of ' + argsList['N'] + ' is required'

        else:
            if len(argsList['PWD']) < 6 or len(argsList['PWD']) > 127:
                return 0, 'password of ' + argsList['N'] + ' is a string of 6 to 127 characters'

        if argsList['DOMAIN'] == '':
            return 0, ''''user_domain_name' is required'''
        else:
            domain = argsList['DOMAIN']
            if not RegularCheckUtil.checkDomainName(domain):
                return 0, '''invalid 'user_domain_name' '''

        if argsList['ADDR1'] == '' and argsList['ADDR2'] == '' and argsList['ADDR3'] == '':
            return 0, '''at least one domain controller server address is required '''

        if argsList['ADDR1'] != '':
            addr1 = argsList['ADDR1']
            if not RegularCheckUtil.checkIP(addr1):
                return 0, '''invalid 'domain_controller1' '''
        if argsList['ADDR2'] != '':
            addr2 = argsList['ADDR2']
            if not RegularCheckUtil.checkIP(addr2):
                return 0, '''invalid 'domain_controller2' '''
        if argsList['ADDR3'] != '':
            addr3 = argsList['ADDR3']
            if not RegularCheckUtil.checkIP(addr3):
                return 0, '''invalid 'domain_controller3' '''
        if argsList['T'] == '':
            data = {
                'domain_controller1': argsList['ADDR1'],
                'domain_controller2': argsList['ADDR2'],
                'domain_controller3': argsList['ADDR3'],
                'enable': 1,
                'id': 1,
                'secret_username': argsList['N'],
                'user_domain_name': argsList['DOMAIN'],
                'secret_password': argsList['PWD']
            }
        else:
            data = {
                'domain_controller1': argsList['ADDR1'],
                'domain_controller2': argsList['ADDR2'],
                'domain_controller3': argsList['ADDR3'],
                'enable': 1,
                'id': 1,
                'timeout': argsList['T'],
                'secret_username': argsList['N'],
                'user_domain_name': argsList['DOMAIN'],
                'secret_password': argsList['PWD']
            }
        responds = RestFunc.setADByRest(client, data)
        if responds['code'] == 0 and responds['data'] is not None:
            if argsList['S'] == 0:
                return 2, 'ok'
            else:
                return 1, 'ok'
        else:
            return 0, 'failed to set ad'
    # 禁用 AD
    else:
        data = {
            'domain_controller1': "",
            'domain_controller2': "",
            'domain_controller3': "",
            'enable': 0,
            'id': 1,
            'secret_username': "",
            'user_domain_name': ""
        }
        responds = RestFunc.setADByRest(client, data)
        if responds['code'] == 0 and responds['data'] is not None:
            if argsList['S'] == 0:
                return 2, 'ok'
            else:
                return 1, 'ok'
        else:
            return 0, 'failed to set ad'


def ad(client, args, path_ad):
    f = open(path_ad, 'r')

    ad = f.read()
    f.close()
    dict = json.loads(ad)
    argsList = {}
    argsList['S'] = dict['enable']
    argsList['N'] = dict['secret_username']
    argsList['DOMAIN'] = dict['user_domain_name']
    argsList['ADDR1'] = dict['domain_controller1']
    argsList['ADDR2'] = dict['domain_controller2']
    argsList['ADDR3'] = dict['domain_controller3']
    if 'timeout' in dict:
        argsList['T'] = dict['timeout']
    else:
        argsList['T'] = ''
    argsList['PWD'] = ''
    f = open(args.passpath, 'r')
    password = f.read()
    f.close()
    pwd = json.loads(password)
    for item in pwd['AD']:
        if argsList['N'] == item['username']:
            argsList['PWD'] = item['password']
            break

    return adfun(client, argsList)


def deladgroupfun(client, argsList):
    group = getADgroup(client)
    if group is None:
        return 0, 'Cannot get AD role group information'
    else:
        id = -1
        for item in group:
            if item['role_group_name'] == argsList['N']:
                id = item['id']

        if id == -1:
            return 0, 'No group ' + argsList['N']

    responds = RestFunc.delADGroupByRest(client, id)
    if responds['code'] == 0 and responds['data'] is not None:
        return 1, 'ok'
    else:
        return 0, 'failed to delete AD role group'


def deladgroup(client, args, delName):
    for item in delName:
        argsList = {}
        argsList['N'] = item

        status, info = deladgroupfun(client, argsList)
        if status != 1:
            return status, info
    return 1, 'ok'


def addadgroupfun(client, argsList):
    if argsList['BASE'] == '':
        return 0, ''''role_group_domain' is required '''
    if argsList['PRI'] == '':
        return 0, ''''role_group_withoem_privilege' is required '''

    if argsList['KVM'] == '':
        argsList['KVM'] = 0

    if argsList['VM'] == '':
        argsList['VM'] = 0
    data = {
        'id': argsList['ID'],
        'role_group_domain': argsList['BASE'],
        'role_group_kvm_privilege': argsList['KVM'],
        'role_group_name': argsList['N'],
        'role_group_privilege': "none",
        'role_group_vmedia_privilege': argsList['VM'],
        'role_group_withoem_privilege': argsList['PRI']
    }
    responds = RestFunc.setADGroupByRest(client, argsList['ID'], data)
    if responds['code'] == 0 and responds['data'] is not None:
        return 1, 'ok'
    else:
        return 0, 'failed to add AD group'


def addadgroup(client, args, path):
    # get settings
    f = open(path, 'r')
    group = f.read()
    f.close()
    dict = json.loads(group)
    for item in dict:
        argsList = {}
        argsList['ID'] = item['id']
        argsList['N'] = item['role_group_name']
        if argsList['N'] == '':
            continue
        argsList['BASE'] = item['role_group_domain']
        argsList['PRI'] = item['role_group_withoem_privilege']
        argsList['KVM'] = item['role_group_kvm_privilege']
        argsList['VM'] = item['role_group_vmedia_privilege']
        status, info = addadgroupfun(client, argsList)
        if status != 1:
            return status, info
    return 1, 'ok'
