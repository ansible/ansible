# Copyright (c) 2017 Kyle Haley, <kylephaley@gmail.com>

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import ast
import json

from ansible.module_utils.six import iteritems
from ansible.module_utils.urls import open_url

"""
This is the general construction of the validation map passed in.
URI_CONFIG_MAP["uri_key"] is a substring of the target artifactory URL,
such as "api/repositories" or "api/security/groups". The need for URL substring
exists since some modules may need to cover multiple URLs, such as a security
module, which may need to touch on
"api/security/groups" or "api/security/users" or "api/security/permissions".

KEY_CONFIG_MAP = {
    "config_key":
        {"valid_values": list(),
         "required_keys": list(),
         "values_require_keys": dict(),
         "always_required": bool}}

URI_CONFIG_MAP = {
    "uri_key": KEY_CONFIG_MAP}
"""


class ArtifactoryBase(object):
    def __init__(self, username=None, password=None,
                 auth_token=None, validate_certs=False, client_cert=None,
                 client_key=None, force_basic_auth=False, config_map=None):
        self.username = username
        self.password = password
        self.auth_token = auth_token

        self.validate_certs = validate_certs
        self.client_cert = client_cert
        self.client_key = client_key
        self.force_basic_auth = force_basic_auth

        self.config_map = config_map

        self.headers = {"Content-Type": "application/json"}
        if auth_token:
            self.headers["X-JFrog-Art-Api"] = auth_token

    def convert_config_to_dict(self, config):
        if isinstance(config, dict):
            return config
        else:
            error_occurred = False
            message = ""
            try:
                test_dict = ast.literal_eval(config)
                if isinstance(test_dict, dict):
                    config = test_dict
                else:
                    raise ValueError()
            except ValueError as ve:
                error_occurred = True
                message = str(ve)
            except SyntaxError as se:
                error_occurred = True
                message = str(se)

            if error_occurred:
                raise ConfigValueTypeMismatch("Configuration data provided "
                                              "is not valid json.\n %s"
                                              % message)
        return config

    def serialize_config_data(self, config_data):
        if not config_data or not isinstance(config_data, dict):
            raise InvalidConfigurationData("Config is null, empty, or is not"
                                           " a dictionary.")
        serial_config_data = json.dumps(config_data)
        return serial_config_data

    def query_artifactory(self, url, method, data=None):
        if self.auth_token:
            response = open_url(url, data=data, headers=self.headers,
                                method=method,
                                validate_certs=self.validate_certs,
                                client_cert=self.client_cert,
                                client_key=self.client_key,
                                force_basic_auth=self.force_basic_auth)
        else:
            response = open_url(url, data=data, headers=self.headers,
                                method=method,
                                validate_certs=self.validate_certs,
                                client_cert=self.client_cert,
                                client_key=self.client_key,
                                force_basic_auth=self.force_basic_auth,
                                url_username=self.username,
                                url_password=self.password)
        return response

    def validate_config_values(self, url, config_dict):
        validation_dict = self.get_uri_key_map(url, self.config_map)
        if not validation_dict or isinstance(validation_dict, bool):
            return
        for config_key in config_dict:
            if config_key in validation_dict:
                if "valid_values" in validation_dict[config_key]:
                    valid_values = validation_dict[config_key]["valid_values"]
                    config_val = config_dict[config_key]
                    if valid_values and config_val not in valid_values:
                        except_message = ("'%s' is not a valid value for "
                                          "key '%s'"
                                          % (config_val, config_key))
                        raise InvalidConfigurationData(except_message)

    def get_uri_key_map(self, url, uri_config_map):
        if not url or not uri_config_map:
            raise InvalidConfigurationData("url or config is None or empty."
                                           " url: %s, config: %s"
                                           % (url, uri_config_map))
        temp = None
        for uri_substr in uri_config_map:
            if uri_substr in url:
                temp = uri_config_map[uri_substr]
                break
        if temp:
            return temp
        else:
            raise InvalidArtifactoryURL("The url '%s' could not be "
                                        "mapped to a known set of "
                                        "configuration rules." % url)

    def validate_config_required_keys(self, url, config_dict):
        req_keys = self.get_always_required_keys(url, config_dict)
        for required in req_keys:
            if required not in config_dict:
                message = ("%s key is missing from config." % required)
                raise InvalidConfigurationData(message)
        return req_keys

    def get_always_required_keys(self, url, config_dict):
        """Return keys that are always required for creating a repo."""
        validation_dict = self.get_uri_key_map(url, self.config_map)
        req_keys = list()
        # If the resulting validation dict is boolean True, then this just
        # verifies that the url is correct for this module. Return empty list.
        if not validation_dict or isinstance(validation_dict, bool):
            return req_keys
        for config_req in validation_dict:
            if "always_required" in validation_dict[config_req]:
                if validation_dict[config_req]["always_required"]:
                    req_keys.append(config_req)
        for config_key in config_dict:
            if config_key in validation_dict:
                valid_sub_dict = validation_dict[config_key]
                # If config_key exists, check if other keys are required.
                if "required_keys" in valid_sub_dict:
                    if isinstance(valid_sub_dict["required_keys"], list):
                        req_keys.extend(valid_sub_dict["required_keys"])
                    else:
                        raise InvalidConfigurationData(
                            "Values defined in 'required_keys' should be"
                            " a list. ['%s']['required_keys'] is not a"
                            " list." % config_key)
                # If config_key exists, check if the value of config_key
                # requires other keys.
                # If the value of the key 'rclass' is 'remote', then the 'url'
                # key must be defined. The value in the mapping should be a
                # list.
                if "values_require_keys" in valid_sub_dict:
                    config_value = config_dict[config_key]
                    val_req_keys = valid_sub_dict["values_require_keys"]
                    if val_req_keys and config_value in val_req_keys:
                        if isinstance(val_req_keys[config_value], list):
                            req_keys.extend(val_req_keys[config_value])
                        else:
                            raise InvalidConfigurationData(
                                "Values defined in in the dict"
                                " 'values_require_keys' should be lists."
                                " ['values_require_keys']['%s'] is not a"
                                " list." % config_value)
        return req_keys


class InvalidArtifactoryURL(Exception):
    pass


class ConfigValueTypeMismatch(Exception):
    pass


class InvalidConfigurationData(Exception):
    pass


TOP_LEVEL_FAIL = ("Conflicting config values. "
                  "top level parameter {1} != {0}[{1}]. "
                  "Only one config value need be set. ")


def validate_top_level_params(top_level_param, module, config, config_hash,
                              config_name, config_hash_name):
    """Validate top-level params against different configuration sources.
        These modules can have multiple configuration sources. If these sources
        have identical keys, but different values, aggregate error messages to
        alert the user for each one that does not match and the source.
        return a list of those messages.
    """
    validation_fail_messages = []
    config_hash_fail_msg = ""
    config_fail_msg = ""
    if not top_level_param or not module.params[top_level_param]:
        return validation_fail_messages
    value = module.params[top_level_param]
    if isinstance(value, list):
        value = sorted(value)
    if config_hash and top_level_param in config_hash:
        if isinstance(config_hash[top_level_param], list):
            config_hash[top_level_param] = sorted(config_hash[top_level_param])
        if value != config_hash[top_level_param]:
            config_hash_fail_msg = TOP_LEVEL_FAIL.format(config_hash_name,
                                                         top_level_param)
            validation_fail_messages.append(config_hash_fail_msg)
    if config and top_level_param in config:
        if isinstance(config[top_level_param], list):
            config[top_level_param] = sorted(config[top_level_param])
        if value != config[top_level_param]:
            config_fail_msg = TOP_LEVEL_FAIL.format(config_name,
                                                    top_level_param)
            validation_fail_messages.append(config_fail_msg)

    return validation_fail_messages


CONFIG_PARAM_FAIL = ("Conflicting config values. "
                     "{1}[{0}] != "
                     "{2}[{0}]. "
                     "Only one config value need be "
                     "set. ")


def validate_config_params(config, config_hash, config_name, config_hash_name):
    """Validate two different configuration sources.
        These modules can have multiple configuration sources. If these sources
        have identical keys, but different values, aggregate error messages to
        alert the user for each one that does not match and the source.
        return a list of those messages.
    """
    validation_fail_messages = []
    if not config_hash or not config:
        return validation_fail_messages
    for key, val in iteritems(config):
        if key in config_hash:
            if isinstance(config_hash[key], list):
                config_hash[key] = sorted(config_hash[key])
            if isinstance(config[key], list):
                config[key] = sorted(config[key])
            if config_hash[key] != config[key]:
                fail_msg = CONFIG_PARAM_FAIL.format(key, config_name,
                                                    config_hash_name)
                validation_fail_messages.append(fail_msg)
    return validation_fail_messages
