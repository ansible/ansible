# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: avi
author: Sandeep Bandi <sandeepb@avinetworks.com>
version_added: 2.9
short_description: Look up ``Avi`` objects.
description:
    - Given an object_type, fetch all the objects of that type or fetch
      the specific object that matches the name/uuid given via options.
    - For single object lookup. If you want the output to be a list, you may
      want to pass option wantlist=True to the plugin.

options:
    obj_type:
        description:
            - type of object to query
        required: True
    obj_name:
        description:
            - name of the object to query
    obj_uuid:
        description:
            - UUID of the object to query
extends_documentation_fragment: avi
"""

EXAMPLES = """
# Lookup query for all the objects of a specific type.
- debug: msg="{{ lookup('avi', avi_credentials=avi_credentials, obj_type='virtualservice') }}"
# Lookup query for an object with the given name and type.
- debug: msg="{{ lookup('avi', avi_credentials=avi_credentials, obj_name='vs1', obj_type='virtualservice', wantlist=True) }}"
# Lookup query for an object with the given UUID and type.
- debug: msg="{{ lookup('avi', obj_uuid='virtualservice-5c0e183a-690a-45d8-8d6f-88c30a52550d', obj_type='virtualservice') }}"
# We can replace lookup with query function to always the get the output as list.
# This is helpful for looping.
- debug: msg="{{ query('avi', obj_uuid='virtualservice-5c0e183a-690a-45d8-8d6f-88c30a52550d', obj_type='virtualservice') }}"
"""

RETURN = """
 _raw:
     description:
         - One ore more objects returned from ``Avi`` API.
     type: list
     elements: dictionary
"""

from ansible.module_utils._text import to_native
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from ansible.module_utils.network.avi.avi_api import (ApiSession,
                                                      AviCredentials,
                                                      AviServerError,
                                                      ObjectNotFound,
                                                      APIError)

display = Display()


def _api(avi_session, path, **kwargs):
    '''
    Generic function to handle both /<obj_type>/<obj_uuid> and /<obj_type>
    API resource endpoints.
    '''
    rsp = []
    try:
        rsp_data = avi_session.get(path, **kwargs).json()
        if 'results' in rsp_data:
            rsp = rsp_data['results']
        else:
            rsp.append(rsp_data)
    except ObjectNotFound as e:
        display.warning('Resource not found. Please check obj_name/'
                        'obj_uuid/obj_type are spelled correctly.')
        display.v(to_native(e))
    except (AviServerError, APIError) as e:
        raise AnsibleError(to_native(e))
    except Exception as e:
        # Generic excption handling for connection failures
        raise AnsibleError('Unable to communicate with controller'
                           'due to error: %s' % to_native(e))

    return rsp


class LookupModule(LookupBase):
    def run(self, terms, variables=None, avi_credentials=None, **kwargs):

        api_creds = AviCredentials(**avi_credentials)
        # Create the session using avi_credentials
        try:
            avi = ApiSession(avi_credentials=api_creds)
        except Exception as e:
            raise AnsibleError(to_native(e))

        # Return an empty list if the object is not found
        rsp = []
        try:
            path = kwargs.pop('obj_type')
        except KeyError:
            raise AnsibleError("Please pass the obj_type for lookup")

        if kwargs.get('obj_name', None):
            name = kwargs.pop('obj_name')
            try:
                display.v("Fetching obj: %s of type: %s" % (name, path))
                rsp_data = avi.get_object_by_name(path, name, **kwargs)
                if rsp_data:
                    # Append the return data only if it is not None. i.e object
                    # with specified name is present
                    rsp.append(rsp_data)
            except AviServerError as e:
                raise AnsibleError(to_native(e))
        elif kwargs.get('obj_uuid', None):
            obj_uuid = kwargs.pop('obj_uuid')
            obj_path = "%s/%s" % (path, obj_uuid)
            display.v("Fetching obj: %s of type: %s" % (obj_uuid, path))
            rsp = _api(avi, obj_path, **kwargs)
        else:
            display.v("Fetching all objects of type: %s" % path)
            rsp = _api(avi, path, **kwargs)

        return rsp
