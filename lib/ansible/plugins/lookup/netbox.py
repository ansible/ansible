from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: netbox
    author: Chris Mills <chris@discreet-its.co.uk>
    version_added: "2.9"
    short_description: returns elements from Netbox
    description:
        - Queries Netbox via its API to return virtually any information capable of being held in Netbox.
          While secrets can be queried, the plugin doesn't yet support decrypting them.
    options:
        _terms:
            description:
                - The Netbox object type to query
            required: True
        api_endpoint:
            description:
                - The URL to the Netbox instance to query
            required: True
        token:
            description:
                - The API token created through Netbox
            required: True
"""

EXAMPLES = """
tasks:
  # query a list of devices
  - name: Obtain list of devices from Netbox
    debug:
      msg: "Device {{ item.value.display_name }} (ID: {{ item.key }}) was manufactured by {{ item.value.device_type.manufacturer.name }}"
    loop: "{{ query('netbox', 'devices', api_endpoint='http://localhost/', token='<redacted>') }}"
"""

RETURN = """
  _list:
    description:
      - list of composed dictonaries with key and value
    type: list
"""

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.common._collections_compat import Mapping
from ansible.utils.display import Display

from pprint import pformat

import pynetbox

display = Display()


NETBOX_ENDPOINT_MAP = {
    'aggregates':                    { 'endpoint': 'ipam.aggregates'                     },
    'circuit-terminations':          { 'endpoint': 'circuits.circuit_terminations'       },
    'circuit-types':                 { 'endpoint': 'circuits.circuit_types'              },
    'circuits':                      { 'endpoint': 'circuits.circuits',                  },
    'circuit-providers':             { 'endpoint': 'circuits.providers',                 },
    'cables':                        { 'endpoint': 'dcim.cables',                        },
    'cluster-groups':                { 'endpoint': 'virtualization.cluster_groups',      },
    'cluster-types':                 { 'endpoint': 'virtualization.cluster_types',       },
    'clusters':                      { 'endpoint': 'virtualization.clusters',            },
    'config-contexts':               { 'endpoint': 'extras.config_contexts',             },
    'console-connections':           { 'endpoint': 'dcim.console_connections',           },
    'console-ports':                 { 'endpoint': 'dcim.console_ports',                 },
    'console-server-port-templates': { 'endpoint': 'dcim.console_server_port_templates', },
    'console-server-ports':          { 'endpoint': 'dcim.console_server_ports',          },
    'device-bay-templates':          { 'endpoint': 'dcim.device_bay_templates',          },
    'device-bays':                   { 'endpoint': 'dcim.device_bays',                   },
    'device-roles':                  { 'endpoint': 'dcim.device_roles',                  },
    'device-types':                  { 'endpoint': 'dcim.device_types',                  },
    'devices':                       { 'endpoint': 'dcim.devices',                       },
    'export-templates':              { 'endpoint': 'dcim.export_templates',              },
    'front-port-templates':          { 'endpoint': 'dcim.front_port_templates',          },
    'front-ports':                   { 'endpoint': 'dcim.front_ports',                   },
    'graphs':                        { 'endpoint': 'extras.graphs',                      },
    'image-attachments':             { 'endpoint': 'extras.image_attachments',           },
    'interface-connections':         { 'endpoint': 'dcim.interface_connections',         },
    'interface-templates':           { 'endpoint': 'dcim.interface_templates',           },
    'interfaces':                    { 'endpoint': 'dcim.interfaces',                    },
    'inventory-items':               { 'endpoint': 'dcim.inventory_items',               },
    'ip-addresses':                  { 'endpoint': 'ipam.ip_addresses',                  },
    'manufacturers':                 { 'endpoint': 'dcim.manufacturers',                 },
    'object-changes':                { 'endpoint': 'extras.object_changes',              },
    'platforms':                     { 'endpoint': 'dcim.platforms',                     },
    'power-connections':             { 'endpoint': 'dcim.power_connections',             },
    'power-outlet-templates':        { 'endpoint': 'dcim.power_outlet_templates',        },
    'power-outlets':                 { 'endpoint': 'dcim.power_outlets',                 },
    'power-port-templates':          { 'endpoint': 'dcim.power_port_templates',          },
    'power-ports':                   { 'endpoint': 'dcim.power_ports',                   },
    'prefixes':                      { 'endpoint': 'ipam.prefixes',                      },
    'rack-groups':                   { 'endpoint': 'dcim.rack_groups',                   },
    'rack-reservations':             { 'endpoint': 'dcim.rack_reservations',             },
    'rack-roles':                    { 'endpoint': 'dcim.rack_roles',                    },
    'racks':                         { 'endpoint': 'dcim.racks',                         },
    'rear-port-templates':           { 'endpoint': 'dcim.rear_port_templates',           },
    'rear-ports':                    { 'endpoint': 'dcim.rear_ports',                    },
    'regions':                       { 'endpoint': 'dcim.regions',                       },
    'reports':                       { 'endpoint': 'extras.reports',                     },
    'rirs':                          { 'endpoint': 'ipam.rirs',                          },
    'roles':                         { 'endpoint': 'ipam.roles',                         },
    'secret-roles':                  { 'endpoint': 'secrets.secret_roles',               },

    ### Note: Currently unable to decrypt secrets as key wizardry needs to take place first
    ### but term will return unencrypted elements of secrets - i.e. that they exist etc.
    'secrets':                       { 'endpoint': 'secrets.secrets',                    },

    'services':                      { 'endpoint': 'ipam.services',                      },
    'sites':                         { 'endpoint': 'dcim.sites',                         },
    'tags':                          { 'endpoint': 'extras.tags',                        },
    'tenant-groups':                 { 'endpoint': 'tenancy.tenant_groups',              },
    'tenants':                       { 'endpoint': 'tenancy.tenants',                    },
    'topology-maps':                 { 'endpoint': 'extras.topology-maps',               },
    'virtual-chassis':               { 'endpoint': 'dcim.virtual_chassis',               },
    'virtual-machines':              { 'endpoint': 'dcim.virtual_machines',              },
    'virtualization-interfaces':     { 'endpoint': 'virtualization.interfaces',          },
    'vlan-groups':                   { 'endpoint': 'ipam.vlan_groups',                   },
    'vlans':                         { 'endpoint': 'ipam.vlans',                         },
    'vrfs':                          { 'endpoint': 'ipam.vrfs',                          },
}



class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        netbox_api_token = kwargs.get('token')
        netbox_api_endpoint = kwargs.get('api_endpoint')
        netbox_private_key_file = kwargs.get('key_file')

        if not isinstance(terms, list):
            terms = [terms]

        netbox = pynetbox.api(netbox_api_endpoint, token=netbox_api_token, private_key_file=netbox_private_key_file)

        results = []
        for term in terms:


            try:
                endpoint = 'netbox.'+NETBOX_ENDPOINT_MAP[term]['endpoint']+'.all()'
            except KeyError:
                raise AnsibleError("Unrecognised term %s. Check documentation" % term)

            display.vvvv(u"Netbox lookup for %s to %s using token %s" % (term, netbox_api_endpoint, netbox_api_token))
            api_results = eval(endpoint)
            for object in api_results:

                object_as_dict = dict(object)

                display.vvvvv(pformat(dict(object)))

                key = object_as_dict["id"]
                result = { key: object_as_dict } 

                results.extend(self._flatten_hash_to_list(result))


        return results
