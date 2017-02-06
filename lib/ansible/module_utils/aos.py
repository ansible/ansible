#
# (c) 2017 Apstra Inc, <community@apstra.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

"""
This module adds shared support for Apstra AOS modules

In order to use this module, include it as part of your module

from ansible.module_utils.aos import *

"""
import json

try:
    from apstra.aosom.session import Session
    import apstra.aosom.exc as aosExc

    HAS_AOS_PYEZ = True
except ImportError:
    HAS_AOS_PYEZ = False

def get_aos_session(module, auth):
    """
    Resume an existing session and return an AOS object.

    Args:
        auth (dict): An AOS session as obtained by aos_login module blocks::

            dict( headers=dict(AUTHTOKEN=<token>),
                  url=http://<ip>:<port>/api
                )

    Return:
        Aos object
    """
    if not HAS_AOS_PYEZ:
        module.fail_json(msg='aos-pyez is not installed.  Please see details '
                             'here: https://github.com/Apstra/aos-pyez')


    aos = Session()
    aos.api.resume(auth['url'], auth['headers'])

    return aos

def find_collection_item(collection, item_name=False, item_id=False):
    """
    Find collection_item based on name or id from a collection object
    Both Collection_item and Collection Objects are provided by aos-pyez library

    Return
        collection_item: object corresponding to the collection type
    """
    my_dict = None

    if item_name:
        my_dict = collection.find(method='display_name', key=item_name)
    elif item_id:
        my_dict = collection.find(method='id', key=item_id)

    if my_dict is None:
        return collection['']
    else:
        return collection[my_dict['display_name']]

def get_display_name_from_file(module, file=''):
    """
    Read a JSON file and extract the display_name
    """
    datum = None

    try:
        datum = json.load(open(file))
    except Exception:
        module.fail_json(msg="unable to read file'%s'" % file)

    if 'display_name' in datum.keys():
        return datum['display_name']
    else:
        module.fail_json(msg="unable to find display_name in file'%s'" % file)

def do_load_resource(module, collection, file=''):
    """
    Load a JSON file directly to the AOS API
    """

    datum = None

    try:
        datum = json.load(open(file))
    except Exception:
        module.fail_json(msg="unable to load src file '%s'" % file)

    try:
        item = find_collection_item(collection, datum['display_name'], '')
        if item.exists:
            module.exit_json( changed=False,
                              name=item.name,
                              id=item.id,
                              value=item.value )

        if not module.check_mode:
            item.datum = datum
            item.write()

    except KeyError:
        module.fail_json(msg="src data missing display_name, check file contents")

    except SessionRqstError:
        module.fail_json(msg="unable to write item content",
                         content=datum)

    module.exit_json( changed=True,
                      name=item.name,
                      id=item.id,
                      value=item.value )
