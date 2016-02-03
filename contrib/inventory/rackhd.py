#!/usr/bin/python
import json
import requests
import os
import argparse
import types

RACKHD_URL = 'http://localhost:8080'

class RackhdInventory(object):
    def __init__(self, nodeids):
        self._inventory = {}
        for nodeid in nodeids:
            self._load_inventory_data(nodeid)
        output = '{\n'
        for nodeid,info in self._inventory.iteritems():
            output += self._format_output(nodeid, info)
            output += ',\n'
        output = output[:-2]
        output += '}\n'
        print (output)

    def _load_inventory_data(self, nodeid):
        info = {}
        info['ohai'] = RACKHD_URL + '/api/common/nodes/{0}/catalogs/ohai'.format(nodeid )
        info['lookup'] = RACKHD_URL + '/api/common/lookups/?q={0}'.format(nodeid)

        results = {}
        for key,url in info.iteritems():
            r = requests.get( url, verify=False)
            results[key] = r.text

        self._inventory[nodeid] = results

    def _format_output(self, nodeid, info):
        output = ''
        try:
            node_info = json.loads(info['lookup'])
            ipaddress = ''
            if len(node_info) > 0:
                ipaddress = node_info[0]["ipAddress"]
            output += '  "' + nodeid + '" : {\n'
            output += '    "hosts": [ "' + ipaddress + '" ],\n'
            output += '    "vars" : {\n'
            for key,result in info.iteritems():
                output += '      "' + key + '": ' + json.dumps(json.loads(result), sort_keys=True, indent=2) + ',\n'
            output += '      "ansible_ssh_user": "renasar"\n'
            output += '    }\n'
            output += '  }\n'
        except KeyError:
            pass
        return output

try:
    #check if rackhd url(ie:10.1.1.45:8080) is specified in the environment
    RACKHD_URL = 'http://' + str(os.environ['RACKHD_URL'])
except:
    #use default values
    pass

# Use the nodeid specified in the environment to limit the data returned
# or return data for all available nodes
nodeids = []
try:
    nodeids += os.environ['nodeid'].split(',')
except KeyError:
    url = RACKHD_URL + '/api/common/nodes'
    r = requests.get( url, verify=False)
    data = json.loads(r.text)
    for entry in data:
        if entry['type'] == 'compute':
            nodeids.append(entry['id'])
RackhdInventory(nodeids)
