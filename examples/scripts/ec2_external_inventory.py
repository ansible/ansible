#!/usr/bin/python -tt

"""
EC2 external inventory script
=================================

NOTE: This script assumes Ansible is being executed where the environment
variables needed for Boto have been set:
    export AWS_ACCESS_KEY_ID=''
    export AWS_SECRET_ACCESS_KEY=''
For more details, see: http://docs.pythonboto.org/en/latest/boto_config_tut.html
"""

import os
import argparse
import re
from time import time
from boto import ec2

try:
    import json
except ImportError:
    import simplejson as json


### Settings

# I can see other uses where this variable is something else, say if someone
# is running Ansible within EC2, these might be internal IP addresses
destinationVariable = "public_dns_name"
vpcDestinationVariable = "ip_address"

cachePath = "/tmp/ansible-ec2.cache"
cacheMaxAge = 300  # seconds


# Command line argument processing
parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on EC2')
parser.add_argument('--list', action='store_true', default=True, 
                   help='list instances (default: True)')
parser.add_argument('--refresh-cache', action='store_true', default=False, 
                   help='refreshes the cache by making API requests to EC2 (default: False, use cache)')
args = parser.parse_args()



# Instance IDs, tags, security groups, regions, availability zones
inventory = {}


def doApiCall(regionInfo):
    # Loop over all regions
    region = regionInfo.name
    conn = ec2.connect_to_region(region)
    
    inventory[region] = []
    
    reservations = conn.get_all_instances()
    for reservation in reservations:
        for instance in reservation.instances:
            if instance.state == 'terminated':
                continue
            
            # Select the best destination address
            if instance.subnet_id:
                dest = getattr(instance, vpcDestinationVariable)
            else:
                dest =  getattr(instance, destinationVariable)
    
            if dest == None:
                # Skip instances we cannot address (e.g. VPC private subnet)
                continue
    
            # Group by instance ID (always a group of 1)
            inventory[instance.id] = [dest]
            
            # Group by region
            inventory[region].append(dest);
                            
            # Group by availability zone
            if instance.placement in inventory:
                inventory[instance.placement].append(dest);
            else:
                inventory[instance.placement] = [dest]
            
            # Group by security group
            for group in instance.groups:
                key = toSafe("security-group_" + group.name)
                if key in inventory:
                    inventory[key].append(dest);
                else:
                    inventory[key] = [dest]
                    
            # Group by tag keys
            for k, v in instance.tags.iteritems():
                key = toSafe("tag_" + k + "=" + v)
                if key in inventory:
                    inventory[key].append(dest);
                else:
                    inventory[key] = [dest]     
                   
    return formatInventory(True)

def getInventoryFromCache():
    cache = open(cachePath, 'r')
    jsonInventory = cache.read()
    return jsonInventory

def getInventoryFromApiUpdateCache():
    for region in ec2.regions():
        doApiCall(region)
    
    jsonInventory = formatInventory(True)
    cache = open(cachePath, 'w')
    cache.write(jsonInventory)
    cache.close()
    return jsonInventory

def toSafe(word):
    return re.sub("[^A-Za-z0-9\-]", "_", word)
    
def formatInventory(pretty=False):
    if pretty:
        return json.dumps(inventory, sort_keys=True, indent=2)
    else:
        return json.dumps(inventory)
    
    
# Do work here
if args.refresh_cache:
    jsonInventory = getInventoryFromApiUpdateCache()
    
elif os.path.isfile(cachePath):
    modTime = os.path.getmtime(cachePath)
    currentTime = time()
    if (modTime + cacheMaxAge) > currentTime:
        # Use cache
        jsonInventory = getInventoryFromCache()
    else:
        jsonInventory = getInventoryFromApiUpdateCache()
        
else:
    jsonInventory = getInventoryFromApiUpdateCache()
    


print jsonInventory

