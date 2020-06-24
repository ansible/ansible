# -*- coding:utf-8 -*-
import os
import time
import platform
import json
from ansible.plugins.inspur_sdk.command import RestFunc
from ansible.plugins.inspur_sdk.interface.ResEntity import ResultBean


def dns(client, args):
    responds = RestFunc.getDNSByRestM5(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        if platform.system() == 'Linux':
            f = open(args.backuppath + '/DNS.conf', 'w')
        else:
            f = open(args.backuppath + '\\DNS.conf', 'w')
        f.write(json.dumps(result, indent=4))
        f.close()
        return 1, "ok"
    else:
        return -1, "can not get dns info"


def network(client, args):
    responds = RestFunc.getNetworkByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        if platform.system() == 'Linux':
            f = open(args.backuppath + '/network.conf', 'w')
        else:
            f = open(args.backuppath + '\\network.conf', 'w')
        f.write(json.dumps(result, indent=4))
        f.close()
        return 1, "ok"
    else:
        return -1, "can not get network info"


def service(client, args):
    responds = RestFunc.getServiceInfoByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        file_name = 'Services.conf'
        file_name_all = args.backuppath + file_name
        f = open(file_name_all, 'w')
        f.write(json.dumps(result, indent=4))
        f.close()
        return 1, "ok"
    else:
        return -1, "can not get service info"


def ntp(client, args):
    responds = RestFunc.getDatetimeByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        if platform.system() == 'Linux':
            f = open(args.backuppath + '/NTP.conf', 'w')
        else:
            f = open(args.backuppath + '\\NTP.conf', 'w')
        f.write(json.dumps(result, indent=4))
        f.close()
        return 1, "ok"
    else:
        return -1, "can not get ntp info"


def smtp(client, args):
    responds = RestFunc.getSMTPM5ByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        if platform.system() == 'Linux':
            f = open(args.backuppath + '/SMTP.conf', 'w')
        else:
            f = open(args.backuppath + '\\SMTP.conf', 'w')
        f.write(json.dumps(result, indent=4))
        f.close()
        return 1, "ok"
    else:
        return -1, "can not get smtp info"


def snmptrap(client, args):
    responds = RestFunc.getSnmpInfoByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        if platform.system() == 'Linux':
            f = open(args.backuppath + '/SNMPtrap.conf', 'w')
        else:
            f = open(args.backuppath + '\\SNMPtrap.conf', 'w')
        f.write(json.dumps(result, indent=4))
        f.close()
        return 1, "ok"
    else:
        return -1, "can not get snmp trap info"


def alert(client, args):
    pass


def ad(client, args):
    responds = RestFunc.getADByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        f = open(args.backuppath + 'AD.conf', 'w')
        f.write(json.dumps(result, indent=4))
        f.close()
        return 1, "ok"
    else:
        return -1, "can not get ad info"


def adgroup(client, args):
    responds = RestFunc.getADGroupByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        f = open(args.backuppath + 'ADgroup.conf', 'w')
        f.write(json.dumps(result, indent=4))
        f.close()
        return 1, "ok"
    else:
        return -1, "can not get ad group info"


def ldap(client, args):
    responds = RestFunc.getLDAPM6(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        f = open(args.backuppath + 'LDAP.conf', 'w')
        f.write(json.dumps(result, indent=4))
        f.close()
        return 1, "ok"
    else:
        return -1, "can not get ldap info"


def ldapgroup(client, args):
    responds = RestFunc.getLDAPgroupM6(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        f = open(args.backuppath + 'LDAPgroup.conf', 'w')
        f.write(json.dumps(result, indent=4))
        f.close()
        return 1, "ok"
    else:
        return -1, "can not get ldap group info"


def user(client, args):
    responds = RestFunc.getUserByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        f = open(args.backuppath + 'User.conf', 'w')
        f.write(json.dumps(result, indent=4))
        f.close()
        return 1, "ok"
    else:
        return -1, "can not get user info"


def usergroup(client, args):
    responds = RestFunc.getUserGroupByRest(client)
    if responds['code'] == 0 and responds['data'] is not None:
        result = responds['data']
        f = open(args.backuppath + 'UserGroup.conf', 'w')
        f.write(json.dumps(result, indent=4))
        f.close()
        return 1, "ok"
    else:
        return -1, "can not get user group info"


def bios(client, args):
    file_name = 'Bios.conf'
    responds = RestFunc.exportTwoBiosCfgByRest(client, os.path.join(args.backuppath, file_name), file_name)
    if responds['code'] == 0 and responds['data'] is not None:
        return 1, "ok"
    else:
        return -1, "can not get bios info"


def backup(client, args):
    backtime = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    if platform.system() == 'Linux':
        path = args.bak_file + "backup/" + args.host + "-" + backtime + "/"
    else:
        path = args.bak_file + "backup\\" + args.host + "-" + backtime + "\\"
    if not os.path.exists(path):
        os.makedirs(path)
    args.backuppath = path
    password_path = path + "password.txt"
    if not os.path.exists(password_path):
        passwd_templet = {'SMTP': [{'serverip': '0.0.0.0', 'username': 'admin', 'password': 'admin'}], 'USERS': [{'username': 'admin', 'password': 'admin'}, {'username': 'root', 'password': 'root'}], 'LDAP': [{'serverip': '0.0.0.0', 'password': 'password', "ca_certificate_file": "", "certificate_file": "", "private_key": ""}], 'AD': [{'username': 'username', 'password': 'password'}]}
        f = open(password_path, 'w')
        f.write(json.dumps(passwd_templet, indent=4))
        f.close()

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
    if dnsFlag == True:
        # dns
        status, info = dns(client, args)
        if status == 1:
            infoList.append('Success: backup DNS settings success.')
        else:
            infoList.append("Failure: backup DNS settings failed. " + info)
    if networkFlag == True:
        # network
        status, info = network(client, args)
        if status == 1:
            infoList.append("Success: backup network settings success.")
        else:
            infoList.append("Failure: backup network settings failed. " + info)
    if serviceFlag == True:
        # services
        status, info = service(client, args)
        if status == 1:
            infoList.append("Success: backup services settings success.")
        else:
            infoList.append("Failure: backup services settings failed. " + info)
    if ntpFlag == True:
        # ntp
        status, info = ntp(client, args)
        if status == 1:
            infoList.append("Success: backup NTP settings success.")
        else:
            infoList.append("Failure: backup NTP settings failed. " + info)
    if smtpFlag == True:
        # smtp
        status, info = smtp(client, args)
        if status == 1:
            infoList.append("Success: backup SMTP settings success.")
        else:
            infoList.append("Failure: backup SMTP settings failed. " + info)
    if snmptrapFlag == True:
        # snmptrap
        status, info = snmptrap(client, args)
        if status == 1:
            infoList.append("Success: backup SNMP trap configuration success.")
        else:
            infoList.append("Failure: backup SNMP trap configuration failed. " + info)
    if adFlag == True:
        # AD
        status, info = ad(client, args)
        if status == 1:
            infoList.append("Success: backup AD settings success.")
        else:
            infoList.append("Failure: backup AD settings failed. " + info)
        # AD group
        status, info = adgroup(client, args)
        if status == 1:
            infoList.append("Success: backup AD group settings success.")
        elif status != 2:
            infoList.append("Failure: backup AD group settings failed. " + info)
    if ldapFlag == True:
        # LDAP
        status, info = ldap(client, args)
        if status == 1:
            infoList.append("Success: backup LDAP settings success.")
        else:
            infoList.append("Failure: backup LDAP settings failed. " + info)
        # LDAP group
        status, info = ldapgroup(client, args)
        if status == 1:
            infoList.append("Success: backup LDAP group settings success.")
        elif status != 2:
            infoList.append("Failure: backup LDAP group settings failed. " + info)

    if userFlag == True:
        # user
        status, info = user(client, args)
        if status == 1:
            infoList.append("Success: backup user settings success.")
        else:
            infoList.append("Failure: backup user settings failed. " + info)
        # user group
        status, info = usergroup(client, args)
        if status == 1:
            infoList.append("Success: backup user group settings success.")
        else:
            infoList.append("Failure: backup user group settings failed. " + info)
    if biosFlag == True:
        # bios
        status, info = bios(client, args)
        if status == 1:
            infoList.append("Success: backup BIOS configuration success.")
        else:
            infoList.append("Failure:  backup BIOS configuration failed. " + info)
    infoList.append('backup complete, backup files in ' + path)
    result = ResultBean()
    result.State('Success')
    result.Message(infoList)
    return result
