#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Jakub Jirutka <jakub@jirutka.cz>
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

import shutil
from os import path
from urllib2 import Request, urlopen, URLError

DOCUMENTATION = '''
---
module: layman
author: Jakub Jirutka
version_added: "1.6"
short_description: Manage Gentoo overlays
description:
  - Uses Layman to manage an additional repositories for the Portage package manager on Gentoo Linux.
    Please note that Layman must be installed on a managed node prior using this module.
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
    required: false
  state:
    description:
      - Whether to install (C(present)), sync (C(updated)), or uninstall (C(absent)) the overlay.
    required: false
    default: present
    choices: [present, absent, updated]
'''

EXAMPLES = '''
# Install the overlay 'mozilla' which is on the central overlays list.
- layman: name=mozilla

# Install the overlay 'cvut' from the specified alternative list.
- layman: name=cvut list_url=http://raw.github.com/cvut/gentoo-overlay/master/overlay.xml

# Update (sync) the overlay 'cvut', or install if not installed yet.
- layman: name=cvut list_url=http://raw.github.com/cvut/gentoo-overlay/master/overlay.xml state=updated

# Update (sync) all of the installed overlays.
- layman: name=ALL state=updated

# Uninstall the overlay 'cvut'.
- layman: name=cvut state=absent
'''

USERAGENT = 'ansible-httpget'

try:
    from layman.api import LaymanAPI
    from layman.config import BareConfig
    HAS_LAYMAN_API = True
except ImportError:
    HAS_LAYMAN_API = False


class ModuleError(Exception): pass


def init_layman(config=None):
    '''Returns the initialized ``LaymanAPI``.

    :param config: the layman's configuration to use (optional)
    '''
    if config is None: config = BareConfig(read_configfile=True, quietness=1)
    return LaymanAPI(config)


def download_url(url, dest):
    '''
    :param url: the URL to download
    :param dest: the absolute path of where to save the downloaded content to;
        it must be writable and not a directory

    :raises ModuleError
    '''
    request = Request(url)
    request.add_header('User-agent', USERAGENT)

    try:
        response = urlopen(request)
    except URLError, e:
        raise ModuleError("Failed to get %s: %s" % (url, str(e)))
    
    try:
        with open(dest, 'w') as f:
            shutil.copyfileobj(response, f)
    except IOError, e:
        raise ModuleError("Failed to write: %s" % str(e))


def install_overlay(name, list_url=None):
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

    if not layman.is_repo(name):
        if not list_url: raise ModuleError("Overlay '%s' is not on the list of known " \
                "overlays and URL of the remote list was not provided." % name)

        overlay_defs = layman_conf.get_option('overlay_defs')
        dest = path.join(overlay_defs, name + '.xml')

        download_url(list_url, dest)

        # reload config
        layman = init_layman()

    if not layman.add_repos(name): raise ModuleError(layman.get_errors())

    return True


def uninstall_overlay(name):
    '''Uninstalls the given overlay repository from the system.

    :param name: the overlay id to uninstall

    :returns: True if the overlay was uninstalled, or False if doesn't exist
        (i.e. nothing has changed)
    :raises ModuleError
    '''
    layman = init_layman()

    if not layman.is_installed(name):
        return False

    layman.delete_repos(name)
    if layman.get_errors(): raise ModuleError(layman.get_errors())

    return True


def sync_overlay(name):
    '''Synchronizes the specified overlay repository.

    :param name: the overlay repository id to sync
    :raises ModuleError
    '''
    layman = init_layman()

    if not layman.sync(name):
        messages = [ str(item[1]) for item in layman.sync_results[2] ]
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
        argument_spec = {
            'name':     { 'required': True },
            'list_url': { 'aliases': ['url'] },
            'state':    { 'default': "present", 'choices': ['present', 'absent', 'updated'] },
        }
    )

    if not HAS_LAYMAN_API:
        module.fail_json(msg='Layman is not installed')

    state, name, url = (module.params[key] for key in ['state', 'name', 'list_url'])

    changed = False
    try:
        if state == 'present':
            changed = install_overlay(name, url)

        elif state == 'updated':
            if name == 'ALL':
                sync_overlays()
            elif install_overlay(name, url):
                changed = True
            else:
                sync_overlay(name)
        else:
            changed = uninstall_overlay(name)

    except ModuleError, e:
        module.fail_json(msg=e.message)
    else:
        module.exit_json(changed=changed, name=name)


# import module snippets
from ansible.module_utils.basic import *
main()
