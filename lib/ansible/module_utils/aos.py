#
# Copyright (c) 2017 Apstra Inc, <community@apstra.com>
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
        my_dict = collection.find(label=item_name)
    elif item_id:
        my_dict = collection.find(uid=item_id)

    if my_dict is None:
        return collection['']
    else:
        return my_dict

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
