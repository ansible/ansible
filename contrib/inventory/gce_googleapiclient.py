#!/usr/bin/env python
"""Usage provided by docoptcfg using the global DOCOPT_USAGE constant"""

from __future__ import print_function

from os.path import basename
from sys import argv, version_info

import collections
import json
import logging as log

import threading

if version_info < (3, 0):
    import Queue as queue
else:
    import queue


from docoptcfg import DocoptcfgFileError
from docoptcfg import docoptcfg

from googleapiclient import discovery

from googleapiclient.errors import HttpError

from oauth2client.client import GoogleCredentials


ENV_PREFIX = 'GCE_'
DEFAULT_API_VERSION = 'v1'

DOCOPT_USAGE = """
Google Cloud Engine Dynamic Inventory
=====================================

Before using:

- Authentication: this script uses the same authentication as
                  gcloud command line. So, set it up before.
- Dependencies: it depends mainly on google-api-python-client
                and docoptcfg. So:

$ pip install google-api-python-client docoptcfg

Usage:
    {script_name} (--project=PROJECT... | --all-projects --billing-account=ACCOUNT_NAME)
                  [--zone=ZONE...|--all-zones]
                  [--max-threads=NUM_THREADS]
                  [options]


Options:
    --billing-account ACCOUNT_NAME --billing-account=ACCOUNT_NAME  Billing account name
    --all-projects                                                 Looks for every avail project for billing account
    --all-zones                                                    Looks for each zone
    -a API_VERSION --api-version=API_VERSION                       The API version used to connect to GCE [default: {default_api_version}]
    -c CONFIG_FILE --config=CONFIG_FILE                            Path to the config file (see docoptcfg docs) [default: ./gce_googleapiclient.ini]
    -l --list                                                      List all hosts (needed by Ansible, but actually doesn't do anything)
    -t --num-threads NUM_THREADS                                   Enable multi-threading, set it to NUM_THREADS [default: 4]
    -p PROJECT --project=PROJECT                                   The GCE project where you want to get the inventory
    -z ZONE --zone=ZONE                                            The GCE zone where you ant to get the inventory
    -h --help                                                      This message.

All the parameters can also be set as environment variables
using the 'GCE_' prefix (i.e. {envvar_prefix}API_VERSION=beta).
""".format(script_name=basename(argv[0]), envvar_prefix=ENV_PREFIX, default_api_version=DEFAULT_API_VERSION)


def get_all_billing_projects(billing_account_name, api_version=DEFAULT_API_VERSION):
    project_ids = []

    credentials = GoogleCredentials.get_application_default()

    service = discovery.build('cloudbilling',
                              version=api_version,
                              credentials=credentials)
    # pylint: disable=no-member
    request = service.billingAccounts().projects(). \
        list(name=billing_account_name)

    while request is not None:
        response = request.execute()

        # pylint: disable=no-member
        request = service.billingAccounts().projects(). \
            list_next(previous_request=request, previous_response=response)

        for project_billing_info in response['projectBillingInfo']:
            if project_billing_info['billingEnabled']:
                project_ids.append(project_billing_info['projectId'])

    return project_ids


def get_all_zones_in_project(projects_queue_in, projects_zones_queue_out, api_version=DEFAULT_API_VERSION):

    try:
        while not projects_queue_in.empty():
            project = projects_queue_in.get(block=False)
            log.info('Retrieving list of zones of project: %s', project)

            try:
                credentials = GoogleCredentials.get_application_default()
                service = discovery.build('compute', api_version, credentials=credentials)

                request = service.zones().list(project=project)

                while request is not None:
                    response = request.execute()

                    for zone in response['items']:
                        projects_zones_queue_out.put((project, zone['name']))

                    request = service.zones().list_next(previous_request=request,
                                                        previous_response=response)

            except HttpError as exception:
                log.warn('Could not retrieve list of zones of project: %s', project)
                log.warn(exception)

    except queue.Empty:
        pass


def get_instances(projects_zones_queue_in, instances_queue_out, api_version=DEFAULT_API_VERSION):
    try:
        while not projects_zones_queue_in.empty():
            project, zone = projects_zones_queue_in.get(block=False)
            log.info('Retrieving list of instances from project/zone: %s/%s', project, zone)
            try:

                credentials = GoogleCredentials.get_application_default()
                service = discovery.build('compute', api_version, credentials=credentials)
                # pylint: disable=no-member
                request = service.instances().list(project=project, zone=zone)

                while request is not None:
                    response = request.execute()

                    if 'items' in response:
                        for instance in response['items']:
                            instances_queue_out.put(instance)

                    request = service.instances().list_next(previous_request=request,
                                                            previous_response=response)

            except HttpError as exception:
                log.warn('Could not retrieve list of instances of project/zone: %s/%s', project, zone)
                log.warn(str(exception))

        # pylint: disable=no-member

    except queue.Empty:
        pass


def get_hostvars(instance):
    hostvars = {
        'gce_name': instance['name'],
        'gce_id': instance['id'],
        'gce_status': instance['status']
    }

    if instance['networkInterfaces'][0]['networkIP']:
        hostvars['ansible_ssh_host'] = instance['networkInterfaces'][0]['networkIP']

    if 'labels' in instance:
        hostvars['gce_labels'] = instance['labels']

    hostvars['gce_metadata'] = {}
    for md in instance['metadata'].get('items', []):
        hostvars['gce_metadata'][md['key']] = md['value']

    if 'items' in instance['tags']:
        hostvars['gce_tags'] = instance['tags']['items']

    hostvars['gce_machine_type'] = instance['machineType'].split('/')[-1]

    hostvars['gce_project'] = instance['selfLink'].split('/')[6]

    hostvars['gce_zone'] = instance['zone'].split('/')[-1]

    hostvars['gce_network'] = instance['networkInterfaces'][0]['network'].split('/')[-1]

    for interface in instance['networkInterfaces']:

        hostvars['gce_subnetwork'] = interface['subnetwork'].split('/')[-1]

        access_configs = interface.get('accessConfigs', [])

        for access_config in access_configs:
            hostvars['gce_public_ip'] = access_config.get('natIP', None)
            break  # get only the first access config

        hostvars['gce_private_ip'] = interface['networkIP']

        break  # get only the first interface

    return hostvars


def get_inventory(instances):
    inventory = collections.defaultdict(list)
    inventory['_meta'] = collections.defaultdict(
        lambda: collections.defaultdict(dict))

    for instance in instances:
        if instance['status'] in ['RUNNING', 'STAGING']:
            inventory['_meta']['hostvars'][instance['name']] \
                = get_hostvars(instance)

            # populate the 'all' group with all hosts found
            inventory['all'].append(instance['name'])

            # create a group for every tag prefixed by 'tag_' and populate
            # accordingly
            for tag in instance['tags'].get('items', []):
                inventory['tag_{}'.format(tag)].append(instance['name'])

            project = instance['selfLink'].split('/')[6]
            inventory['project_{}'.format(project)].append(instance['name'])

            # zone groups are not prefixed to be compatible with the previous gce.py
            zone = instance['zone'].split('/')[-1]
            inventory[zone].append(instance['name'])

            network = instance['networkInterfaces'][0]['network'].split('/')[-1]
            inventory['network_{}'.format(network)].append(instance['name'])

            inventory['status_{}'.format(instance['status'].lower())].append(instance['name'])

            # instance type groups are not prefixed to be compatible with the previous gce.py
            instance_type = instance['machineType'].split('/')[-1]
            inventory[instance_type].append(instance['name'])

    return inventory


def main(args):
    project_list = args['--project']
    all_projects = args['--all-projects']
    all_zones = args['--all-zones']
    zone_list = args['--zone']
    api_version = args['--api-version']
    billing_account_name = args['--billing-account']
    num_threads = int(args['--num-threads'])

    if num_threads < 1:
        num_threads = 1

    instances = []

    if all_projects and billing_account_name:
        project_list = get_all_billing_projects(billing_account_name)

    projects_queue = queue.Queue()
    projects_zones_queue = queue.Queue()
    instances_queue = queue.Queue()

    for project in project_list:
        projects_queue.put(project)

    if not projects_queue.empty():
        log.info('Spawning {} threads to get zone list on each project'.format(num_threads))
        threads = []

        if all_zones:
            for _ in range(0, num_threads):
                project_thread = threading.Thread(target=get_all_zones_in_project,
                                                  args=(projects_queue,
                                                        projects_zones_queue,
                                                        api_version))

                threads.append(project_thread)
                project_thread.start()

            for project_thread in threads:
                project_thread.join()
        else:
            while not projects_queue.empty():
                project = projects_queue.get()
                for zone in zone_list:
                    projects_zones_queue.put((project, zone))

    if not projects_zones_queue.empty():
        threads = []
        for _ in range(0, num_threads):
            zone_thread = threading.Thread(target=get_instances,
                                           args=(projects_zones_queue,
                                                 instances_queue,
                                                 api_version))
            threads.append(zone_thread)
            zone_thread.start()

        for zone_thread in threads:
            zone_thread.join()

        while not instances_queue.empty():
            instances.append(instances_queue.get())

    inventory_json = get_inventory(instances)
    print(json.dumps(inventory_json,
                     sort_keys=True,
                     indent=2))


if __name__ == "__main__":
    log.basicConfig(filename='gce_googleapiclient.log')

    try:
        ARGS = docoptcfg(DOCOPT_USAGE,
                         config_option='--config',
                         env_prefix=ENV_PREFIX)
    except DocoptcfgFileError as exc:
        log.info('Failed reading: %s', str(exc))
        ARGS = docoptcfg(DOCOPT_USAGE, env_prefix=ENV_PREFIX)

    main(ARGS)
