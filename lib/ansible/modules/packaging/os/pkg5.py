#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Peter Oliver <ansible@mavit.org.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: pkg5
author:
- Peter Oliver (@mavit)
short_description: Manages packages with the Solaris 11 Image Packaging System
version_added: '1.9'
description:
  - IPS packages are the native packages in Solaris 11 and higher.
notes:
  - The naming of IPS packages is explained at U(http://www.oracle.com/technetwork/articles/servers-storage-admin/ips-package-versioning-2232906.html).
options:
  name:
    description:
      - An FRMI of the package(s) to be installed/removed/updated.
      - Multiple packages may be specified, separated by C(,).
    required: true
  state:
    description:
      - Whether to install (I(present), I(latest)), or remove (I(absent)) a package.
    choices: [ absent, latest, present ]
    default: present
  accept_licenses:
    description:
      - Accept any licences.
    type: bool
    default: no
    aliases: [ accept, accept_licences ]
  be_name:
    description:
      - Creates a new boot environment with the given name.
    version_added: "2.8"
    type: str
  refresh:
    description:
      - Refresh publishers before execution.
    version_added: "2.8"
    type: bool
    default: yes
'''
EXAMPLES = '''
- name: Install Vim
  pkg5:
    name: editor/vim

- name: Install Vim without refreshing publishers
  pkg5:
    name: editor/vim
    refresh: no

- name: Remove finger daemon
  pkg5:
    name: service/network/finger
    state: absent

- name: Install several packages at once
  pkg5:
    name:
    - /file/gnu-findutils
    - /text/gnu-grep
'''

import re

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='list', required=True),
            state=dict(type='str', default='present', choices=['absent', 'installed', 'latest', 'present', 'removed', 'uninstalled']),
            accept_licenses=dict(type='bool', default=False, aliases=['accept', 'accept_licences']),
            be_name=dict(type='str'),
            refresh=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
    )

    params = module.params
    packages = []

    # pkg(5) FRMIs include a comma before the release number, but
    # AnsibleModule will have split this into multiple items for us.
    # Try to spot where this has happened and fix it.
    for fragment in params['name']:
        if re.search(r'^\d+(?:\.\d+)*', fragment) and packages and re.search(r'@[^,]*$', packages[-1]):
            packages[-1] += ',' + fragment
        else:
            packages.append(fragment)

    # The filtering of packages now happens in functions appropriate to the intended behaviour
    # In the case of "latest", no filtering is necessary
    if params['state'] in ['present', 'installed']:
        ensure(module, 'present', get_fmris_to_install(module, packages), params)
    elif params['state'] in ['latest']:
        ensure(module, 'latest', packages, params)
    elif params['state'] in ['absent', 'uninstalled', 'removed']:
        ensure(module, 'absent', get_fmris_to_uninstall(module, packages), params)


def ensure(module, state, packages, params):
    response = {
        'results': [],
        'msg': '',
    }
    subcommand = ['install']
    if state == 'absent':
        subcommand = ['uninstall']

    if module.check_mode:
        dry_run = ['-n']
    else:
        dry_run = []

    if params['accept_licenses']:
        accept_licenses = ['--accept']
    else:
        accept_licenses = []

    if params['be_name']:
        beadm = ['--be-name=' + module.params['be_name']]
    else:
        beadm = []

    if params['refresh']:
        no_refresh = []
    else:
        no_refresh = ['--no-refresh']

    if packages:
        rc, out, err = module.run_command(['pkg'] + subcommand + dry_run + accept_licenses + beadm + no_refresh + ['-q', '--'] + packages)
        response['rc'] = rc
        response['results'].append(out)
        response['msg'] += err
        response['changed'] = True
        if rc == 4:
            response['changed'] = False
            response['failed'] = False
        elif rc != 0:
            module.fail_json(**response)

    module.exit_json(**response)


def get_fmris_to_uninstall(module, fmri_patterns):
    rc, out, err = module.run_command(['pkg', 'list', '--'] + fmri_patterns)
    installed_fmri_patterns = []
    if err:
        for fmri_pattern in fmri_patterns:
            if (fmri_pattern + "\n") not in err:
                installed_fmri_patterns += [fmri_pattern]
    else:
        installed_fmri_patterns = fmri_patterns
    return installed_fmri_patterns


def get_fmris_to_install(module, all_fmri_patterns):
    remaining_patterns = all_fmri_patterns
    fmri_patterns_to_install = get_latest_patterns(all_fmri_patterns)
    remaining_patterns = [fmri_pattern for fmri_pattern in remaining_patterns if fmri_pattern not in fmri_patterns_to_install]

    # Now get all pattern matches that are or aren't installed (no obsolete or renamed packages) (out)
    # and any not matched patterns (err)
    # TODO: Unsure if using an unsafe shell would be wise if remaining_patterns contains unsanitized user input
    # TODO: Check what happen in case of a timeout (rc code, stderr) and stop appropriately
    rc, out, err = module.run_command(args=" ".join(['pkg', 'list', '-H', '-a', '-v', '--'] + remaining_patterns + ['|', "grep", "[-i]\-\-\$"]), use_unsafe_shell=True)
    # Let any not found patterns always be installed to expose playbook errors
    if err:
        not_matched_fmri_patterns = extract_not_found_patterns(err)
        fmri_patterns_to_install += not_matched_fmri_patterns
        remaining_patterns = [fmri_pattern for fmri_pattern in remaining_patterns if fmri_pattern not in not_matched_fmri_patterns]

    if remaining_patterns and out:
        concrete_package_versions_to_install = []
        package_state_lines = re.sub("\n$", "", out).split("\n")
        current_package_name = ""
        installed_package_version = ""
        most_specific_requested_version = ""
        package_count = len(package_state_lines)
        package_parsed_count = 0

        REGEX_FMRI_NAME_PART = "pkg://.+(?=@)"
        REGEX_FMRI_VERSION_PART = "(?<=@)[^\s]*"
        REGEX_FMRI = REGEX_FMRI_NAME_PART + "@" + REGEX_FMRI_VERSION_PART
        REGEX_FMRI_INSTALLED = "i--"
        REGEX_FMRI_NOT_INSTALLED = "\-\-\-"
        REGEX_FMRI_STATE = "(" + REGEX_FMRI_INSTALLED + "|" + REGEX_FMRI_NOT_INSTALLED + ")"
        REGEX_FMRI_STATE_LINE = "^" + REGEX_FMRI + "\s+" + REGEX_FMRI_STATE + "$"

        for package_state in package_state_lines:
            package_parsed_count += 1
            if not package_state or not re.match(REGEX_FMRI_STATE_LINE, package_state):
                continue
            name_match = re.match(REGEX_FMRI_NAME_PART, package_state)
            parsed_package_name = ""
            if name_match:
                parsed_package_name = name_match.group()
            # Extract package version details
            version_match = re.search(REGEX_FMRI_VERSION_PART, package_state)
            parsed_package_version = ""
            if version_match:
                parsed_package_version = version_match.group()

            if current_package_name != "" and current_package_name != parsed_package_name:
                concrete_package_versions_to_install += get_concrete_version_to_install(current_package_name, installed_package_version, most_specific_requested_version)

            # No current package yet (first package) or changing the current package
            if current_package_name == "" or current_package_name != parsed_package_name:
                # Create the new package context
                installed_package_version = ""
                current_package_name = parsed_package_name
                most_specific_requested_version = get_most_specific_version(module, current_package_name, remaining_patterns)

            if package_state.endswith(REGEX_FMRI_INSTALLED):
                installed_package_version = parsed_package_version

            # At the end of the package list add the last one
            if package_parsed_count == package_count:
                concrete_package_versions_to_install += get_concrete_version_to_install(current_package_name, installed_package_version, most_specific_requested_version)

        fmri_patterns_to_install += concrete_package_versions_to_install
    return fmri_patterns_to_install


def get_concrete_version_to_install(current_package_name, installed_package_version, most_specific_requested_version):
    package_to_install = []
    if installed_package_version:
        if most_specific_requested_version:
            package_to_install = [current_package_name + "@" + most_specific_requested_version]
    else:
        if most_specific_requested_version:
            package_to_install = [current_package_name + "@" + most_specific_requested_version]
        else:
            package_to_install = [current_package_name]
    return package_to_install

def extract_not_found_patterns(pkg_list_stderr):
    # FIXME: Look what stderr brings when a timeout is reached (or other errors)
    stderr_lines = pkg_list_stderr.split("\n")
    not_found_patterns = []
    for stderr_line in stderr_lines:
        if stderr_line.startswith("  "):
            not_found_patterns += [stderr_line.replace("  ", "")]
    return not_found_patterns


def get_most_specific_version(module, requested_package, fmri_patterns):
    most_specific_version = ""
    most_specific_pattern = ""
    for fmri_pattern in fmri_patterns:
        package_name = re.sub("\*", "", fmri_pattern)
        if "@" in package_name:
            package_name = package_name.split("@")[0]
        if package_name not in requested_package:
            continue
        matches = re.search("(?<=@)[^\s]*", fmri_pattern)
        requested_version = ""
        if matches:
            requested_version = matches.group()
        if not requested_version:
            continue
        if most_specific_version == "" or requested_version == most_specific_version:
            most_specific_version = requested_version
            most_specific_pattern = fmri_pattern
            continue
        if len(requested_version) == len(most_specific_version):
            fail_conflicting_patterns(module, [most_specific_pattern, fmri_pattern])
        less_specific_version = min(requested_version, most_specific_version)
        more_specific_version = max(requested_version, most_specific_version)
        if not less_specific_version in more_specific_version:
            fail_conflicting_patterns(module, [most_specific_pattern, fmri_pattern])
        if more_specific_version != most_specific_version:
            most_specific_version = more_specific_version
            most_specific_pattern = fmri_pattern

    return most_specific_version


def get_latest_patterns(fmri_patterns):
    latest_identifier = "@latest"
    latest_patterns = []
    # First select all FMRIs having @latest to always install or update, any updates are ok then
    for fmri_pattern in fmri_patterns:
        if latest_identifier in fmri_pattern:
            latest_patterns += [fmri_pattern]
            continue
    return latest_patterns


def fail_conflicting_patterns(module, conflicting_patterns):
    msg = "You request two different versions of the same package: " + ",".join(conflicting_patterns)
    response = {
        'rc': 1,
        'results': conflicting_patterns,
        'msg': msg,
        'changed': False,
        'failed': True
    }
    module.fail_json(**response)


if __name__ == '__main__':
    main()
