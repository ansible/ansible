# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.compat.ipaddress import ip_address, ip_network
import json
import shutil
import os
import pwd
import time
import xml.etree.ElementTree as ET
from tempfile import mkstemp


class PFSenseModule(object):
    """ class managing pfsense base configuration """

    def __init__(self, module, config='/cf/conf/config.xml'):
        self.module = module
        self.config = config
        self.tree = ET.parse(config)
        self.root = self.tree.getroot()
        self.aliases = self.get_element('aliases')
        self.interfaces = self.get_element('interfaces')
        self.rules = self.get_element('filter')
        self.shapers = self.get_element('shaper')
        self.dnshapers = self.get_element('dnshaper')
        self.vlans = self.get_element('vlans')
        self.ipsec = self.get_element('ipsec')
        self.openvpn = self.get_element('openvpn')
        self.debug = open('/tmp/pfsense.debug', 'w')

    @staticmethod
    def addr_normalize(addr):
        """ return address element formatted like module argument """
        address = ''
        if 'address' in addr:
            address = addr['address']
        if 'any' in addr:
            address = 'any'
        if 'network' in addr:
            address = 'NET:%s' % addr['network']
        if address == '':
            raise ValueError('UNKNOWN addr %s' % addr)
        if 'port' in addr:
            address += ':%s' % (addr['port'])
        if 'not' in addr:
            address = '!' + address
        return address

    def get_element(self, node):
        """ return <node> configuration element """
        return self.root.find(node)

    def get_elements(self, node):
        """ return all <node> configuration elements  """
        return self.root.findall(node)

    def get_index(self, elt):
        """ Get elt index  """
        return list(self.root).index(elt)

    def get_interface_pfsense_by_name(self, name):
        """ return pfsense interface by name """
        for interface in self.interfaces:
            descr_elt = interface.find('descr')
            if descr_elt is not None and descr_elt.text.strip() == name:
                return interface.tag
        return None

    def get_interface_by_physical_name(self, name):
        """ return pfsense interface physical name """
        for interface in self.interfaces:
            if interface.find('if').text.strip() == name:
                return interface.tag
        return None

    def get_interface_display_name(self, iface):
        """ return pfsense interface display name """
        for interface in self.interfaces:
            if interface.tag == iface:
                descr_elt = interface.find('descr')
                if descr_elt is not None:
                    return descr_elt.text.strip()
                break
        return iface

    def get_interface_physical_name(self, iface):
        """ return pfsense interface physical name """
        for interface in self.interfaces:
            if interface.tag == iface:
                return interface.find('if').text.strip()
        return None

    def get_interface_physical_name_by_name(self, name):
        """ return pfsense interface physical name by name """
        for interface in self.interfaces:
            descr_elt = interface.find('descr')
            if descr_elt is not None and descr_elt.text.strip() == name:
                return interface.find('if').text.strip()
        return None

    def is_interface_pfsense(self, name):
        """ determines if arg is a pfsense interface or not """
        for interface in self.interfaces:
            interface_elt = interface.tag.strip()
            if interface_elt == name:
                return True
        return False

    def is_interface_name(self, name):
        """ determines if arg is an interface name or not """
        for interface in self.interfaces:
            descr_elt = interface.find('descr')
            if descr_elt is not None:
                if descr_elt.text.strip() == name:
                    return True
        return False

    def parse_interface(self, interface, fail=True):
        """ validate param interface field """
        if (interface == 'enc0' or interface == 'IPsec') and self.is_ipsec_enabled():
            return 'enc0'
        if (interface == 'openvpn' or interface == 'OpenVPN') and self.is_openvpn_enabled():
            return 'openvpn'

        if self.is_interface_name(interface):
            return self.get_interface_pfsense_by_name(interface)
        elif self.is_interface_pfsense(interface):
            return interface

        if fail:
            self.module.fail_json(msg='%s is not a valid interface' % (interface))
        return None

    def is_ipsec_enabled(self):
        """ return True if ipsec is enabled """
        if self.ipsec is None:
            return False

        for elt in self.ipsec:
            if elt.tag == 'phase1' and elt.find('disabled') is None:
                return True
        return False

    def is_openvpn_enabled(self):
        """ return True if openvpn is enabled """
        if self.openvpn is None:
            return False

        for elt in self.openvpn:
            if elt.tag == 'openvpn-server' or elt.tag == 'openvpn-client':
                return True
        return False

    @staticmethod
    def rule_match_interface(rule_elt, interface, floating):
        """ check if a rule elt match the targeted interface
            floating rules must match the floating mode instead of the interface name
        """
        interface_elt = rule_elt.find('interface')
        floating_elt = rule_elt.find('floating')
        if floating_elt is not None and floating_elt.text == 'yes':
            return floating
        elif floating:
            return False
        return interface_elt is not None and interface_elt.text == interface

    def get_interface_rules_count(self, interface, floating):
        """ get rules count in interface/floating """
        count = 0
        for rule_elt in self.rules:
            if not self.rule_match_interface(rule_elt, interface, floating):
                continue
            count += 1

        return count

    def get_rule_position(self, descr, interface, floating):
        """ get rule position in interface/floating """
        i = 0
        for rule_elt in self.rules:
            if not self.rule_match_interface(rule_elt, interface, floating):
                continue
            descr_elt = rule_elt.find('descr')
            if descr_elt is not None and descr_elt.text == descr:
                return i
            i += 1

        return None

    @staticmethod
    def new_element(tag, text='\n\t\t\t'):
        """ Create and return new XML configuration element  """
        elt = ET.Element(tag)
        # Attempt to preserve some of the formatting of pfSense's config.xml
        elt.text = text
        elt.tail = '\n\t\t'
        return elt

    def copy_dict_to_element(self, src, top_elt, sub=0):
        """ Copy/update top_elt from src """
        changed = False
        for (key, value) in src.items():
            self.debug.write('changed=%s key=%s value=%s\n' % (changed, key, value))
            this_elt = top_elt.find(key)
            if this_elt is None:
                changed = True
                if isinstance(value, dict):
                    self.debug.write('calling copy_dict_to_element()\n')
                    # Create a new element
                    new_elt = ET.Element(key)
                    new_elt.text = '\n%s' % ('\t' * (sub + 4))
                    new_elt.tail = '\n%s' % ('\t' * (sub + 3))
                    self.copy_dict_to_element(value, new_elt, sub=sub + 1)
                    top_elt.append(new_elt)
                elif isinstance(value, list):
                    for item in value:
                        new_elt = self.new_element(key)
                        new_elt.text = item
                        top_elt.append(new_elt)
                else:
                    # Create a new element
                    new_elt = ET.Element(key)
                    new_elt.text = value
                    new_elt.tail = '\n%s' % ('\t' * (sub + 3))
                    top_elt.append(new_elt)
                self.debug.write('changed=%s added key=%s value=%s tag=%s\n' % (changed, key, value, top_elt.tag))
            else:
                if isinstance(value, dict):
                    self.debug.write('calling copy_dict_to_element()\n')
                    subchanged = self.copy_dict_to_element(value, this_elt, sub=sub + 1)
                    if subchanged:
                        changed = True
                elif isinstance(value, list):
                    this_list = list(value)
                    # Remove existing items not in the new list
                    for list_elt in top_elt.findall(key):
                        if list_elt.text in this_list:
                            this_list.remove(list_elt.text)
                        else:
                            top_elt.remove(list_elt)
                            changed = True
                    # Add any remaining items in the new list
                    for item in this_list:
                        new_elt = self.new_element(key)
                        new_elt.text = item
                        top_elt.append(new_elt)
                        changed = True
                elif this_elt.text is None and value == '':
                    pass
                elif this_elt.text != value:
                    this_elt.text = value
                    changed = True
                self.debug.write('changed=%s this_elt.text=%s value=%s\n' % (changed, this_elt.text, value))
        # Sub-elements must be completely described, so remove any missing elements
        if sub:
            for child_elt in list(top_elt):
                if child_elt.tag not in src:
                    changed = True
                    self.debug.write('changed=%s removed tag=%s\n' % (changed, child_elt.tag))
                    top_elt.remove(child_elt)

        return changed

    @staticmethod
    def element_to_dict(src_elt):
        """ Create dict from XML src_elt """
        res = {}
        for elt in list(src_elt):
            if list(elt):
                res[elt.tag] = PFSenseModule.element_to_dict(elt)
            else:
                if elt.tag in res:
                    if isinstance(res[elt.tag], str):
                        res[elt.tag] = [res[elt.tag]]
                    res[elt.tag].append(elt.text)
                else:
                    res[elt.tag] = elt.text if elt.text is not None else ''
        return res

    def get_caref(self, name):
        """ get CA refid for name """
        cas = self.get_elements('ca')
        for elt in cas:
            if elt.find('descr').text == name:
                return elt.find('refid').text
        return None

    @staticmethod
    def get_username():
        """ get username logged """
        username = pwd.getpwuid(os.getuid()).pw_name
        if os.environ.get('SUDO_USER'):
            username = os.environ.get('SUDO_USER')
        # sudo masks this
        sshclient = os.environ.get('SSH_CLIENT')
        if sshclient:
            username = username + '@' + sshclient
        return username

    def find_alias(self, name, aliastype=None):
        """ return alias named name, having type aliastype if specified """
        for alias in self.aliases:
            if alias.find('name').text == name and (aliastype is None or alias.find('type').text == aliastype):
                return alias
        return None

    def is_ip_or_alias(self, address):
        """ return True if address is an ip or an alias """
        # Is it an alias?
        if (self.find_alias(address, 'host') is not None
                or self.find_alias(address, 'network') is not None
                or self.find_alias(address, 'urltable') is not None
                or self.find_alias(address, 'urltable_ports') is not None):
            return True

        # Is it an IP address?
        try:
            ip_address(u'{0}'.format(address))
            return True
        except ValueError:
            pass

        # Is it an IP network?
        try:
            ip_network(u'{0}'.format(address))
            return True
        except ValueError:
            pass

        # None of the above
        return False

    def is_port_or_alias(self, port):
        """ return True if port is a valid port number or an alias """
        if self.find_alias(port, 'port') is not None:
            return True
        try:
            if int(port) > 0 and int(port) < 65536:
                return True
        except ValueError:
            pass
        return False

    def find_queue(self, name, interface=None, enabled=False):
        """ return QOS queue if found """

        # iterate each interface
        for shaper_elt in self.shapers:
            if interface is not None:
                interface_elt = shaper_elt.find('interface')
                if interface_elt is None or interface_elt.text != interface:
                    continue

            if enabled:
                enabled_elt = shaper_elt.find('enabled')
                if enabled_elt is None or enabled_elt.text != 'on':
                    continue

            # iterate each queue
            for queue_elt in shaper_elt.findall('queue'):
                name_elt = queue_elt.find('name')
                if name_elt is None or name_elt.text != name:
                    continue

                if enabled:
                    enabled_elt = queue_elt.find('enabled')
                    if enabled_elt is None or enabled_elt.text != 'on':
                        continue

                # found it
                return queue_elt

        return None

    def find_limiter(self, name, enabled=False):
        """ return QOS limiter if found """

        # iterate each queue
        for queue_elt in self.dnshapers:
            if enabled:
                enabled_elt = queue_elt.find('enabled')
                if enabled_elt is None or enabled_elt.text != 'on':
                    continue

            name_elt = queue_elt.find('name')
            if name_elt is None or name_elt.text != name:
                continue

            return queue_elt

        return None

    def find_vlan(self, interface, tag):
        """ return vlan elt if found """
        for vlan in self.vlans:
            if vlan.find('if').text == interface and vlan.find('tag').text == tag:
                return vlan

        return None

    @staticmethod
    def uniqid(prefix=''):
        """ return an identifier based on time """
        return prefix + hex(int(time.time()))[2:10] + hex(int(time.time() * 1000000) % 0x100000)[2:7]

    def phpshell(self, command):
        """ Run a command in the php developer shell """
        command = "global $debug;\n$debug = 1;\n" + command + "\nexec\nexit"
        # Dummy argument suppresses displaying help message
        return self.module.run_command('/usr/local/sbin/pfSsh.php dummy', data=command)

    def php(self, command):
        """ Run a command in php and return the output """
        cmd = '<?php\n'
        cmd += command
        cmd += '\n?>\n'
        (dummy, stdout, stderr) = self.module.run_command('/usr/local/bin/php', data=cmd)
        # TODO: check stderr for errors
        return json.loads(stdout)

    def write_config(self, descr='Updated by ansible pfsense module'):
        """ Generate config file """
        revision = self.get_element('revision')
        revision.find('time').text = '%d' % time.time()
        revdescr = revision.find('description')
        if revdescr is None:
            revdescr = ET.Element('description')
            revision.append(revdescr)
        revdescr.text = descr
        username = self.get_username()
        revision.find('username').text = username
        (tmp_handle, tmp_name) = mkstemp()
        os.close(tmp_handle)
        # TODO: when pfsense will adopt python3
        # detect python version and use 3.4 short_empty_elements parameter to try to preserve format
        self.tree.write(tmp_name, xml_declaration=True, method='xml')
        shutil.move(tmp_name, self.config)
        os.chmod(self.config, 0o644)
        try:
            os.remove('/tmp/config.cache')
        except OSError as exception:
            if exception.errno == 2:
                # suppress "No such file or directory error
                pass
            else:
                raise


class PFSenseModuleBase(object):
    """ class providing base services for pfSense modules """

    @staticmethod
    def fvalue_idem(value):
        """ dummy value formatting function """
        return value

    def format_cli_field(self, after, field, log_none=False, add_comma=True, fvalue=None, default=None, fname=None):
        """ format field for pseudo-CLI command """
        if fvalue is None:
            fvalue = self.fvalue_idem

        if fname is None:
            fname = field

        res = ''
        if field in after:
            if log_none and after[field] is None:
                res = "{0}=none".format(fname)
            if after[field] is not None:
                if default is None or after[field] != default:
                    if isinstance(after[field], str):
                        res = "{0}='{1}'".format(fname, fvalue(after[field].replace("'", "\\'")))
                    else:
                        res = "{0}={1}".format(fname, fvalue(after[field]))
        elif log_none:
            res = "{0}=none".format(fname)

        if add_comma and res:
            return ', ' + res
        return res

    def format_updated_cli_field(self, after, before, field, log_none=True, add_comma=True, fvalue=None, default=None, fname=None):
        """ format field for pseudo-CLI update command """
        if field in after and field in before:
            if after[field] != before[field]:
                return self.format_cli_field(after, field, log_none=log_none, add_comma=add_comma, fvalue=fvalue, default=default, fname=fname)
        elif field in after and field not in before or field not in after and field in before:
            return self.format_cli_field(after, field, log_none=log_none, add_comma=add_comma, fvalue=fvalue, default=default, fname=fname)
        return ''
