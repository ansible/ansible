#!/usr/bin/env python

'''
nsot
====

Ansible Dynamic Inventory to pull hosts from NSoT, a flexible CMDB by Dropbox

Features
--------

* Define host groups in form of NSoT device attribute criteria

* All parameters defined by the spec as of 2015-09-05 are supported.

  + ``--list``: Returns JSON hash of host groups -> hosts and top-level
    ``_meta`` -> ``hostvars`` which correspond to all device attributes.

    Group vars can be specified in the YAML configuration, noted below.

  + ``--host <hostname>``: Returns JSON hash where every item is a device
    attribute.

* In addition to all attributes assigned to resource being returned, script
  will also append ``site_id`` and ``id`` as facts to utilize.


Confguration
------------

Since it'd be annoying and failure prone to guess where you're configuration
file is, use ``NSOT_INVENTORY_CONFIG`` to specify the path to it.

This file should adhere to the YAML spec. All top-level variable must be
desired Ansible group-name hashed with single 'query' item to define the NSoT
attribute query.

Queries follow the normal NSoT query syntax, `shown here`_

.. _shown here: https://github.com/dropbox/pynsot#set-queries

.. code:: yaml

   routers:
     query: 'deviceType=ROUTER'
     vars:
       a: b
       c: d

   juniper_fw:
     query: 'deviceType=FIREWALL manufacturer=JUNIPER'

   not_f10:
     query: '-manufacturer=FORCE10'

The inventory will automatically use your ``.pynsotrc`` like normal pynsot from
cli would, so make sure that's configured appropriately.

.. note::

    Attributes I'm showing above are influenced from ones that the Trigger
    project likes. As is the spirit of NSoT, use whichever attributes work best
    for your workflow.

If config file is blank or absent, the following default groups will be
created:

* ``routers``: deviceType=ROUTER
* ``switches``: deviceType=SWITCH
* ``firewalls``: deviceType=FIREWALL

These are likely not useful for everyone so please use the configuration. :)

.. note::

    By default, resources will only be returned for what your default
    site is set for in your ``~/.pynsotrc``.

    If you want to specify, add an extra key under the group for ``site: n``.

Output Examples
---------------

Here are some examples shown from just calling the command directly::

   $ NSOT_INVENTORY_CONFIG=$PWD/test.yaml ansible_nsot --list | jq '.'
   {
     "routers": {
       "hosts": [
         "test1.example.com"
       ],
       "vars": {
         "cool_level": "very",
         "group": "routers"
       }
     },
     "firewalls": {
       "hosts": [
         "test2.example.com"
       ],
       "vars": {
         "cool_level": "enough",
         "group": "firewalls"
       }
     },
     "_meta": {
       "hostvars": {
         "test2.example.com": {
           "make": "SRX",
           "site_id": 1,
           "id": 108
         },
         "test1.example.com": {
           "make": "MX80",
           "site_id": 1,
           "id": 107
         }
       }
     },
     "rtr_and_fw": {
       "hosts": [
         "test1.example.com",
         "test2.example.com"
       ],
       "vars": {}
     }
   }


   $ NSOT_INVENTORY_CONFIG=$PWD/test.yaml ansible_nsot --host test1 | jq '.'
   {
      "make": "MX80",
      "site_id": 1,
      "id": 107
   }

'''

from __future__ import print_function
import sys
import os
import pkg_resources
import argparse
import json
import yaml
from textwrap import dedent
from pynsot.client import get_api_client
from pynsot.app import HttpServerError
from click.exceptions import UsageError

from six import string_types


def warning(*objs):
    print("WARNING: ", *objs, file=sys.stderr)


class NSoTInventory(object):
    '''NSoT Client object for gather inventory'''

    def __init__(self):
        self.config = dict()
        config_env = os.environ.get('NSOT_INVENTORY_CONFIG')
        if config_env:
            try:
                config_file = os.path.abspath(config_env)
            except IOError:  # If file non-existent, use default config
                self._config_default()
            except Exception as e:
                sys.exit('%s\n' % e)

            with open(config_file) as f:
                try:
                    self.config.update(yaml.safe_load(f))
                except TypeError:  # If empty file, use default config
                    warning('Empty config file')
                    self._config_default()
                except Exception as e:
                    sys.exit('%s\n' % e)
        else:  # Use defaults if env var missing
            self._config_default()
        self.groups = self.config.keys()
        self.client = get_api_client()
        self._meta = {'hostvars': dict()}

    def _config_default(self):
        default_yaml = '''
        ---
        routers:
          query: deviceType=ROUTER
        switches:
          query: deviceType=SWITCH
        firewalls:
          query: deviceType=FIREWALL
        '''
        self.config = yaml.safe_load(dedent(default_yaml))

    def do_list(self):
        '''Direct callback for when ``--list`` is provided

        Relies on the configuration generated from init to run
        _inventory_group()
        '''
        inventory = dict()
        for group, contents in self.config.items():
            group_response = self._inventory_group(group, contents)
            inventory.update(group_response)
        inventory.update({'_meta': self._meta})
        return json.dumps(inventory)

    def do_host(self, host):
        return json.dumps(self._hostvars(host))

    def _hostvars(self, host):
        '''Return dictionary of all device attributes

        Depending on number of devices in NSoT, could be rather slow since this
        has to request every device resource to filter through
        '''
        device = [i for i in self.client.devices.get()
                  if host in i['hostname']][0]
        attributes = device['attributes']
        attributes.update({'site_id': device['site_id'], 'id': device['id']})
        return attributes

    def _inventory_group(self, group, contents):
        '''Takes a group and returns inventory for it as dict

        :param group: Group name
        :type group: str
        :param contents: The contents of the group's YAML config
        :type contents: dict

        contents param should look like::

            {
              'query': 'xx',
              'vars':
                  'a': 'b'
            }

        Will return something like::

            { group: {
                hosts: [],
                vars: {},
            }
        '''
        query = contents.get('query')
        hostvars = contents.get('vars', dict())
        site = contents.get('site', dict())
        obj = {group: dict()}
        obj[group]['hosts'] = []
        obj[group]['vars'] = hostvars
        try:
            assert isinstance(query, string_types)
        except:
            sys.exit('ERR: Group queries must be a single string\n'
                     '  Group: %s\n'
                     '  Query: %s\n' % (group, query)
                     )
        try:
            if site:
                site = self.client.sites(site)
                devices = site.devices.query.get(query=query)
            else:
                devices = self.client.devices.query.get(query=query)
        except HttpServerError as e:
            if '500' in str(e.response):
                _site = 'Correct site id?'
                _attr = 'Queried attributes actually exist?'
                questions = _site + '\n' + _attr
                sys.exit('ERR: 500 from server.\n%s' % questions)
            else:
                raise
        except UsageError:
            sys.exit('ERR: Could not connect to server. Running?')

        # Would do a list comprehension here, but would like to save code/time
        # and also acquire attributes in this step
        for host in devices:
            # Iterate through each device that matches query, assign hostname
            # to the group's hosts array and then use this single iteration as
            # a chance to update self._meta which will be used in the final
            # return
            hostname = host['hostname']
            obj[group]['hosts'].append(hostname)
            attributes = host['attributes']
            attributes.update({'site_id': host['site_id'], 'id': host['id']})
            self._meta['hostvars'].update({hostname: attributes})

        return obj


def parse_args():
    desc = __doc__.splitlines()[4]  # Just to avoid being redundant

    # Establish parser with options and error out if no action provided
    parser = argparse.ArgumentParser(
        description=desc,
        conflict_handler='resolve',
    )

    # Arguments
    #
    # Currently accepting (--list | -l) and (--host | -h)
    # These must not be allowed together
    parser.add_argument(
        '--list', '-l',
        help='Print JSON object containing hosts to STDOUT',
        action='store_true',
        dest='list_',  # Avoiding syntax highlighting for list
    )

    parser.add_argument(
        '--host', '-h',
        help='Print JSON object containing hostvars for <host>',
        action='store',
    )
    args = parser.parse_args()

    if not args.list_ and not args.host:  # Require at least one option
        parser.exit(status=1, message='No action requested')

    if args.list_ and args.host:  # Do not allow multiple options
        parser.exit(status=1, message='Too many actions requested')

    return args


def main():
    '''Set up argument handling and callback routing'''
    args = parse_args()
    client = NSoTInventory()

    # Callback condition
    if args.list_:
        print(client.do_list())
    elif args.host:
        print(client.do_host(args.host))

if __name__ == '__main__':
    main()
