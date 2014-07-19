#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
VMWARE external inventory script
=================================

shamelessly copied from existing inventory scripts.

This script and it's ini can be used more than once,

i.e vmware.py/vmware_colo.ini vmware_idf.py/vmware_idf.ini
(script can be link)

so if you don't have clustered vcenter  but multiple esx machines or
just diff clusters you can have a inventory  per each and automatically
group hosts based on file name or specify a group in the ini.

You can also use <SCRIPT_NAME>_HOST|USER|PASSWORD environment variables
to override the ini.
'''

import os
import sys
import time
import ConfigParser
from psphere.client import Client
from psphere.managedobjects import HostSystem

try:
    import json
except ImportError:
    import simplejson as json


def save_cache(cache_item, data, config):
    ''' saves item to cache '''

    if config.has_option('cache', 'dir'):
        dpath = os.path.expanduser(config.get('cache', 'dir'))
        try:
            if not os.path.exists(dpath):
                os.makedirs(dpath)
            if os.path.isdir(dpath):
                cache = open('/'.join([dpath,cache_item]), 'w')
                cache.write(json.dumps(data))
                cache.close()
        except IOError, e:
            pass # not really sure what to do here


def get_cache(cache_item, config):
    ''' returns cached item  '''

    inv = {}
    if config.has_option('cache', 'dir'):
        dpath = os.path.expanduser(config.get('cache', 'dir'))
        try:
            cache = open('/'.join([dpath,cache_item]), 'r')
            inv = json.loads(cache.read())
            cache.close()
        except IOError, e:
            pass # not really sure what to do here

    return inv

def cache_available(cache_item, config):
    ''' checks if we have a 'fresh' cache available for item requested '''

    if config.has_option('cache', 'dir'):
        dpath = os.path.expanduser(config.get('cache', 'dir'))

        try:
            existing = os.stat('/'.join([dpath,cache_item]))
        except:
            # cache doesn't exist or isn't accessible
            return False

        if config.has_option('cache', 'max_age'):
            maxage = config.get('cache', 'max_age')
            fileage = int( time.time() - existing.st_mtime )
            if (maxage > fileage):
                return True

    return False

def get_host_info(host):
    ''' Get variables about a specific host '''

    hostinfo = {
        'vmware_name' : host.name,
    }
    for k in host.capability.__dict__.keys():
        if k.startswith('_'):
           continue
        try:
            hostinfo['vmware_' + k] = str(host.capability[k])
        except:
           continue

    return hostinfo


def get_inventory(client, config):
    ''' Reads the inventory from cache or vmware api '''

    inv = {}

    if cache_available('inventory', config):
        inv = get_cache('inventory',config)
    elif client:
        inv= { 'all': {'hosts': []}, '_meta': { 'hostvars': {} } }
        default_group = os.path.basename(sys.argv[0]).rstrip('.py')

        if config.has_option('defaults', 'guests_only'):
            guests_only = config.get('defaults', 'guests_only')
        else:
            guests_only = True

        if not guests_only:
            if config.has_option('defaults','hw_group'):
                hw_group = config.get('defaults','hw_group')
            else:
                hw_group = default_group + '_hw'
            inv[hw_group] = []

        if config.has_option('defaults','vm_group'):
            vm_group = config.get('defaults','vm_group')
        else:
            vm_group = default_group + '_vm'
        inv[vm_group] = []

        # Loop through physical hosts:
        hosts = HostSystem.all(client)
        for host in hosts:
            if not guests_only:
                inv['all']['hosts'].append(host.name)
                inv[hw_group].append(host.name)
                inv['_meta']['hostvars'][host.name] = get_host_info(host)
                save_cache(vm.name, inv['_meta']['hostvars'][host.name], config)

            for vm in host.vm:
                inv['all']['hosts'].append(vm.name)
                inv[vm_group].append(vm.name)
                inv['_meta']['hostvars'][vm.name] = get_host_info(vm)
                save_cache(vm.name, inv['_meta']['hostvars'][vm.name], config)

        save_cache('inventory', inv, config)

    return json.dumps(inv)

def get_single_host(client, config, hostname):

    inv = {}
    if cache_available(hostname, config):
        inv = get_cache(hostname,config)
    elif client:
        hosts = HostSystem.all(client) #TODO: figure out single host getter
        for host in hosts:
            if hostname == host.name:
                inv = get_host_info(host)
                break
            for vm in host.vm:
                if hostname == vm.name:
                    inv = get_host_info(vm)
                    break
        save_cache(hostname,inv,config)

    return json.dumps(inv)

if __name__ == '__main__':

    inventory = {}
    hostname = None

    if len(sys.argv) > 1:
        if sys.argv[1] == "--host":
            hostname = sys.argv[2]

    # Read config
    config = ConfigParser.SafeConfigParser()
    me = os.path.abspath(sys.argv[0]).rstrip('.py')
    for configfilename in [me + '.ini', 'vmware.ini']:
        if os.path.exists(configfilename):
            config.read(configfilename)
            break

    mename = os.path.basename(me).upper()
    host =  os.getenv('VMWARE_' + mename + '_HOST',os.getenv('VMWARE_HOST', config.get('auth','host')))
    user = os.getenv('VMWARE_' + mename + '_USER', os.getenv('VMWARE_USER', config.get('auth','user')))
    password = os.getenv('VMWARE_' + mename + '_PASSWORD',os.getenv('VMWARE_PASSWORD', config.get('auth','password')))

    try:
        client =  Client( host,user,password )
    except Exception, e:
        client = None
        #print >> STDERR "Unable to login (only cache avilable): %s", str(e)

    # Actually do the work
    if hostname is None:
        inventory = get_inventory(client, config)
    else:
        inventory = get_single_host(client, config, hostname)

    # Return to ansible
    print inventory
