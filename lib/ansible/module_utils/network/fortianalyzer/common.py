# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Fortinet, Inc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


# BEGIN STATIC DATA AND MESSAGES
class FAZMethods:
    GET = "get"
    SET = "set"
    EXEC = "exec"
    EXECUTE = "exec"
    UPDATE = "update"
    ADD = "add"
    DELETE = "delete"
    REPLACE = "replace"
    CLONE = "clone"
    MOVE = "move"


BASE_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}


# FAZ RETURN CODES
FAZ_RC = {
    "faz_return_codes": {
        0: {
            "msg": "OK",
            "changed": True,
            "stop_on_success": True
        },
        -100000: {
            "msg": "Module returned without actually running anything. "
            "Check parameters, and please contact the authors if needed.",
            "failed": True
        },
        -2: {
            "msg": "Object already exists.",
            "skipped": True,
            "changed": False,
            "good_codes": [0, -2]
        },
        -6: {
            "msg": "Invalid Url. Sometimes this can happen because the path is mapped to a hostname or object that"
            " doesn't exist. Double check your input object parameters."
        },
        -3: {
            "msg": "Object doesn't exist.",
            "skipped": True,
            "changed": False,
            "good_codes": [0, -3]
        },
        -10131: {
            "msg": "Object dependency failed. Do all named objects in parameters exist?",
            "changed": False,
            "skipped": True
        },
        -9998: {
            "msg": "Duplicate object. Try using mode='set', if using add. STOPPING. Use 'ignore_errors=yes' in playbook"
            "to override and mark successful.",
        },
        -20042: {
            "msg": "Device Unreachable.",
            "skipped": True
        },
        -10033: {
            "msg": "Duplicate object. Try using mode='set', if using add.",
            "changed": False,
            "skipped": True
        },
        -10000: {
            "msg": "Duplicate object. Try using mode='set', if using add.",
            "changed": False,
            "skipped": True
        },
        -20010: {
            "msg": "Device already added to FortiAnalyzer. Serial number already in use.",
            "good_codes": [0, -20010],
            "changed": False,
            "stop_on_failure": False
        },
        -20002: {
            "msg": "Invalid Argument -- Does this Device exist on FortiAnalyzer?",
            "changed": False,
            "skipped": True,
        }
    }
}

DEFAULT_RESULT_OBJ = (-100000, {"msg": "Nothing Happened. Check that handle_response is being called!"})
FAIL_SOCKET_MSG = {"msg": "Socket Path Empty! The persistent connection manager is messed up. "
                   "Try again in a few moments."}


# BEGIN ERROR EXCEPTIONS
class FAZBaseException(Exception):
    """Wrapper to catch the unexpected"""

    def __init__(self, msg=None, *args, **kwargs):
        if msg is None:
            msg = "An exception occurred within the fortianalyzer.py httpapi connection plugin."
        super(FAZBaseException, self).__init__(msg, *args)

# END ERROR CLASSES


# BEGIN CLASSES
class FAZCommon(object):

    @staticmethod
    def format_request(method, url, *args, **kwargs):
        """
        Formats the payload from the module, into a payload the API handler can use.

        :param url: Connection URL to access
        :type url: string
        :param method: The preferred API Request method (GET, ADD, POST, etc....)
        :type method: basestring
        :param kwargs: The payload dictionary from the module to be converted.

        :return: Properly formatted dictionary payload for API Request via Connection Plugin.
        :rtype: dict
        """

        params = [{"url": url}]
        if args:
            for arg in args:
                params[0].update(arg)
        if kwargs:
            keylist = list(kwargs)
            for k in keylist:
                kwargs[k.replace("__", "-")] = kwargs.pop(k)
            if method == "get" or method == "clone":
                params[0].update(kwargs)
            else:
                if kwargs.get("data", False):
                    params[0]["data"] = kwargs["data"]
                else:
                    params[0]["data"] = kwargs
        return params

    @staticmethod
    def split_comma_strings_into_lists(obj):
        """
        Splits a CSV String into a list.  Also takes a dictionary, and converts any CSV strings in any key, to a list.

        :param obj: object in CSV format to be parsed.
        :type obj: str or dict

        :return: A list containing the CSV items.
        :rtype: list
        """
        return_obj = ()
        if isinstance(obj, dict):
            if len(obj) > 0:
                for k, v in obj.items():
                    if isinstance(v, str):
                        new_list = list()
                        if "," in v:
                            new_items = v.split(",")
                            for item in new_items:
                                new_list.append(item.strip())
                            obj[k] = new_list
                return_obj = obj
        elif isinstance(obj, str):
            return_obj = obj.replace(" ", "").split(",")

        return return_obj

    @staticmethod
    def cidr_to_netmask(cidr):
        """
        Converts a CIDR Network string to full blown IP/Subnet format in decimal format.
        Decided not use IP Address module to keep includes to a minimum.

        :param cidr: String object in CIDR format to be processed
        :type cidr: str

        :return: A string object that looks like this "x.x.x.x/y.y.y.y"
        :rtype: str
        """
        if isinstance(cidr, str):
            cidr = int(cidr)
            mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
            return (str((0xff000000 & mask) >> 24) + '.'
                    + str((0x00ff0000 & mask) >> 16) + '.'
                    + str((0x0000ff00 & mask) >> 8) + '.'
                    + str((0x000000ff & mask)))

    @staticmethod
    def paramgram_child_list_override(list_overrides, paramgram, module):
        """
        If a list of items was provided to a "parent" paramgram attribute, the paramgram needs to be rewritten.
        The child keys of the desired attribute need to be deleted, and then that "parent" keys' contents is replaced
        With the list of items that was provided.

        :param list_overrides: Contains the response from the FortiAnalyzer.
        :type list_overrides: list
        :param paramgram: Contains the paramgram passed to the modules' local modify function.
        :type paramgram: dict
        :param module: Contains the Ansible Module Object being used by the module.
        :type module: classObject

        :return: A new "paramgram" refactored to allow for multiple entries being added.
        :rtype: dict
        """
        if len(list_overrides) > 0:
            for list_variable in list_overrides:
                try:
                    list_variable = list_variable.replace("-", "_")
                    override_data = module.params[list_variable]
                    if override_data:
                        del paramgram[list_variable]
                        paramgram[list_variable] = override_data
                except BaseException as e:
                    raise FAZBaseException("Error occurred merging custom lists for the paramgram parent: " + str(e))
        return paramgram

    @staticmethod
    def syslog(module, msg):
        try:
            module.log(msg=msg)
        except BaseException:
            pass


# RECURSIVE FUNCTIONS START
def prepare_dict(obj):
    """
    Removes any keys from a dictionary that are only specific to our use in the module. FortiAnalyzer will reject
    requests with these empty/None keys in it.

    :param obj: Dictionary object to be processed.
    :type obj: dict

    :return: Processed dictionary.
    :rtype: dict
    """

    list_of_elems = ["mode", "adom", "host", "username", "password"]

    if isinstance(obj, dict):
        obj = dict((key, prepare_dict(value)) for (key, value) in obj.items() if key not in list_of_elems)
    return obj


def scrub_dict(obj):
    """
    Removes any keys from a dictionary that are EMPTY -- this includes parent keys. FortiAnalyzer doesn't
    like empty keys in dictionaries

    :param obj: Dictionary object to be processed.
    :type obj: dict

    :return: Processed dictionary.
    :rtype: dict
    """

    if isinstance(obj, dict):
        return dict((k, scrub_dict(v)) for k, v in obj.items() if v and scrub_dict(v))
    else:
        return obj
