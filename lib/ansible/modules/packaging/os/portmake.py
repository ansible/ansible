#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Daniel Winter
# Based on the portinstall module by https://github.com/berenddeboer <berend@pobox.com>
#
# make_args parameter added by Daniel Winter https://github.com/planet-winter <daniel@planets.world>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: portmake
short_description: Installing packages from FreeBSD's Ports system with make configure options
description:
    - Manage packages for FreeBSD using the Ports system.
    - Set or unset  make configure options per Port
    - Saves the ports configure options to /etc/make.conf making them persistent for eg a portsupgrade
    - Allows overriding DISABLE_VULNERABILITIES to install Ports regardless of vulnerabilities known to make ansible run succeed.
version_added: "2.8"
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
    options_set:
        description:
            - specific compile options to set (as set with make configure)
        required: false
    options_unset:
        description:
            - specific compile options to unset (as set with make configure)
        required: false
    disable_vulnerabilities:
        description:
            - override DISABLE_VULNERABILITIES to install Ports regardless of vulnerabilities. Ensure ansible run installs required ports regardless.
        required: false
        type: bool
        default: false
author: "Daniel Winter (@planet-winter)"
'''

EXAMPLES = '''
# Install package security/cyrus-sasl2-saslauthd
- portinstall_make_args:
    name: security/cyrus-sasl2-saslauthd
    state: present

# Install several packages with options each
- portinstall_make_args:
    name: "{{ item.name }}"
    state: "present"
    options_set: "{{ item.options_set }}"
    options_unset: "{{ item.options_unset }}"
    with_items:
      - { name: "sysutils/screen", options_set: "XTERM_256", options_unset: "SYSTEM_SCREENRC" }
      - { name: "lang/php56-extensions", options_set: "PGSQL", options_unset: "" }

'''

RETURN = '''
stdout:
    description: output from make process
    returned: success, when needed
    type: str
    sample: ""
stderr:
    description: error output from make process
    returned: success, when needed
    type: str
    sample: ""
'''

import os
import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import shlex_quote
from tempfile import mkstemp
import shutil


class PortMake(object):

    def __init__(self, module):
        self.module = module
        self.pkgng = None
        self.makefile = MakeFile()

        # if pkg_info not found assume pkgng
        if self.module.get_bin_path('pkg_info', False):
            self.pkg_info_path = self.module.get_bin_path('pkg_info', False)
            self.pkgng = False
        else:
            pkg_info_path = self.module.get_bin_path('pkg', True)
            self.pkg_info_path = pkg_info_path + " info"
            self.pkgng = True

        # If pkg_delete not found, we assume pkgng
        if self.module.get_bin_path('pkg_delete', False):
            self.pkg_delete_path = self.module.get_bin_path(
                'pkg_delete', False)
            self.pkgng = False
        else:
            pkg_delete_path = self.module.get_bin_path('pkg', True)
            self.pkg_delete_path = pkg_delete_path + " delete -y"
            self.pkgng = True

        if self.module.get_bin_path('ports_glob', False):
            self.ports_glob_path = module.get_bin_path('ports_glob', False)
        else:
            rc, out, err = self.module.run_command(
                "pkg install -y portupgrade")
            # self.install_packages("ports-mgmt/portupgrade", "","", "")
            self.ports_glob_path = module.get_bin_path('ports_glob', True)

    def package_installed(self, package):
        """
        query the pkg system wether a package is installed
        """

        found = False

        if not self.pkgng:
            rc, out, err = self.module.run_command(
                "%s -e `ports_glob %s`" % (self.pkg_info_path, shlex_quote(package)), use_unsafe_shell=True)
        else:
            rc, out, err = self.module.run_command(
                "%s --exists %s" % (self.pkg_info_path, package))
        if rc == 0:
            found = True

        if not found:
            # databases/mysql55-client installs as mysql-client, so try solving
            # that the ugly way. Pity FreeBSD doesn't have a fool proof way of checking
            # some package is installed
            package_without_digits = re.sub('[0-9]', '', package)
            if package != package_without_digits:
                rc, out, err = self.module.run_command(
                    "%s %s" % (self.pkg_info_path, package_without_digits))
            if rc == 0:
                found = True

        return found

    def get_package_options(self, package):
        """
        get a string of options package has been compiled with
        """

        rc, out, err = self.module.run_command(
            "%s %s" % (self.pkg_info_path, package))

        re_opt = re.compile(r"\s+(\w+)\s+:\s+on", re.IGNORECASE)
        options_list = re_opt.findall(out)

        options = " ".join(options_list)

        return options

    def package_options_match(self, package, options_set, options_unset):
        """
        for found package check if all the set options match the ones of the installed package info
        """

        rc, out, err = self.module.run_command(
            "%s %s" % (self.pkg_info_path, package))

        options = options_set
        for opt_set in options.split():
            re_opt_set = re.compile(r"\s+?%s\s+?:\s+?on" % (opt_set))
            if not re_opt_set.findall(out):
                return False

        for opt_unset in options_unset.split():
            re_opt_unset = re.compile(r"\s+?%s\s+?:\s?off" % (opt_unset))
            if not re_opt_unset.findall(out):
                return False

        return True

    def matching_packages(self, package):
        """
        counts the number of packages found
        """
        # rc, out, err = self.module.run_command("make -C /usr/ports/ quicksearch name=%s" %(package.split('/')[-1]))

        rc, out, err = self.module.run_command(
            "%s %s" % (self.ports_glob_path, package))

        occurrences = out.count('\n')
        if occurrences == 0:
            package_without_digits = re.sub('[0-9]', '', package)
            if package != package_without_digits:
                rc, out, err = self.module.run_command("%s %s" % (
                    self.ports_glob_path, package_without_digits))
                occurrences = out.count('\n')
                # rc, out, err = self.module.run_command("make -C /usr/ports/ quicksearch name=%s" % (package_without_digits))
        return occurrences

    
    def remove_package(self, package):
        """
        removes a single package using system's pkg and cleans up all corresponding options in make.conf
        """
        rc, out, err = self.module.run_command("%s %s" % (
            self.pkg_delete_path, shlex_quote(package)), use_unsafe_shell=True)

        if self.package_installed(package):
            name_without_digits = re.sub('[0-9]', '', package)
            rc, out, err = self.module.run_command("%s %s" % (
                self.pkg_delete_path, shlex_quote(name_without_digits)), use_unsafe_shell=True)
        if self.package_installed(package):
            self.module.fail_json(
                msg="failed to remove %s: %s" % (package, out))
        else:
            options_name = self.get_options_name(package)
            self.makefile.remove_port_options(package, options_name)

    def remove_packages(self, packages):
        """
        removes a list of packages
        """
        remove_c = 0

        # Using a for loop in case of error, we can report the package that failed
        for package in packages:
            # Query the package first, to see if we even need to remove
            if not self.package_installed(package):
                continue

            self.remove_package(package)
            remove_c += 1

        return remove_c

    def get_options_name(self, package):
        rc, out, err = self.module.run_command(
            "make -C /usr/ports/%s -V OPTIONS_NAME" % (package))
        if rc == 0:
            options_name = out.rstrip()
            return options_name
        else:
            self.module.fail_json(
                msg="failed to figure out configure options name for %s: %s" % (package, out))

    def install_packages(self, packages, options_set_list, options_unset_list, disable_vulnerabilities=False):
        """
        installs a list of packages using portinstall with make options given
        """
        install_c = 0

        for (package, options_set, options_unset) in zip(packages, options_set_list, options_unset_list):
            if self.package_installed(package):
                # package is installed. check options
                if self.package_options_match(package, options_set, options_unset):
                    # all ok no need to do anything for this package
                    continue
                else:
                    # some options differ
                    # remove package leave options in makle.conf
                    rc, out, err = self.module.run_command("%s %s" % (
                        self.pkg_delete_path, shlex_quote(package)), use_unsafe_shell=True)

            # install package as it is not here yet or has just been uninstalled
            matches = self.matching_packages(package)
            if matches == 1:
                # unset seems to have higher prio than set
                # empty unset variables to override any set ones in /var/db/ports/*/*/options
                # could not get portinstall to pass settings to make via --make-args, using ENV

                options_name = self.get_options_name(package)

                if options_set != []:
                    self.makefile.set_port_option(options_name, options_set)
                if options_unset != []:
                    self.makefile.unset_port_option(
                        options_name, options_unset)

                compile_options = ""
                if disable_vulnerabilities:
                    compile_options = compile_options + "-DDISABLE_VULNERABILITIES"

                rc, out, err = self.module.run_command(
                    "make -C /usr/ports/%s clean" % (package))
                rc, out, err = self.module.run_command(
                    "make -C /usr/ports/%s install %s BATCH=yes" % (package, compile_options))
                rc, out, err = self.module.run_command(
                    "make -C /usr/ports/%s clean" % (package))

                if self.package_installed(package):
                    install_c += 1
                else:
                    self.module.fail_json(
                        msg="failed to install %s: %s" % (package, out))

            elif matches == 0:
                self.module.fail_json(
                    msg="no matches for package %s" % (package))

            else:
                self.module.fail_json(
                    msg="%s matches found for package name %s" % (matches, package))

        if install_c > 0:
            self.module.exit_json(
                changed=True, msg="present %s package(s)" % (install_c))

        self.module.exit_json(changed=False, msg="package(s) already present")


class MakeFile():

    def __init__(self):
        self.make_conf = "/etc/make.conf"
        # temporary file in the current directory for os.rename to be atomic
        fd, self.tempfile = mkstemp(dir=os.path.dirname(self.make_conf))
        self.make_config = self._read_make_conf()

    def _read_make_conf(self):
        make_config = []
        if os.path.isfile(self.make_conf):
            shutil.copy(self.make_conf, self.tempfile)
            with open(self.tempfile, 'r') as tempfile:
                for line in tempfile:
                    make_config.append(line)
        return make_config

    def _write_make_conf(self):
        with open(self.tempfile, 'w') as tempfile:
            for line in self.make_config:
                tempfile.write(line)
        # atomic operation
        os.rename(self.tempfile, self.make_conf)

    def _port_option_is_set(self, option, value):
        option_value_pattern = r"%s\+=%s" % (option, value)
        for line in self.make_config:
            if bool(re.match(option_value_pattern, line)):
                return True
        return False

    def set_port_option(self, option, values):
        self._port_option(option, values, kind="SET")

    def unset_port_option(self, option, values):
        self._port_option(option, values, kind="UNSET")

    def _port_option(self, option, values, kind=None):
        self._read_make_conf()
        option_set = "%s_%s" % (option, kind)
        for value in values.split():
            if not self._port_option_is_set(option_set, value):
                self.make_config.append("%s+=%s\n" % (option_set, value))
        self._write_make_conf()

    def remove_port_options(self, package, options_name=None):
        self._read_make_conf()
        if options_name is not None:
            options_pattern = "%s" % (options_name)
            lines_remove = []
            for line in self.make_config:
                if bool(re.match(options_pattern, line)):
                    lines_remove.append(line)
            for line in lines_remove:
                self.make_config.remove(line)
        # we might be trying to remove a package which is not in
        #  the ports tree anymore, thus having no options_name is valid as well
        self._write_make_conf()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default="present", choices=["present", "absent"]),
            name=dict(type='str', required=True),
            options_set=dict(type='list', required=False),
            options_unset=dict(type='list', required=False),
            disable_vulnerabilities=dict(type='bool', required=False)
        )
    )

    params = module.params

    pkg_list = params["name"].split(",")

    # add empty parameters for each package if none are given
    if params["options_set"]:
        options_set_list = params["options_set"]
    else:
        options_set_list = []
        for pkg in pkg_list:
            options_set_list.append("")

    if params["options_unset"]:
        options_unset_list = params["options_unset"]
    else:
        options_unset_list = []
        for pkg in pkg_list:
            options_unset_list.append("")

    if (len(pkg_list) != len(options_set_list) or
            len(pkg_list) != len(options_unset_list)):
        module.fail_json(msg="""
            %s packages given. This does not match the
            %s options_set or %s options_unset lists specified."""
                         % (len(pkg_list), len(options_set_list), len(options_unset_list))
                         )

    if params["disable_vulnerabilities"]:
        disable_vulnerabilities = params["disable_vulnerabilities"]
    else:
        disable_vulnerabilities = False

    pm = PortMake(module)

    if params["state"] == "present":
        pm.install_packages(pkg_list, options_set_list, options_unset_list,
                            disable_vulnerabilities=disable_vulnerabilities)

    elif params["state"] == "absent":
        remove_count = pm.remove_packages(pkg_list)
        if remove_count > 0:
            module.exit_json(
                changed=True, msg="removed %s package(s)" % remove_count)
        module.exit_json(changed=False, msg="package(s) already absent")


if __name__ == '__main__':
    main()
