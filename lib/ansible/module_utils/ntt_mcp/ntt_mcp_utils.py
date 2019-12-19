# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Ken Sinfield <ken.sinfield@cis.ntt.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Ken Sinfield (@kensinfield)
#   - get_credentials from Aimon Bustardo <aimon.bustardo@dimensiondata.com>
#
# Common methods to be used by versious module components

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    import configparser
    HAS_CONFIGPARSER = True
except ImportError:
    HAS_CONFIGPARSER = False
import string
import random
from os.path import expanduser
from os import environ
import struct
import socket
try:
    from ipaddress import ip_address as IP
    HAS_IPADDRESS = True
except ImportError:
    HAS_IPADDRESS = False
from ansible.module_utils.ntt_mcp.ntt_mcp_config import API_ENDPOINTS

# Python3 workaround for unicode function so the same code can be used with ipaddress later
try:
    unicode('')
except NameError:
    unicode = str


def IP_TO_INT(ip):
    return struct.unpack('!I', socket.inet_aton(ip))[0]


def INT_TO_IP(i):
    return socket.inet_ntoa(struct.pack('!I', i))


def utils_check_imports():
    """
    Check if the required Python modules for ntt_mcp_utils are installed
    """
    if not HAS_CONFIGPARSER:
        raise ImportError('Missing Python module: configparser')
    if not HAS_IPADDRESS:
        raise ImportError('Missing Python module: ipaddress')


def return_object(return_type='data'):
    """
    Create a generic return object for Ansible module_utils
    :arg return_type: The type of object to be returned
    :returns: A generic return Object
    """
    return_data = {}
    return_data['count'] = 0
    return_data[return_type] = []
    return return_data


def get_credentials(module):
    """
    Determine the Cloud Control API credentials to be Used
    """
    return_data = {
        'user_id': None,
        'password': None,
        'api_endpoint': None,
        'api_version': None
    }

    # Check Imports
    try:
        utils_check_imports()
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))

    # Attempt to grab from environment
    if 'NTTMCP_USER' in environ and 'NTTMCP_PASSWORD' in environ:
        return_data['user_id'] = environ['NTTMCP_USER']
        return_data['password'] = environ['NTTMCP_PASSWORD']
    # Environment failed try dot file
    else:
        try:
            home = expanduser('~')
            config = configparser.RawConfigParser()
            config.read("%s/.nttmcp" % home)
            return_data['user_id'] = config.get("nttmcp", "NTTMCP_USER")
            return_data['password'] = config.get("nttmcp", "NTTMCP_PASSWORD")
        except AttributeError:
            module.fail_json(msg='Could not read the format of the .nttmcp file. Check the syntax of the file.')
        except (configparser.NoSectionError, configparser.ParsingError, configparser.NoOptionError) as e:
            module.fail_json(msg='Error in the .nttmcp credential file syntax: {0}'.format(e))

    # Check if a custom API endpoint or version has been supplied
    try:
        if 'NTTMCP_API' in environ:
            return_data['api_endpoint'] = environ.get('NTTMCP_API')
        if 'NTTMCP_API_VERSION' in environ:
            return_data['api_version'] = environ.get('NTTMCP_API_VERSION')
        else:
            home = expanduser('~')
            config = configparser.RawConfigParser()
            config.read("%s/.nttmcp" % home)
            return_data['api_endpoint'] = config.get('nttmcp', 'NTTMCP_API')
            return_data['api_version'] = config.get('nttmcp', 'NTTMCP_API_VERSION')
    except (configparser.NoSectionError, configparser.ParsingError, configparser.NoOptionError):
        pass

    # Return False if either are not found
    if return_data.get('user_id') is None or return_data.get('password') is None:
        return False

    # Both found, return data
    return return_data


def generate_password():
    """
    Generate a random password
    """
    length = random.randint(12, 19)
    pwd = []
    count = 0
    while count != length:
        select = random.randint(0, 2)
        if select == 0:
            pwd.append(random.choice(string.ascii_lowercase))
        elif select == 1:
            pwd.append(random.choice(string.ascii_uppercase))
        elif select == 2:
            pwd.append(str(random.randint(0, 9)))
        count = count + 1

    random.shuffle(pwd)
    pwd_string = ''.join(pwd)

    return pwd_string


def get_ntt_mcp_regions():
    """
    Return a list of Cloud Control regions
    """
    regions = []
    for region in API_ENDPOINTS:
        regions.append(region)
    return regions


def get_ip_version(ip_address):
    """
    Return the IP version of the provided IP address
    :arg ip_address: The IP address to return the version of
    :returns: The version of the IP address as an integer
    """
    version = None
    # Attempt to determine the IP version from the IP address, fail if the IP address is invalid
    if ip_address:
        try:
            addr = IP(unicode(ip_address))
            version = addr.version
        except ValueError:
            raise Exception('Invalid IP address: {0}'.format(ip_address))
        if version not in [4, 6]:
            raise Exception('Could not determine the IP version from the provided IP address {0}'.format(ip_address))
    else:
        raise Exception('A valid IPv4 or IPv6 address is required')
    return version


def is_ip_private(ip_address):
    """
    Determines if an IPv4 address is considered a RFC 1918 address
    :arg ip_address: The IP address to return the RFC 1918 status of
    :returns: boolean
    """
    if ip_address:
        try:
            addr = IP(unicode(ip_address))
            return addr.is_private
        except ValueError:
            raise Exception('Invalid IP address: {0}'.format(ip_address))
    else:
        raise Exception('A valid IP address is required')


def compare_json(a, b, parent):
    """
    Compare two JSON objects and return a dict of if they are different and
    any differences between the two objects
    :arg a: JSON object 1
    :arg b: JSON object 2
    :arg parent: The parent object - used when recursing through child objects
    :returns: dict containing any differences
    """
    modified = {
        'changes': False,
        'updated': {},
        'removed': {},
        'added': {}
    }
    try:
        for tag in a:
            if type(a[tag]) is dict:
                if tag in b:
                    r_modified = compare_json(a[tag], b[tag], tag)
                    if r_modified['updated']:
                        modified['updated'][str(tag)] = r_modified['updated']
                        modified['changes'] = r_modified['changes']
                    if r_modified['removed']:
                        modified['removed'][str(tag)] = r_modified['removed']
                        modified['changes'] = r_modified['changes']
                    if r_modified['added']:
                        modified['added'][str(tag)] = r_modified['added']
                        modified['changes'] = r_modified['changes']
                else:
                    modified['added'][str(tag)] = str(a[tag])
            if tag not in b:
                modified['added'][str(tag)] = str(a[tag])
                modified['changes'] = True
            else:
                if type(a[tag]) is list:
                    a[tag].sort()
                if type(b[tag]) is list:
                    b[tag].sort()
                if a[tag] != b[tag] and not type(a[tag]) is dict:
                    modified['changes'] = True
                    if parent != "":
                        modified['updated'][str(tag)] = {
                            'old_value': str(b[tag]),
                            'new_value': str(a[tag])
                        }
                    else:
                        modified['updated'][str(tag)] = {
                            'old_value': str(b[tag]),
                            'new_value': str(a[tag])
                        }
        for tag in b:
            if tag not in a:
                modified['changes'] = True
                modified['removed'][str(tag)] = str(b[str(tag)])
    except (KeyError, IndexError, AttributeError, TypeError):
        return False
    return modified
