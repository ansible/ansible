# -*- coding: utf-8 -*-
# Copyright: (c) 2019 Wilhelm, Wonigkeit (wilhelm.wonigkeit@vorteil.io)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
import uuid
import time
import traceback

try:
    from ansible.module_utils.ansible_release import __version__ as ansible_version
except Exception:
    ansible_version = 'unknown'

REQUESTS_IMP_ERR = None
try:
    # requests is required for exception handling of the ConnectionError
    import requests
    HAS_REQUESTS = True
except ImportError:
    REQUESTS_IMP_ERR = traceback.format_exc()
    HAS_REQUESTS = False

TOML_IMP_ERR = None
try:
    # toml is required for parsing vorteil configuration (VCFG) data
    import toml
    HAS_TOML = True
except ImportError:
    TOML_IMP_ERR = traceback.format_exc()
    HAS_TOML = False


class VorteilClient(object):
    # Short description:    Initialise module parameters & repo_url to be used in util functions,
    #                       additionally check if user has required modules.
    # Parameters:
    #       module:         Module object from passed from parent ansible module, This is needs
    #                       to be passed so the VorteilClient can have a record of the module.params
    # Module Parameters:
    #       repo_address:   FQDN or IP address to the Vorteil Repository
    #       repo_proto:     repository protocol, can either be HTTP or HTTPS (default = "http")
    #       repo_port:      Vorteil repository port (default = "7472")
    def __init__(self, module):
        self.module = module
        self.repo_cookie = ""
        self.repo_url = "{}://{}".format(self.module.params['repo_proto'], self.module.params['repo_address'])
        if self.module.params['repo_port'] is not None:
            self.repo_url += ":{}".format(self.module.params["repo_port"])

        if not HAS_REQUESTS:
            self.module.fail_json(msg=missing_required_lib('requests'),
                                  exception=REQUESTS_IMP_ERR)

        if not HAS_TOML:
            self.module.fail_json(msg=missing_required_lib('toml'),
                                  exception=TOML_IMP_ERR)

    # Short description: login with user key, return cookie for subsequent sessions
    # Module Parameters:
    #       repo_key:       user key generated as part of the initialisation of the Vorteil Repository
    def set_repo_cookie(self):

        """
        Builds an authentication token for the user. Takes input of the Vorteil.io user key, fqdn of the repo,
        protocol (http or https) and port on which it runs
        """

        # For the Vorteil.io repo the /api/login endpoint services logins and Cookies
        param = "api/login"
        url = '{}/{}'.format(self.repo_url, param)

        # Create the payload for the authentication. Example of the payload is:
        # {
        # "key" : "{{repo-key}}" <--- where repo-key is the User Authentication Key (see support.vorteil.io)
        # }
        payload = '{{"key":"{}"}}'.format(self.module.params['repo_key'])
        headers = {
            'accept': "application/json",
            'content-type': "application/json"
        }

        response = requests.request("POST", url, data=payload, headers=headers, verify=False)

        if response.status_code != 200:
            return ('POST /api/login/ {}'.format(response.status_code)), True
        self.repo_cookie = response.cookies
        return self.repo_cookie, False

    # Short description: list all of the buckets configured in the repository
    def list_buckets(self):

        """
        Gets a list of all the buckets within the Vorteil.io repo. Please note that if the target Vorteil.io
        repo requires authentication, it is required to run the set_repo_cookie() function to generate a
        session key, given a valid authentication key.
        """

        # Even though we have a GraphQL interface, the requests are static. Below query is the full GraphQL
        # extended as a simple URL with variable substitution where necessary
        # To test the GraphQL queries, use the Vorteil Developer Studio or the Vorteil Repository GraphQL
        # interfaces for testing
        param = "graphql?query=query{listBuckets{edges{node{name}}}}"
        url = '{}/{}'.format(self.repo_url, param)

        headers = {
            'accept': "application/json",
            'content-type': "application/json"
        }

        response = requests.request("GET", url, headers=headers, verify=False, cookies=self.repo_cookie)
        if 'errors' in response.json():
            self.module.fail_json(msg="Vorteil.io Repo Response: " + response.json()['errors'][0]['message'])

        if response.status_code != 200:
            return Exception('GET {} {}'.format(url, response.status_code)), True
        return response.json()['data']['listBuckets']['edges'], False

    # Short description: list all of the provisioners configured in the repository
    def list_provisioners(self):

        """
        Gets a list of all the provisioners within the Vorteil.io repo. Please note that if the target Vorteil.io
        repo requires authentication, it is required to run the set_repo_cookie() function to generate a
        session key, given a valid authentication key.
        """

        # Even though we have a GraphQL interface, the requests are static. Below query is the full GraphQL
        # extended as a simple URL with variable substitution where necessary
        # To test the GraphQL queries, use the Vorteil Developer Studio or the Vorteil Repository GraphQL
        # interfaces for testing
        param = "graphql?query=query{listProvisioners{provisioners{name, type}}}"
        url = '{}/{}'.format(self.repo_url, param)

        headers = {
            'accept': "application/json",
            'content-type': "application/json"
        }

        response = requests.request("GET", url, headers=headers, verify=False, cookies=self.repo_cookie)
        if 'errors' in response.json():
            self.module.fail_json(msg="Vorteil.io Repo Response: " + response.json()['errors'][0]['message'])

        if response.status_code != 200:
            return Exception('GET {} {}'.format(url, response.status_code)), True
        return response.json()['data']['listProvisioners']['provisioners'], False

    # Short description: list applications within a specific bucket
    # Module Parameters:
    #       repo_bucket:    bucket to query for applications
    def list_apps_in_bucket(self):

        """
        Gets a list of all the applications in in a specific Vorteil.io bucket.
        """

        # Even though we have a GraphQL interface, the requests are static. Below query is the full GraphQL
        # extended as a simple URL with variable substitution where necessary
        # To test the GraphQL queries, use the Vorteil Developer Studio or the Vorteil Repository GraphQL
        # interfaces for testing
        param = 'graphql?query=query{bucket(name:"' + self.module.params['repo_bucket'] + \
                '"){appsList{edges{node{name}}}}}'
        url = '{}/{}'.format(self.repo_url, param)

        headers = {
            'accept': "application/json",
            'content-type': "application/json"
        }

        response = requests.request("GET", url, headers=headers, verify=False, cookies=self.repo_cookie)
        if 'errors' in response.json():
            self.module.fail_json(msg="Vorteil.io Repo Response: " + response.json()['errors'][0]['message'])

        retresponse = response.json()['data']['bucket']['appsList']
        retresponse['bucket'] = self.module.params['repo_bucket']

        if response.status_code != 200:
            return Exception('GET {} {}'.format(url, response.status_code)), True
        return retresponse, False

    # Short description: get the packageInfo for a specific application
    # Module Parameters:
    #       repo_app:       application to query within the bucket
    #       repo_bucket:    bucket to query for applications
    def get_app(self):

        """
        Gets the configuration settings for an application in a specific Vorteil.io bucket.
        """

        attr_list_str = ""
        if self.module.params['repo_app_attr'] is None:
            attr_list_str = 'app author programs{args binary stderr stdout} cpus' + \
                            ' description diskSize kernel memory summary totalNICs url version'
        else:
            switcher = {
                'app': 'app',
                'author': 'author',
                'programs': 'programs{args binary stderr stdout}',
                'cpus': 'cpus',
                'description': 'description',
                'diskSize': 'diskSize',
                'kernel': 'kernel',
                'memory': 'memory',
                'summary': 'summary',
                'totalNICs': 'totalNICs',
                'url': 'url',
                'version': 'version'
            }
            app_attr_set = set([])
            for i in self.module.params['repo_app_attr']:
                app_attr_set.add(" " + switcher.get(i, ""))

            for attr in app_attr_set:
                attr_list_str += attr

        param = 'graphql?query=query{packageConfig(bucket:"' + self.module.params['repo_bucket'] + '",app:"' + \
                self.module.params[
                    'repo_app'] + '",ref:""){info{' + attr_list_str + ' }}}'
        url = '{}/{}'.format(self.repo_url, param)
        headers = {
            'accept': "application/json",
            'content-type': "application/json"
        }

        response = requests.request("GET", url, headers=headers, verify=False, cookies=self.repo_cookie)
        if 'errors' in response.json():
            self.module.fail_json(msg="Vorteil.io Repo Response: " + response.json()['errors'][0]['message'])

        retresponse = response.json()['data']
        retresponse['bucket'] = self.module.params['repo_bucket']
        retresponse['app'] = self.module.params['repo_app']
        if response.status_code != 200:
            return Exception('GET {} {}'.format(url, response.status_code)), True
        return retresponse, False

    # Short description: create the injection URI for the disk build process
    # Module Parameters:
    #       repo_disktype:  disk type which needs to be built (disk types can be )
    #       repo_app:       application to query within the bucket
    #       repo_bucket:    bucket to query for applications
    def create_injection_uri(self):

        """
        This uses the mutation function of the GraphQL interface to create an injection URI which can be used in the
        disk configuration and building process. This is step 1 of 3 to create the disk
        Step 1: create_injection_uri: create the injection URI job <--- THIS IS THE FUNCTION YOU'RE LOOKING AT
        Step 2: create_injection_config: send configuration options to the job
        Step 3: create_injection_disk: create and download the disk
        """

        # Firstly, create a unique ID to be used for the injection and to isolate any
        # configurations changes we make to this specific mutation
        repo_uuid = str(uuid.uuid4())

        param = 'graphql?query=mutation{build(germ: ":' + self.module.params['repo_bucket'] + '/' + \
                self.module.params['repo_app'] + '", injections: ["' + repo_uuid + \
                '"],kernelType: "PROD", diskFormat: "' + self.module.params['repo_disktype'] + '"){uri,job{id}}}'
        url = '{}/{}'.format(self.repo_url, param)

        headers = {
            'accept': "*/*",
            'content-type': "application/json"
        }

        response = requests.request("GET", url, headers=headers, cookies=self.repo_cookie)
        if 'errors' in response.json():
            self.module.fail_json(msg="Vorteil.io Repo Response: " + response.json()['errors'][0]['message'])

        retresponse = response.json()['data']

        retresponse['build']['uuid'] = repo_uuid
        if response.status_code != 200:
            return Exception('GET {} {}'.format(url, response.status_code)), True

        return retresponse, False

    # Short description: create the POST action to configure the application for disk build
    # Module Parameters:
    #       injection_toml:     TOML configuration to inject into the build process (dictionary type)
    #       injection_uuiduri:  dictionary type with UUID and URI for the germination
    def create_injection_config(self):

        """
        This uses the mutation function of the GraphQL interface to inject Vorteil configuration data into a started
        Vorteil disk process. The targeted job is dependant on the jobs uri. This is step 2 of 3 to create the disk.
        Step 1: create_injection_uri: create the injection URI job
        Step 2: create_injection_config: send configuration options to the job <-THIS IS THE FUNCTION YOU'RE LOOKING AT
        Step 3: create_injection_disk: create and download the disk
        """

        param = 'api/build/' + self.module.params['injection_uuiduri']['response']['build']['uri']
        url = '{}/{}'.format(self.repo_url, param)

        headers = {
            'accept': "*/*",
            'content-type': "text/plain",
            'Injection-Id': self.module.params['injection_uuiduri']['response']['build']['uuid'],
            'Injection-Type': 'configuration'
        }

        if self.module.params['use_default_kernel']:
            default_kernel = self.get_kernel_default(self.module.params, self.repo_cookie)
            self.module.params['injection_json']['vm']['kernel'] = default_kernel[0]['data']['getDefault'][
                'kernel']  # "1.0.6"

        payload = toml.dumps(self.module.params['injection_json'])

        response = requests.request("POST", url, data=payload, headers=headers, verify=False, cookies=self.repo_cookie)

        if response.status_code != 200:
            return Exception('POST {} {}'.format(url, response.status_code)), True
        return "Success", False

    # Short description: Get the default kernel version set on the repo
    def get_kernel_default(self):

        """
        Gets the default kernel which is used, if we are overriding the packaged kernel
        """

        # Even though we have a GraphQL interface, the requests are static. Below query is the full GraphQL
        # extended as a simple URL with variable substitution where necessary
        # To test the GraphQL queries, use the Vorteil Developer Studio or the Vorteil Repository GraphQL
        # interfaces for testing
        param = "graphql?query=query{getDefault{kernel}}"
        url = '{}/{}'.format(self.repo_url, param)

        headers = {
            'accept': "application/json",
            'content-type': "application/json"
        }

        response = requests.request("GET", url, headers=headers, verify=False, cookies=self.repo_cookie)
        if 'errors' in response.json():
            self.module.fail_json(msg="Vorteil.io Repo Response: " + response.json()['errors'][0]['message'])

        if response.status_code != 200:
            return Exception('GET {} {}'.format(url, response.status_code)), True
        return response.json(), False

    # Short description: download the disk to the local machine passed as an argument
    # Parameters:
    #       disk_directory:directory where the disk is to be stored on the local machine
    #       injection_uuiduri:  dictionary type with UUID and URI for the germination
    #       repo_disktype:      disk type which needs to be built (disk types can be )
    #       repo_app:           application to query within the bucket
    #       repo_bucket:        bucket to query for applications
    def create_injection_disk(self):

        """
        This uses the mutation function of the GraphQL interface to create an injection URI which can be used in the
        disk configuration and building process. This is step 3 of 3 to create a disk
        Step 1: create_injection_uri: create the injection URI job
        Step 2: create_injection_config: send configuration options to the job
        Step 3: create_injection_disk: create and download the disk <--- THIS IS THE FUNCTION YOU'RE LOOKING AT
        """

        def file_extension(fx):
            return {
                'gcp': 'tar.gz',
                'raw': 'raw',
                'ova': 'ova',
                'vmdk': 'vmdk',
                'vhd': 'vhd'
            }[fx]

        disk_response = dict(
            file_name=dict(type='str', required=True),
            file_location=dict(type='str', required=True)
        )

        file_extension = file_extension(self.module.params['repo_disktype'])

        param = 'api/build/' + self.module.params['injection_uuiduri']['response']['build']['uri']
        url = '{}/{}'.format(self.repo_url, param)

        headers = {
            'accept': "*/*",
        }

        response = requests.request("GET", url, headers=headers, verify=False, cookies=self.repo_cookie)

        disk_response['file_name'] = self.module.params['repo_bucket'] + "-" + self.module.params[
            'repo_app'] + "-" + str(
            time.time()) + "." + file_extension
        disk_response['file_location'] = self.module.params['disk_directory'] + "/" + self.module.params[
            'repo_bucket'] + "-" + self.module.params['repo_app'] + "-" + str(time.time()) + "." + file_extension

        if response.status_code != 200:
            return Exception('GET /api/build/ {}'.format(response.status_code)), True

        with open(disk_response['file_location'], 'wb') as filehandle:
            try:
                filehandle.write(response.content)
                return disk_response, False
            except Exception:
                return ('Could not create disk image file:{}'.format(disk_response['file_location'])), True

    # Short description: create the injection URI for provisioning the disk build process
    # Module Parameters:
    #       repo_disktype:  disk type which needs to be built (disk types can be )
    #       repo_app:       application to query within the bucket
    #       repo_bucket:    bucket to query for applications
    def provision_injection_uri(self):

        """
        This uses the mutation function of the GraphQL interface to create an injection URI which can be used in the
        disk configuration and building process. This is step 1 of 2 to create the disk for provisioning
        Step 1: provision_injection_uri: create the injection URI job <--- THIS IS THE FUNCTION YOU'RE LOOKING AT
        Step 2: provision_injection_config: send configuration options to the job
        """

        # Firstly, create a unique ID to be used for the injection and to isolate any
        # configurations changes we make to this specific mutation
        repo_uuid = str(uuid.uuid4())

        param = 'graphql?query=mutation{provision(germ: ":' + self.module.params['repo_bucket'] + '/' +\
                self.module.params['repo_app'] + '", injections: ["' + repo_uuid + '"], name: "' +\
                self.module.params['repo_image_name'] + '" , provisioner: "' +\
                self.module.params['repo_provisioner'] + '"){uri,job{id}}}'
        url = '{}/{}'.format(self.repo_url, param)
        headers = {
            'accept': "*/*",
            'content-type': "application/json"
        }

        response = requests.request("GET", url, headers=headers, cookies=self.repo_cookie)
        if 'errors' in response.json():
            self.module.fail_json(msg="Vorteil.io Repo Response: " + response.json()['errors'][0]['message'])

        retresponse = response.json()['data']

        retresponse['provision']['uuid'] = repo_uuid
        if response.status_code != 200:
            return Exception('GET {} {}'.format(url, response.status_code)), True

        return retresponse, False

    # Short description: create the POST action to configure the application for provisioning the disk build
    # Parameters:
    #       injection_json:     TOML configuration to inject into the build process (dictionary type)
    #       injection_uuiduri:  dictionary type with UUID and URI for the germination
    def provision_injection_config(self):

        """
        This uses the mutation function of the GraphQL interface to inject Vorteil configuration data into a started
        Vorteil disk process. The targeted job is dependant on the jobs uri.
        This is step 2 of 2 to create the disk for provisioning.
        Step 1: provision_injection_uri: create the injection URI job
        Step 2: provision_injection_config: send configuration options to the job <--
        --THIS IS THE FUNCTION YOU'RE LOOKING AT
        """

        param = 'api/provision/' + self.module.params['injection_uuiduri']['response']['provision']['uri']
        url = '{}/{}'.format(self.repo_url, param)
        headers = {
            'accept': "*/*",
            'content-type': "text/plain",
            'Injection-Id': self.module.params['injection_uuiduri']['response']['provision']['uuid'],
            'Injection-Type': 'configuration'
        }

        if self.module.params['use_default_kernel']:
            default_kernel = self.get_kernel_default(self.module.params, self.repo_cookie)
            self.module.params['injection_json']['vm']['kernel'] = default_kernel[0]['data']['getDefault'][
                'kernel']  # "1.0.6"

        payload = toml.dumps(self.module.params['injection_json'])

        response = requests.request("POST", url, data=payload, headers=headers, verify=False, cookies=self.repo_cookie)

        if response.status_code != 200:
            return Exception('POST {} {}'.format(url, response.status_code)), True
        return "Success", False
