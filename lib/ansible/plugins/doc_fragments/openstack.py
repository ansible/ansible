# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Hewlett-Packard Development Company, L.P.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard openstack documentation fragment
    DOCUMENTATION = r'''
options:
  cloud:
    description:
      - Named cloud or cloud config to operate against.
        If I(cloud) is a string, it references a named cloud config as defined
        in an OpenStack clouds.yaml file. Provides default values for I(auth)
        and I(auth_type). This parameter is not needed if I(auth) is provided
        or if OpenStack OS_* environment variables are present.
        If I(cloud) is a dict, it contains a complete cloud configuration like
        would be in a section of clouds.yaml.
    type: raw
  auth:
    description:
      - Dictionary containing auth information as needed by the cloud's auth
        plugin strategy. For the default I(password) plugin, this would contain
        I(auth_url), I(username), I(password), I(project_name) and any
        information about domains if the cloud supports them. For other plugins,
        this param will need to contain whatever parameters that auth plugin
        requires. This parameter is not needed if a named cloud is provided or
        OpenStack OS_* environment variables are present.
    type: dict
  auth_type:
    description:
      - Name of the auth plugin to use. If the cloud uses something other than
        password authentication, the name of the plugin should be indicated here
        and the contents of the I(auth) parameter should be updated accordingly.
    type: str
  region_name:
    description:
      - Name of the region.
    type: str
  wait:
    description:
      - Should ansible wait until the requested resource is complete.
    type: bool
    default: yes
  timeout:
    description:
      - How long should ansible wait for the requested resource.
    type: int
    default: 180
  api_timeout:
    description:
      - How long should the socket layer wait before timing out for API calls.
        If this is omitted, nothing will be passed to the requests library.
    type: int
  validate_certs:
    description:
      - Whether or not SSL API requests should be verified.
      - Before Ansible 2.3 this defaulted to C(yes).
    type: bool
    default: no
    aliases: [ verify ]
  ca_cert:
    description:
      - A path to a CA Cert bundle that can be used as part of verifying
        SSL API requests.
    type: str
    aliases: [ cacert ]
  client_cert:
    description:
      - A path to a client certificate to use as part of the SSL transaction.
    type: str
    aliases: [ cert ]
  client_key:
    description:
      - A path to a client key to use as part of the SSL transaction.
    type: str
    aliases: [ key ]
  interface:
    description:
        - Endpoint URL type to fetch from the service catalog.
    type: str
    choices: [ admin, internal, public ]
    default: public
    aliases: [ endpoint_type ]
    version_added: "2.3"
requirements:
  - python >= 2.7
  - openstacksdk
notes:
  - The standard OpenStack environment variables, such as C(OS_USERNAME)
    may be used instead of providing explicit values.
  - Auth information is driven by openstacksdk, which means that values
    can come from a yaml config file in /etc/ansible/openstack.yaml,
    /etc/openstack/clouds.yaml or ~/.config/openstack/clouds.yaml, then from
    standard environment variables, then finally by explicit parameters in
    plays. More information can be found at
    U(https://docs.openstack.org/openstacksdk/)
'''
