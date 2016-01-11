#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, bleader
# Written by bleader <bleader@ratonland.org>
# Based on pkgin module written by Shaun Zinck <shaun.zinck at gmail.com>
# that was based on pacman module written by Afterburn <http://github.com/afterburn> 
#  that was based on apt module written by Matthew Williams <matthew@flowroute.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = '''
---
module: pkgng
short_description: Package manager for FreeBSD >= 9.0
description:
    - Manage binary packages for FreeBSD using 'pkgng' which
      is available in versions after 9.0.
version_added: "1.2"
options:
    name:
        description:
            - name of package to install/remove
        required: true
    state:
        description:
            - state of the package
        choices: [ 'present', 'absent' ]
        required: false
        default: present
    cached:
        description:
            - use local package base or try to fetch an updated one
        choices: [ 'yes', 'no' ]
        required: false
        default: no
    annotation:
        description:
            - a comma-separated list of keyvalue-pairs of the form
              <+/-/:><key>[=<value>]. A '+' denotes adding an annotation, a
              '-' denotes removing an annotation, and ':' denotes modifying an 
              annotation.
              If setting or modifying annotations, a value must be provided.
        required: false
        version_added: "1.6"
    pkgsite:
        description:
            - for pkgng versions before 1.1.4, specify packagesite to use
              for downloading packages, if not specified, use settings from
              /usr/local/etc/pkg.conf
              for newer pkgng versions, specify a the name of a repository
              configured in /usr/local/etc/pkg/repos
        required: false
    rootdir:
        description:
            - for pkgng versions 1.5 and later, pkg will install all packages
              within the specified root directory
        required: false
author: "bleader (@bleader)" 
notes:
    - When using pkgsite, be careful that already in cache packages won't be downloaded again.
'''

EXAMPLES = '''
# Install package foo
- pkgng: name=foo state=present

# Annotate package foo and bar
- pkgng: name=foo,bar annotation=+test1=baz,-test2,:test3=foobar

# Remove packages foo and bar 
- pkgng: name=foo,bar state=absent
'''


import shlex
import os
import re
import sys

def query_package(module, pkgng_path, name, rootdir_arg):

    rc, out, err = module.run_command("%s %s info -g -e %s" % (pkgng_path, rootdir_arg, name))

    if rc == 0:
        return True

    return False

def pkgng_older_than(module, pkgng_path, compare_version):

    rc, out, err = module.run_command("%s -v" % pkgng_path)
    version = map(lambda x: int(x), re.split(r'[\._]', out))

    i = 0
    new_pkgng = True
    while compare_version[i] == version[i]:
        i += 1
        if i == min(len(compare_version), len(version)):
            break
    else:
        if compare_version[i] > version[i]:
            new_pkgng = False
    return not new_pkgng


def remove_packages(module, pkgng_path, packages, rootdir_arg):
    
    remove_c = 0
    # Using a for loop incase of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, pkgng_path, package, rootdir_arg):
            continue

        if not module.check_mode:
            rc, out, err = module.run_command("%s %s delete -y %s" % (pkgng_path, rootdir_arg, package))

        if not module.check_mode and query_package(module, pkgng_path, package, rootdir_arg):
            module.fail_json(msg="failed to remove %s: %s" % (package, out))
    
        remove_c += 1

    if remove_c > 0:

        return (True, "removed %s package(s)" % remove_c)

    return (False, "package(s) already absent")


def install_packages(module, pkgng_path, packages, cached, pkgsite, rootdir_arg):

    install_c = 0

    # as of pkg-1.1.4, PACKAGESITE is deprecated in favor of repository definitions
    # in /usr/local/etc/pkg/repos
    old_pkgng = pkgng_older_than(module, pkgng_path, [1, 1, 4])
    if pkgsite != "":
        if old_pkgng:
            pkgsite = "PACKAGESITE=%s" % (pkgsite)
        else:
            pkgsite = "-r %s" % (pkgsite)

    batch_var = 'env BATCH=yes' # This environment variable skips mid-install prompts,
                                # setting them to their default values.

    if not module.check_mode and not cached:
        if old_pkgng:
            rc, out, err = module.run_command("%s %s update" % (pkgsite, pkgng_path))
        else:
            rc, out, err = module.run_command("%s update" % (pkgng_path))
        if rc != 0:
            module.fail_json(msg="Could not update catalogue")

    for package in packages:
        if query_package(module, pkgng_path, package, rootdir_arg):
            continue

        if not module.check_mode:
            if old_pkgng:
                rc, out, err = module.run_command("%s %s %s install -g -U -y %s" % (batch_var, pkgsite, pkgng_path, package))
            else:
                rc, out, err = module.run_command("%s %s %s install %s -g -U -y %s" % (batch_var, pkgng_path, rootdir_arg, pkgsite, package))

        if not module.check_mode and not query_package(module, pkgng_path, package, rootdir_arg):
            module.fail_json(msg="failed to install %s: %s" % (package, out), stderr=err)

        install_c += 1
    
    if install_c > 0:
        return (True, "added %s package(s)" % (install_c))

    return (False, "package(s) already present")

def annotation_query(module, pkgng_path, package, tag, rootdir_arg):
    rc, out, err = module.run_command("%s %s info -g -A %s" % (pkgng_path, rootdir_arg, package))
    match = re.search(r'^\s*(?P<tag>%s)\s*:\s*(?P<value>\w+)' % tag, out, flags=re.MULTILINE)
    if match:
        return match.group('value')
    return False


def annotation_add(module, pkgng_path, package, tag, value, rootdir_arg):
    _value = annotation_query(module, pkgng_path, package, tag, rootdir_arg)
    if not _value:
        # Annotation does not exist, add it.
        rc, out, err = module.run_command('%s %s annotate -y -A %s %s "%s"'
            % (pkgng_path, rootdir_arg, package, tag, value))
        if rc != 0:
            module.fail_json("could not annotate %s: %s"
                % (package, out), stderr=err)
        return True
    elif _value != value:
        # Annotation exists, but value differs
        module.fail_json(
            mgs="failed to annotate %s, because %s is already set to %s, but should be set to %s"
            % (package, tag, _value, value))
        return False
    else:
        # Annotation exists, nothing to do
        return False

def annotation_delete(module, pkgng_path, package, tag, value, rootdir_arg):
    _value = annotation_query(module, pkgng_path, package, tag, rootdir_arg)
    if _value:
        rc, out, err = module.run_command('%s %s annotate -y -D %s %s'
            % (pkgng_path, rootdir_arg, package, tag))
        if rc != 0:
            module.fail_json("could not delete annotation to %s: %s"
                % (package, out), stderr=err)
        return True
    return False

def annotation_modify(module, pkgng_path, package, tag, value, rootdir_arg):
    _value = annotation_query(module, pkgng_path, package, tag, rootdir_arg)
    if not value:
        # No such tag
        module.fail_json("could not change annotation to %s: tag %s does not exist"
            % (package, tag))
    elif _value == value:
        # No change in value
        return False
    else:
        rc,out,err = module.run_command('%s %s annotate -y -M %s %s "%s"'
            % (pkgng_path, rootdir_arg, package, tag, value))
        if rc != 0:
            module.fail_json("could not change annotation annotation to %s: %s"
                % (package, out), stderr=err)
        return True


def annotate_packages(module, pkgng_path, packages, annotation, rootdir_arg):
    annotate_c = 0
    annotations = map(lambda _annotation:
        re.match(r'(?P<operation>[\+-:])(?P<tag>\w+)(=(?P<value>\w+))?',
            _annotation).groupdict(),
        re.split(r',', annotation))

    operation = {
        '+': annotation_add,
        '-': annotation_delete,
        ':': annotation_modify
    }

    for package in packages:
        for _annotation in annotations:
            if operation[_annotation['operation']](module, pkgng_path, package, _annotation['tag'], _annotation['value']):
                annotate_c += 1

    if annotate_c > 0:
        return (True, "added %s annotations." % annotate_c)
    return (False, "changed no annotations")

def main():
    module = AnsibleModule(
            argument_spec       = dict(
                state           = dict(default="present", choices=["present","absent"], required=False),
                name            = dict(aliases=["pkg"], required=True, type='list'),
                cached          = dict(default=False, type='bool'),
                annotation      = dict(default="", required=False),
                pkgsite         = dict(default="", required=False),
                rootdir         = dict(default="", required=False)),
            supports_check_mode = True)

    pkgng_path = module.get_bin_path('pkg', True)

    p = module.params

    pkgs = p["name"]

    changed = False
    msgs = []
    rootdir_arg = ""

    if p["rootdir"] != "":
        old_pkgng = pkgng_older_than(module, pkgng_path, [1, 5, 0])
        if old_pkgng:
            module.fail_json(msg="To use option 'rootdir' pkg version must be 1.5 or greater")
        else:
            rootdir_arg = "--rootdir %s" % (p["rootdir"])

    if p["state"] == "present":
        _changed, _msg = install_packages(module, pkgng_path, pkgs, p["cached"], p["pkgsite"], rootdir_arg)
        changed = changed or _changed
        msgs.append(_msg)

    elif p["state"] == "absent":
        _changed, _msg = remove_packages(module, pkgng_path, pkgs, rootdir_arg)
        changed = changed or _changed
        msgs.append(_msg)

    if p["annotation"]:
        _changed, _msg = annotate_packages(module, pkgng_path, pkgs, p["annotation"], rootdir_arg)
        changed = changed or _changed
        msgs.append(_msg)

    module.exit_json(changed=changed, msg=", ".join(msgs))



# import module snippets
from ansible.module_utils.basic import *
    
main()        
