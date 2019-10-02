# -*- coding: utf-8 -*-

# Copyright (c), Entrust Datacard Corporation, 2019
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Plugin options for Entrust Certificate Services (ECS) credentials
    DOCUMENTATION = r'''
options:
    entrust_api_user:
        description:
            - The username for authentication to the Entrust Certificate Services (ECS) API.
        type: str
        required: true
    entrust_api_key:
        description:
            - The key (password) for authentication to the Entrust Certificate Services (ECS) API.
        type: str
        required: true
    entrust_api_client_cert_path:
        description:
            - The path to the client certificate used to authenticate to the Entrust Certificate Services (ECS) API.
        type: path
        required: true
    entrust_api_client_cert_key_path:
        description:
            - The path to the key for the client certificate used to authenticate to the Entrust Certificate Services (ECS) API.
        type: path
        required: true
    entrust_api_specification_path:
        description:
            - The path to the specification file defining the Entrust Certificate Services (ECS) API configuration.
            - You can use this to keep a local copy of the specification to avoid downloading it every time the module is used.
        type: path
        default: https://cloud.entrust.net/EntrustCloud/documentation/cms-api-2.1.0.yaml
requirements:
    - "PyYAML >= 3.11"
'''
