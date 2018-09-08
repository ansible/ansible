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

from ansible.module_utils.network.aos.aos import (check_aos_version, get_aos_session, find_collection_item,
                                      content_to_dict, do_load_resource)

"""
import json

from distutils.version import LooseVersion

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from apstra.aosom.session import Session

    HAS_AOS_PYEZ = True
except ImportError:
    HAS_AOS_PYEZ = False

from ansible.module_utils._text import to_native


def check_aos_version(module, min=False):
    """
    Check if the library aos-pyez is present.
    If provided, also check if the minimum version requirement is met
    """
    if not HAS_AOS_PYEZ:
        module.fail_json(msg='aos-pyez is not installed.  Please see details '
                             'here: https://github.com/Apstra/aos-pyez')

    elif min:
        import apstra.aosom
        AOS_PYEZ_VERSION = apstra.aosom.__version__

        if LooseVersion(AOS_PYEZ_VERSION) < LooseVersion(min):
            module.fail_json(msg='aos-pyez >= %s is required for this module' % min)

    return True


def get_aos_session(module, auth):
    """
    Resume an existing session and return an AOS object.

    Args:
        auth (dict): An AOS session as obtained by aos_login module blocks::

            dict( token=<token>,
                  server=<ip>,
                  port=<port>
                )

    Return:
        Aos object
    """

    check_aos_version(module)

    aos = Session()
    aos.session = auth

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


def content_to_dict(module, content):
    """
    Convert 'content' into a Python Dict based on 'content_format'
    """

    # if not HAS_YAML:
    #     module.fail_json(msg="Python Library Yaml is not present, mandatory to use 'content'")

    content_dict = None

    #     try:
    #         content_dict = json.loads(content.replace("\'", '"'))
    #     except:
    #         module.fail_json(msg="Unable to convert 'content' from JSON, please check if valid")
    #
    # elif format in ['yaml', 'var']:

    try:
        content_dict = yaml.safe_load(content)

        if not isinstance(content_dict, dict):
            raise Exception()

        # Check if dict is empty and return an error if it's
        if not content_dict:
            raise Exception()

    except Exception:
        module.fail_json(msg="Unable to convert 'content' to a dict, please check if valid")

    # replace the string with the dict
    module.params['content'] = content_dict

    return content_dict


def do_load_resource(module, collection, name):
    """
    Create a new object (collection.item) by loading a datastructure directly
    """

    try:
        item = find_collection_item(collection, name, '')
    except Exception:
        module.fail_json(msg="An error occurred while running 'find_collection_item'")

    if item.exists:
        module.exit_json(changed=False, name=item.name, id=item.id, value=item.value)

    # If not in check mode, apply the changes
    if not module.check_mode:
        try:
            item.datum = module.params['content']
            item.write()
        except Exception as e:
            module.fail_json(msg="Unable to write item content : %r" % to_native(e))

    module.exit_json(changed=True, name=item.name, id=item.id, value=item.value)
