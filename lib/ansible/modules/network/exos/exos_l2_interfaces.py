#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################
"""
The module file for exos_l2_interfaces
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: exos_l2_interfaces
version_added: "2.10"
short_description:  Manage L2 interfaces on Extreme Networks EXOS devices.
description: This module provides declarative management of L2 interfaces on Extreme Networks EXOS network devices.
author: Jayalakshmi Viswanathan (@jayalakshmiV)
notes:
  - Tested against EXOS 30.2.1.8
  - This module works with connection C(httpapi).
    See L(EXOS Platform Options,../network/user_guide/platform_exos.html)
options:
  config:
    description: A dictionary of L2 interfaces options
    type: list
    elements: dict
    suboptions:
      name: 
        description:
          - Name of the interface
        type: str
        required: True
      access:
        description:
          - Switchport mode access command to configure the interface as a layer 2 access.
        type: dict
        suboptions:
          vlan:
            description:
              - Configure given VLAN in access port. It's used as the access VLAN ID.
            type: int
      trunk:
        description:
          - Switchport mode trunk command to configure the interface as a Layer 2 trunk.
        type: dict
        suboptions:
          native_vlan:
            description:
              - Native VLAN to be configured in trunk port. It's used as the trunk native VLAN ID.
            type: int
          trunk_allowed_vlans:
            description:
              - List of allowed VLANs in a given trunk port. These are the only VLANs that will be configured on the trunk.
            type: list
  state:
    description:
      - The state the configuration should be left in
    type: str
    choices:
      - merged
      - replaced
      - overridden
      - deleted
    default: merged
"""
EXAMPLES = """
# Using deleted

# Before state:
# -------------
# path: /rest/restconf/data/openconfig-interfaces:interfaces/
# method: GET
# data:
# {
#   "openconfig-interfaces:interfaces": {
#     "interface": [
#       {
#         "name": "1",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 10
#             }
#           }
#         }
#       },
#       {
#         "name": "2",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "TRUNK",
#               "native-vlan": 1,
#               "trunk-vlans": [
#                 10
#               ]
#             }
#           }
#         }
#       },
#       {
#         "name": "3",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "TRUNK",
#               "native-vlan": 10,
#               "trunk-vlans": [
#                 20,
#                 30
#               ]
#             }
#           }
#         }
#       }
#     ]
#   }
# }

- name: Delete L2 interface configuration for the given arguments
  exos_l2_interfaces:
    config:
      - name: '3'
    state: deleted

# Module Execution Results:
# -------------------------
#
# "before": [
#     {
#         "access": {
#             "vlan": 10
#         },
#         "name": "1",
#         "trunk": null
#     },
#     {
#         "access": null,
#         "name": "2",
#         "trunk": {
#             "native_vlan": 1,
#             "trunk_allowed_vlans": [
#                 10
#             ]
#         }
#     },
#     {
#         "access": null,
#         "name": "3",
#         "trunk": {
#             "native_vlan": 10,
#             "trunk_allowed_vlans": [
#                 20,
#                 30
#             ]
#         }
#     }
# ],
#
# "requests": [
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "access-vlan": 1,
#            "interface-mode": "ACCESS"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=3/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     }
# ],
#
# "after": [
#     {
#         "access": {
#             "vlan": 10
#         },
#         "name": "1",
#         "trunk": null
#     },
#     {
#         "access": null,
#         "name": "2",
#         "trunk": {
#             "native_vlan": 1,
#             "trunk_allowed_vlans": [
#                 10
#             ]
#         }
#     },
#     {
#         "access": {
#             "vlan": 1
#         },
#         "name": "3",
#         "trunk": null
#     }
# ]
#
# After state:
# -------------
#
# path: /rest/restconf/data/openconfig-interfaces:interfaces/
# method: GET
# data:
# {
#   "openconfig-interfaces:interfaces": {
#     "interface": [
#       {
#         "name": "1",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 10
#             }
#           }
#         }
#       },
#       {
#         "name": "2",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "TRUNK",
#               "native-vlan": 1,
#               "trunk-vlans": [
#                 10
#               ]
#             }
#           }
#         }
#       },
#       {
#         "name": "3",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 1
#             }
#           }
#         }
#       }
#     ]
#   }
# }


# Using deleted without any config passed
#"(NOTE: This will delete all of configured resource module attributes from each configured interface)"

# Before state:
# -------------
# path: /rest/restconf/data/openconfig-interfaces:interfaces/
# method: GET
# data:
# {
#   "openconfig-interfaces:interfaces": {
#     "interface": [
#       {
#         "name": "1",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 10
#             }
#           }
#         }
#       },
#       {
#         "name": "2",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "TRUNK",
#               "native-vlan": 1,
#               "trunk-vlans": [
#                 10
#               ]
#             }
#           }
#         }
#       },
#       {
#         "name": "3",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "TRUNK",
#               "native-vlan": 10,
#               "trunk-vlans": [
#                 20,
#                 30
#               ]
#             }
#           }
#         }
#       }
#     ]
#   }
# }

- name: Delete L2 interface configuration for the given arguments
  exos_l2_interfaces:
    state: deleted

# Module Execution Results:
# -------------------------
#
# "before": [
#     {
#         "access": {
#             "vlan": 10
#         },
#         "name": "1",
#         "trunk": null
#     },
#     {
#         "access": null,
#         "name": "2",
#         "trunk": {
#             "native_vlan": 1,
#             "trunk_allowed_vlans": [
#                 10
#             ]
#         }
#     },
#     {
#         "access": null,
#         "name": "3",
#         "trunk": {
#             "native_vlan": 10,
#             "trunk_allowed_vlans": [
#                 20,
#                 30
#             ]
#         }
#     }
# ],
#
# "requests": [
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "access-vlan": 1,
#            "interface-mode": "ACCESS"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=1/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     },
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "access-vlan": 1,
#            "interface-mode": "ACCESS"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=2/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     },
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "access-vlan": 1,
#            "interface-mode": "ACCESS"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=3/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     }
# ],
#
# "after": [
#     {
#         "access": {
#             "vlan": 1
#         },
#         "name": "1",
#         "trunk": null
#     },
#     {
#         "access": {
#             "vlan": 1
#         },
#         "name": "2",
#         "trunk": null
#     },
#     {
#         "access": {
#             "vlan": 1
#         },
#         "name": "3",
#         "trunk": null
#     }
# ]
#
# After state:
# -------------
#
# path: /rest/restconf/data/openconfig-interfaces:interfaces/
# method: GET
# data:
# {
#   "openconfig-interfaces:interfaces": {
#     "interface": [
#       {
#         "name": "1",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 1
#             }
#           }
#         }
#       },
#       {
#         "name": "2",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 1
#             }
#           }
#         }
#       },
#       {
#         "name": "3",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 1
#             }
#           }
#         }
#       }
#     ]
#   }
# }


# Using merged

# Before state:
# -------------
# path: /rest/restconf/data/openconfig-interfaces:interfaces/
# method: GET
# data:
# {
#   "openconfig-interfaces:interfaces": {
#     "interface": [
#       {
#         "name": "1",
#	  "openconfig-if-ethernet:ethernet": {
#	    "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 1
#             },
#           }
#         }
#       },
#       {
#         "name": "2",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 1
#             },
#           }
#         }
#       },
#       {
#         "name": "3",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 1
#             },
#           }
#         }
#       },
#     ]
#   }
# }

- name: Merge provided configuration with device configuration
  exos_l2_interfaces:
    config:
      - access:
          vlan: 10
        name: '1'
      - name: '2'
        trunk:
          trunk_allowed_vlans: 10
      - name: '3'
        trunk:
          native_vlan: 10
          trunk_allowed_vlans: 20
    state: merged

# Module Execution Results:
# -------------------------
#
# "before": [
#     {
#         "access": {
#             "vlan": 1
#         },
#         "name": "1",
#         "trunk": null
#     },
#     {
#         "access": {
#             "vlan": 1
#         },
#         "name": "2",
#         "trunk": null
#     },
#     {
#         "access": {
#             "vlan": 1
#         },
#         "name": "3",
#         "trunk": null
#     }
# ],
#
# "requests": [
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "access-vlan": 10,
#            "interface-mode": "ACCESS"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=1/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     },
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "trunk-vlans": [10],
#            "interface-mode": "TRUNK"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=2/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     },
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "native-vlan": 10,
#	     "trunk-vlans": [20],
#            "interface-mode": "TRUNK"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=3/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     }
# ],
#
# "after": [
#     {
#         "access": {
#             "vlan": 10
#         },
#         "name": "1",
#         "trunk": null
#     },
#     {
#         "access": null,
#         "name": "2",
#         "trunk": {
#             "native_vlan": 1,
#             "trunk_allowed_vlans": [
#                 10
#             ]
#         }
#     },
#     {
#         "access": null,
#         "name": "3",
#         "trunk": {
#             "native_vlan": 10,
#             "trunk_allowed_vlans": [
#                 20
#             ]
#         }
#     }
# ]
#
# After state:
# -------------
#
# path: /rest/restconf/data/openconfig-interfaces:interfaces/
# method: GET
# data:
# {
#   "openconfig-interfaces:interfaces": {
#     "interface": [
#       {
#         "name": "1",
#	  "openconfig-if-ethernet:ethernet": {
#	    "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 10
#             }
#           }
#         }
#       },
#       {
#         "name": "2",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "TRUNK",
#		"native-vlan": 1,
#               "trunk-vlans": [
#                 10
#               ]
#             }
#           }
#         }
#       },
#       {
#         "name": "3",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "TRUNK",
#		"native-vlan": 10,
#               "trunk-vlans": [
#		  20
#               ]
#             }
#           }
#         }
#       },
#     ]
#   }
# }


# Using overridden

# Before state:
# -------------
# path: /rest/restconf/data/openconfig-interfaces:interfaces/
# method: GET
# data:
# {
#   "openconfig-interfaces:interfaces": {
#     "interface": [
#       {
#         "name": "1",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 10
#             }
#           }
#         }
#       },
#       {
#         "name": "2",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "TRUNK",
#               "native-vlan": 1,
#               "trunk-vlans": [
#                 10
#               ]
#             }
#           }
#         }
#       },
#       {
#         "name": "3",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "TRUNK",
#               "native-vlan": 10,
#               "trunk-vlans": [
#                 20,
#		  30
#               ]
#             }
#           }
#         }
#       }
#     ]
#   }
# }

- name: Overrride device configuration of all L2 interfaces with provided configuration 
  exos_l2_interfaces:
    config:
      - access:
          vlan: 10
        name: '2'
    state: overridden

# Module Execution Results:
# -------------------------
#
# "before": [
#     {
#         "access": {
#             "vlan": 10
#         },
#         "name": "1",
#         "trunk": null
#     },
#     {
#         "access": null,
#         "name": "2",
#         "trunk": {
#             "native_vlan": 1,
#             "trunk_allowed_vlans": [
#                 10
#             ]
#         }
#     },
#     {
#         "access": null,
#         "name": "3",
#         "trunk": {
#             "native_vlan": 10,
#             "trunk_allowed_vlans": [
#                 20,
#                 30
#             ]
#         }
#     }
# ],
#
# "requests": [
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "access-vlan": 1,
#            "interface-mode": "ACCESS"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=1/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     },
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "access-vlan": 10,
#            "interface-mode": "ACCESS"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=2/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     }
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "access-vlan": 1,
#            "interface-mode": "ACCESS"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=3/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     }
# ],
#
# "after": [
#     {
#         "access": {
#             "vlan": 1
#         },
#         "name": "1",
#         "trunk": null
#     },
#     {
#         "access": {
#             "vlan": 10
#         },
#         "name": "2",
#         "trunk": null
#     },
#     {
#         "access": {
#             "vlan": 1
#         },
#         "name": "3",
#         "trunk": null
#     }
# ]
#
# After state:
# -------------
#
# path: /rest/restconf/data/openconfig-interfaces:interfaces/
# method: GET
# data:
# {
#   "openconfig-interfaces:interfaces": {
#     "interface": [
#       {
#         "name": "1",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 1
#             }
#           }
#         }
#       },
#       {
#         "name": "2",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 10
#             }
#           }
#         }
#       },
#       {
#         "name": "3",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 1
#             }
#           }
#         }
#       }
#     ]
#   }
# }


# Using replaced

# Before state:
# -------------
# path: /rest/restconf/data/openconfig-interfaces:interfaces/
# method: GET
# data:
# {
#   "openconfig-interfaces:interfaces": {
#     "interface": [
#       {
#         "name": "1",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 10
#             }
#           }
#         }
#       },
#       {
#         "name": "2",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 20
#             }
#           }
#         }
#       },
#       {
#         "name": "3",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "TRUNK",
#               "native-vlan": 1,
#		"trunk-vlans": [
#		  10
#		]
#             }
#           }
#         }
#       }
#     ]
#   }
# }

- name: Replace device configuration of listed L2 interfaces with provided configuration 
  exos_l2_interfaces:
    config:
      - access:
          vlan: 20
        name: '1'
      - name: '2'
        trunk:
          trunk_allowed_vlans: 10
      - name: '3'
        trunk:
          native_vlan: 10
          trunk_allowed_vlan: 20,30
    state: replaced

# Module Execution Results:
# -------------------------
#
# "before": [
#     {
#         "access": {
#             "vlan": 10
#         },
#         "name": "1",
#         "trunk": null
#     },
#     {
#         "access": {
#             "vlan": 20
#         },
#         "name": "2",
#         "trunk": null
#     },
#     {
#         "access": null,
#         "name": "3",
#         "trunk": {
#             "native_vlan": 1,
#             "trunk_allowed_vlans": [
#                 10
#             ]
#         }
#     }
# ],
#
# "requests": [
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "access-vlan": 20,
#            "interface-mode": "ACCESS"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=1/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     },
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "trunk-vlans": [10],
#            "interface-mode": "TRUNK"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=2/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     },
#     {
#        "data": {
#          "openconfig-vlan:config": {
#            "native-vlan": 10,
#            "trunk-vlans": [20, 30]
#            "interface-mode": "TRUNK"
#          }
#        }
#        "method": "PATCH",
#        "path": "rest/restconf/data/openconfig-interfaces:interfaces/interface=3/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
#     }
# ],
#
# "after": [
#     {
#         "access": {
#             "vlan": 20
#         },
#         "name": "1",
#         "trunk": null
#     },
#     {
#         "access": null,
#         "name": "2",
#         "trunk": {
#             "native_vlan": null,
#             "trunk_allowed_vlans": [
#                 10
#             ]
#         }
#     },
#     {
#         "access": null,
#         "name": "3",
#         "trunk": {
#             "native_vlan": 10,
#             "trunk_allowed_vlans": [
#                 20,
#                 30
#             ]
#         }
#     }
# ]
#
# After state:
# -------------
#
# path: /rest/restconf/data/openconfig-interfaces:interfaces/
# method: GET
# data:
# {
#   "openconfig-interfaces:interfaces": {
#     "interface": [
#       {
#         "name": "1",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "ACCESS",
#               "access-vlan": 20
#             }
#           }
#         }
#       },
#       {
#         "name": "2",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "TRUNK",
#               "trunk-vlans": [
#		  10
# 		]
#             }
#           }
#         }
#       },
#       {
#         "name": "3",
#         "openconfig-if-ethernet:ethernet": {
#           "openconfig-vlan:switched-vlan": {
#             "config": {
#               "interface-mode": "TRUNK",
#               "native-vlan": 10,
#               "trunk-vlans": [
#		  20,
# 		  30
#		]
#             }
#           }
#         }
#       }
#     ]
#   }
# }


"""
RETURN = """
before:
  description: The configuration prior to the model invocation.
  returned: always
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
  type: list
after:
  description: The resulting configuration model invocation.
  returned: when changed
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
  type: list
requests:
  description: The set of requests pushed to the remote device.
  returned: always
  type: list
  sample: [{"data": "...", "method": "...", "path": "..."}, {"data": "...", "method": "...", "path": "..."}, {"data": "...", "method": "...", "path": "..."}]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.exos.argspec.l2_interfaces.l2_interfaces import L2_interfacesArgs
from ansible.module_utils.network.exos.config.l2_interfaces.l2_interfaces import L2_interfaces


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    required_if = [('state', 'merged', ('config', )),
                   ('state', 'replaced', ('config', ))]
    module = AnsibleModule(argument_spec=L2_interfacesArgs.argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    result = L2_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
