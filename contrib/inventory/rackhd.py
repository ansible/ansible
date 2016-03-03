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
        for nodeid,info in self._inventory.iteritems():
            print(json.dumps(self._format_output(nodeid, info)))

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
        try:
            node_info = json.loads(info['lookup'])
            ipaddress = ''
            if len(node_info) > 0:
                ipaddress = node_info[0]['ipAddress']
            output = {nodeid:{ 'hosts':[ipaddress],'vars':{}}}
            for key,result in info.iteritems():
                output[nodeid]['vars'][key] = json.loads(result)
            output[nodeid]['vars']['ansible_ssh_user'] = 'monorail'
        except KeyError:
            pass
        return output


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host')
    parser.add_argument('--list', action='store_true')
    return parser.parse_args()

try:
    #check if rackhd url(ie:10.1.1.45:8080) is specified in the environment
    RACKHD_URL = 'http://' + str(os.environ['RACKHD_URL'])
except:
    #use default values
    pass

# Use the nodeid specified in the environment to limit the data returned
# or return data for all available nodes
nodeids = []

if (parse_args().host):
    try:
        nodeids += parse_args().host.split(',')
        RackhdInventory(nodeids)
    except:
        pass
if (parse_args().list):
    try:
        url = RACKHD_URL + '/api/common/nodes'
        r = requests.get( url, verify=False)
        data = json.loads(r.text)
        for entry in data:
            if entry['type'] == 'compute':
                nodeids.append(entry['id'])
        RackhdInventory(nodeids)
    except:
        pass
