#!/usr/bin/env python
"""
Google Cloud Engine Dynamic Inventory
=====================================

Before using:

- Authentication: this script uses the same authentication as gcloud command
  line. So, set it up before according to:
        https://cloud.google.com/ml-engine/docs/quickstarts/command-line

- Dependencies: it depends on google-api-python-client and docoptcfg. To
  install them, run:
        $ pip install google-api-python-client docoptcfg

All parameters can be set in the following 3 different ways (in the order of
precedence, least to higher):

1. gce_googleapiclient.ini file:
    Check included gce_googleapiclient.ini on how to use it.
    The config file name can be overridden by using --config command line
    parameter or GCE_CONFIG environment variable.

2. Environment variables (prefixed by 'GCE_'):
    The variables needs to be set with the same names as the parameters, but
    with in UPPERCASE and underscore (_) instead of dashes (-)
    Ex: to set --billing-account using environment variables you'd need to
        create one called GCE_BILLING_ACCOUNT

3. Command line arguments:

Usage:
    gce_googleapiclient.py [--project=PROJECT]... [--zone=ZONE]...
        [--billing-account=ACCOUNT_NAME] [--config=CONFIG_FILE]
        [--num-threads=NUM_THREADS] [--timeout=TIMEOUT]
        [options]

Arguments:
    -b ACCOUNT_NAME --billing-account=ACCOUNT_NAME  The billing account associated with the projects you want to get
                                                information. It is only needed to get the list of the projects
                                                (when --project parameter isn' set)
    -c CONFIG_FILE --config=CONFIG_FILE         Path to the config file (see docoptcfg docs) [default: ./gce_googleapiclient.ini]
    -p PROJECT --project PROJECT                Google Cloud projects to search for instances
    -t NUM_THREADS --num-threads=NUM_THREADS    Enable multi-threading, set it to NUM_THREADS [default: 4]
    -z ZONE --zone ZONE                         Google Cloud zones to search for instances
    --timeout TIMEOUT                           Length of timeout in seconds for worker threads [default: 3600]

Options:
    -d --debug                                  Set debugging level to DEBUG on log file
    -h --help                                   Prints the application help
    -l --list                                   Needed by Ansible, but actually doesn't change anything

Setting multiple values parameters:
    Some parameters can have multiple values (ZONE and PROJECT) and to set them
    use:

1. Command line:
    $ ./gce_googleapiclient.py (...) --zone zone1 --zone zone2 (...)

2. Environment variables:
    $ (...) GCE_ZONE0=zone1 GCE_ZONE1=zone2 (...) ./gce_googleapiclient.py
        Obs: from docoptcfg documentation "(...) can set PREFIX_KEY=one,
    PREFIX_KEY0=two, and so on (up to 99 is supported). They can also start at
    1: PREFIX_KEY=one, PREFIX_KEY1=two, PREFIX_KEY2=three. They can even skip
    the integer-less variable and do PREFIX_KEY0=one, PREFIX_KEY1=two and so
    on. The first variable must start either integer-less or with 0."

3. Config ini file:
    [gce_googleapiclient.py]
    (...)
    zone = zone1
           zone2
    (...)
        Obs: It is important to have at least one space or tab char before 'zone2'
"""

from __future__ import print_function

from sys import version_info, stderr

import collections
import json
import logging as log
import multiprocessing as mp
import signal

from Crypto import Random

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
API_VERSION = 'v1'


class GCloudAPI(object):
    """
    Class for handling the access to Google Cloud API.
    """
    def __init__(self, api_version=API_VERSION):
        # type: (str) -> None
        """
        Initialize Google Cloud API wrapper.

        :param str api_version: api version used to connect
        """

        self.credentials = GoogleCredentials.get_application_default()
        self.api_version = api_version
        self.services = {}  # type: Dict[str, Any]

        for service_type in ['compute', 'cloudbilling']:
            self.get_service(service_type)

    def get_service(self, service_name):
        # type: (str) -> Any
        """
        Get service object; initialize if not initialized yet.

        :param str service_name: name of the service object to get
        """

        if service_name not in self.services:
            self.services[service_name] = discovery.build(serviceName=service_name,
                                                          version=self.api_version,
                                                          credentials=self.credentials)

        return self.services[service_name]


GCAPI = GCloudAPI()


def signal_handler():  # pragma: no cover
    # type: () -> None
    """Signal handler for all worker processes, allowing clean CTRL-C"""

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    # when forking using multiprocessing, this is required to re-init random seed
    Random.atfork()  # type: ignore


def get_all_billing_projects(billing_account_name):
    project_ids = []

    # pylint: disable=no-member
    service = GCAPI.get_service('cloudbilling')

    request = service.billingAccounts().projects().list(name=billing_account_name)

    while request is not None:
        response = request.execute()

        # pylint: disable=no-member
        request = service.billingAccounts().projects().list_next(previous_request=request,
                                                                 previous_response=response)

        for project_billing_info in response['projectBillingInfo']:
            if project_billing_info['billingEnabled']:
                project_ids.append(project_billing_info['projectId'])

    return project_ids


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
        hostvars['gce_metadata'][md['key']] = md['value'].replace('{', '\{').replace('}', '\}')

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
            inventory['_meta']['hostvars'][instance['name']] = get_hostvars(instance)

            # populate the 'all' group with all hosts found
            inventory['all'].append(instance['name'])

            # create a group for every tag prefixed by 'tag_' and populate accordingly
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


def get_project_zone_list(project):
    # type: (str) -> Tuple[str, List[str]]
    """Get list of all zones for particular project (Worker process)"""

    project = project
    zones = []
    log.info('Retrieving list of zones of project: %s', project)

    service = GCAPI.get_service('compute')

    try:
        request = service.zones().list(project=project)

        while request is not None:
            response = request.execute()

            for zone in response['items']:
                zones.append(zone['name'])

            request = service.zones().list_next(previous_request=request,
                                                previous_response=response)

    except HttpError as exception:
        log.warn('Could not retrieve list of zones on project: %s', project)
        log.warn(exception)

    return project, zones


def get_project_zone_instances(project_zone):
    # type: (Tuple[str, str]) -> List[str]
    """Get list of all instances for particular project/zone (Worker process)"""

    project, zone = project_zone
    instance_list = []

    service = GCAPI.get_service('compute')

    try:
        # pylint: disable=no-member
        request = service.instances().list(project=project, zone=zone)

        while request is not None:
            response = request.execute()
            instance_list.extend(response.get('items', []))

            # pylint: disable=no-member
            request = service.instances().list_next(previous_request=request,
                                                    previous_response=response)

    except HttpError as exception:
        log.warn('Could not retrieve list of instances of project/zone: %s/%s',
                 project,
                 zone)
        log.warn(str(exception))

    return instance_list


def main(args):

    if not args['--debug']:
        log.basicConfig(level=log.ERROR)

    project_list = args['--project']
    zone_list = args['--zone']
    billing_account_name = args['--billing-account']
    num_threads = int(args['--num-threads'])
    timeout = int(args['--timeout'])

    if not project_list and not billing_account_name:
        print("ERROR: You didn't specified any project (parameter: --project) which means you want"
              "all projects. However, to get the list of all projects, we need the billing account"
              "name (parameter: --billing-account, format: billingAccounts/XXXXXX-XXXXXX-XXXXXX)",
              file=stderr)
        exit(1)

    if num_threads < 2:
        num_threads = 1

    pool_workers = mp.Pool(num_threads, signal_handler)

    if not project_list:
        project_list = get_all_billing_projects(billing_account_name)

    if zone_list:
        project_zone_list = [
            (project, zone)
            for project in project_list
            for zone in zone_list
        ]
    else:
        project_zone_list = [
            (project_name, zone)
            for project_name, zone_list in pool_workers.map_async(get_project_zone_list,
                                                                  project_list).get(timeout)
            for zone in zone_list
        ]

    instance_list = []

    for zone_instances in pool_workers.map_async(get_project_zone_instances,
                                                 project_zone_list).get(timeout):
        instance_list.extend(zone_instances)

    inventory_json = get_inventory(instance_list)
    print(json.dumps(inventory_json,
                     sort_keys=True,
                     indent=2))

if __name__ == "__main__":
    log.basicConfig(filename='gce_googleapiclient.log', level=log.DEBUG)

    try:
        ARGS = docoptcfg(__doc__,
                         config_option='--config',
                         env_prefix=ENV_PREFIX)
    except DocoptcfgFileError as exc:
        log.info('Failed reading: %s', str(exc))
        ARGS = docoptcfg(__doc__, env_prefix=ENV_PREFIX)

    main(ARGS)
