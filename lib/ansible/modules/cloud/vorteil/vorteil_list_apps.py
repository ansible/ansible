#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019 Wilhelm, Wonigkeit (wilhelm.wonigkeit@vorteil.io)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vorteil_list_apps

short_description: List all of the applications in the repository

version_added: "2.10"

description:
    - Gets a list of all the applications within the Vorteil repo across all buckets

notes:
    - Vorteil.io repos that require permission will require a authentication key to login
    - Please set your repo_key to login.

extends_documentation_fragment:
    - vorteil

author:
    - Wilhelm Wonigkeit (@bigwonig)
    - Jon Alfaro (@jalfvort)

requirements: 
    - requests
    - toml
    - Vorteil >=3.0.6
'''

EXAMPLES = r'''
- name: List Vorteil repo apps
  vorteil_list_apps:
    repo_key: '{{ var_repo_key }}'
    repo_address: '{{ var_repo_address }}'
    repo_port : "{{ var_repo_port }}"
    repo_proto : "{{ var_repo_proto }}"
'''

RETURN = r'''
results:
    description:
    - dict with the list of apps in the Vorteil repository
    returned: success
    type: list
    sample:
        [
            {
                "bucket": "blog",
                "edges": [
                    {
                        "node": {
                            "name": "cockroachdb"
                        }
                    }
                ]
            },
            {
                "bucket": "vorteil",
                "edges": [
                    {
                        "node": {
                            "name": "cassandra"
                        }
                    },
                    {
                        "node": {
                            "name": "cockroachdb"
                        }
                    },
                    {
                        "node": {
                            "name": "consul"
                        }
                    },
                    {
                        "node": {
                            "name": "coredns"
                        }
                    },
                    {
                        "node": {
                            "name": "dotnet21"
                        }
                    },
                    {
                        "node": {
                            "name": "drupal"
                        }
                    },
                    {
                        "node": {
                            "name": "elasticsearch"
                        }
                    },
                    {
                        "node": {
                            "name": "etcd"
                        }
                    },
                    {
                        "node": {
                            "name": "gitea"
                        }
                    },
                    {
                        "node": {
                            "name": "gnatsd"
                        }
                    },
                    {
                        "node": {
                            "name": "gogs"
                        }
                    },
                    {
                        "node": {
                            "name": "grafana"
                        }
                    },
                    {
                        "node": {
                            "name": "helloworld"
                        }
                    },
                    {
                        "node": {
                            "name": "influxdb"
                        }
                    },
                    {
                        "node": {
                            "name": "java18"
                        }
                    },
                    {
                        "node": {
                            "name": "jetty"
                        }
                    },
                    {
                        "node": {
                            "name": "kibana"
                        }
                    },
                    {
                        "node": {
                            "name": "mariadb"
                        }
                    },
                    {
                        "node": {
                            "name": "memcached"
                        }
                    },
                    {
                        "node": {
                            "name": "minecraft"
                        }
                    },
                    {
                        "node": {
                            "name": "mongodb"
                        }
                    },
                    {
                        "node": {
                            "name": "moodle"
                        }
                    },
                    {
                        "node": {
                            "name": "mosquitto"
                        }
                    },
                    {
                        "node": {
                            "name": "mysqld"
                        }
                    },
                    {
                        "node": {
                            "name": "nginx"
                        }
                    },
                    {
                        "node": {
                            "name": "nodejs"
                        }
                    },
                    {
                        "node": {
                            "name": "openliberty"
                        }
                    },
                    {
                        "node": {
                            "name": "owncloud"
                        }
                    },
                    {
                        "node": {
                            "name": "perl"
                        }
                    },
                    {
                        "node": {
                            "name": "php"
                        }
                    },
                    {
                        "node": {
                            "name": "postgres"
                        }
                    },
                    {
                        "node": {
                            "name": "python3"
                        }
                    },
                    {
                        "node": {
                            "name": "redis"
                        }
                    },
                    {
                        "node": {
                            "name": "ruby"
                        }
                    },
                    {
                        "node": {
                            "name": "rubyonrails"
                        }
                    },
                    {
                        "node": {
                            "name": "solr"
                        }
                    },
                    {
                        "node": {
                            "name": "tomcat"
                        }
                    },
                    {
                        "node": {
                            "name": "wildfly"
                        }
                    },
                    {
                        "node": {
                            "name": "wildflyswarm"
                        }
                    },
                    {
                        "node": {
                            "name": "wordpress"
                        }
                    }
                ]
            }
        ]
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vorteil import VorteilClient


def main():

    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        repo_key=dict(type='str', required=False),
        repo_address=dict(type='str', required=True),
        repo_proto=dict(type='str', choices=['http', 'https'], default='http'),
        repo_port=dict(type='str', required=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    # Init vorteil client
    vorteil_client = VorteilClient(module)

    # set repo_cookie if repo_key is provided
    if module.params['repo_key'] is not None:
        cookie_response, is_error = vorteil_client.set_repo_cookie()
        if is_error:
            module.fail_json(msg="Failed to retrieve cookie", meta=cookie_response)

    # Create the empty list which we will use to store dictionary objects in
    list_apps = []

    # Get the list of buckets in the repository
    bucket_response, is_error = vorteil_client.list_buckets()

    if is_error:
        module.fail_json(msg="Failed to retrieve bucket list", meta=bucket_response)
    else:
        for bucket in bucket_response:
            # Extract the applications for each of the buckets using the list_apps_in_bucket call
            module.params['repo_bucket'] = bucket['node']['name']
            apps_repsonse, is_error = vorteil_client.list_apps_in_bucket()

            if is_error:
                module.fail_json(msg="Failed to retrieve application list", meta=apps_repsonse)
            else:
                apps_repsonse['bucket'] = bucket['node']['name']
                list_apps.append(apps_repsonse)

        module.exit_json(changed=False, response=list_apps)


if __name__ == '__main__':
    main()
