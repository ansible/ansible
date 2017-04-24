#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2017  Matthias Tafelmeier

# pkt_steering is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# pkt_steering is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: pkt_steering
short_description: Control active and configured kernel packet steering settings
description:
     - This module controls active and configured kernel packet steering
       settings in a convenient way. (ref.
       U(https://www.kernel.org/doc/Documentation/networking/scaling.txt))
version_added: "2.5"
options:
    tech:
        description:
         - Packet Steering technology to configure.
        required: true
        choices: ['rfs', 'rps', 'xps']
    state:
        description:
         - State of the specific packet steering technology. The state also
           decides about the steering resources distribution. For xps/rps
           C(absent), C(balanced), C(specific) are allowed. C(balanced)
           purposes to bring about a benevolent distribution with respecting
           also numa arches intrinsics like a split node cache hierarchy.  Rfs
           only discerns C(present) and C(absent).
        required: true
        choices : ['present', 'absent', 'balanced', 'specific']
    iface:
        description:
         - Kernel net interface steering to configure on. E.g. eth0, or enp2s0.
        required : true
    distribution:
        description:
         - Path to json file holding the individually thought up packet
           steering queues to cpu association. Available for C(tech=xps) or
           C(tech=rps) - it's useful when something else than balanced
           steering is required.
           Required when C(state=specific).
        required : false
        default: None
    tab_size:
        description:
          -  Kernel RFS flow dissection table size for rfs.
             Optional when C(tech=rfs).
        required : false
        default: 32768

author:
    - Matthias Tafelmeier (@cherusk)
'''

EXAMPLES = '''
# balance out tx queues of a potentially numa based arch via XPS
- name: balanced xps
  pkt_steering:
    tech: xps
    state: balanced
    iface: enp2s0

# balance rps based on distribution spec
- name: rps based on own steering distribution
  pkt_steering:
    tech: rps
    state: balanced
    iface=: enp2s0
    distribution: ./my_distr.json
'''
#  Basic example for the content of ./my_distr.json:
#  {
#      "distr": [
#      { "0": [1, [4, 5]] },
#      { "1": [1, [2, 3]] },
#        [...]
#      ]
#  }
#  Would spread queue 0 to cpus 1,4-5 and so on.

RETURN = '''
changed:
    description: success of execution
    returned: always
    type: string
    sample: 'false'
'''

import json
import re
from ansible.module_utils.basic import AnsibleModule


class KernelInteractor:
    ''' Abstracting away kernel config interface interactions. '''

    numa_arch_re = re.compile(r"^(?P<cpu>\d+),(?P<numa_n>\d+)")

    def __init__(self, module):
        self.module = module
        self.abbr_to_f = {
            'rfs_tab': '/proc/sys/net/core/rps_sock_flow_entries',
            'rfs_f_cnt': '/sys/class/net/%s/queues/rx-%s/rps_flow_cnt',
            'rps_cpus': '/sys/class/net/%s/queues/rx-%s/rps_cpus',
            'xps_cpus': '/sys/class/net/%s/queues/tx-%s/xps_cpus'}

    def out_cnfg(self, what, content, iface=None):
        changed = False

        if what == 'xps_cpus' or what == 'rps_cpus':
            for qu, mask in content.items():
                f = self.abbr_to_f[what] % (iface, qu)
                changed = self._write_f(f, mask)

        if what == 'rfs_tab':
            f = self.abbr_to_f[what]
            changed = self._write_f(f, content)

        if what == 'rfs_f_cnt':
            qu_num = content[0]
            for qu in range(0, qu_num):
                f = self.abbr_to_f[what] % (iface, qu)
                changed = self._write_f(f, content[1])

        return changed

    def determine_qu_num(self, _type, iface):
        cmd = 'ls -d /sys/class/net/%s/queues/%s-* | wc -l' % (iface, _type)

        rc, out, err = self.module.run_command(cmd, use_unsafe_shell=True)
        if rc == 0:
            return int(out)
        else:
            self.module.fail_json(msg="CMD: %s \n cannot determine queue number" % (cmd))

    def determine_arch_nodes(self):
        arch_specs = {}
        cmd = 'lscpu -p=CPU,NODE'

        rc, out, err = self.module.run_command(cmd)
        if rc == 0:
            out = [line for line in out.splitlines() if not line.startswith('#')]
            for line in out:
                numa_spec = self.numa_arch_re.search(line)
                cpu = int(numa_spec.group("cpu"))
                numa_n = int(numa_spec.group("numa_n"))

                if numa_n not in arch_specs.keys():
                    arch_specs[numa_n] = []

                arch_specs[numa_n].append(cpu)

            return arch_specs
        else:
            self.module.fail_json(msg="CMD: %s \n cannot determine arch outline" % (cmd))

    def _read_f(self, f):
        content = ""
        with open(f, 'rb') as in_f:
            content = in_f.read()
        return content

    def _write_f(self, f, content):
        hex_bef = self.module.digest_from_file(f, 'sha1')
        with open(f, "w+") as out_f:
            out_f.write(str(content))
            out_f.flush()
        hex_aft = self.module.digest_from_file(f, 'sha1')

        return (hex_bef != hex_aft)


class Associator:
    ''' Component to hold the queue to cpu association mapping logic for the varios steering technologies.'''
    def __init__(self, args, module, interactor, translator):
        self.k_interactor = interactor
        self.translator = translator
        self.args = args
        self.module = module

    def distribute(self):
        path = "_do_%s" % self.args['state']
        path = getattr(self, path, "unknown")

        if path == "unknown":
            raise RuntimeError("unknown code path")

        return path()

    def _do_balanced(self):
        arch_specs = self.k_interactor.determine_arch_nodes()
        numa_n_num = len(arch_specs.keys())
        qu_num = 0
        numa_to_qus = {}

        qu_num = self._tech_spec_qu_num()

        if qu_num < numa_n_num:
            self.module.fail_json(msg="Less driver qus than numa nodes (qus: %s, \
            nodes: %s)\n -> steering is rather deteriorating your netstack \
            performance in this scenario - consider aligning driver to CPUs \
            first or go for state specific" % (str(qu_num), str(numa_n_num)))

        fraternal = int(qu_num / numa_n_num)
        rest = qu_num % numa_n_num

        last = 0
        for n in range(0, numa_n_num):
            delta = fraternal
            if rest > 0:
                delta = delta + 1
                rest = rest - 1
            numa_to_qus[n] = (last, last + delta - 1)  # since of start at 0
            last = last + delta

        qu_to_mask = self.translator.form_qu_to_mask(arch_specs, numa_to_qus)

        what = "%s_cpus" % self.args['tech']
        return self.k_interactor.out_cnfg(what, qu_to_mask, iface=self.args['iface'])

    def _do_specific(self):
        _qu_mask_map = json.loads(self.k_interactor._read_f(self.args['distribution']))
        _qu_mask_map = self.translator.ext_to_internal_qu_map(_qu_mask_map)

        if _qu_mask_map is None:
            self.module.fail_json(msg="SyntaxError in specific distribution param")

        what = "%s_cpus" % self.args['tech']
        return self.k_interactor.out_cnfg(what, _qu_mask_map, iface=self.args['iface'])

    def _do_absent(self):
        qu_num = self._tech_spec_qu_num()
        cleansing_tab = {}

        for qu in range(0, qu_num):
            cleansing_tab[qu] = "0"

        what = "%s_cpus" % self.args['tech']
        return self.k_interactor.out_cnfg(what, cleansing_tab, iface=self.args['iface'])

    def _tech_spec_qu_num(self):
        direction = ''
        if self.args['tech'] == 'rps':
            direction = 'rx'
        if self.args['tech'] == 'xps':
            direction = 'tx'
        return self.k_interactor.determine_qu_num(direction, self.args['iface'])


class Translator:
    ''' Actor for the external to internal and overall internal content translations'''
    def __init__(self):
        pass

    def ext_to_internal_qu_map(self, ext_qu_mask):
        intern_qu_mask = {}

        for elem in ext_qu_mask['distr']:
            for qu, cpus in elem.items():
                intern_cpus = self._expand_ext_cpus(cpus)
                if intern_cpus is None:
                    return intern_cpus
                mask = self._form_per_node_bitmask(intern_cpus)
                intern_qu_mask[qu] = mask

        return intern_qu_mask

    def form_qu_to_mask(self, arch_specs, numa_to_qus):
        qu_to_mask = {}
        for n, qus in numa_to_qus.items():
            for qu in range(qus[0], qus[1]):
                mask = self._form_per_node_bitmask(arch_specs[n])
                qu_to_mask[qu] = mask

        return qu_to_mask

    def _expand_ext_cpus(self, cpus):
        int_cpus = []

        for repres in cpus:
            if isinstance(repres, int):
                int_cpus.append(repres)
            elif isinstance(repres, list):
                if len(repres) > 2:
                    return None
                try:
                    int_cpus.extend(range(repres[0], repres[1] + 1))
                except:
                    return None
            else:
                return None

        return int_cpus

    def _form_per_node_bitmask(self, cpus):
        bitmask = 0
        for cpu in cpus:
            bitmask = bitmask | (1 << int(cpu))

        out = "%x" % bitmask
        out_l = len(out)
        if out_l > 8:
            left_marg = out_l % 8
            sub_grps = (out_l / 8) - 1
            idx_l = [left_marg]
            idx_l.extend(range(left_marg, left_marg + 8 * sub_grps, 8))
            for idx in idx_l:
                out = out[:idx] + "," + out[idx:]

        return out


def run(module, args):

    interactor = KernelInteractor(module)

    changed = False

    if args['tech'] == 'rfs':
        if args['state'] == 'absent':
            changed = interactor.out_cnfg('rfs_tab', '0')

        if args['state'] == 'present':
            f1 = open("/tmp/dbg1", "w+")
            qu_num = interactor.determine_qu_num('rx', args['iface'])
            f1.write(str(qu_num))
            per_qu_flows = int(args['tab_size']) / int(qu_num)
            out_para = (qu_num, per_qu_flows)

            changed = interactor.out_cnfg('rfs_tab', args['tab_size'])
            changed = interactor.out_cnfg('rfs_f_cnt', out_para, iface=args['iface'])
    else:
        # rps or xps
        translator = Translator()
        associator = Associator(args, module, interactor, translator)
        changed = associator.distribute()

    # todo: gconsider return qu_masks
    module.exit_json(changed=changed, **args)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, choices=['present', 'absent', 'balanced', 'specific']),
            tech=dict(required=True, choices=['rfs', 'rps', 'xps']),
            iface=dict(required=True),
            distribution=dict(required=False, default=None),
            tab_size=dict(required=False, type='int', default=32768)),
        supports_check_mode=False
    )

    args = {
        'tech': module.params['tech'],
        'state': module.params['state'],
        'iface': module.params['iface'],
        'distribution': module.params['distribution'],
        'tab_size': module.params['tab_size']
    }

    if args['tech'] == "rfs" and args['state'] in ['balanced', 'specific']:
        module.fail_json(msg="Tech %s: only allows states: present, absent" % (args['tech']))

    if args['tech'] in ['rps', 'xps'] and args['state'] == "present":
        module.fail_json(msg="Tech %s: only allows states: absent, balanced, specific" % (args['tech']))

    if args['state'] == "specific":
        if args['distribution'] is None:
            module.fail_json(msg="State %s: requires param distribution" % (args['state']))

    run(module, args)


if __name__ == '__main__':
    main()
