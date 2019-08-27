#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Jakub Jirutka <jakub@jirutka.cz>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: layman
author: "Jakub Jirutka (@jirutka)"
version_added: "1.6"
short_description: Manage Gentoo overlays
description:
  - Uses Layman to manage an additional repositories for the Portage package manager on Gentoo Linux.
    Please note that Layman must be installed on a managed node prior using this module.
requirements:
  - "python >= 2.6"
  - layman python module
options:
  name:
    description:
      - The overlay id to install, synchronize, or uninstall.
        Use 'ALL' to sync all of the installed overlays (can be used only when C(state=updated)).
    required: true
  list_url:
    description:
      - An URL of the alternative overlays list that defines the overlay to install.
        This list will be fetched and saved under C(${overlay_defs})/${name}.xml), where
        C(overlay_defs) is readed from the Layman's configuration.
  state:
    description:
      - Whether to install (C(present)), sync (C(updated)), or uninstall (C(absent)) the overlay.
    default: present
    choices: [present, absent, updated]
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be
        set to C(no) when no other option exists.  Prior to 1.9.3 the code
        defaulted to C(no).
    type: bool
    default: 'yes'
    version_added: '1.9.3'
'''

EXAMPLES = '''
# Install the overlay 'mozilla' which is on the central overlays list.
- layman:
    name: mozilla

# Install the overlay 'cvut' from the specified alternative list.
- layman:
    name: cvut
    list_url: 'http://raw.github.com/cvut/gentoo-overlay/master/overlay.xml'

# Update (sync) the overlay 'cvut', or install if not installed yet.
- layman:
    name: cvut
    list_url: 'http://raw.github.com/cvut/gentoo-overlay/master/overlay.xml'
    state: updated

# Update (sync) all of the installed overlays.
- layman:
    name: ALL
    state: updated

# Uninstall the overlay 'cvut'.
- layman:
    name: cvut
    state: absent
'''

import shutil
import traceback

from os import path

LAYMAN_IMP_ERR = None
try:
    from layman.api import LaymanAPI
    from layman.config import BareConfig
    HAS_LAYMAN_API = True
except ImportError:
    LAYMAN_IMP_ERR = traceback.format_exc()
    HAS_LAYMAN_API = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.urls import fetch_url


USERAGENT = 'ansible-httpget'


class ModuleError(Exception):
    pass


def init_layman(config=None):
    '''Returns the initialized ``LaymanAPI``.

    :param config: the layman's configuration to use (optional)
    '''
    if config is None:
        config = BareConfig(read_configfile=True, quietness=1)
    return LaymanAPI(config)


def download_url(module, url, dest):
    '''
    :param url: the URL to download
    :param dest: the absolute path of where to save the downloaded content to;
        it must be writable and not a directory

    :raises ModuleError
    '''

    # Hack to add params in the form that fetch_url expects
    module.params['http_agent'] = USERAGENT
    response, info = fetch_url(module, url)
    if info['status'] != 200:
        raise ModuleError("Failed to get %s: %s" % (url, info['msg']))

    try:
        with open(dest, 'w') as f:
            shutil.copyfileobj(response, f)
    except IOError as e:
        raise ModuleError("Failed to write: %s" % str(e))


def install_overlay(module, name, list_url=None):
    '''Installs the overlay repository. If not on the central overlays list,
    then :list_url of an alternative list must be provided. The list will be
    fetched and saved under ``%(overlay_defs)/%(name.xml)`` (location of the
    ``overlay_defs`` is read from the Layman's configuration).

    :param name: the overlay id
    :param list_url: the URL of the remote repositories list to look for the overlay
        definition (optional, default: None)

    :returns: True if the overlay was installed, or False if already exists
        (i.e. nothing has changed)
    :raises ModuleError
    '''
    # read Layman configuration
    layman_conf = BareConfig(read_configfile=True)
    layman = init_layman(layman_conf)

    if layman.is_installed(name):
        return False

    if module.check_mode:
        mymsg = 'Would add layman repo \'' + name + '\''
        module.exit_json(changed=True, msg=mymsg)

    if not layman.is_repo(name):
        if not list_url:
            raise ModuleError("Overlay '%s' is not on the list of known "
                              "overlays and URL of the remote list was not provided." % name)

        overlay_defs = layman_conf.get_option('overlay_defs')
        dest = path.join(overlay_defs, name + '.xml')

        download_url(module, list_url, dest)

        # reload config
        layman = init_layman()

    if not layman.add_repos(name):
        raise ModuleError(layman.get_errors())

    return True


def uninstall_overlay(module, name):
    '''Uninstalls the given overlay repository from the system.

    :param name: the overlay id to uninstall

    :returns: True if the overlay was uninstalled, or False if doesn't exist
        (i.e. nothing has changed)
    :raises ModuleError
    '''
    layman = init_layman()

    if not layman.is_installed(name):
        return False

    if module.check_mode:
        mymsg = 'Would remove layman repo \'' + name + '\''
        module.exit_json(changed=True, msg=mymsg)

    layman.delete_repos(name)
    if layman.get_errors():
        raise ModuleError(layman.get_errors())

    return True


def sync_overlay(name):
    '''Synchronizes the specified overlay repository.

    :param name: the overlay repository id to sync
    :raises ModuleError
    '''
    layman = init_layman()

    if not layman.sync(name):
        messages = [str(item[1]) for item in layman.sync_results[2]]
        raise ModuleError(messages)


def sync_overlays():
    '''Synchronize all of the installed overlays.

    :raises ModuleError
    '''
    layman = init_layman()

    for name in layman.get_installed():
        sync_overlay(name)


def main():
    # define module
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            list_url=dict(aliases=['url']),
            state=dict(default="present", choices=['present', 'absent', 'updated']),
            validate_certs=dict(required=False, default=True, type='bool'),
        ),
        supports_check_mode=True
    )

    if not HAS_LAYMAN_API:
        module.fail_json(msg=missing_required_lib('Layman'), exception=LAYMAN_IMP_ERR)

    state, name, url = (module.params[key] for key in ['state', 'name', 'list_url'])

    changed = False
    try:
        if state == 'present':
            changed = install_overlay(module, name, url)

        elif state == 'updated':
            if name == 'ALL':
                sync_overlays()
            elif install_overlay(module, name, url):
                changed = True
            else:
                sync_overlay(name)
        else:
            changed = uninstall_overlay(module, name)

    except ModuleError as e:
        module.fail_json(msg=e.message)
    else:
        module.exit_json(changed=changed, name=name)


if __name__ == '__main__':
    main()
