import re
import pprint

data = '''interface Ethernet1/1
interface Ethernet1/2
  ip access-group acl01 in
interface Ethernet1/3
  ip access-group acl01 out
interface Ethernet1/4
  ip access-group acl01 out
  ip port access-group acl01 in
interface Ethernet1/5
'''
data = data.split('interface')
for i in range(len(data)):
    if not re.search('ip(v6)?( port)? (access-group|traffic-filter)', data[i]):
        data[i] = ''

data = list(filter(None, data))


for config in data:
    # config = data[0]
    conf = {}
    conf.update({'name': config.split('\n')[0], 'access_groups': []})
    v4 = {'afi': 'ipv4', 'acls': []}
    v6 = {'afi': 'ipv6', 'acls': []}
    for c in config.split('\n')[1:]:
        if c:
            acl4 = re.search('ip( port)? access-group (\w*) (\w*)', c)
            acl6 = re.search('ipv6( port)? traffic-filter (\w*) (\w*)', c)
            if acl4:
                acl = {'name': acl4.group(2), 'direction': acl4.group(3)}
                if acl4.group(1):
                    acl.update({'port': True})
                v4['acls'].append(acl)
            elif acl6:
                acl = {'name': acl6.group(1), 'direction': acl6.group(2)}
                if acl6.group(1):
                    acl.update({'port': True})
                v6['acls'].append(acl)

    if len(v4['acls']) > 0:
        conf['access_groups'].append(v4)
    if len(v6['acls']) > 0:
        conf['access_groups'].append(v6)

# print(v4, v6)
    pprint.pprint(conf)
