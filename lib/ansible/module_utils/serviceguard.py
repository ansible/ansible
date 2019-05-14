# -*- coding: utf-8 -*-
# Copyright (c) 2019, Christian Sandrini
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

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
