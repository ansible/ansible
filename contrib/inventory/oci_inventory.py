#!/usr/bin/env python
# Copyright (c) 2018, 2019, Oracle and/or its affiliates.
# This software is made available to you under the terms of the GPL 3.0 license.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Requirements
#   - oci >= 2.1.7

"""
Oracle Cloud Infrastructure(OCI) Inventory Script
=================================================
This script generates Ansible dynamic inventory for OCI by using the OCI Python SDK.
The complete Oracle Cloud Infrastructure Ansible Modules can be downloaded from
U(https://github.com/oracle/oci-ansible-modules/releases).

The order of precedence for reading parameters is command line arguments, then environment variables followed by options
in inventory settings file. The dynamic inventory settings file defaults to "./oci_inventory.ini" file.
The config file defaults to "~/.oci/config" file. The script reads "DEFAULT" profile from the config file if no profile
name is specified.

This script accepts following command line arguments:

usage: oci_inventory.py [-h] [--list] [--host HOST] [-config CONFIG_FILE]
                        [--profile PROFILE] [--tenancy TENANCY]
                        [--compartment-ocid COMPARTMENT_OCID]
                        [--compartment COMPARTMENT]
                        [--parent-compartment-ocid PARENT_COMPARTMENT_OCID]
                        [--fetch-hosts-from-subcompartments] [--refresh-cache]
                        [--debug] [--auth {api_key,instance_principal}]
                        [--enable-parallel-processing]
                        [--max-thread-count MAX_THREAD_COUNT]
                        [--freeform-tags FREEFORM_TAGS]
                        [--defined-tags DEFINED_TAGS] [--regions REGIONS]
                        [--exclude-regions EXCLUDE_REGIONS]
                        [--hostname-format {fqdn,private_ip,public_ip}]
                        [--strict-hostname-checking {yes,no}]

Produce an Ansible Inventory file based on OCI

optional arguments:
  -h, --help            show this help message and exit
  --list                List instances (default: True)
  --host HOST           Get all information about a compute instance
  -config CONFIG_FILE, --config-file CONFIG_FILE
                        OCI config file location
  --profile PROFILE     OCI config profile for connecting to OCI
  --tenancy TENANCY     OCID of the tenancy for which dynamic inventory must
                        be generated.
  --compartment-ocid COMPARTMENT_OCID
                        OCID of the compartment for which dynamic inventory
                        must be generated. If specified, any value specified
                        for compartment and parent-compartment-ocid options is
                        ignored.
  --compartment COMPARTMENT
                        Name of the compartment for which dynamic inventory
                        must be generated. If you want to generate a dynamic
                        inventory for the root compartment of the tenancy,
                        specify the tenancy name as the name of the
                        compartment.
  --parent-compartment-ocid PARENT_COMPARTMENT_OCID
                        Only valid when --compartment is set. Parent
                        compartment ocid of the specified compartment.Defaults
                        to tenancy ocid.
  --fetch-hosts-from-subcompartments
                        Only valid when --compartment is set. Default is
                        false. When set to true, inventory is built with the
                        entire hierarchy of the given compartment.
  --refresh-cache, -r   Force refresh of cache by making API requests to OCI.
                        Use this option whenever you are building inventory
                        with new filter options to avoid reading cached
                        inventory. (default: False - use cache files)
  --debug               Send debug messages to STDERR
  --auth {api_key,instance_principal}
                        The type of authentication to use for making API
                        requests. By default, the API key in your config will
                        be used. Set this option to `instance_principal` to
                        use instance principal based authentication. This
                        value can also be provided in the
                        OCI_ANSIBLE_AUTH_TYPE environment variable.
  --enable-parallel-processing
                        Inventory generation for tenants with huge number of
                        instances might take a long time.When this flag is
                        set, the inventory script uses thread pools to
                        parallelise the inventory generation.
  --max-thread-count MAX_THREAD_COUNT
                        Only valid when --enable-parallel-processing is set.
                        When set, this script uses threads to improve the
                        performance of building the inventory. This option
                        specifies the maximum number of threads to use.
                        Defaults to 50. This value can also be provided in the
                        settings config file.
  --freeform-tags FREEFORM_TAGS
                        Freeform tags provided as a string in valid JSON
                        format. Example: { "stage": "dev", "app": "demo"} Use
                        this option to build inventory of only those hosts
                        which are tagged with all the specified key-value
                        pairs.
  --defined-tags DEFINED_TAGS
                        Defined tags provided as a string in valid JSON
                        format. Example: {"namespace1": {"key1": "value1",
                        "key2": "value2"}, "namespace2": {"key": "value"}} Use
                        this option to build inventory of only those hosts
                        which are tagged with all the specified key-value
                        pairs.
  --regions REGIONS     Comma separated region names to build the inventory
                        from. Default is the region specified in the config.
                        Please specify 'all' to build inventory from all the
                        subscribed regions. Example: us-ashburn-1,us-phoenix-1
  --exclude-regions EXCLUDE_REGIONS
                        Comma separated region names to exclude while building
                        the inventory. Example: us-ashburn-1,uk-london-1
  --hostname-format {fqdn,private_ip,public_ip}
                        Host naming format to use.
  --strict-hostname-checking {yes,no}
                        The default behavior of this script is to ignore hosts
                        without valid hostnames(determined according to the
                        hostname format). When set to yes, the script fails
                        when any host does not have a valid hostname.

The script reads following environment variables:
OCI_CONFIG_FILE,
OCI_INI_PATH,
OCI_CONFIG_PROFILE,
OCI_USER_ID,
OCI_USER_FINGERPRINT,
OCI_USER_KEY_FILE,
OCI_TENANCY,
OCI_REGION,
OCI_USER_KEY_PASS_PHRASE,
OCI_CACHE_DIR,
OCI_CACHE_MAX_AGE,
OCI_HOSTNAME_FORMAT
OCI_ANSIBLE_AUTH_TYPE
OCI_INVENTORY_REGIONS
OCI_INVENTORY_EXCLUDE_REGIONS
OCI_COMPARTMENT_OCID
OCI_STRICT_HOSTNAME_CHECKING

The inventory generated is by default grouped by each of the following:
region
compartment_name
availability domain
vcn_id
subnet_id
security_list_id
image_id when the instance is launched using an image
instance shape
freeform tags with group name as "tag_key=value"
defined tags with group name as "namespace#key=value"
metadata (key, value) with group name as "key=value"
extended metadata (key, value) with group name as "key=value"

By default, the inventory is generated for all the compartments in the tenancy. You must have COMPARTMENT_INSPECT
permission on the root compartment for this script to be able to get all the compartments. But when compartment_ocid
is specified, the inventory is generated only for the specific compartment and you need COMPARTMENT_INSPECT permission
only on the compartment specified.

By default, all non-alphanumeric characters except HASH(#), EQUALS(=), PERIOD(.) and DASH(-) in group names and host
names are replaced with an UNDERSCORE when the inventory is generated, so that the names can be used as Ansible
groups. To disable this replacement, set sanitize_names to False in the dynamic inventory settings file(default
./oci_inventory.ini). To also replace DASH(-) when sanitize_names is True, set replace_dash_in_names to True in
the settings file.

When run for a specific host using the --host option, this script returns the following variables:
{
    "availability_domain": "IwGV:US-ASHBURN-AD-1",
    "compartment_id": "ocid1.compartment.oc1..xxxxxEXAMPLExxxxx",
    "defined_tags": {},
    "display_name": "ansible-test-instance-448",
    "extended_metadata": {},
    "freeform_tags": {},
    "id": "ocid1.instance.oc1.iad.xxxxxEXAMPLExxxxx",
    "image_id": "ocid1.image.oc1.iad.xxxxxEXAMPLExxxxx",
    "ipxe_script": null,
    "launch_mode": "CUSTOM",
    "launch_options": {
      "boot_volume_type": "ISCSI",
      "firmware": "UEFI_64",
      "network_type": "VFIO",
      "remote_data_volume_type": "ISCSI"
    },
    "lifecycle_state": "AVAILABLE",
    "metadata": {
      "baz": "quux",
      "foo": "bar"
    },
    "region": "iad",
    "shape": "VM.Standard1.1",
    "source_details": {
      "image_id": "ocid1.image.oc1.iad.xxxxxEXAMPLExxxxx",
      "source_type": "image"
    },
    "time_created": "2018-01-16T12:13:35.336000+00:00"
}

author: "Rohit Chaware (@rohitChaware)"
        "Manoj Meda (@manojmeda)"
"""

from __future__ import print_function
import argparse
import json
import os
import re
import sys
from time import time
from ansible.module_utils import six
from ansible.module_utils.six.moves import configparser
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.urls import open_url
from collections import deque, defaultdict
from multiprocessing.pool import ThreadPool
from contextlib import contextmanager
import hashlib
from functools import partial
import traceback

try:
    import oci
    from oci.retry import RetryStrategyBuilder
    from oci.constants import HEADER_NEXT_PAGE
    from oci.core.compute_client import ComputeClient
    from oci.identity.identity_client import IdentityClient
    from oci.core.virtual_network_client import VirtualNetworkClient
    from oci.util import to_dict
    from oci.exceptions import ServiceError

    HAS_OCI_PY_SDK = True
except ImportError:
    HAS_OCI_PY_SDK = False

__version__ = "1.10.0"


def _get_retry_strategy():
    retry_strategy_builder = RetryStrategyBuilder(
        max_attempts_check=True,
        max_attempts=3,
        retry_max_wait_between_calls_seconds=30,
        retry_base_sleep_time_seconds=10,
        backoff_type=oci.retry.BACKOFF_FULL_JITTER_EQUAL_ON_THROTTLE_VALUE,
    )
    retry_strategy_builder.add_service_error_check(
        service_error_retry_config={429: [], 400: ["QuotaExceeded", "LimitExceeded"]},
        service_error_retry_on_any_5xx=True,
    )
    return retry_strategy_builder.get_retry_strategy()


def list_all_resources(target_fn, **kwargs):
    """
    Return all resources after paging through all results returned by target_fn.
    :param target_fn: The target OCI SDK paged function to call
    :param kwargs: All arguments that the OCI SDK paged function expects
    :return: List of all objects returned by target_fn
    :raises ServiceError: When the Service returned an Error response
    :raises MaximumWaitTimeExceededError: When maximum wait time is exceeded while invoking target_fn
    """
    existing_resources = None
    response = call_with_backoff(target_fn, **kwargs)
    existing_resources = response.data
    while response.has_next_page:
        kwargs.update(page=response.headers.get(HEADER_NEXT_PAGE))
        response = call_with_backoff(target_fn, **kwargs)
        existing_resources += response.data
    return existing_resources


def call_with_backoff(fn, **kwargs):
    if "retry_strategy" not in kwargs:
        kwargs["retry_strategy"] = _get_retry_strategy()
    try:
        return fn(**kwargs)
    except TypeError as te:
        if "unexpected keyword argument" in str(te):
            del kwargs["retry_strategy"]
            return fn(**kwargs)


class OCIInventory:

    LIFECYCLE_ACTIVE_STATE = "ACTIVE"
    LIFECYCLE_RUNNING_STATE = "RUNNING"
    LIFECYCLE_ATTACHED_STATE = "ATTACHED"

    def __init__(self):
        self.inventory = {"all": {"hosts": [], "vars": {}}, "_meta": {"hostvars": {}}}
        self.config = {}
        self._region_subscriptions = None
        self._regions = None
        self._region_short_names = None
        self._region_long_names = None
        self.params = {
            "ini_file": os.path.join(
                to_bytes(os.path.dirname(os.path.realpath(__file__))),
                to_bytes("oci_inventory.ini"),
            ),
            "config_file": os.path.join(os.path.expanduser("~"), ".oci", "config"),
            "profile": "DEFAULT",
            "user": None,
            "fingerprint": None,
            "key_file": None,
            "tenancy": None,
            "region": None,
            "pass_phrase": None,
            "cache_dir": ".",
            "cache_max_age": 300,
            "cache_file": None,
            "compartment_ocid": None,
            "compartment": None,
            "parent_compartment_ocid": None,
            "fetch_hosts_from_subcompartments": False,
            "debug": False,
            "hostname_format": "public_ip",
            "sanitize_names": True,
            "replace_dash_in_names": False,
            "auth": "api_key",
            "enable_parallel_processing": False,
            "max_thread_count": 50,
            "freeform_tags": None,
            "defined_tags": None,
            "regions": None,
            "exclude_regions": None,
            "strict_hostname_checking": "no",
        }
        boolean_options = [
            "sanitize_names",
            "replace_dash_in_names",
            "ignore_hostname_errors",
        ]
        dict_options = ["freeform_tags", "defined_tags"]
        try:
            self.parse_cli_args()

            if self.args.debug:
                self.params["debug"] = True
                self.log("Executing in debug mode.")

            if "OCI_INI_PATH" in os.environ:
                oci_ini_file_path = os.path.expanduser(
                    os.path.expandvars(to_bytes(os.environ.get("OCI_INI_PATH")))
                )
                if os.path.isfile(to_bytes(oci_ini_file_path)):
                    self.params["ini_file"] = oci_ini_file_path

            self.settings_config = configparser.ConfigParser()
            self.settings_config.read(to_text(self.params["ini_file"]))

            # Preference order: CLI args > environment variable > settings from config file.
            if (
                "config_file" in self.args
                and getattr(self.args, "config_file") is not None
            ):
                self.params["config_file"] = os.path.expanduser(self.args.config_file)
            elif "OCI_CONFIG_FILE" in os.environ:
                self.params["config_file"] = os.path.expanduser(
                    os.path.expandvars(os.environ.get("OCI_CONFIG_FILE"))
                )
            elif self.settings_config.has_option("oci", "config_file"):
                self.params["config_file"] = os.path.expanduser(
                    self.settings_config.get("oci", "config_file")
                )

            if "profile" in self.args and getattr(self.args, "profile") is not None:
                self.params["profile"] = self.args.profile
            elif "OCI_CONFIG_PROFILE" in os.environ:
                self.params["profile"] = os.environ.get("OCI_CONFIG_PROFILE")
            elif self.settings_config.has_option("oci", "profile"):
                self.params["profile"] = self.settings_config.get("oci", "profile")

            self.read_config()
            self.read_settings_config(boolean_options, dict_options)
            self.read_env_vars()
            self.read_cli_args(dict_options)

            self.identity_client = self.create_service_client(IdentityClient)
            # For the case, when auth="instance_principal", tenancy_id & region name are not available.
            if self.params["auth"] == "instance_principal":
                # self.params.update(self.get_instance_details_from_metadata())
                instance_details = self.get_instance_details_from_metadata()
                self.params.update(instance_details)

            self.validate_params()

            self.log("Using following parameters for OCI dynamic inventory:")
            self.log(self.params)

            self._compute_clients = dict(
                (region, self.create_service_client(ComputeClient, region=region))
                for region in self.regions
            )

            self._virtual_nw_clients = dict(
                (
                    region,
                    self.create_service_client(VirtualNetworkClient, region=region),
                )
                for region in self.regions
            )

            self.params["cache_file"] = self._get_cache_file()

            if not self.args.refresh_cache and self.is_cache_valid():
                self.log(
                    "Reading inventory from cache {0}.".format(
                        self.params["cache_file"]
                    )
                )
                self.inventory = self.read_from_cache()
            else:
                self.build_inventory()
                self.write_to_cache(self.inventory)

            if self.args.host:
                if self.args.host in self.inventory["_meta"]["hostvars"]:
                    print(
                        json.dumps(
                            self.inventory["_meta"]["hostvars"][self.args.host],
                            sort_keys=True,
                            indent=2,
                        )
                    )
                else:
                    self.log(
                        "Either the specified host does not exist or its facts cannot be retrieved."
                    )
                    print({})

            else:
                print(json.dumps(self.inventory, sort_keys=True, indent=2))

        except Exception as ex:
            stacktrace = traceback.format_exc()
            try:
                error_message = ex.message
            except AttributeError:
                error_message = str(ex)
            self.fail(message=error_message, stacktrace=stacktrace)

    def _is_instance_principal_auth(self):
        # check if auth is set to `instance_principal`.
        return self.params["auth"] == "instance_principal"

    @staticmethod
    def create_instance_principal_signer():
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        except Exception as ex:
            raise Exception(
                "Failed retrieving certificates from localhost. Instance principal based authentication is only"
                "possible from within OCI compute instances. Exception: {0}".format(
                    str(ex)
                )
            )
        return signer

    def create_service_client(self, service_client_class, region=None):
        if not region:
            region = self.params["region"]
        params = dict(self.params, region=region)
        kwargs = {}
        if self._is_instance_principal_auth():
            kwargs["signer"] = self.create_instance_principal_signer()

        # Create service client class with the signer.
        client = service_client_class(params, **kwargs)

        return client

    def get_region_short_name(self, name):
        if name in self.region_long_names:
            return self.region_long_names[name]
        if name.lower() in self.region_long_names:
            return self.region_long_names[name.lower()]
        # check if name is already a short name
        if name.lower() in self.region_short_names:
            return name.lower()
        raise ValueError("Could not get the short name of the region {0}.".format(name))

    def get_region_long_name(self, name):
        if name.lower() in self.region_short_names:
            return self.region_short_names[name.lower()]
        # check if name is already a long name
        if name in self.region_long_names:
            return name
        if name.lower() in self.region_long_names:
            return name.lower()
        raise ValueError(
            "Could not get the long region name of the region {0}.".format(name)
        )

    @property
    def region_short_names(self):
        if not self._region_short_names:
            self._region_short_names = dict(
                (region.key.lower(), region.name)
                for region in call_with_backoff(self.identity_client.list_regions).data
            )
        return self._region_short_names

    @property
    def region_long_names(self):
        if not self._region_long_names:
            self._region_long_names = dict(
                (region_long_name, region_short_name)
                for region_short_name, region_long_name in six.iteritems(
                    self.region_short_names
                )
            )
        return self._region_long_names

    def get_compute_client_for_region(self, region):
        if region not in self._compute_clients:
            raise ValueError(
                "Could not fetch the compute client for region {0}.".format(region)
            )
        return self._compute_clients[region]

    def get_virtual_nw_client_for_region(self, region):
        if region not in self._compute_clients:
            raise ValueError(
                "Could not fetch the virtual network for region {0}.".format(region)
            )
        return self._virtual_nw_clients[region]

    def log(self, *args, **kwargs):
        if self.params["debug"]:
            print(*args, file=sys.stderr, **kwargs)

    def get_instance_details_from_metadata(self):
        """Get and return the instance details using the metadata endpoint"""
        metadata_url = "http://169.254.169.254/opc/v1/instance"
        # use ansible provided open_url to avoid external dependencies
        try:
            response = open_url(metadata_url, method="GET")
            metadata_response = json.loads(response.read())
            self.log("Response from metadata: {0}".format(metadata_response))
        except Exception as ex:
            raise Exception(
                "Getting instance metadata details failed with error: {0}".format(
                    str(ex)
                )
            )
        instance_details = dict(
            compartmentId=metadata_response["compartmentId"],
            region=self.get_region_long_name(metadata_response["region"]),
            tenancy=self.params["tenancy"]
            or getattr(self.create_instance_principal_signer(), "tenancy_id", None),
        )
        self.log("Instance parameters from metadata: {0}".format(instance_details))
        if not (
            instance_details["region"]
            or instance_details["compartmentId"]
            or instance_details["tenancy"]
        ):
            raise Exception("Error getting details from instance metadata.")
        return instance_details

    def read_config(self):
        if os.path.isfile(to_bytes(self.params["config_file"])):
            self.config = oci.config.from_file(
                file_location=self.params["config_file"],
                profile_name=self.params["profile"],
            )

        self.config["additional_user_agent"] = "Oracle-Ansible/{0}".format(__version__)

        for setting in self.config:
            self.params[setting] = self.config[setting]

    def read_env_vars(self):
        EnvParamsMapping = dict(
            OCI_CONFIG_FILE="config_file",
            OCI_INI_PATH="ini_path",
            OCI_TENANCY="tenancy",
            OCI_REGION="region",
            OCI_CACHE_DIR="cache_dir",
            OCI_CACHE_MAX_AGE="cache_max_age",
            OCI_HOSTNAME_FORMAT="hostname_format",
            OCI_USER_ID="user",
            OCI_USER_FINGERPRINT="fingerprint",
            OCI_USER_KEY_FILE="key_file",
            OCI_USER_KEY_PASS_PHRASE="pass_phrase",
            OCI_CONFIG_PROFILE="profile",
            OCI_ANSIBLE_AUTH_TYPE="auth",
            OCI_INVENTORY_REGIONS="regions",
            OCI_INVENTORY_EXCLUDE_REGIONS="exclude_regions",
            OCI_COMPARTMENT_OCID="compartment_ocid",
            OCI_STRICT_HOSTNAME_CHECKING="strict_hostname_checking",
        )

        for env_var in os.environ:
            if env_var in EnvParamsMapping:
                self.params[EnvParamsMapping[env_var]] = os.environ.get(env_var)

    def read_cli_args(self, dict_options):
        for setting in vars(self.args):
            if getattr(self.args, setting) is not None:
                if setting in dict_options:
                    self.params[setting] = json.loads(getattr(self.args, setting))
                    if type(self.params[setting]) != dict:
                        raise TypeError("Invalid JSON input for {0}.".format(setting))
                else:
                    self.params[setting] = getattr(self.args, setting)

    def validate_params(self):
        """Validate the parameters passed."""
        if (
            not self.params["tenancy"]
            and self.params["auth"] != "instance_principal"
        ):
            self.fail("Tenany OCID required.")
        if self.params["regions"]:
            # Check if the regions passed are valid
            subscribed_regions = [
                region_subscription.region_name
                for region_subscription in self.region_subscriptions
            ]
            for region in self.regions:
                if region not in subscribed_regions:
                    raise ValueError(
                        "Region {0} is either invalid or not subscribed.".format(region)
                    )

    def _get_cache_file(self):
        """Calculate and return the cache file name from the parameters passed."""
        params_str = u""
        if self.params["tenancy"]:
            params_str += u"@{0}:{1}@".format("tenancy", self.params["tenancy"])
        params_str += u"@{0}:{1}@".format("regions", ",".join(sorted(self.regions)))
        if self.params["compartment_ocid"]:
            params_str += u"@{0}:{1}@".format(
                "compartment", self.params["compartment_ocid"]
            )
        else:
            if self.params["compartment"]:
                params_str += u"@{0}:{1}@".format(
                    "compartment", self.params["compartment"]
                )
            if self.params["parent_compartment_ocid"]:
                params_str += u"@{0}:{1}@".format(
                    "parent_compartment_ocid", self.params["parent_compartment_ocid"]
                )
        params_str += u"@{0}:{1}@".format(
            "fetch_hosts_from_subcompartments",
            self.params["fetch_hosts_from_subcompartments"],
        )
        params_str += u"@{0}:{1}@".format(
            "hostname_format", self.params["hostname_format"]
        )
        if self.params["freeform_tags"]:
            freeform_tag_params_str = u""
            for key in sorted(self.params["freeform_tags"]):
                freeform_tag_params_str += u"{0}={1},".format(
                    key, self.params["freeform_tags"][key]
                )
            params_str += u"@{0}:{1}@".format("freeform_tags", freeform_tag_params_str)
        if self.params["defined_tags"]:
            defined_tag_params_str = u""
            for namespace in sorted(self.params["defined_tags"]):
                for key in sorted(self.params["defined_tags"][namespace]):
                    defined_tag_params_str += u"{0}={1}={2},".format(
                        namespace, key, self.params["defined_tags"][namespace][key]
                    )
            params_str += u"@{0}:{1}@".format("defined_tags", defined_tag_params_str)
        hashed_params_str = hashlib.md5(to_bytes(params_str)).hexdigest()
        self.log(
            u"Cache file name formed from the params {0} is {1}.".format(
                params_str, hashed_params_str
            )
        )
        return os.path.join(
            to_bytes(self.params["cache_dir"]),
            to_bytes("ansible-oci-{0}.cache".format(hashed_params_str)),
        )

    def is_cache_valid(self):
        if os.path.isfile(to_bytes(self.params["cache_file"])):
            mod_time = os.path.getmtime(to_bytes(self.params["cache_file"]))
            current_time = time()
            if (mod_time + float(self.params["cache_max_age"])) > current_time:
                return True
            else:
                self.log("Cache is outdated.")
        else:
            self.log("Cache file is invalid.")
        return False

    def read_from_cache(self):
        with open(to_bytes(self.params["cache_file"]), "r") as cache:
            return json.loads(cache.read())

    def write_to_cache(self, data):
        json_data = json.dumps(data, sort_keys=True, indent=2)
        with open(to_bytes(self.params["cache_file"]), "w") as f:
            f.write(json_data)

    @property
    def region_subscriptions(self):
        if self._region_subscriptions:
            return self._region_subscriptions
        if not self.params["tenancy"]:
            raise Exception("Tenancy OCID required to get the region subscriptions.")
        self._region_subscriptions = call_with_backoff(
            self.identity_client.list_region_subscriptions,
            tenancy_id=self.params["tenancy"],
        ).data
        return self._region_subscriptions

    @property
    def regions(self):
        if self._regions:
            return self._regions
        if self.params["regions"]:
            if self.params["regions"] == "all":
                self._regions = [
                    region_subscription.region_name
                    for region_subscription in self.region_subscriptions
                ]
            else:
                self._regions = [region for region in self.params["regions"].split(",")]
        else:
            self._regions = [self.params["region"]]
        if self.params["exclude_regions"]:
            exclude_regions = self.params["exclude_regions"].split(",")
            self._regions = [
                region for region in self._regions if region not in exclude_regions
            ]
        return self._regions

    def get_compartments(
        self,
        compartment_ocid=None,
        parent_compartment_ocid=None,
        compartment_name=None,
        fetch_hosts_from_subcompartments=False,
    ):
        """
        Get the compartments based on the parameters passed. When compartment_name is None, all the compartments
        including the root compartment is returned.

        When compartment_name is passed, the compartment with that name and its hierarchy of compartments are returned
        if fetch_hosts_from_subcompartments is true.

        The tenancy is returned when compartment_name is the tenancy name.

        :param str compartment_ocid: (optional)
            OCID of the compartment. If None, root compartment is assumed to be parent.
        :param str parent_compartment_ocid: (optional)
            OCID of the parent compartment. If None, root compartment is assumed to be parent.
        :param str compartment_name: (optional)
            Name of the compartment. If None and :attr:`compartment_ocid` is not set, all the compartments including
            the root compartment are returned.
        :param str fetch_hosts_from_subcompartments: (optional)
            Only applicable when compartment_name is specified. When set to true, the entire hierarchy of compartments
            of the given compartment is returned.
        :raises ServiceError: When the Service returned an Error response
        :raises MaximumWaitTimeExceededError: When maximum wait time is exceeded while invoking target_fn
        :return: list of :class:`~oci.identity.models.Compartment`
        """
        if compartment_ocid:
            try:
                compartment_with_ocid = call_with_backoff(
                    self.identity_client.get_compartment,
                    compartment_id=compartment_ocid,
                ).data
            except ServiceError as se:
                if se.status == 404:
                    raise Exception(
                        "Compartment with OCID {0} either does not exist or "
                        "you do not have permission to access it.".format(
                            compartment_ocid
                        )
                    )
            else:
                if not fetch_hosts_from_subcompartments:
                    return [compartment_with_ocid]
                return self.get_sub_compartments(compartment_with_ocid)

        if not self.params["tenancy"]:
            raise Exception(
                "Tenancy OCID required to get the compartments in the tenancy."
            )

        try:
            tenancy = call_with_backoff(
                self.identity_client.get_compartment,
                compartment_id=self.params["tenancy"],
            ).data
        except ServiceError as se:
            if se.status == 404:
                raise Exception(
                    "Either tenancy ocid is invalid or need inspect permission on root compartment to get the "
                    "compartments in the tenancy."
                )

        all_compartments = [tenancy] + [
            compartment
            for compartment in list_all_resources(
                target_fn=self.identity_client.list_compartments,
                compartment_id=self.params["tenancy"],
                compartment_id_in_subtree=True,
            )
            if self.filter_resource(
                compartment, lifecycle_state=self.LIFECYCLE_ACTIVE_STATE
            )
        ]

        # return all the compartments if compartment_name is not passed
        if not compartment_name:
            return all_compartments

        if compartment_name == tenancy.name:
            # return all the compartments when fetch_hosts_from_subcompartments is true
            if fetch_hosts_from_subcompartments:
                return all_compartments
            else:
                return [tenancy]

        if not parent_compartment_ocid:
            parent_compartment_ocid = tenancy.id

        compartment_with_name = None
        for compartment in all_compartments:
            if (
                compartment.name == compartment_name
                and compartment.compartment_id == parent_compartment_ocid
            ):
                compartment_with_name = compartment
                break

        if not compartment_with_name:
            raise Exception(
                "Compartment with name {0} not found.".format(compartment_name)
            )

        if not fetch_hosts_from_subcompartments:
            return [compartment_with_name]

        return self.get_sub_compartments(compartment_with_name)

    def get_sub_compartments(self, root):
        # OCI SDK does not support fetching sub-compartments for non root compartments
        # So traverse the compartment tree to fetch all the sub compartments
        compartments = []
        queue = deque()
        queue.append(root)
        while len(queue) > 0:
            parent_compartment = queue.popleft()
            compartments.append(parent_compartment)
            child_compartments = [
                compartment
                for compartment in list_all_resources(
                    target_fn=self.identity_client.list_compartments,
                    compartment_id=parent_compartment.id,
                )
                if self.filter_resource(
                    compartment, lifecycle_state=self.LIFECYCLE_ACTIVE_STATE
                )
            ]
            for child_compartment in child_compartments:
                queue.append(child_compartment)
        return compartments

    @staticmethod
    def filter_resource(resource, **kwargs):
        for key, val in six.iteritems(kwargs):
            if getattr(resource, key, None) != val:
                return False
        return True

    def get_instances(self, compartment_ocids):
        """Get and return instances from all the specified compartments and regions.

        :param compartment_ocids: List of compartment ocid's to fetch the instances from
        :return: dict with region as key and list of instances of the region as value
        """
        instances = defaultdict(list)

        if self.params["enable_parallel_processing"]:
            for region in self.regions:
                num_threads = min(
                    len(compartment_ocids), self.params["max_thread_count"]
                )
                self.log(
                    "Parallel processing enabled. Getting instances from {0} in {1} threads.".format(
                        region, num_threads
                    )
                )

                with self.pool(processes=num_threads) as pool:
                    get_filtered_instances_for_region = partial(
                        self.get_filtered_instances, region=region
                    )
                    lists_of_instances = pool.map(
                        get_filtered_instances_for_region, compartment_ocids
                    )
                for sublist in lists_of_instances:
                    instances[region].extend(sublist)

        else:
            for region in self.regions:
                for compartment_ocid in compartment_ocids:
                    instances[region].extend(
                        self.get_filtered_instances(compartment_ocid, region)
                    )

        return instances

    def get_filtered_instances(self, compartment_ocid, region):
        try:
            compute_client = self.get_compute_client_for_region(region)
            self.log(
                "Listing all RUNNING instances from compartment: {0} and region: {1}".format(
                    compartment_ocid, region
                )
            )
            instances = list_all_resources(
                target_fn=compute_client.list_instances,
                compartment_id=compartment_ocid,
                lifecycle_state="RUNNING",
            )
            self.log(
                "All RUNNING instances from compartment {0}:{1}".format(
                    compartment_ocid, instances
                )
            )
            if self.params["freeform_tags"]:
                instances = [
                    instance
                    for instance in instances
                    if all(
                        instance.freeform_tags.get(key) == value
                        for key, value in six.iteritems(self.params["freeform_tags"])
                    )
                ]
                self.log(
                    "Instances in compartment {0} which match all the freeform tags: {1}".format(
                        compartment_ocid, instances
                    )
                )
            if self.params["defined_tags"]:
                instances = [
                    instance
                    for instance in instances
                    if all(
                        (instance.defined_tags.get(namespace, {})).get(key) == value
                        for namespace in self.params["defined_tags"]
                        for key, value in six.iteritems(
                            self.params["defined_tags"][namespace]
                        )
                    )
                ]
                self.log(
                    "Instances in compartment {0} which match all the freeform & defined tags: {1}".format(
                        compartment_ocid, instances
                    )
                )
            return instances
        except ServiceError as ex:
            if ex.status == 401:
                self.log(ex)
                raise
            self.log(ex)
            return []

    def get_host_name(self, vnic, region):
        virtual_nw_client = self.get_virtual_nw_client_for_region(region)
        if self.params["hostname_format"] == "fqdn":
            subnet = call_with_backoff(
                virtual_nw_client.get_subnet, subnet_id=vnic.subnet_id
            ).data
            vcn = call_with_backoff(
                virtual_nw_client.get_vcn, vcn_id=subnet.vcn_id
            ).data

            values = [
                vnic.hostname_label,
                subnet.dns_label,
                vcn.dns_label,
                "oraclevcn.com",
            ]
            fqdn = None if None in values else ".".join(values)
            self.log("FQDN for VNIC: {0} is {1}.".format(vnic.id, fqdn))
            return fqdn

        elif self.params["hostname_format"] == "private_ip":
            self.log(
                "Private IP for VNIC: {0} is {1}.".format(vnic.id, vnic.private_ip)
            )
            return vnic.private_ip

        self.log("Public IP for VNIC: {0} is {1}.".format(vnic.id, vnic.public_ip))
        return vnic.public_ip

    def build_inventory_for_instance(self, instance, region):
        """Build and return inventory for an instance"""
        try:
            self.log("Building inventory for instance {0}".format(instance.id))
            instance_inventory = {}
            compute_client = self.get_compute_client_for_region(region)
            virtual_nw_client = self.get_virtual_nw_client_for_region(region)
            compartment = self.compartments[instance.compartment_id]

            instance_vars = to_dict(instance)

            common_groups = set("all")
            # Group by availability domain
            ad = self.sanitize(instance.availability_domain)
            common_groups.add(ad)

            # Group by compartments
            compartment_name = self.sanitize(compartment.name)
            common_groups.add(compartment_name)

            # Group by region
            region_grp = self.sanitize("region_" + self.get_region_short_name(region))
            common_groups.add(region_grp)

            # Group by image OCID
            if hasattr(instance.source_details, "image_id"):
                common_groups.add(instance.source_details.image_id)

            # Group by instance shape
            shape_name = self.sanitize(instance.shape)
            common_groups.add(shape_name)

            # Group by freeform tags tag_key=value
            for key in instance.freeform_tags:
                tag_group_name = self.sanitize(
                    "tag_" + key + "=" + instance.freeform_tags[key]
                )
                common_groups.add(tag_group_name)

            # Group by defined tags
            for namespace in instance.defined_tags:
                for key in instance.defined_tags[namespace]:
                    defined_tag_group_name = self.sanitize(
                        namespace
                        + "#"
                        + key
                        + "="
                        + instance.defined_tags[namespace][key]
                    )
                    common_groups.add(defined_tag_group_name)

            # Group by metadata
            for key in instance.metadata:
                # Group using only custom metadata keys.
                if key not in ["ssh_authorized_keys", "user_data"]:
                    group_name = self.sanitize(key + "=" + instance.metadata[key])
                    common_groups.add(group_name)

            # Group by extended metadata
            for key in instance.extended_metadata:
                if key not in ["ssh_authorized_keys", "user_data"]:
                    ext_metadata_grp_name = self.sanitize(
                        key + "=" + str(instance.extended_metadata[key])
                    )
                    common_groups.add(ext_metadata_grp_name)

            vnic_attachments = [
                vnic_attachment
                for vnic_attachment in list_all_resources(
                    target_fn=compute_client.list_vnic_attachments,
                    compartment_id=compartment.id,
                    instance_id=instance.id,
                )
                if self.filter_resource(
                    vnic_attachment, lifecycle_state=self.LIFECYCLE_ATTACHED_STATE
                )
            ]

            for vnic_attachment in vnic_attachments:

                vnic = call_with_backoff(
                    virtual_nw_client.get_vnic, vnic_id=vnic_attachment.vnic_id
                ).data
                self.log(
                    "VNIC {0} is attached to instance {1}.".format(
                        vnic.id, vnic_attachment.instance_id
                    )
                )

                host_name = self.get_host_name(vnic, region=region)

                # Skip host which is not addressable using hostname_format
                if not host_name:
                    if self.params["strict_hostname_checking"] == "yes":
                        raise Exception(
                            "Instance with OCID: {0} does not have a valid hostname.".format(
                                vnic_attachment.instance_id
                            )
                        )
                    self.log(
                        "Skipped instance with OCID:" + vnic_attachment.instance_id
                    )
                    return None

                if self.args.host and self.args.host != host_name:
                    self.log("Skipped instance with hostname:" + host_name)
                    continue

                host_name = self.sanitize(host_name)

                groups = set(common_groups)

                subnet = call_with_backoff(
                    virtual_nw_client.get_subnet, subnet_id=vnic.subnet_id
                ).data
                groups.add(subnet.id)
                groups.add(subnet.vcn_id)

                # Group by security list
                for sec_list_id in subnet.security_list_ids:
                    groups.add(sec_list_id)

                self.log("Creating inventory for host {0}.".format(host_name))
                self.create_instance_inventory_for_host(
                    instance_inventory,
                    host_name,
                    vars=instance_vars,
                    groups=groups,
                    parents=[ad, subnet.vcn_id, region_grp, region_grp],
                    children=[subnet.id, subnet.id, ad, subnet.vcn_id],
                )

            return instance_inventory

        except ServiceError as ex:
            if ex.status == 401:
                self.log(ex)
                raise
            self.log(ex)

    @staticmethod
    def create_instance_inventory_for_host(
        instance_inventory, host_name, vars, groups, parents, children
    ):
        instance_inventory.setdefault(host_name, {"groups": {}, "vars": {}})
        instance_inventory[host_name]["vars"] = vars
        for group in groups:
            instance_inventory[host_name]["groups"].setdefault(group, {"children": []})
        for parent, child in zip(parents, children):
            instance_inventory[host_name]["groups"][parent]["children"].append(child)
        return instance_inventory

    def merge_instance_inventories(self, instance_inventories):
        """Merge all instance inventories into the main inventory"""
        for instance_inventory in instance_inventories:
            if instance_inventory:
                for host_name, host_inventory in six.iteritems(instance_inventory):
                    self.add_host(
                        host_name,
                        vars=host_inventory["vars"],
                        groups=host_inventory["groups"],
                    )

    @contextmanager
    def pool(self, **kwargs):
        pool = ThreadPool(**kwargs)
        try:
            yield pool
        finally:
            pool.close()
            # wait for all the instances to be processed
            pool.join()
            # terminate the pool
            pool.terminate()

    def build_inventory(self):
        self.log("Building inventory.")

        # Compartments(including the root compartment) from which the instances are to be retrieved.
        self.compartments = dict(
            (compartment.id, compartment)
            for compartment in self.get_compartments(
                compartment_ocid=self.params["compartment_ocid"],
                parent_compartment_ocid=self.params["parent_compartment_ocid"],
                compartment_name=self.params["compartment"],
                fetch_hosts_from_subcompartments=self.params[
                    "fetch_hosts_from_subcompartments"
                ],
            )
        )

        if not self.compartments:
            self.log("No compartments matching the criteria.")
            return

        self.log("Building inventory for compartments {0}".format(self.compartments))

        instances_by_region = self.get_instances(self.compartments)

        self.log("Building inventory for instances {0}".format(instances_by_region))

        instance_inventories = []

        if self.params["enable_parallel_processing"]:
            instance_inventories = []
            for region in instances_by_region:
                instances = instances_by_region[region]
                if instances:
                    num_threads = min(len(instances), self.params["max_thread_count"])
                    self.log(
                        "Parallel processing enabled. Building individual instance inventories in {0} threads.".format(
                            num_threads
                        )
                    )
                    with self.pool(processes=num_threads) as pool:
                        instance_inventories.extend(
                            pool.map(
                                partial(
                                    self.build_inventory_for_instance, region=region
                                ),
                                instances,
                            )
                        )

        else:
            instance_inventories = [
                self.build_inventory_for_instance(instance, region)
                for region in instances_by_region
                for instance in instances_by_region[region]
            ]

        self.log("Instance inventories: {0}".format(instance_inventories))
        self.log("Merging instance inventories.")

        self.merge_instance_inventories(instance_inventories)

    def fail(self, message=None, exit_code=1, stacktrace=None):
        if stacktrace:
            self.log(stacktrace)
        if message:
            print(message, file=sys.stderr)
        sys.exit(exit_code)

    def parse_cli_args(self):
        parser = argparse.ArgumentParser(
            description="Produce an Ansible Inventory file based on OCI"
        )

        parser.add_argument(
            "--list",
            action="store_true",
            default=True,
            help="List instances (default: True)",
        )

        parser.add_argument(
            "--host",
            action="store",
            help="Get all information about a compute instance",
        )

        parser.add_argument(
            "-config",
            "--config-file",
            action="store",
            dest="config_file",
            help="OCI config file location",
        )

        parser.add_argument(
            "--profile",
            action="store",
            dest="profile",
            help="OCI config profile for connecting to OCI",
        )

        parser.add_argument(
            "--tenancy",
            action="store",
            help="OCID of the tenancy for which dynamic inventory must be generated.",
        )

        parser.add_argument(
            "--compartment-ocid",
            action="store",
            help="OCID of the compartment for which dynamic inventory must be generated. If specified, any value "
            "specified for compartment and parent-compartment-ocid options is ignored.",
        )

        parser.add_argument(
            "--compartment",
            action="store",
            help="Name of the compartment for which dynamic inventory must be generated. If you want "
            "to generate a dynamic inventory for the root compartment of the tenancy, specify the "
            "tenancy name as the name of the compartment.",
        )

        parser.add_argument(
            "--parent-compartment-ocid",
            action="store",
            help="Only valid when --compartment is set. Parent compartment ocid of the specified compartment."
            "Defaults to tenancy ocid.",
        )

        parser.add_argument(
            "--fetch-hosts-from-subcompartments",
            action="store_true",
            default=False,
            help="Only valid when --compartment is set. Default is false. When set to true, inventory "
            "is built with the entire hierarchy of the given compartment.",
        )

        parser.add_argument(
            "--refresh-cache",
            "-r",
            action="store_true",
            default=False,
            help="Force refresh of cache by making API requests to OCI. Use this option whenever you are "
            "building inventory with new filter options to avoid reading cached inventory. "
            "(default: False - use cache files)",
        )

        parser.add_argument(
            "--debug",
            action="store_true",
            default=False,
            help="Send debug messages to STDERR",
        )

        parser.add_argument(
            "--auth",
            action="store",
            choices=["api_key", "instance_principal"],
            help="The type of authentication to use for making API requests. By default, the API key "
            "in your config will be used. Set this option to `instance_principal` to use instance "
            "principal based authentication. This value can also be provided in the "
            "OCI_ANSIBLE_AUTH_TYPE environment variable.",
        )

        parser.add_argument(
            "--enable-parallel-processing",
            action="store_true",
            help="Inventory generation for tenants with huge number of instances might take a long time."
            "When this flag is set, the inventory script uses thread pools to parallelise the "
            "inventory generation.",
        )

        parser.add_argument(
            "--max-thread-count",
            action="store",
            type=int,
            help="Only valid when --enable-parallel-processing is set. When set, this script uses threads to "
            "improve the performance of building the inventory. This option specifies the maximum number of "
            "threads to use. Defaults to 50. This value can also be provided in the settings config file.",
        )

        parser.add_argument(
            "--freeform-tags",
            action="store",
            help='Freeform tags provided as a string in valid JSON format. Example: { "stage":  "dev", "app": "demo"} '
            "Use this option to build inventory of only those hosts which are tagged with all the specified "
            "key-value pairs.",
        )

        parser.add_argument(
            "--defined-tags",
            action="store",
            help="Defined tags provided as a string in valid JSON format. "
            'Example: {"namespace1": {"key1": "value1", "key2": "value2"}, "namespace2": {"key": "value"}} '
            "Use this option to build inventory of only those hosts which are tagged with all the specified "
            "key-value pairs.",
        )

        parser.add_argument(
            "--regions",
            action="store",
            help="Comma separated region names to build the inventory from. Default is the region specified in "
            "the config. Please specify 'all' to build inventory from all the subscribed regions. "
            "Example: us-ashburn-1,us-phoenix-1",
        )

        parser.add_argument(
            "--exclude-regions",
            action="store",
            help="Comma separated region names to exclude while building the inventory. "
            "Example: us-ashburn-1,uk-london-1",
        )

        parser.add_argument(
            "--hostname-format",
            action="store",
            choices=["fqdn", "private_ip", "public_ip"],
            help="Host naming format to use.",
        )

        parser.add_argument(
            "--strict-hostname-checking",
            action="store",
            choices=["yes", "no"],
            help="The default behavior of this script is to ignore hosts without valid hostnames(determined according "
            "to the hostname format). When set to yes, the script fails when any host does not have a "
            "valid hostname.",
        )

        self.args = parser.parse_args()

    def read_settings_config(self, boolean_options, dict_options):
        if self.settings_config.has_section("oci"):
            for option in self.settings_config.options("oci"):
                if option in boolean_options:
                    self.params[option] = self.settings_config.getboolean("oci", option)
                elif option in dict_options:
                    self.params[option] = json.loads(
                        self.settings_config.get("oci", option)
                    )
                else:
                    self.params[option] = self.settings_config.get("oci", option)

    def sanitize(self, word):
        # regex represents an invalid non-alphanumeric character except UNDERSCORE, HASH, EQUALS and DOT
        regex = r"[^A-Za-z0-9_#=."
        if self.params["sanitize_names"]:
            if not self.params["replace_dash_in_names"]:
                # Add DASH as a valid character in regex.
                regex += r"-"

            # Replace all invalid characters with UNDERSCORE
            return re.sub(regex + "]", "_", word)
        return word

    def add_host(self, host, groups=None, vars=None):
        """Add host to the inventory"""
        if not groups:
            groups = set("all")
        for group in groups:
            self.add_group(group, children=groups[group].setdefault("children", []))
            if host not in self.inventory[group]["hosts"]:
                self.inventory[group]["hosts"].append(host)
        if vars:
            self.add_host_vars(host, vars)

    def add_host_vars(self, host, vars):
        """Add vars to the host in inventory"""
        self.inventory["_meta"]["hostvars"][host] = vars

    def add_group(self, group, children=None):
        """Add group to the inventory"""
        self.inventory.setdefault(group, {"hosts": []})
        if children:
            for child in children:
                self.add_child_group(group, child)

    def add_child_group(self, parent, child):
        """Add child group to the inventory"""
        self.add_group(parent)
        children = self.inventory[parent].setdefault("children", [])
        if child not in children:
            children.append(child)


if __name__ == "__main__":
    if not HAS_OCI_PY_SDK:
        sys.exit(
            "OCI Python SDK is not installed. Try `pip install oci` to install OCI Python SDK."
        )
    OCIInventory()
