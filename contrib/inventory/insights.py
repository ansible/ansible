#!/usr/bin/env python

'''
This script requires access to the RedHat insights SaaS platform API.
https://access.redhat.com/insights
The script will create Ansible json inventory based on the systems present
within a users insights portal.

This script bridges the gap between insights generated playbooks and Ansible by generating 
dynamic inventory.

Requirements for use with Ansible Tower :
 - Create a custom Ansible Tower credential that will a login and password
   credential and export as environment variables for use within this script.
 - Paste this script into Ansible Tower - Settings->Inventory Scripts->Add
 - Combine both the credential and dynamic inventory scripts as part of an inventory
   definition

Example Ansible Tower Custom Credential type.
-------
INPUT CONFIGURATION
fields:
  - type: string
    id: login
    label: Username
  - secret: true
    type: string
    id: password
    label: Password


INJECTOR CONFIGURATION
env:
  INSIGHTS_PASSWORD: '{{password}}'
  INSIGHTS_USERNAME: '{{login}}'


Requirements for use with Ansible Core :
 - Simply export the shell variables prior to running
   %export INSIGHTS_PASSWORD=password;
   %export INSIGHTS_USERNAME=my-insights-username
   %ansible-playbook -i ./insightsInventory.py playbook.yaml

Credits / Questions:
Richard Hailstone : "rhailsto @ redhat . com"
'''

import json
import os
import urllib2
import urllib
import base64
import sys
import ssl
import re
import argparse
import ConfigParser
import time

from six import iteritems


class error_colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


class InsightsInventory(object):

    def return_meta(self):
      return {
        'hostvars': {
         }
      }

    def base_inventory(self):
      return {
          'servergroup': {
              'hosts': [],
               'vars': {
                }
          },
          '_meta': {
              'hostvars': {
              }
          }
      }

    def __init__(self):
        parser = argparse.ArgumentParser(description='Insights Inventory', epilog='Epilogue')
        parser.add_argument( '-l', '--list', action='store_true', help='gives out a list')
        args = parser.parse_args()
        insights_url = 'access.redhat.com'
        insights_uri = '/r/insights/v2/systems'
        VERBOSE = False
        self.login = os.environ.get("INSIGHTS_USERNAME")
        self.password = os.environ.get("INSIGHTS_PASSWORD")
        groups={}
        # This is the group name that will show up in the Tower inventory.
        # playbooks hosts section should use 'insights'
        # The group definitions within insights will be the format in the future and
        # wont need to statically define it here..

        section_name = 'insights'

        if section_name not in groups:
          groups[section_name] = set()
        
        systemdata = []

        try:
          url = "https://" + insights_url + insights_uri
          request = urllib2.Request(url)
          if VERBOSE:
             print "%s" % ('=') * 80
             print "[%sVERBOSE%s] Connecting to -> %s " % (error_colors.OKGREEN, error_colors.ENDC, url)
          base64string = base64.encodestring('%s:%s' % (self.login, self.password)).strip()
          request.add_header("Authorization", "Basic %s" % base64string)
          request.add_header("Content-Type", "application/json")
          requestresult = urllib2.urlopen(request)
          jsonresult = json.loads(requestresult.read().decode('utf-8'))
          systemdata += jsonresult['resources']

        except urllib2.URLError, e:
          print "Error: cannot connect to the API: %s" % (e)
          print "Check your URL & try to login using the same user/pass via the WebUI and check the error!"
          sys.exit(1)
        except Exception, e:
          print "FATAL Error - %s" % (e)
          sys.exit(2)

        inv_exclude = re.compile("some.example.com|other.example.com")

        # you can set a value in the re.match below with a hostname pattern in insights. 
        # Useful for subsets of hosts and not purely everything.

        for system in systemdata:
          m = re.match("(^.*)",system["hostname"])
          if inv_exclude.search(system["hostname"]):
            continue
          if m and system['isCheckingIn'] == True:
            groups[section_name].add(system["hostname"])

        final = dict([(k, list(s)) for k, s in iteritems(groups)])

        # _meta tag prevents Ansible from calling this script for each server with --host
        final["_meta"] = self.return_meta()
        print(json.dumps(final))
        sys.exit(0)

if __name__ == '__main__':
    InsightsInventory()
