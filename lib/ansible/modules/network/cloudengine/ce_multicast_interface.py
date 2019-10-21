#!/usr/bin/python
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ce_multicast_interface
version_added: "2.10"
author: xuxiaowei0512 (@CloudEngine-Ansible)
short_description: Manages multicast interface resources and attributes on Huawei CloudEngine switches.
description:
  - Manages multicast interface configurations on Huawei CloudEngine switches.
options:
  vrf_name:
     description:
       - VPN instance name, string length 1 to 32.
     required: true
     default: _public_
     type: str
  interface:
    description:
      -Specify interface name.
    required: true
    type: str
  pim:
   description:
     - pim mode, sm or dm.
   type: str
   choices: ['sm', 'dm']
  bsr_boundary:
    description:
      - Specify pim bsr-boundary, Both or incoming,default is None.
    type: str
    choices: ['Incoming', 'Both']
  timer_hello:
    description:
      - Specify pim timer hello interval,value of interval is from 1 to 1800.
    type: int
  graft_retry:
    description:
      - Specify pim timer graft-retry.
    type: int
  hello_opt_holdtime:
    description:
      - Specify pim hello-option holdtime interval,int value of interval is from 1 to 65535.
    type: int
  neighbor_policy:
    description:
      - Specify pim neighbor-policy basic-acl-number or acl-name acl-name.
    type: str
  require_genid:
    description:
      - Enable pim require-genid.
    type: bool
  dr_priority:
    description:
      - Specify pim timer dr-switch-delay interval,range is from 0 to 4294967295.
    type: int
  dr_switch_delay:
    description:
      - Specify pim timer dr-switch-delay interval,int value of interval is from 10 to 3600.
    type: int
  timer_join_prune:
    description:
      - Specify pim timer join-prune interval,range is form 1 to 1800.
    type: int
  holdtime_join_prune:
    description:
      - Specify pim holdtime join-prune interval,and value of interval is from 1 to 65535.
    type: int
  hello_lan_delay:
    description:
      - Specify pim hello-option lan-delay interval,and interval is from 7 to 65535.
    type: int
  override_interval:
    description:
      - Specify pim hello-option override-interval,int value of interval is from 1 to 65535.
    type: int
  join_policy:
    description:
      - Specify pim join-policy asm-acl or ssm-acl or acl.
      - The acl may be a number that is from 2000 to 2999 or 3000 to 3999, or a string
      - the length of which is from 1 to 32 and does not start with a number and is not all numbers.
    type: str
  holdtime_assert:
    description:
      - Specify pim holdtime assert interval,The device default interval is 180,and value of which is
        from 7 to 65535.
    type: int
  bfd:
    description:
      - Specify pim bfd enable.
    type: bool
  bfd_min_rx:
    description:
      - Specify pim bfd min-rx-interval, and min-rx-interval is from 3 to 1000.
    type: int
  bfd_min_tx:
    description:
      - Specify pim bfd min-tx-interval, and min-tx-interval is from 3 to 100.
    type: int
  bfd_detect_multiplier:
    description:
      - Specify pim bfd detect-multiplier,range is form 3 to 50.
    type: int
  silent:
    description:
      - Specify pim silent.
    type: bool
  igmp:
    description:
      - Specify igmp enable.
    type: bool
  state:
    description:
      - Manage the state of the resource.
    type: str
    default: present
    choices: ['present','absent']
'''

EXAMPLES = '''
---
  - name: "pim test1"
    ce_multicast_interface:
      vrf_name: _public_
      interface:  10GE2/0/9
      pim: sm
      bsr_boundary: Incoming
      timer_hello: 345
      hello_opt_holdtime: 345
      neighbor_policy: a
      require_genid: true
      dr_priority: 232
      dr_switch_delay: 232
      timer_join_prune: 232
      holdtime_join_prune: 232
      hello_lan_delay: 232
      override_interval: 232
      join_policy: asm a,ssm a2
      holdtime_assert: 232
      bfd: true
      bfd_min_rx: 232
      bfd_min_tx: 232
      bfd_detect_multiplier: 34
      igmp: true
      graft_retry: 1111
      state: present

  - name: "pim test2"
    ce_multicast_interface:
      vrf_name: _public_
      interface: 10GE2/0/9
      pim: sm
      bsr_boundary: Incoming
      timer_hello: 345
      hello_opt_holdtime: 345
      neighbor_policy: a
      require_genid: true
      dr_priority: 232
      dr_switch_delay: 232
      timer_join_prune: 232
      holdtime_join_prune: 232
      hello_lan_delay: 232
      override_interval: 232
      join_policy: asm a,ssm a2
      holdtime_assert: 232
      bfd: true
      bfd_min_rx: 232
      bfd_min_tx: 232
      bfd_detect_multiplier: 34
      igmp: true
      graft_retry: 1111
      state: absent
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"addressFamily": "ipv4unicast", "state": "present", "vrfName": "_public_"}
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: null
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample: {"addressFamily": "ipv4unicast", "state": "present", "vrfName": "_public_"}
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: ["pim sm"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, execute_nc_action
from xml.etree import ElementTree

INTERFACE_PIM_GET = '''
<filter type="subtree">
      <pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <pimafspro>
          <pimAfsIfCfgs>
              %s
          </pimAfsIfCfgs>
        </pimafspro>
      </pim>
    </filter>
'''
INTERFACE_PIM_CONFIG = '''
 <config>
      <pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <pimafspro>
          <pimAfsIfCfgs>
            %s
          </pimAfsIfCfgs>
        </pimafspro>
      </pim>
    </config>
'''
INTERFACE_PIM_IGMP_CONFIG = '''
<config>
      <pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <pimafspro>
          <pimAfsIfCfgs>
            %s
          </pimAfsIfCfgs>
        </pimafspro>
      </pim>
      <dgmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <dgmpIfCfgs>
          %s
        </dgmpIfCfgs>
      </dgmp>
    </config>
'''
INTERFACE_PIM_IGMP_GET = '''
<filter type="subtree">
      <pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <pimafspro>
          <pimAfsIfCfgs>
              %s
          </pimAfsIfCfgs>
        </pimafspro>
      </pim>
      <dgmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <dgmpIfCfgs>
            %s
        </dgmpIfCfgs>
      </dgmp>
    </filter>
'''
INTERFACE_IGMP_CONFIG = '''
    <config>
      <dgmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <dgmpIfCfgs>
          %s
        </dgmpIfCfgs>
      </dgmp>
    </config>
'''
INTERFACE_IGMP_GET = '''
    <filter type="subtree">
      <dgmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <dgmpIfCfgs>
            %s
        </dgmpIfCfgs>
      </dgmp>
    </filter>
'''

def repr_acl(arg):
    """check acl number or acl-name"""
    if re.match(r'(2|3)[0-9]{3}', arg):
        return arg
    return 'acl-name ' + arg


def check_policy_acl(arg):
    """
    arg is the name of acl or basic acl number,
    1<=len(name)<=32, 2000<=number<=2999
     """

    arg = arg.strip()
    if re.match(r'2\d{3}$', arg):
        return True
    elif re.match(r'[a-zA-Z0-9]\S{0,31}$', arg) \
            and not re.match(r'[0-9]{1,32}$', arg):
        return True
    return False


def cmd_changed_map(tag, changed, state=''):
    """ map the change to command
    """
    if tag is None:
        return ''
    tag = tag.strip()
    changed = changed.strip()
    if tag == 'pimMode':
        if state == 'absent':
            if changed == 'Sparse':
                return 'undo pim sm'
            elif changed == 'Dense':
                return 'undo pim dm'
        else:
            if changed == 'Sparse':
                return 'pim sm'
            elif changed == 'Dense':
                return 'pim dm'
    if tag == 'pimBsrBoundary':
        if state == 'absent':
            if changed == 'Incoming':
                return 'undo pim bsr-boundary incoming'
            elif changed == 'None':
                return 'undo pim bsr-boundary'
            elif changed == 'Both':
                return 'undo pim bsr-boundary'
        else:
            if changed == 'Incoming':
                return 'pim bsr-boundary incoming'
            elif changed == 'None':
                return 'undo pim bsr-boundary'
            elif changed == 'Both':
                return 'pim bsr-boundary'
    if tag == 'helloInterval':
        if state == 'absent':
            return 'undo pim timer hello ' + changed
        return 'pim timer hello ' + changed
    if tag == 'helloHoldtime':
        if state == 'absent':
            return 'undo pim hello-option holdtime ' + changed
        elif state == 'present':
            return 'pim hello-option holdtime ' + changed
    if tag == 'nbrPlyName':
        if not re.match(r'2\d{3}', changed):
            changed = 'acl-name ' + changed
        if state == 'absent':
            return 'undo pim neighbor-policy ' + changed
        elif state == 'present':
            return 'pim neighbor-policy ' + changed
    if tag == 'requireGenId':
        if changed == 'true' and state != 'absent':
            return 'pim require-genid'
        elif changed == 'false' or state == 'absent':
            return 'undo pim require-genid '
    if tag == 'drPriority':
        if state == 'absent':
            return 'undo pim hello-option dr-priority ' + changed
        elif state == 'present':
            return 'pim hello-option dr-priority ' + changed
    if tag == 'drSwtDelayInterval':
        if state == 'absent':
            return 'undo pim timer dr-switch-delay ' + changed
        elif state == 'present':
            return 'pim timer dr-switch-delay ' + changed
    if tag == 'jpTimerInterval':
        if state == 'absent':
            return 'undo pim timer join-prune ' + changed
        elif state == 'present':
            return 'pim timer join-prune ' + changed
    if tag == 'jpHoldtime':
        if state == 'absent':
            return 'undo pim holdtime join-prune ' + changed
        elif state == 'present':
            return 'pim holdtime join-prune ' + changed
    if tag == 'helloLanDelay':
        if state == 'absent':
            return 'undo pim hello-option lan-delay ' + changed
        elif state == 'present':
            return 'pim hello-option lan-delay ' + changed
    if tag == 'helloOverride':
        if state == 'absent':
            return 'undo pim hello-option override-interval ' + changed
        elif state == 'present':
            return 'pim hello-option override-interval ' + changed
    if tag == 'assertHoldtime':
        if state == 'absent':
            return 'undo pim holdtime assert ' + changed
        elif state == 'present':
            return 'pim holdtime assert ' + changed
    if tag == 'bfdEnable':
        if state == 'absent':
            return 'undo pim bfd enable'
        elif state == 'present' and changed == 'false':
            return 'undo pim bfd enable '
        return 'pim bfd enable'
    if tag == 'bfdMinRx':
        if state == 'absent':
            return 'undo pim bfd min-rx-interval ' + changed
        elif state == 'present':
            return 'pim bfd min-rx-interval ' + changed
    if tag == 'bfdMinTx':
        if state == 'absent':
            return 'undo pim bfd min-tx-interval ' + changed
        elif state == 'present':
            return 'pim bfd min-tx-interval ' + changed
    if tag == 'bfdMultiplier':
        if state == 'absent':
            return 'undo pim bfd detect-multiplier ' + changed
        elif state == 'present':
            return 'pim bfd detect-multiplier ' + changed
    if tag == 'isSilent':
        if state == 'absent':
            return 'undo pim silent'
        elif state == 'present':
            return 'pim silent'
    if tag == 'jpAsmPlyName':
        if state == 'absent':
            return 'undo pim join-policy asm ' + repr_acl(changed)
        elif state == 'present':
            return 'pim join-policy asm ' + repr_acl(changed)
    if tag == 'jpSsmPlyName':
        if state == 'absent':
            return 'undo pim join-policy ssm ' + repr_acl(changed)
        elif state == 'present':
            return 'pim join-policy ssm ' + repr_acl(changed)
    if tag == 'jpPlyName':
        if state == 'absent':
            return 'undo pim join-policy ' + repr_acl(changed)
        elif state == 'present':
            return 'pim join-policy ' + repr_acl(changed)
    if tag == 'graftRetry':
        if state == 'absent':
            return 'undo pim timer graft-retry ' + changed
        elif state == 'present':
            return 'pim timer graft-retry ' + changed
    if tag == 'gmpEnable':
        if state == 'absent' or changed == 'null':
            return 'undo igmp enable'
        return 'igmp enable'
    return ''


def bulid_pim_xml(kwargs, opt='get'):
    """bulid xml string from dict """
    result = ''
    for key in kwargs.keys():
        if kwargs.get(key) and key != 'gmpEnable':
            if opt == 'get' and key != 'ifName':
                result += '<%s></%s>' % (key, key)
            else:
                result += '<%s>%s</%s>' % (key, kwargs[key], key)
    if opt == 'merge':
        return '<pimAfsIfCfg operation="merge">%s</pimAfsIfCfg>' % result
    elif opt == 'delete':
        return '<pimAfsIfCfg operation="delete">%s</pimAfsIfCfg>' % result
    return '<pimAfsIfCfg>%s</pimAfsIfCfg>' % result


def build_igmp_xml(kwargs, opt=''):
    """bulid xml string from dict """
    if kwargs.get('gmpEnable') is None:
        return ''
    gmp = kwargs.get('gmpEnable')
    interface = kwargs.get('ifName')
    vrf = kwargs.get('vrfName')
    if opt == 'merge':
        return '<dgmpIfCfg operation="merge"><vrfName>%s</vrfName><ifName>%s</ifName><addrFamily>ipv4unicast\
        </addrFamily><gmpEnable>%s</gmpEnable></dgmpIfCfg>' % (vrf, interface, gmp)
    elif opt == 'delete':
        return '<dgmpIfCfg operation="delete"><vrfName>%s</vrfName><ifName>%s</ifName><addrFamily>ipv4unicast\
        </addrFamily><gmpEnable>%s</gmpEnable></dgmpIfCfg>' % (vrf, interface, gmp)
    return '<dgmpIfCfg><vrfName></vrfName><ifName>%s</ifName><addrFamily>ipv4unicast\
        </addrFamily><gmpEnable></gmpEnable></dgmpIfCfg>' % interface


class MulticastInterface(object):
    """
     Manages Multicast Interface resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.config_xml = ''
        self._pim_config = ''
        self.current_cfg = dict()
        self.proposed = dict()
        self.config_imgp = ''
        self.existing = dict()
        self.end_state = dict()
        # interface config info
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)
        self.intf_name = self.module.params['interface']
        self.xml_dict = dict(addressFamily='ipv4unicast')
        self.state = self.module.params['state']

        # state
        self.results = dict()
        self.updates_cmd = []
        self.changed = False

    def _check_arg_int(self, name, int_range=(), tag=''):
        arg = self.module.params.get(name)
        if arg is None:
            return ''
        elif int_range[0] <= int(arg) <= int_range[1] and tag != '':
            self.proposed[name] = arg
            self.xml_dict[tag] = arg
            return 'ok'
        return 'error'

    def _check_arg_boolean(self, name, tag=''):
        arg = self.module.params.get(name)
        if arg is None:
            return ''
        elif arg.strip().lower() in ['true', 'false']:
            self.proposed[name] = arg
            self.xml_dict[tag] = arg
            return 'ok'
        return 'error'

    def _check_arg_str(self, name, str_range=(), tag=''):
        arg = self.module.params.get(name)
        if arg is None:
            return ''
        elif arg.strip() in str_range:
            self.proposed[name] = arg
            self.xml_dict[tag] = arg
            return 'ok'
        return 'error'

    def check_arg_jply(self, acl):
        """check acl param
        """
        value_acl = re.sub(r'(ssm|asm)', '', acl)
        value_acl = re.sub(r'acl-name', '', value_acl).lower().strip()
        if re.match(r'([2-3][0-9]{3})$', value_acl) or re.match(r'[^0-9]\S{0,31}$', value_acl):
            if 'asm' in acl:
                self.xml_dict['jpAsmPlyName'] = value_acl
            elif 'ssm' in acl:
                self.xml_dict['jpSsmPlyName'] = value_acl
            else:
                self.xml_dict['jpPlyName'] = value_acl
            self.proposed['join_policy'] = acl
            return 'ok'
        return 'error'

    def check_params(self):
        """check module params"""
        param = self.module.params.copy()
        self.xml_dict['ifName'] = param.get('interface')
        self.xml_dict['vrfName'] = param.get('vrf_name') or '_public_'
        # pim enable,
        # if self._check_arg_boolean('pim','pimsmEnable') == 'error':
        # self.module.fail_json(
        # msg='Error: pim enable must be true or false.')

        # key: pim ; cmd:pim pim sm|dm; xml tag:pimBsrBoundary; value: 'none','both','Incoming'.
        pim_mode = param.get('pim')
        if pim_mode is not None and pim_mode.strip().lower() in ['sm', 'dm']:
            if pim_mode.strip().lower() == 'sm':
                self.proposed['pim'] = 'sm'
                self.xml_dict['pimsmEnable'] = 'true'
                self.xml_dict['pimMode'] = 'Sparse'
            else:
                self.proposed['pim'] = 'dm'
                self.xml_dict['pimsmEnable'] = 'true'
                self.xml_dict['pimMode'] = 'Dense'
        elif pim_mode is not None:
            self.module.fail_json(
                msg='Error: pim enable sm or dm.')

        # key: bsr_boundary; cmd:pim bsr-boundary [ incoming ]; xml tag:pimBsrBoundary; value: 'none','both','Incoming'.
        if self._check_arg_str('bsr_boundary', str_range=('None', 'Both', 'Incoming'), tag='pimBsrBoundary') == 'error':
            self.module.fail_json(
                msg='Error: pim bsr-boundary is none, both or incoming.')

        # key: timer_hello; cmd:pim timer hello interval; xml tag:helloInterval; value: 1 - 65535, default 105.
        if self._check_arg_int('timer_hello', int_range=(1, 1800), tag='helloInterval') == 'error':
            self.module.fail_json(
                msg='Error: pim timer hello interval is in range 1-18000.')

        # key: timer_hello; cmd:pim hello-option holdtime interval; xml tag:helloHoldtime;
        #  value: 1 - 65535, default 105.
        if self._check_arg_int('hello_opt_holdtime', int_range=(1, 65535), tag='helloHoldtime') == 'error':
            self.module.fail_json(
                msg='Error: pim hello-option holdtime  is in range 1-65535.')

        # key: neighbor_policy; cmd:pim neighbor-policy { basic-acl-number | acl-name acl-name };
        # xml tag:nbrPlyName; value: int(2000 - 2999) or basic acl name(0<len(name)<33).
        nei_policy = param.get('neighbor_policy')
        if nei_policy is not None:
            if check_policy_acl(nei_policy):
                self.proposed['neighbor_policy'] = nei_policy
                # nei_policy = nei_policy.replace('acl-name ','')
                self.xml_dict['nbrPlyName'] = nei_policy
            else:
                self.module.fail_json(
                    msg='Error: pim neighbor-policy acl is wrong.')

        # key: require_genid; cmd:pim require-genid ; xml tag:requireGenId; value: 'true' or 'false'.
        if self._check_arg_boolean('require_genid', 'requireGenId') == 'error':
            self.module.fail_json(
                msg='Error: pim require-genid must be true or false.')

        # key: dr_priority; cmd:pim hello-option dr-priority interval; xml tag:drPriority;
        #  value: 0 - 4294967295, default 1.
        if self._check_arg_int('dr_priority', int_range=(0, 4294967295), tag='drPriority') == 'error':
            self.module.fail_json(
                msg='Error: pim hello-option dr-priority is wrong value.')

        # key: dr_switch_delay; cmd:pim timer dr-switch-delay interval; xml tag:drSwtDelayInterval; value: 10 - 3600.
        if self._check_arg_int('dr_switch_delay', int_range=(10, 3600), tag='drSwtDelayInterval') == 'error':
            self.module.fail_json(
                msg='Error: pim timer dr-switch-delay is wrong value.')

        # key: timer_join_prune; cmd:pim timer join-prune interval; xml tag:jpTimerInterval; value: 1 - 1800,default 60.
        if self._check_arg_int('timer_join_prune', int_range=(1, 1800), tag='jpTimerInterval') == 'error':
            self.module.fail_json(
                msg='Error: pim timer join-prune is wrong value.')

        # key: holdtime_join_prune; cmd:pim holdtime join-prune interval; xml tag:jpHoldtime;
        # value: 1 - 65535,default 210.
        if self._check_arg_int('holdtime_join_prune', int_range=(1, 65535), tag='jpHoldtime') == 'error':
            self.module.fail_json(
                msg='Error: pim holdtime join-prune is wrong value.')

        # key: hello_lan_delay; cmd:pim hello-option lan-delay interval; xml tag:helloLanDelay;
        #  value: 7 - 65535,default 180.
        if self._check_arg_int('hello_lan_delay', int_range=(1, 32767), tag='helloLanDelay') == 'error':
            self.module.fail_json(
                msg='Error: pim hello-option lan-delay is wrong value.')

        # key: override_interval; cmd:pim hello-option override-interval interval; xml tag:helloOverride;
        #  value: 1 - 65535,default 2500.
        if self._check_arg_int('override_interval', int_range=(1, 65535), tag='helloOverride') == 'error':
            self.module.fail_json(
                msg='Error: pim hello-option override-interval is wrong value.')

        # key: holdtime_assert; cmd:pim holdtime assert interval; xml tag:bfdMinRx; value: 7 - 65535,default 180.
        if self._check_arg_int('holdtime_assert', int_range=(7, 65535), tag='assertHoldtime') == 'error':
            self.module.fail_json(
                msg='Error: pim holdtime assert is wrong value.')

        # key: join_policy;
        # cmd:pim join-policy { asm { basic-acl-number | acl-name acl-name } | ssm { advanced-acl-number |
        #  acl-name acl-name } | advanced-acl-number | acl-name acl-name };
        # xml tag:jpPlyName/jpAsmPlyName/jpSsmPlyName; value: .
        jpply = param.get('join_policy')
        if jpply is not None:
            plys = jpply.split(',')
            for ply in plys:
                if ply.strip() == '':
                    continue
                elif self.check_arg_jply(ply) == 'error':
                    self.module.fail_json(
                        msg='Error: pim join-policy acl(s) wrong.')
                    break

        # key: bfd; cmd:pim bfd enable; xml tag:bfdEnable; value: 'true' or 'false'.
        if self._check_arg_boolean('bfd', 'bfdEnable') == 'error':
            self.module.fail_json(
                msg='Error: pim bfd enable must be true or false.')

        # key: bfd_min_tx; cmd:min-rx-interval ; xml tag:bfdMinRx; value: 3 - 1000,default 1000.
        if self._check_arg_int('bfd_min_rx', int_range=(3, 1000), tag='bfdMinRx') == 'error':
            self.module.fail_json(
                msg='Error: pim min-rx-interval is wrong value.')

        # key: bfd_min_tx; cmd:min-tx-interval ; xml tag:bfdMinTx; value: 3 - 1000,default 1000.
        if self._check_arg_int('bfd_min_tx', int_range=(3, 1000), tag='bfdMinTx') == 'error':
            self.module.fail_json(
                msg='Error: pim min-tx-interval is wrong value.')

        # key: bfd_detect_multiplier; cmd:detect-multiplier ; xml tag:assertHoldtime; value: 3 - 50,default 3.
        if self._check_arg_int('bfd_detect_multiplier', int_range=(3, 50), tag='bfdMultiplier') == 'error':
            self.module.fail_json(
                msg='Error: pim detect-multiplier is wrong value.')

        # key: graft_retry; cmd:pim timer graft-retry ; xml tag:graftRetry; value: 1 - 65535,default 3.
        if self._check_arg_int('graft_retry', int_range=(1, 65535), tag='graftRetry') == 'error':
            self.module.fail_json(
                msg='Error: pim detect-multiplier is wrong value.')

        # key: silent; cmd:pim silent; xml tag:isSilent; value: 'true' or 'false'.
        if self._check_arg_boolean('silent', 'isSilent') == 'error':
            self.module.fail_json(
                msg='Error: pim enable silent must be true or false.')

        # key: igmp; cmd:igmp enable; xml tag:gmpEnable; value: 'true' or 'false'.
        igmp_enable = param.get('igmp')
        if igmp_enable is not None:
            if igmp_enable.strip().lower() in ['true', 'false']:
                self.config_imgp = '<gmpEnable>%s</gmpEnable>' % igmp_enable
                self.proposed['igmp'] = igmp_enable
                self.xml_dict['gmpEnable'] = igmp_enable
            elif igmp_enable is not None:
                self.module.fail_json(
                    msg='Error: igmp enable must be true or false.')

    def bulid_xml(self, opt='get'):
        """bulid xml
        """
        flag = 0
        pim_entry = ''
        if self.xml_dict.get('drSwtDelayInterval'):
            self.xml_dict['isDrSwtDelay'] = 'true'
        if opt == 'delete':
            for xkey in iter(self.xml_dict):
                if xkey not in ['addressFamily', 'ifName', 'gmpEnable', 'vrfName'] and pim_entry == '':
                    pim_entry = bulid_pim_xml(self.xml_dict, opt)
        else:
            pim_entry = bulid_pim_xml(self.xml_dict, opt)
        if flag == 1:
            pim_entry = bulid_pim_xml(self.xml_dict, opt)
        igmp_entry = build_igmp_xml(self.xml_dict, opt)
        if pim_entry != '' and igmp_entry != '':
            if opt == 'get' or opt == '':
                return INTERFACE_PIM_IGMP_GET % (pim_entry, igmp_entry)
            return INTERFACE_PIM_IGMP_CONFIG % (pim_entry, igmp_entry)
        elif pim_entry != '':
            if opt == 'get' or opt == '':
                return INTERFACE_PIM_GET % pim_entry
            return INTERFACE_PIM_CONFIG % pim_entry
        elif igmp_entry != '':
            if opt == 'get' or opt == '':
                return INTERFACE_IGMP_GET % igmp_entry
            return INTERFACE_IGMP_CONFIG % igmp_entry
        return ''

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)
            return False
        return True

    def get_interface_pim(self):
        """get interface pim configure"""
        tmp_dict = {}
        required_xml = self.bulid_xml()
        if required_xml == '':
            return None
        recv_xml = get_nc_config(self.module, required_xml)
        if "<data/>" in recv_xml:
            return None
        else:
            xml_str = recv_xml.replace('\r', '').replace('\n', ''). \
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            pimaic = root.iter('pimAfsIfCfg')
            for aic in pimaic:
                for tmp in aic.iter():
                    if tmp.tag != 'pimAfsIfCfg':
                        tmp_dict[tmp.tag] = tmp.text

            dgmpic = root.iter('dgmpIfCfg')
            for dgmp in dgmpic:
                for tmp in dgmp.iter():
                    if tmp.tag != 'dgmpIfCfg':
                        tmp_dict[tmp.tag] = tmp.text
        return tmp_dict

    def check_difference(self):
        """check difference between existing and end-state"""
        if self.end_state:
            for key in iter(self.end_state):
                end = self.end_state[key]
                exi = None
                if self.existing:
                    exi = self.existing.get(key)
                if exi is None or end != exi:
                    self.changed = True
                    update_cmd = cmd_changed_map(key, end, state=self.state)
                    if update_cmd != '' and update_cmd not in self.updates_cmd:
                        self.updates_cmd.append(update_cmd)
            if self.existing:
                for key in iter(self.existing):
                    if self.end_state.get(key):
                        if self.end_state[key] != self.existing[key]:
                            self.changed = True
                            update_cmd = cmd_changed_map(key, self.end_state[key], state='present')
                            if update_cmd != '' and update_cmd not in self.updates_cmd:
                                self.updates_cmd.append(update_cmd)
                    else:
                        self.changed = True
                        update_cmd = cmd_changed_map(key, 'null', 'absent')
                        if update_cmd != '' and update_cmd not in self.updates_cmd:
                            self.updates_cmd.append(update_cmd)

        else:
            if self.existing:
                for key in iter(self.existing):
                    self.changed = True
                    update_cmd = cmd_changed_map(key, self.existing[key], state=self.state)
                    if update_cmd != '' and update_cmd not in self.updates_cmd:
                        self.updates_cmd.append(update_cmd)

    def edit_interface_pim(self):
        """configure interface pim"""
        required_xml = self.bulid_xml(opt='merge')
        if required_xml != '':
            obj = set_nc_config(self.module, required_xml)
            if self.check_response(obj, 'merge'):
                self.results['stdout'] = '<ok/>'

    def delete_interface_pim(self):
        """delete config """
        existing = self.get_existing()
        if existing is None or existing == {}:
            self.results['stdout'] = '<ok/>'
            return
        required_xml = self.bulid_xml(opt='delete')
        if required_xml != '':
            obj = set_nc_config(self.module, required_xml)
            if self.check_response(obj, 'delete'):
                self.results['stdout'] = '<ok/>'

    def get_existing(self):
        """get existing """
        if self.existing:
            return self.existing
        self.existing = self.get_interface_pim()
        return self.existing

    def get_end_state(self):
        """get end state"""
        if self.end_state:
            return self.end_state
        self.end_state = self.get_interface_pim()
        return self.end_state

    def work(self):
        """worker."""
        self.check_params()
        self.get_existing()
        if self.current_cfg == {}:
            curr_dict = self.get_interface_pim()
            if curr_dict is not None:
                self.current_cfg.update(curr_dict)

        if self.state == 'present':
            self.edit_interface_pim()
        else:
            self.delete_interface_pim()

        self.get_end_state()
        self.check_difference()
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        self.results['updates'] = self.updates_cmd
        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        vrf_name=dict(required=False, type='str', default='_public_'),
        interface=dict(required=True),
        pim=dict(required=False, choices=['sm', 'dm']),
        bsr_boundary=dict(required=False, choices=['Incoming', 'Both']),
        timer_hello=dict(type='int', required=False),
        hello_opt_holdtime=dict(type='int', required=False),
        neighbor_policy=dict(required=False, type='str'),
        require_genid=dict(type='bool'),
        dr_priority=dict(type='int', required=False),
        graft_retry=dict(type='int', required=False),
        dr_switch_delay=dict(type='int', required=False),
        timer_join_prune=dict(type='int', required=False),
        holdtime_join_prune=dict(type='int', required=False),
        hello_lan_delay=dict(type='int', required=False),
        override_interval=dict(type='int', required=False),
        join_policy=dict(required=False, type='str'),
        holdtime_assert=dict(type='int', required=False),
        bfd=dict(type='bool'),
        bfd_min_rx=dict(type='int', required=False),
        bfd_min_tx=dict(type='int', required=False),
        bfd_detect_multiplier=dict(type='int', required=False),
        silent=dict(type='bool'),
        igmp=dict(type='bool')
    )
    multicast = MulticastInterface(argument_spec)
    multicast.work()


if __name__ == '__main__':
    main()
