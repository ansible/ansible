# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Christian Sandrini
# All rights reserved.
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
import re


def parse_cluster_state(module):
    cmviewcl = module.params['path'] + '/cmviewcl'

    retval = {}
    retval['nodes'] = {}
    retval['pkgs'] = {}

    (rc, out, err) = module.run_command([cmviewcl, '-v', '-f', 'line'])

    if rc != 0:
        module.fail_json(msg="Failure %d running cmviewcl: %s" % (rc, err))

    for line in out.split('\n'):

        normExec = re.search(r'(^[0-9a-z_]+)=([0-9a-zA-Z_]+)$', line)
        subExec = re.search(r'(\w+):([0-9a-z-_]+)\|(.*\|)*([0-9a-zA-Z_]+)=(.+)$', line)

        if normExec is not None:
            retval[normExec.group(1)] = normExec.group(2)
        elif subExec is not None:
            section = subExec.group(1)
            name = subExec.group(2)

            if section == 'node':
                if name not in retval['nodes'].keys():
                    retval['nodes'][name] = {}

                if subExec.group(3) is None:
                    retval['nodes'][name][subExec.group(4)] = subExec.group(5).replace('"', '')
                    retval['nodes'][name]['pkgs'] = {}

            elif section == 'package':
                if subExec.group(3) is None:
                    if subExec.group(4) == 'name':
                        pkgTempName = subExec.group(5)
                        retval['pkgs'][pkgTempName] = {}
                    else:
                        retval['pkgs'][pkgTempName][subExec.group(4)] = subExec.group(5).replace('"', '')
                elif subExec.group(3).startswith("node"):
                    if subExec.group(5) == 'Primary':
                        primaryNode = re.search(r'(\w+):(\w+)|$', subExec.group(3))
                        retval['pkgs'][pkgTempName]['primary_node'] = primaryNode.group(2)

    return retval
