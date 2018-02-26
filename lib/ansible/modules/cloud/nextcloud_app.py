#!/usr/bin/python

# (c) 2017-2018, Jonas Meurer <jonas@freesources.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

# TODO:
# * properly set file attributes (module.set_fs_attributes_if_different)
# * Deal with Apps that are not on apps.nextcloud.com
#   * Add some way to download apps from a custom URL

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nextcloud_app
short_description: Manage Nextcloud apps
description:
    - This module manages the apps of a Nextcloud instance.
    - Supports to install/upgrade, enable/disable or query the status of
      Nextcloud apps.
version_added: "2.6"
author:
    - Jonas Meurer (@mejo-)
options:
    name:
        required: true
        description:
            - Name of the Nextcloud app
    nextcloud_path:
        required: true
        default: None
        description:
            - Path to the Nextcloud installation
    state:
        required: true
        choices: [ "latest", "enabled", "disabled", "report" ]
        description:
            - Desired app state. C(latest) ensures that the latest (or in
              C(version) defined) version is installed and enabled. C(enabled)
              will install latest/defined version only if no local version
              exists and ensures that the app is enabled. C(disabled) will make
              sure that the app is disabled and C(report) will keep the app
              untouched and just report the current state.
    version:
        required: false
        description:
            - Pin the app to a specific version.
    app_store_url:
        required: false
        default: "https://apps.nextcloud.com/api/v1/platform/{0}/apps.json"
        description:
            - URL to the app store index in JSON format ({0} will automatically
              be replaced by the detected Nextcloud platform).
    validate_certs:
        required: false
        type: bool
        default: "yes"
        description:
            - If C(False), SSL certificates will not be validated. This should
              only be used on personally controlled sites using self-signed
              certificates.
    keep_newer:
        required: false
        type: bool
        default: "no"
        description:
            - Do not replace existing files that are newer than files
              from the archive.
requirements:
    - semantic-version
notes:
    - Requires C(gtar) command on target host for app installation/update.
    - Existing files/directories in the app destination path which are not
      in the archive are not touched at upgrades.
extends_documentation_fragment: files
'''

EXAMPLES = r'''
# Get details about Nextcloud app 'circles'
- nextcloud_app:
    name: circles
    nextcloud_path: /var/www/nextcloud
    state: report
  register: nc_app_circles

# Install and enable latest version of Nextcloud app 'passman'
- nextcloud_app:
    name: passman
    nextcloud_path: /var/www/nextcloud
    state: latest

# Disable Nextcloud app 'firstrunwizard'
- nextcloud_app:
    name: firstrunwizard
    nextcloud_path: /var/www/nextcloud
    state: disabled
'''

RETURN = r'''
name:
    description: Name of the Nextcloud app
    returned: success
    type: str
    sample: circles
installed:
    description: Is the app installed locally?
    returned: success
    type: boolean
    sample: True
enabled:
    description: Is the app enabled?
    returned: success
    type: boolean
    sample: True
version_local:
    description: Locally installed version of the app
    returned: success
    type: str
    sample: "0.13.4"
path_local:
    description: Local path to the installed app
    returned: success
    type: string
    sample: "/var/www/nextcloud/apps/circles"
version_remote:
    description: Latest/desired version of the app found in app store
    returned: success
    type: str
    sample: "0.13.6"
url_remote:
    description: URL to latest/desired version of the app from app store
    returned: success
    type: str
    sample: "https://github.com/nextcloud/circles/releases/download/v0.13.6/circles-0.13.6.tar.gz"
platform:
    description: Nextcloud platform version
    returned: success
    type: str
    sample: "12.0.2"
'''

import os
import re
import tempfile
from datetime import datetime, timedelta
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_bytes, to_native

try:  # python 3.3+
    from shlex import quote
except ImportError:  # older python
    from pipes import quote

try:
    from semantic_version import Version, Spec
except ImportError:
    semantic_version_found = False
else:
    semantic_version_found = True

# When downloading an archive, how much of the archive to download before
# saving to a tempfile (64k)
BUFSIZE = 65536


def occ_command(module, occ_path, occ_command, occ_options='', occ_json=True):
    php_path = module.get_bin_path("php", True, ["/usr/local/bin"])
    cmd = [php_path, occ_path, '--no-interaction', '--no-warnings', occ_command]
    if occ_json:
        cmd.append('--output=json')
    if occ_options:
        cmd.append(occ_options)
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        module.fail_json(msg='occ command {0} failed: {1}'.format(cmd, err))
    return out


def app_store_fetch_json(module, url):
    dest = "/tmp/ansible-nextcloud_app-apps.json"
    content = None
    store_json = None
    use_local_file = False

    # Ugly json file caching: only fetch if local version is older two minutes.
    # This is necessary as the module is often used in loops and the upstream
    # webserver has rate limits implemented.
    # A better solution would be to use the upstream ETag header, but up to
    # now, the Ansible URL utils don't support ETag headers yet.
    if os.path.exists(dest):
        dest_mtime = datetime.fromtimestamp(os.path.getmtime(dest))
        check_time = datetime.now() - timedelta(minutes=2)
        if dest_mtime > check_time:
            use_local_file = True

    if use_local_file:
        fd = open(dest, 'r')
        try:
            content = fd.read()
        except Exception as e:
            module.fail_json(msg="failed to read from file: {0}".format(to_native(e)))
    else:
        resp, info = fetch_url(module, url, method='GET')

        if info['status'] != 200:
            module.fail_json(msg="Failed to fetch url {0}: {1}".format(url, info['msg']))

        try:
            content = resp.read()
        except AttributeError:
            if info['body']:
                content = info['body']

        if content:
            fd = open(dest, 'wb')
            try:
                fd.write(content)
            except Exception as e:
                os.remove(dest)
                module.fail_json(msg="Failed to write to file: {0}".format(to_native(e)))
            fd.close()

    try:
        store_json = module.from_json(content.decode('utf8'))
    except ValueError:
        module.fail_json(msg="Failed to parse URL {0} content: {1}".format(url, content))

    return store_json


def app_state_store(module, app_store_url, app_version_local=''):
    store_json = app_store_fetch_json(module, app_store_url)

    app_version_store = '0.0.0'
    app_url_store = ''
    for app in store_json:
        if app['id'] == module.params['name']:
            for release in app['releases']:
                if app_version_local and app_version_local == release['version']:
                    app_version_store = release['version']
                    app_url_store = release['download']
                    break
                if not release['isNightly']:
                    if Version(release['version']) >= Version(app_version_store):
                        app_version_store = release['version']
                        app_url_store = release['download']
            break
    if app_version_store == '0.0.0':
        app_version_store = ''
    elif app_version_local and app_version_local != app_version_store:
        module.fail_json(msg='Version {0} of app {1} not found'.format(app_version_local, module.params['name']))
    return (app_version_store, app_url_store)


def app_state_local(module, occ_path, app_name):
    out = occ_command(module, occ_path, 'app:list')
    apps_local = module.from_json(out)

    app_installed = False
    app_enabled = False
    app_version_local = ''
    app_path_local = ''

    # determine if app is installed locally
    if app_name in apps_local['enabled']:
        app_installed = True
        app_enabled = True
        app_version_local = apps_local['enabled'][app_name]
    elif app_name in apps_local['disabled']:
        app_installed = True

    # get local path if app_installed
    if app_installed:
        out = occ_command(module, occ_path, 'app:getpath', app_name)
        app_path_local = out.rstrip()

    return (app_installed, app_enabled, app_version_local, app_path_local)


def app_fetch(module, app_url):
    # Download the app tar.gz to a a temporary file
    fd, app_tmp = tempfile.mkstemp(suffix=".tar.gz", prefix="ansible-")
    try:
        resp, info = fetch_url(module, app_url)
        # If download fails, raise a proper exception
        if resp is None:
            raise Exception(info['msg'])

        # Read 1kb at a time to save on ram
        while True:
            data = resp.read(BUFSIZE)
            data = to_bytes(data, errors='surrogate_or_strict')

            if len(data) < 1:
                break  # End of file, break while loop

            os.write(fd, data)
        os.close(fd)
    except Exception as e:
        module.fail_json(msg="Failure downloading {0}, {1}".format(app_url, to_native(e)))

    if not os.access(app_tmp, os.R_OK):
        module.fail_json(msg="Source '{0}' not readable".format(app_tmp))

    # skip working with 0 size archives
    try:
        if os.path.getsize(app_tmp) == 0:
            module.fail_json(msg="Invalid archive '{0}', the file is 0 bytes".format(app_tmp))
    except Exception as e:
        module.fail_json(msg="Source '{0}' not readable, {1}".format(app_tmp, to_native(e)))

    return app_tmp


def app_unarchive(module, app_archive, apps_dir, file_args):
    tar_path = module.get_bin_path('gtar', None)
    if not tar_path:
        # Fallback to tar
        tar_path = module.get_bin_path('tar')
    cmd = [tar_path, '-C', apps_dir, '-z']
    if file_args['owner']:
        cmd.append('--owner=' + quote(file_args['owner']))
    if file_args['group']:
        cmd.append('--group=' + quote(file_args['group']))
    if module.params['keep_newer']:
        cmd.append('--keep-newer-files')

    cmd.extend(['--extract', '-f', app_archive])

    rc, out, err = module.run_command(cmd, cwd=apps_dir, environ_update=dict(LANG='C', LC_ALL='C', LC_MESSAGES='C'))
    if rc != 0:
        module.fail_json(msg="failed to unpack {0} to {1}".format(app_archive, apps_dir))
    return out


def main():
    # define the available arguments/parameters
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', choices=["enabled", "latest", "disabled", "report"], required=True),
        nextcloud_path=dict(type='path', required=True),
        app_store_url=dict(type='str', required=False, default="https://apps.nextcloud.com/api/v1/platform/{0}/apps.json"),
        version=dict(type='str', required=False, default=None),
        validate_certs=dict(type='bool', default=True),
        keep_newer=dict(type='bool', default=False),
    )

    # seed the result dict in the object
    result = dict(
        changed=False,
        platform='',
        name='',
        installed=False,
        enabled=False,
        version_local='',
        path_local='',
        version_remote='',
        url_remote='',
        diff={'before': '', 'after': ''}
    )

    # set empty diff
    diff_after = ''

    # AnsibleModule object
    module = AnsibleModule(
        argument_spec=module_args,
        add_file_common_args=True,
        supports_check_mode=True
    )

    app_name = module.params['name']
    result['name'] = app_name

    # requires Python module 'semantic_version'
    if not semantic_version_found:
        module.fail_json(msg='The python semantic-version library is required', **result)

    # requires occ script in Nextcloud path
    occ_path = os.path.join(module.params['nextcloud_path'], 'occ')
    if not os.path.isfile(occ_path):
        module.fail_json(msg='No occ found in nextcloud_path', **result)

    # get Nextcloud platform
    out = occ_command(module, occ_path, 'status')
    result['platform'] = module.from_json(out)['versionstring']

    # read in local Nextcloud apps
    (result['installed'], result['enabled'], result['version_local'], result['path_local']) = app_state_local(module, occ_path, app_name)

    # get version and URL from app store
    (result['version_remote'], result['url_remote']) = app_state_store(module, module.params['app_store_url'].format(result['platform']),
                                                                       module.params['version'])

    if (((module.params['state'] == 'latest' and
            result['version_local'] != result['version_remote']) or
            (module.params['state'] == 'enabled' and not result['installed'])) and
            result['url_remote']):
        # INSTALL/UPDATE
        apps_dir = os.path.join(module.params['nextcloud_path'], 'apps')
        app_archive = app_fetch(module, result['url_remote'])

        module.params['dest'] = os.path.join(apps_dir, app_name)
        file_args = module.load_file_common_arguments(module.params)

        # temporarly disable the app
        if result['enabled']:
            if not module.check_mode:
                out = occ_command(module, occ_path, 'app:disable', app_name, False)
            result['enabled'] = False
            result['changed'] = True

        # install/upgrade the app
        if not module.check_mode:
            out = app_unarchive(module, app_archive, apps_dir, file_args)
        result['installed'] = True
        result['version_local'] = module.params['version']
        result['changed'] = True
        diff_after = diff_after + '- installed app {0} version {1}\n'.format(app_name, result['version_local'])

        os.unlink(app_archive)

    if (module.params['state'] in ['latest', 'enabled'] and
            not result['enabled']):
        # ENABLE
        if not module.check_mode:
            out = occ_command(module, occ_path, 'app:enable', app_name, False)
        result['enabled'] = True
        result['changed'] = True
        diff_after = diff_after + '- enabled app {0}\n'.format(app_name)

    elif (module.params['state'] == 'disabled' and result['enabled']):
        # DISABLE
        if not module.check_mode:
            out = occ_command(module, occ_path, 'app:disable', app_name, False)
        result['enabled'] = False
        result['version_local'] = ''
        result['changed'] = True
        diff_after = diff_after + '- disabled app {0}\n'.format(app_name)

    result['diff']['after'] = diff_after
    module.exit_json(**result)

if __name__ == '__main__':
    main()
