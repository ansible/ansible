#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Franck Cuny <franck@lumberjaph.net>
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

DOCUMENTATION = '''
---
module: cpanm
short_description: Manages Perl library dependencies.
description:
  - Manage Perl library dependencies.
version_added: "1.6"
options:
  name:
    description:
      - The name of the Perl library to install. You may use the "full distribution path", e.g.  MIYAGAWA/Plack-0.99_05.tar.gz
    required: false
    default: null
    aliases: ["pkg"]
  from_path:
    description:
      - The local directory from where to install
    required: false
    default: null
  notest:
    description:
      - Do not run unit tests
    required: false
    default: false
  locallib:
    description:
      - Specify the install base to install modules
    required: false
    default: false
  mirror:
    description:
      - Specifies the base URL for the CPAN mirror to use
    required: false
    default: false
  mirror_only:
    description:
      - Use the mirror's index file instead of the CPAN Meta DB
    required: false
    default: false
  installdeps:
    description:
      - Only install dependencies
    required: false
    default: false
    version_added: "2.0"
notes:
   - Please note that U(http://search.cpan.org/dist/App-cpanminus/bin/cpanm, cpanm) must be installed on the remote host.
author: "Franck Cuny (@franckcuny)"
'''

EXAMPLES = '''
# install Dancer perl package
- cpanm: name=Dancer

# install version 0.99_05 of the Plack perl package
- cpanm: name=MIYAGAWA/Plack-0.99_05.tar.gz

# install Dancer into the specified locallib
- cpanm: name=Dancer locallib=/srv/webapps/my_app/extlib

# install perl dependencies from local directory
- cpanm: from_path=/srv/webapps/my_app/src/

# install Dancer perl package without running the unit tests in indicated locallib
- cpanm: name=Dancer notest=True locallib=/srv/webapps/my_app/extlib

# install Dancer perl package from a specific mirror
- cpanm: name=Dancer mirror=http://cpan.cpantesters.org/
'''

def _is_package_installed(module, name, locallib, cpanm):
    cmd = ""
    if locallib:
        os.environ["PERL5LIB"] = "%s/lib/perl5" % locallib
    cmd = "%s perl -M%s -e '1'" % (cmd, name)
    res, stdout, stderr = module.run_command(cmd, check_rc=False)
    if res == 0:
       return True
    else:
       return False

def _build_cmd_line(name, from_path, notest, locallib, mirror, mirror_only,
                    installdeps, cpanm):
    # this code should use "%s" like everything else and just return early but not fixing all of it now.
    # don't copy stuff like this
    if from_path:
        cmd = "{cpanm} {path}".format(cpanm=cpanm, path=from_path)
    else:
        cmd = "{cpanm} {name}".format(cpanm=cpanm, name=name)

    if notest is True:
        cmd = "{cmd} -n".format(cmd=cmd)

    if locallib is not None:
        cmd = "{cmd} -l {locallib}".format(cmd=cmd, locallib=locallib)

    if mirror is not None:
        cmd = "{cmd} --mirror {mirror}".format(cmd=cmd, mirror=mirror)

    if mirror_only is True:
        cmd = "{cmd} --mirror-only".format(cmd=cmd)

    if installdeps is True:
        cmd = "{cmd} --installdeps".format(cmd=cmd)

    return cmd


def main():
    arg_spec = dict(
        name=dict(default=None, required=False, aliases=['pkg']),
        from_path=dict(default=None, required=False),
        notest=dict(default=False, type='bool'),
        locallib=dict(default=None, required=False),
        mirror=dict(default=None, required=False),
        mirror_only=dict(default=False, type='bool'),
        installdeps=dict(default=False, type='bool'),
    )

    module = AnsibleModule(
        argument_spec=arg_spec,
        required_one_of=[['name', 'from_path']],
    )

    cpanm       = module.get_bin_path('cpanm', True)
    name        = module.params['name']
    from_path   = module.params['from_path']
    notest      = module.boolean(module.params.get('notest', False))
    locallib    = module.params['locallib']
    mirror      = module.params['mirror']
    mirror_only = module.params['mirror_only']
    installdeps = module.params['installdeps']

    changed   = False

    installed = _is_package_installed(module, name, locallib, cpanm)

    if not installed:
        out_cpanm = err_cpanm = ''
        cmd       = _build_cmd_line(name, from_path, notest, locallib, mirror,
                                    mirror_only, installdeps, cpanm)

        rc_cpanm, out_cpanm, err_cpanm = module.run_command(cmd, check_rc=False)

        if rc_cpanm != 0:
            module.fail_json(msg=err_cpanm, cmd=cmd)

        if err_cpanm and 'is up to date' not in err_cpanm:
            changed = True

    module.exit_json(changed=changed, binary=cpanm, name=name)

# import module snippets
from ansible.module_utils.basic import *

main()
