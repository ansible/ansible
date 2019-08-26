#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 NTT Communictions Cloud Infrastructure Services
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#   - Ken Sinfield (@kensinfield)
#   - get_credentials from Aimon Bustardo <aimon.bustardo@dimensiondata.com>
#
# Common methods to be used by versious module components

from __future__ import (absolute_import, division, print_function)

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


IP_TO_INT = lambda ip_address: struct.unpack('!I', socket.inet_aton(ip_address))[0]
INT_TO_IP = lambda i: socket.inet_ntoa(struct.pack('!I', i))

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
    user_id = None
    password = None

    # Check Imports
    try:
        utils_check_imports()
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))

    # Attempt to grab from environment
    if 'NTTMCP_USER' in environ and 'NTTMCP_PASSWORD' in environ:
        user_id = environ['NTTMCP_USER']
        password = environ['NTTMCP_PASSWORD']

    # Environment failed try dot file
    elif user_id is None or password is None:
        try:
            home = expanduser('~')
            config = configparser.RawConfigParser()
            config.read("%s/.nttmcp" % home)
            user_id = config.get("nttmcp", "NTTMCP_USER")
            password = config.get("nttmcp", "NTTMCP_PASSWORD")
        except AttributeError:
            module.fail_json(msg='Could not read the format of the .nttmcp file. Check the syntax of the file.')
        except configparser.NoSectionError as e:
            module.fail_json(msg='Error in the .nttmcp credential file syntax: {0}'.format(e))

    else:
        module.fail_json(msg='Could not locate credentials in either the environment variables or .nttmcp file in the users home directory')

    # Return False if either are not found
    if user_id is None or password is None:
        return False

    # Both found, return data
    return (user_id, password)

def generate_password():
    """
    Generate a random password
    """
    length = random.randint(12, 19)
    #special_characters = str(string.punctuation).translate(None, '<>\'\\%|')
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
        #else:
        #    pwd.append(random.choice(special_characters))
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
        except:
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
        except:
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
            if not tag in b:
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
                            'oldval': str(b[tag]),
                            'newval': str(a[tag])
                        }
                    else:
                        modified['updated'][str(tag)] = {
                            'oldval': str(b[tag]),
                            'newval': str(a[tag])
                        }
        for tag in b:
            if not tag in a:
                modified['changes'] = True
                modified['removed'][str(tag)] = str(b[str(tag)])
    except Exception as e:
        return False
    return modified
