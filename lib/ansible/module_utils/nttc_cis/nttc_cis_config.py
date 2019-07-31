#!/usr/bin/python
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
"""
Module configuration parameters
"""

# HTTP HEADERS
HTTP_HEADERS = {'Content-Type': 'application/json',
                'Accept': 'application/json'}

# API Versions
API_VERSION = '2.9'

# API end-points
API_ENDPOINTS = {
    'na': {
        'name': 'North America (NA)',
        'host': 'api-na.dimensiondata.com',
        'vendor': 'NTTC-CIS'
    },
    'eu': {
        'name': 'Europe (EU)',
        'host': 'api-eu.dimensiondata.com',
        'vendor': 'NTTC-CIS'
    },
    'au': {
        'name': 'Australia (AU)',
        'host': 'api-au.dimensiondata.com',
        'vendor': 'NTTC-CIS'
    },
    'au-gov': {
        'name': 'Australia Canberra ACT (AU)',
        'host': 'api-canberra.dimensiondata.com',
        'vendor': 'NTTC-CIS'
    },
    'af': {
        'name': 'Africa (AF)',
        'host': 'api-mea.dimensiondata.com',
        'vendor': 'NTTC-CIS'
    },
    'ap': {
        'name': 'Asia Pacific (AP)',
        'host': 'api-ap.dimensiondata.com',
        'vendor': 'NTTC-CIS'
    },
    'ca': {
        'name': 'Canada (CA)',
        'host': 'api-canada.dimensiondata.com',
        'vendor': 'NTTC-CIS'
    },
    'is-na': {
        'name': 'North America (NA)',
        'host': 'usapi.cloud.is.co.za',
        'vendor': 'InternetSolutions'
    },
    'is-eu': {
        'name': 'Europe (EU)',
        'host': 'euapi.cloud.is.co.za',
        'vendor': 'InternetSolutions'
    },
    'is-au': {
        'name': 'Australia (AU)',
        'host': 'auapi.cloud.is.co.za',
        'vendor': 'InternetSolutions'
    },
    'is-af': {
        'name': 'Africa (AF)',
        'host': 'meaapi.cloud.is.co.za',
        'vendor': 'InternetSolutions'
    },
    'is-ap': {
        'name': 'Asia Pacific (AP)',
        'host': 'apapi.cloud.is.co.za',
        'vendor': 'InternetSolutions'
    },
    'is-latam': {
        'name': 'South America (LATAM)',
        'host': 'latamapi.cloud.is.co.za',
        'vendor': 'InternetSolutions'
    },
    'is-canada': {
        'name': 'Canada (CA)',
        'host': 'canadaapi.cloud.is.co.za',
        'vendor': 'InternetSolutions'
    },
    'ntta-na': {
        'name': 'North America (NA)',
        'host': 'cloudapi.nttamerica.com',
        'vendor': 'NTTNorthAmerica'
    },
    'ntta-eu': {
        'name': 'Europe (EU)',
        'host': 'eucloudapi.nttamerica.com',
        'vendor': 'NTTNorthAmerica'
    },
    'ntta-au': {
        'name': 'Australia (AU)',
        'host': 'aucloudapi.nttamerica.com',
        'vendor': 'NTTNorthAmerica'
    },
    'ntta-af': {
        'name': 'Africa (AF)',
        'host': 'sacloudapi.nttamerica.com',
        'vendor': 'NTTNorthAmerica'
    },
    'ntta-ap': {
        'name': 'Asia Pacific (AP)',
        'host': 'hkcloudapi.nttamerica.com',
        'vendor': 'NTTNorthAmerica'
    },
    'cisco-na': {
        'name': 'North America (NA)',
        'host': 'iaas-api-na.cisco-ccs.com',
        'vendor': 'Cisco'
    },
    'cisco-eu': {
        'name': 'Europe (EU)',
        'host': 'iaas-api-eu.cisco-ccs.com',
        'vendor': 'Cisco'
    },
    'cisco-au': {
        'name': 'Australia (AU)',
        'host': 'iaas-api-au.cisco-ccs.com',
        'vendor': 'Cisco'
    },
    'cisco-af': {
        'name': 'Africa (AF)',
        'host': 'iaas-api-mea.cisco-ccs.com',
        'vendor': 'Cisco'
    },
    'cisco-ap': {
        'name': 'Asia Pacific (AP)',
        'host': 'iaas-api-ap.cisco-ccs.com',
        'vendor': 'Cisco'
    },
    'cisco-latam': {
        'name': 'South America (LATAM)',
        'host': 'iaas-api-sa.cisco-ccs.com',
        'vendor': 'Cisco'
    },
    'cisco-canada': {
        'name': 'Canada (CA)',
        'host': 'iaas-api-ca.cisco-ccs.com',
        'vendor': 'Cisco'
    },
    'med1-il': {
        'name': 'Israel (IL)',
        'host': 'api.cloud.med-1.com',
        'vendor': 'Med-1'
    },
    'med1-na': {
        'name': 'North America (NA)',
        'host': 'api-na.cloud.med-1.com',
        'vendor': 'Med-1'
    },
    'med1-eu': {
        'name': 'Europe (EU)',
        'host': 'api-eu.cloud.med-1.com',
        'vendor': 'Med-1'
    },
    'med1-au': {
        'name': 'Australia (AU)',
        'host': 'api-au.cloud.med-1.com',
        'vendor': 'Med-1'
    },
    'med1-af': {
        'name': 'Africa (AF)',
        'host': 'api-af.cloud.med-1.com',
        'vendor': 'Med-1'
    },
    'med1-ap': {
        'name': 'Asia Pacific (AP)',
        'host': 'api-ap.cloud.med-1.com',
        'vendor': 'Med-1'
    },
    'med1-latam': {
        'name': 'South America (LATAM)',
        'host': 'api-sa.cloud.med-1.com',
        'vendor': 'Med-1'
    },
    'med1-canada': {
        'name': 'Canada (CA)',
        'host': 'api-ca.cloud.med-1.com',
        'vendor': 'Med-1'
    },
    'indosat-id': {
        'name': 'Indonesia (ID)',
        'host': 'iaas-api.indosat.com',
        'vendor': 'Indosat'
    },
    'indosat-na': {
        'name': 'North America (NA)',
        'host': 'iaas-usapi.indosat.com',
        'vendor': 'Indosat'
    },
    'indosat-eu': {
        'name': 'Europe (EU)',
        'host': 'iaas-euapi.indosat.com',
        'vendor': 'Indosat'
    },
    'indosat-au': {
        'name': 'Australia (AU)',
        'host': 'iaas-auapi.indosat.com',
        'vendor': 'Indosat'
    },
    'indosat-af': {
        'name': 'Africa (AF)',
        'host': 'iaas-afapi.indosat.com',
        'vendor': 'Indosat'
    },
    'bsnl-in': {
        'name': 'India (IN)',
        'host': 'api.bsnlcloud.com',
        'vendor': 'BSNL'
    },
    'bsnl-na': {
        'name': 'North America (NA)',
        'host': 'usapi.bsnlcloud.com',
        'vendor': 'BSNL'
    },
    'bsnl-eu': {
        'name': 'Europe (EU)',
        'host': 'euapi.bsnlcloud.com',
        'vendor': 'BSNL'
    },
    'bsnl-au': {
        'name': 'Australia (AU)',
        'host': 'auapi.bsnlcloud.com',
        'vendor': 'BSNL'
    },
    'bsnl-af': {
        'name': 'Africa (AF)',
        'host': 'afapi.bsnlcloud.com',
        'vendor': 'BSNL'
    }
}

# Valid server states
SERVER_STATES = ['NORMAL', 'PENDING_ADD', 'PENDING_CHANGE', 'PENDING_DELETE',
                 'FAILED_ADD', 'FAILED_CHANGE', 'FAILED_DELETE', 'REQUIRES_SUPPORT']

# Disk speeds that support variable IOPS
VARIABLE_IOPS = ['PROVISIONEDIOPS']

# Valid disk speeds
DISK_SPEEDS = ['STANDARD', 'HIGHPERFORMANCE', 'ECONOMY', 'PROVISIONEDIOPS']

# Default API end-point for the base connection class.
DEFAULT_REGION = 'na'

# SCSI Adapter Types
SCSI_ADAPTER_TYPES = ['LSI_LOGIC_PARALLEL', 'LSI_LOGIC_SAS', 'VMWARE_PARAVIRTUAL', 'BUS_LOGIC']

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
