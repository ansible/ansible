# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 NTT Communications Cloud Infrastructure Services
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
# Author: Ken Sinfield (@kensinfield)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""
Module configuration parameters
"""

# HTTP HEADERS
HTTP_HEADERS = {'Content-Type': 'application/json',
                'Accept': 'application/json'}

# API Versions
API_VERSION = '2.10'

# API end-points
API_ENDPOINTS = {
    'na': {
        'name': 'North America (NA)',
        'host': 'api-na.mcp-services.net',
        'vendor': 'NTT'
    },
    'eu': {
        'name': 'Europe (EU)',
        'host': 'api-eu.mcp-services.net',
        'vendor': 'NTT'
    },
    'au': {
        'name': 'Australia (AU)',
        'host': 'api-au.mcp-services.net',
        'vendor': 'NTT'
    },
    'af': {
        'name': 'Africa (AF)',
        'host': 'api-mea.mcp-services.net',
        'vendor': 'NTT'
    },
    'ap': {
        'name': 'Asia Pacific (AP)',
        'host': 'api-ap.mcp-services.net',
        'vendor': 'NTT'
    },
    'ca': {
        'name': 'Canada (CA)',
        'host': 'api-canada.mcp-services.net',
        'vendor': 'NTT'
    }
}

# Valid server states
SERVER_STATES = ['NORMAL', 'PENDING_ADD', 'PENDING_CHANGE', 'PENDING_DELETE',
                 'FAILED_ADD', 'FAILED_CHANGE', 'FAILED_DELETE', 'REQUIRES_SUPPORT']

# Disk speeds that support variable IOPS
VARIABLE_IOPS = ['PROVISIONEDIOPS']

# The multiplier used to figure out the minimum valid IOPS for a disk. Multiplied by disk size
IOPS_MULTIPLIER = 3

# The maximum IOPS per GB of storage
MAX_IOPS_PER_GB = 15

# The maximum IOPS per disk
MAX_IOPS_PER_DISK = 15000

# The maximum size of a single disk on a server in GB. This can be overriden if need be
MAX_DISK_SIZE = 1000

# The maximum IOPS for a single disk. This can be overriden if need be
MAX_DISK_IOPS = 15000

# Valid disk speeds
DISK_SPEEDS = ['STANDARD', 'HIGHPERFORMANCE', 'ECONOMY', 'PROVISIONEDIOPS']

# Default API end-point for the base connection class.
DEFAULT_REGION = 'na'

# SCSI Adapter Types
SCSI_ADAPTER_TYPES = ['LSI_LOGIC_PARALLEL', 'LSI_LOGIC_SAS', 'VMWARE_PARAVIRTUAL', 'BUS_LOGIC']

# Disk Controller Types
DISK_CONTROLLER_TYPES = ['ideController', 'sataController', 'scsiController']

# NIC Adapter Types
NIC_ADAPTER_TYPES = ['E1000', 'VMXNET3']

# VIP Node States
VIP_NODE_STATES = ['ENABLED', 'DISABLED', 'FORCED_OFFLINE']

# Load Balancing Methods
LOAD_BALANCING_METHODS = ['ROUND_ROBIN', 'LEAST_CONNECTIONS_MEMBER', 'LEAST_CONNECTIONS_NODE', 'OBSERVED_MEMBER',
                          'OBSERVED_NODE', 'PREDICTIVE_MEMBER', 'PREDICTIVE_NODE']

# Service Actions for VIP Pools
VIP_POOL_SERVICE_DOWN_ACTIONS = ['NONE', 'DROP', 'RESELECT']

# Virtual Listener Types
VIP_LISTENER_TYPES = ['STANDARD', 'PERFORMANCE_LAYER_4']

# Virtual Listener Protocols
VIP_LISTENER_PROTO = {
    'STANDARD': ['ANY', 'TCP', 'UDP', 'HTTP', 'FTP', 'SMTP'],
    'PERFORMANCE_LAYER_4': ['ANY', 'TCP', 'UDP', 'HTTP', 'FTP']
}
# Virtual Listener Source Port Preservation Types
VIP_LISTENER_PRESERVATION = ['PRESERVE', 'PRESERVE_STRICT']

# Virtual Listener Optimization Profiles
VIP_LISTENER_OPTOMIZATION = {
    'TCP': [None, 'TCP', 'LAN_OPT', 'WAN_OPT', 'MOBILE_OPT', 'TCP_LEGACY'],
    'UDP': [None, 'SMTP', 'SIP']
}
