# -*- coding:utf-8 -*-
import json
import re


def checkIP(ip):
    if ip == "0.0.0.0":
        return False
    p = r'^((25[0-5]|2[0-4]\d|((1\d{2}|[1-9]?\d)))\.){3}(25[0-5]|2[0-4]\d|((1\d{2}|[1-9]?\d)))$'
    if re.search(p, ip, re.I):
        return True
    else:
        return False


def checkSubnetMask(ip):
    if ip == "0.0.0.0":
        return False
    p = r'^((25[0-5]|2[0-4]\d|((1\d{2}|[1-9]?\d)))\.){3}(25[0-5]|2[0-4]\d|((1\d{2}|[1-9]?\d)))$'
    m1 = r'(128|192|224|240|248|252|254|255)\.0\.0\.0|'
    m2 = r'255\.(0|128|192|224|240|248|252|254|255)\.0\.0|'
    m3 = r'255\.255\.(0|128|192|224|240|248|252|254|255)\.0|'
    m4 = r'255\.255\.255\.(0|128|192|224|240|248|252|254)'
    pSubnetMask = '^' + m1 + m2 + m3 + m4 + '$'
    if re.search(p, ip, re.I):
        if re.search(pSubnetMask, ip, re.I):
            return True
        else:
            return False
    else:
        return False


# bmc username
def checkUsername(z):
    p = r'^[a-zA-Z]([a-zA-Z0-9_\-@]){0,15}$'
    if re.search(p, z, re.I):
        return True
    else:
        return False


# bmc password
def checkPassword(z):
    # 不多于16
    if len(z) == 0 or len(z) > 16:
        return False
    else:
        return True


# bmc time 2018-05-31T10:10+08:00
def checkBMCTime(bmctime):
    import time
    p = r"^[0-9]{4}\-[0-9]{2}\-[0-9]{2}T[0-9]{2}:[0-9]{2}(\+|\-)[0-9]{2}:[0-9]{2}$"
    if re.search(p, bmctime, re.I):
        if "+" in bmctime:
            data = bmctime.split("+")[0]
            zone = bmctime.split("+")[1]
            we = "+"
        else:
            zone = bmctime.split("-")[-1]
            data = bmctime.split("-" + zone)[0]
            we = "-"
        # check date
        try:
            struct_time = time.strptime(data, "%Y-%m-%dT%H:%M")
        except BaseException:
            return False
        # check zone
        hour = int(zone.split(":")[0])
        minitue = int(zone.split(":")[1])
        zoneMinutes = int(we + str(hour * 60 + minitue))
        if zoneMinutes < -720 or zoneMinutes > 840:
            return False
        return True
    else:
        return False


# bmc time 2018-05-31T10:10+08:00
def checkBMCZone(bmczone_raw):
    import time
    p = r"^\[(\+|\-)[0-9]{2}:[0-9]{2}\]$"
    if re.search(p, bmczone_raw, re.I):
        bmczone = bmczone_raw[1:-1]
        if "+" in bmczone:
            zone = bmczone.split("+")[1]
            we = "+"
        else:
            zone = bmczone.split("-")[1]
            we = "-"
        # check zone
        hour = int(zone.split(":")[0])
        minitue = int(zone.split(":")[1])
        zoneMinutes = int(we + str(hour * 60 + minitue))
        if zoneMinutes < -720 or zoneMinutes > 840:
            return 2
        return 0
    else:
        return 1


def checkSubnetPrefixLength(spl):
    try:
        spl_int = int(spl)
        if spl_int < 0 or spl_int > 128:
            return False
        return True
    except BaseException:
        return False


def checkIPv6(ip):
    # p = '^(([\da-fA-F]{1,4}):){7}([\da-fA-F]{1,4})$'
    p = r'^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:[0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){5}(:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|((:[0-9A-Fa-f]{1,4}){1,2})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|((:[0-9A-Fa-f]{1,4}){1,3})|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|((:[0-9A-Fa-f]{1,4}){1,4})|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|((:[0-9A-Fa-f]{1,4}){1,5})|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|((:[0-9A-Fa-f]{1,4}){1,6})|:))|(:(((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|((:[0-9A-Fa-f]{1,4}){1,7})|:)))$'
    if re.search(p, ip, re.I):
        return True
    else:
        return False


# bmc username
def checkM3Username(z):
    p = r'^[a-zA-Z0-9_]([a-zA-Z0-9_\-\.]){0,14}([a-zA-Z0-9_\-\.]|\$)$'
    if re.search(p, z, re.I):
        return True
    else:
        return False


# bmc password
def checkM3Password(z):
    # 不多于16
    p1 = '[a-zA-Z]'
    p2 = '[0-9]'
    p3 = r'\S'
    if len(z) < 8 or len(z) > 16:
        return 1
    else:
        if re.search(p1, z, re.I) and re.search(p2, z, re.I) and re.search(p3, z, re.I):
            return 0
        else:
            return 2


# IP 地址 ( IPv4 和 IPv6 格式)。
# - FQDN (全称域名) 格式
def checkIP46d(s):
    if s == "0.0.0.0":
        return False
    # ipv6
    ip6 = '^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}' \
          '|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))' \
          '|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d' \
          '|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})' \
          '|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))' \
          '|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d' \
          '|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})' \
          '|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))' \
          '|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d' \
          '|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})' \
          '|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))' \
          r'|:)))(%.+)?\s*$'
    if re.search(ip6, s, re.I):
        return True
    # ipv4
    ip4 = r'^((25[0-5]|2[0-4]\d|((1\d{2}|[1-9]?\d)))\.){3}(25[0-5]|2[0-4]\d|((1\d{2}|[1-9]?\d)))$'
    if re.search(ip4, s, re.I):
        return True
    # domain name contains \d A-Z a-z \.
    # only \d is not allowed
    dn = r'^([\da-zA-Z]+\.)*[\da-zA-Z]+\.[\da-zA-Z]+$'
    dnd = r'^([\d]+\.)*[\d]+\.[\d]+$'
    if re.search(dn, s, re.I) and not re.search(dnd, s, re.I):
        return True
    return False


def checkIndex(index):
    if index < 0 or index > 15:
        return False
    return True


def checkPrefix(prefix):
    if prefix < 0 or prefix > 128:
        return False
    return True


def checkDomainName(dm):
    p1 = r'\.'
    p2 = '[a-zA_Z]'
    if re.search(p1, dm, re.I) and re.search(p2, dm, re.I):
        return True
    else:
        return False


def checkHostName(hm):
    if len(hm) > 64 or len(hm) < 1:
        return False
    p = r'^[a-zA-Z0-9\_\-]+$'
    if re.search(p, hm, re.I):
        return True
    else:
        return False


def checkZone(z):
    p = r'^((\-?([0-9]|10|11|12))(\.5)?|12)$'
    if re.search(p, z, re.I):
        return True
    else:
        return False


def checkPass(password):
    if len(password) < 8 or len(password) > 16:
        return False
    return True


# check the legitimacy of engineId
def checkEngineId(engineId):
    if engineId == "":
        return True
    if len(engineId) < 10 or len(engineId) > 48:
        return False
    if len(engineId) % 2 != 0:
        return False
    s = re.search('[0-9a-fA-F]{10,48}', engineId, re.I)
    if s:
        return True
    return False


def checkEmail(email):
    p = r'^\w+@[a-z0-9]+\.[a-z]{2,4}$'
    if re.search(p, email, re.I):
        return True
    else:
        return False


def checkSMTPName(name):
    p = u'^[a-zA-Z][^\u4e00-\u9fa5\\\\,:; ]{3,64}$'
    # name = unicode(name, 'utf-8')
    if re.search(p, name, re.I):
        return True
    else:
        return False


def checkSMTPPassword(pw):
    p = u'^[^\u4e00-\u9fa5 ]{4,65}'
    # pw = unicode(pw, 'utf-8')
    if re.search(p, pw, re.I):
        return True
    else:
        return False


def checkID(id):
    if id < 2 or id > 4094:
        return False
    return True


def checkVP(p):
    if p < 1 or p > 7:
        return False
    return True


def checkFileSize(fs):
    if fs < 3 or fs > 65535:
        return False
    else:
        return True


def checkPort(p):
    if p < 0 or p > 65535:
        return False
    else:
        return True


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        try:
            import unicodedata
            unicodedata.numeric(s)
            return True
        except (TypeError, ValueError):
            return False


# createldisk
def check_arg(arg):
    if is_number(arg) is not True:
        print("the parameter must be integer")
        return None
    else:
        import string
        arg = string.atoi(arg)
        return arg


def checkFile(str):
    try:
        f = open(str)
        f.close()
        return True
    except IOError:
        return False


def checkBase(s):
    # 域名名称是一个64字母数字组成的字串。
    # 开头字符必须是字母。
    # 允许特殊字符如点(.)，逗号(,)，连字符(-)，下划线(_)，等于号(=)。
    # 范例: cn=manager,ou=login, dc=domain,dc=com
    dn = r'^[a-zA-Z][a-zA-Z\-_\.\,\=]{4,64}$'
    if re.search(dn, s, re.I):
        return True
    return False
