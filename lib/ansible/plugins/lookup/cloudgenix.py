# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: cloudgenix

short_description: "Query and iterate CloudGenix API responses."

version_added: "2.6"

description:
    - "This lookup module can be used to iterate or query sets of items from the CloudGenix API. In addition to
       returning ALL items, responses can be filtered 'by_id' or 'by_name' using a single item or a list of items.
       NOTE: for items without a 'name' value, the 'by_name' filter will search the most likely name-like field."

options:
    sites:
        description:
            - Query and return all Site objects.

    elements:
        description:
            - Query and return all Element objects.

    machines:
        description:
            - Query and return all Machine objects.

    element_images:
        description:
            - Query and return all Element Image objects.

    waninterfaces:
        description:
            - Query and return all WAN Interface (Site WAN Interface/SWI) objects. Requires 'site' ID sub-objects.

    lannetworks:
        description:
            - Query and return all LAN Network objects. Requires 'site' ID sub-objects.

    interfaces:
        description:
            - Query and return all Interface objects. Requires 'site' and 'element' ID sub-objects.

    vff_licenses:
        description:
            - Query and return all Virtual Form Factor (VFF) License objects.

    vff_tokens:
        description:
            - "Query and return all Virtual Form Factor Token objects in a Virtual Form Factor (VFF) License.
              Requires 'vff_license' ID sub-object."

    coreroutepeers:
        description:
            - Query and return all Core Router Peer objects. Requires 'site' ID sub-object.

    edgeroutepeers:
        description:
            - Query and return all Edge Router Peer objects. Requires 'site' ID sub-objects.

    staticroutes:
        description:
            - Query and return all Static Route objects. Requires 'site' and 'element' ID sub-objects.

    circuit_categories:
        description:
            - Query and return all Circuit Category (WAN Interface Label) objects.

    network_policysets:
        description:
            - Query and return all Network Policyset objects.

    security_policysets:
        description:
            - Query and return all Security Policyset objects.

    service_binding_maps:
        description:
            - Query and return all Service Binding Map objects.

    service_labels:
        description:
            - Query and return all Service Label / Datacenter Group objects.

    securityzones:
        description:
            - Query and return all Security Zone objects.

    network_contexts:
        description:
            - Query and return all Network Context objects.

    appdefs:
        description:
            - Query and return all Application Definition objects.

    localprefixfilters:
        description:
            - Query and return all Local Prefix Filter objects.

    globalprefixfilters:
        description:
            - Query and return all Global Prefix Filter objects.

    wannetworks:
        description:
            - Query and return all WAN Network objects.

    network_policyrules:
        description:
            - "Query and return all Network Policyrule objects from a Network Policyset. Requires 'network_policyset'
              ID sub-object."

    security_policyrules:
        description:
            - "Query and return all Security Policyrule objects from a Security Policyset. Requires 'security_policyset'
              ID sub-object."
author:
    - Aaron Edwards (@ebob9)
"""

EXAMPLES = """
  - name: Get all sites
    debug:
       msg: "Item = {{ item }}"
    with_cloudgenix:
      sites:

  - name: Get a site IDs from site named "Home Office 1" and "Home Office 2"
    debug:
       msg: "Item ID = {{ item.id }}"
    with_cloudgenix:
      sites:
        by_name:
          - Home Office 1
          - Home Office 2

  - name: Dump WAN Interfaces
    debug:
       msg: "Item = {{ item }}"
    with_cloudgenix:
      waninterfaces:
       site: 21363455653567700

  - name: set element image (must be after auth_token)
    set_fact:
      upgrade_image_id: "{{ lookup('cloudgenix', attribute='element_images', by_name='4.5.1-b34').id }}"

  - name: Upgrade all east coast elements
    cloudgenix_element_state:
      auth_token: "{{ auth_token }}"
      operation: "modify"
      id: "{{ item.id }}"
      image_id: "{{ upgrade_image_id }}"
    register: modify_results

    with_cloudgenix:
      elements:
        by_name:
          - East coast store 1
          - East coast store 2
          - East coast store 3
          - East coast store 4

  - name: Get Named LAN Network (must be after auth_token)
    set_fact:
      lan_network_id: "{{ lookup('cloudgenix', attribute='lannetworks', by_name='default_test_ln', site='6667444718388585').id }}"

  - name: Get All Interfaces from a site/element
    debug:
       msg: "Item = {{ item }}"
    with_cloudgenix:
      interfaces:
        site: 21345029595114002
        element: 21390053595443600

  - name: Get 3102v VFF license ID
    set_fact:
       vff3102v_id: "{{ item.id }}"
    with_cloudgenix:
      vff_licenses:
        by_name: "ion 3102v"

  - name: Revoke all currently valid 3102v tokens
    cloudgenix_vff_tokens:
      auth_token: "{{ auth_token }}"
      operation: "revoke"
      vff_license: "{{ vff3102v_id }}"
      id: "{{ item.id }}"
    when:
      - item.is_expired == False
      - item.is_revoked == False
    with_cloudgenix:
      vff_tokens:
        vff_license: "{{ vff3102v_id }}"

  - name: Core Route peers
    debug:
       msg: "Item = {{ item }}"
    with_cloudgenix:
      coreroutepeers:
       site: 21363455653567700

  - name: Edge Route peers
    debug:
       msg: "Item = {{ item }}"
    with_cloudgenix:
      edgeroutepeers:
       site: 21363455653567700

  - name: Get all static routes
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      staticroutes:
        site: 21345029595114002
        element: 21390053595443600

  - name: Get circuit_categories
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      circuit_categories:

  - name: Get network_policysets
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      network_policysets:

  - name: Get security_policysets
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      security_policysets:

  - name: Get service_binding_maps
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      service_binding_maps:

  - name: Get service_labels
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      service_labels:

  - name: Get securityzones
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      securityzones:

  - name: Get network_contexts
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      network_contexts:

  - name: Get appdefs
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      appdefs:

  - name: Get localprefixfilters
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      localprefixfilters:

  - name: Get globalprefixfilters
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      globalprefixfilters:

  - name: Get wannetworks
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      wannetworks:

  - name: Get network_policyrules
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      network_policyrules:
        network_policyset: "21331330670809400"

  - name: Get security_policyrules
    debug:
       msg: "{{ item }}"
    with_cloudgenix:
      security_policyrules:
        security_policyset: 21353202122620201
"""

RETURN = """
API_RESPONSES:
  description:
    - "This Lookup module returns vars set based on CloudGenix API responses. (API_RESPONSES is not actually returned).
       For more info, see https://developers.cloudgenix.com."
  value: Various objects based on the type of API request
"""
import sys
from ansible.errors import AnsibleError

try:
    import cloudgenix
except ImportError:
    raise AnsibleError("The lookup cloudgenix requires python module cloudgenix.")

from ansible.plugins import AnsiblePlugin
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.cloudgenix_util import (HAS_CLOUDGENIX, cloudgenix_common_arguments,
                                                  setup_cloudgenix_connection)
from ansible.module_utils._text import to_native
from ansible.module_utils.six import string_types, text_type, binary_type

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


VALID_ATTRIBUTES = [
    'sites',
    'elements',
    'machines',
    'element_images',
    'waninterfaces',
    'lannetworks',
    'interfaces',
    'vff_licenses',
    'vff_tokens',
    'coreroutepeers',
    'edgeroutepeers',
    'staticroutes',
    'circuit_categories',
    'network_policysets',
    'security_policysets',
    'service_binding_maps',
    'service_labels',
    'securityzones',
    'network_contexts',
    'appdefs',
    'localprefixfilters',
    'globalprefixfilters',
    'wannetworks',
    'network_policyrules',
    'security_policyrules'
]

VALID_SUBKEYS = [
    'by_name',
    'by_id',
    'site',
    'element',
    'vff_license',
    'network_policyset',
    'security_policyset'
]

SETUP_KEYS = [
    'auth_token',
    'controller',
    'tenant_id',
    'ssl_verify',
    'ignore_region'
]


def parse_response(resp, name_key, id_key, name_val=None, id_val=None):
    """
    Function to handle the parsing of an inventory api response, and return all, name, or id based on query.
    Args:
        resp: cloudgenix response object
        name_key: name key for this API.
        id_key: ID key for this API.
        name_val: Optional Name to select an individual item
        id_val: Optional ID to select an individual item.

    Returns: text for now.
    """

    if not resp.cgx_status:
        raise AnsibleError("CloudGenix API call failed: {0}.".format(resp.cgx_content))

    items = resp.cgx_content.get('items', [])

    display.vvvv("parse_response:\n"
                 "\t{0}: {1}\n"
                 "\t{2}: {3}\n".format(text_type(name_key), text_type(name_val), text_type(id_key), text_type(id_val)))

    display.vvvvv("\titems: {0}".format(text_type(items)))

    if name_val:
        # if string, return one value.
        if isinstance(name_val, string_types):
            retval = [myname for myname in items if myname.get(name_key) == text_type(name_val)]
        else:  # has to be list, (needs verified in parent.)
            retval = []
            for individual_name in name_val:
                retval.extend([myname for myname in items if myname.get(name_key) == text_type(individual_name)])
            return retval

    elif id_val:
        # if string, return one value.
        if isinstance(id_val, string_types):
            retval = [myid for myid in items if myid.get(id_key) == str(id_val)]
        else:  # has to be list, (needs verified in parent.)
            retval = []
            for individual_id in id_val:
                retval.extend([myid for myid in items if myid.get(id_key) == text_type(individual_id)])
            return retval
    else:
        # return everything
        retval = items

    return retval


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):

        # Debugs
        display.vvvvv("cloudgenix input:\n"
                      "\tTERMS: {0}\n"
                      "\tKWARGS: {1}\n".format(text_type(terms), text_type(kwargs)))

        # try and pull cloudgenix auth info out of variables, fail back to seeing if in kwargs
        auth_token = variables.get('auth_token')
        controller = variables.get('controller')
        tenant_id = variables.get('tenant_id')
        ssl_verify = variables.get('ssl_verify')
        ignore_region = variables.get('ignore_region')

        # Check args, then check root terms as well.
        if not auth_token:
            auth_token = kwargs.get(text_type('auth_token'))
            if not auth_token and isinstance(terms, dict):
                auth_token = terms.get('auth_token')
        if not controller:
            controller = kwargs.get(text_type('controller'))
            if not controller and isinstance(terms, dict):
                controller = terms.get('controller')
        if not tenant_id:
            tenant_id = kwargs.get(text_type('tenant_id'))
            if not tenant_id and isinstance(terms, dict):
                tenant_id = terms.get('tenant_id')
        if not ssl_verify:
            ssl_verify = kwargs.get(text_type('ssl_verify'))
            if not ssl_verify and isinstance(terms, dict):
                ssl_verify = terms.get('ssl_verify')
        if not ignore_region:
            ignore_region = kwargs.get(text_type('ignore_region'))
            if not ignore_region and isinstance(terms, dict):
                ignore_region = terms.get('ignore_region')

        auth_token, controller, tenant_id, cgx_session = \
            setup_cloudgenix_connection(auth_token=auth_token,
                                        controller=controller,
                                        tenant_id=tenant_id,
                                        ssl_verify=ssl_verify,
                                        ignore_region=ignore_region,
                                        display=display)

        # check kwargs first.
        attribute = kwargs.get(text_type('attribute'))
        by_name = kwargs.get(text_type('by_name'))
        by_id = kwargs.get(text_type('by_id'))
        site = kwargs.get(text_type('site'))
        element = kwargs.get(text_type('element'))
        vff_license = kwargs.get(text_type('vff_license'))
        network_policyset = kwargs.get(text_type('network_policyset'))
        security_policyset = kwargs.get(text_type('security_policyset'))

        display.vvvvvv("cloudgenix cloudgenix vars:\n"
                       "\tAUTH_TOKEN: {0}\n"
                       "\tCONTROLLER: {1}\n"
                       "\tTENANT_ID: {2}\n"
                       "\tCGX_SESSION: {3}\n".format(text_type(auth_token),
                                                     text_type(controller),
                                                     text_type(tenant_id),
                                                     text_type(cgx_session)))

        # if these are all null, check terms - we are in a loop.
        if all(field is None for field in [attribute, by_id, by_name]):
            # we are likely launched with with_cloudgenix
            if not isinstance(terms, dict):
                raise AnsibleError("Terms must be provided in a dictionary format only.")

            # Remove setup terms from dict.
            cleanup = []
            for key, value in terms.items():
                if key in SETUP_KEYS:
                    cleanup.append(key)
            for key in cleanup:
                terms.pop(key)

            # TODO allow multiple terms in one operation
            if len(terms) > 1:
                raise AnsibleError("Only a single root term is currently supported in lookup module cloudgenix.")

            # dict_handling
            for key, value in terms.items():
                if key in VALID_ATTRIBUTES:
                    attribute = key

                # lets check values.
                if not isinstance(value, (dict, type(None))):
                    raise AnsibleError("Term search key {0} values must have sub terms 'by_name', "
                                       "'by_id', or blank/None.".format(key))

                if value:
                    # we have a value set that is by_name or by_id.
                    for subkey, subvalue in value.items():
                        if subkey in VALID_SUBKEYS:
                            # check sub values. Allow int, as IDs can look like int, but get cast later.
                            if not isinstance(subvalue, (list, string_types, int)):
                                # What is set is not usable.
                                raise AnsibleError("Term search key '{0}' sub term '{1}' value must be either "
                                                   "a list or a string.".format(key, subkey))

                            # set variable named in subkey to subvalue. Using IF as it is safer than eval()
                            if subkey == 'by_name':
                                by_name = subvalue
                            elif subkey == 'by_id':
                                by_id = subvalue
                            elif subkey == 'site':
                                if isinstance(subvalue, (string_types, int)):
                                    site = subvalue
                                else:
                                    raise AnsibleError('"site" must be a string.')
                            elif subkey == 'element':
                                if isinstance(subvalue, (string_types, int)):
                                    element = subvalue
                                else:
                                    raise AnsibleError('"element" must be a string.')
                            elif subkey == 'vff_license':
                                if isinstance(subvalue, (string_types, int)):
                                    vff_license = subvalue
                                else:
                                    raise AnsibleError('"vff_license" must be a string.')
                            elif subkey == 'network_policyset':
                                if isinstance(subvalue, (string_types, int)):
                                    network_policyset = subvalue
                                else:
                                    raise AnsibleError('"vff_license" must be a string.')
                            elif subkey == 'security_policyset':
                                if isinstance(subvalue, (string_types, int)):
                                    security_policyset = subvalue
                                else:
                                    raise AnsibleError('"vff_license" must be a string.')

                        else:
                            raise AnsibleError("Term search key '{0}' has an invalid sub term "
                                               "'{1}'".format(key, subkey))

        if attribute is None:
            raise AnsibleError("Attribute value required and not set.")

        if by_name and by_id:
            raise AnsibleError("by_name OR by_id can be set, but not both.")

        if attribute.lower() not in VALID_ATTRIBUTES:
            raise AnsibleError("Unsupported attribute: {0}.".format(attribute))

        # Start actual work
        # no required subkeys
        if attribute.lower() == 'sites':
            # make the query
            return parse_response(cgx_session.get.sites(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'elements':
            # make the query
            return parse_response(cgx_session.get.elements(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'machines':
            # make the query
            return parse_response(cgx_session.get.machines(), 'sl_no', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'element_images':
            # make the query
            return parse_response(cgx_session.get.element_images(), 'version', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'vff_licenses':
            # make the query
            return parse_response(cgx_session.get.vfflicenses(), 'model', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'circuit_categories':
            # make the query
            return parse_response(cgx_session.get.waninterfacelabels(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'circuit_categories':
            # make the query
            return parse_response(cgx_session.get.waninterfacelabels(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'network_policysets':
            # make the query
            return parse_response(cgx_session.get.policysets(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'security_policysets':
            # make the query
            return parse_response(cgx_session.get.securitypolicysets(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'service_binding_maps':
            # make the query
            return parse_response(cgx_session.get.servicebindingmaps(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'service_labels':
            # make the query
            return parse_response(cgx_session.get.servicelabels(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'securityzones':
            # make the query
            return parse_response(cgx_session.get.securityzones(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'network_contexts':
            # make the query
            return parse_response(cgx_session.get.networkcontexts(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'appdefs':
            # make the query
            return parse_response(cgx_session.get.networkcontexts(), 'display_name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'globalprefixfilters':
            # make the query
            return parse_response(cgx_session.get.globalprefixfilters(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'localprefixfilters':
            # make the query
            return parse_response(cgx_session.get.localprefixfilters(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'wannetworks':
            # make the query
            return parse_response(cgx_session.get.wannetworks(), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)

        # Requires 'site' subkey
        elif attribute.lower() == 'waninterfaces':
            if any(field is None for field in [site]):
                raise AnsibleError('"site" is required for WAN Interface lookup.')
            # make the query
            return parse_response(cgx_session.get.waninterfaces(site), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'lannetworks':
            if any(field is None for field in [site]):
                raise AnsibleError('"site" is required for LAN Network lookup.')
            # make the query
            return parse_response(cgx_session.get.lannetworks(site), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'coreroutepeers':
            if any(field is None for field in [site]):
                raise AnsibleError('"site" is required for Core Route Peer lookup.')
            # due to CGB-9486, coreroutepeers needs to be fixed into the appropriate structure.
            core_response = cgx_session.get.coreroutepeers(site)
            fixed_content = {
                "items": core_response.cgx_content
            }
            core_response.cgx_content = fixed_content
            # make the query, Name key does not exist for core route peers
            return parse_response(core_response, None, 'id',
                                  name_val=None,
                                  id_val=by_id)
        elif attribute.lower() == 'edgeroutepeers':
            if any(field is None for field in [site]):
                raise AnsibleError('"site" is required for Core Route Peer lookup.')
            # due to CGB-9486, edgeroutepeers needs to be fixed into the appropriate structure.
            edge_response = cgx_session.get.edgeroutepeers(site)
            fixed_content = {
                "items": edge_response.cgx_content
            }
            edge_response.cgx_content = fixed_content
            # make the query, Name key does not exist for core route peers
            return parse_response(edge_response, None, 'id',
                                  name_val=None,
                                  id_val=by_id)

        # Requires 'site', 'element' subkey
        elif attribute.lower() == 'interfaces':
            if any(field is None for field in [site, element]):
                raise AnsibleError('"site" and "element" are required for Interface lookup.')
            # make the query
            return parse_response(cgx_session.get.interfaces(site, element), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        elif attribute.lower() == 'staticroutes':
            if any(field is None for field in [site, element]):
                raise AnsibleError('"site" and "element" are required for Static Route lookup.')
            # make the query
            return parse_response(cgx_session.get.staticroutes(site, element), 'destination_prefix', 'id',
                                  name_val=by_name,
                                  id_val=by_id)

        # Requires 'vff_license' subkey
        elif attribute.lower() == 'vff_tokens':
            if any(field is None for field in [vff_license]):
                raise AnsibleError('"vff_license" is required for VFF Token lookup.')
            # make the query
            return parse_response(cgx_session.get.vfflicense_tokens(vff_license), 'ion_key', 'id',
                                  name_val=by_name,
                                  id_val=by_id)

        # Requires 'network_policyset' subkey
        elif attribute.lower() == 'network_policyrules':
            if any(field is None for field in [network_policyset]):
                raise AnsibleError('"network_policyset" is required for Network Policy Rule lookup.')
            # make the query
            return parse_response(cgx_session.get.policyrules(network_policyset), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)

        # Requires 'security_policyset' subkey
        elif attribute.lower() == 'security_policyrules':
            if any(field is None for field in [security_policyset]):
                raise AnsibleError('"security_policyset" is required for Security Policy Rule lookup.')
            # make the query
            return parse_response(cgx_session.get.securitypolicyrules(security_policyset), 'name', 'id',
                                  name_val=by_name,
                                  id_val=by_id)
        else:
            # no parseable terms
            raise AnsibleError('"{0}" attribute is unknown.'.format(attribute))
