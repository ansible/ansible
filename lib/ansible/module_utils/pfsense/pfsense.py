# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import ipaddress
import shutil
import os
import pwd
import time
import xml.etree.ElementTree as ET


class PFSenseModule(object):
    """ class managing pfsense base configuration """

    def __init__(self, module, config='/cf/conf/config.xml'):
        self.module = module
        self.config = config
        self.tree = ET.parse(config)
        self.root = self.tree.getroot()
        self.aliases = self.get_element('aliases')
        self.interfaces = self.get_element('interfaces')
        self.debug = open('/tmp/pfsense.debug', 'w')

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
            interface_name = interface.find('descr').text
            if interface_name.strip() == name:
                return interface.tag
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

    @staticmethod
    def new_element(tag):
        """ Create and return new XML configuration element  """
        elt = ET.Element(tag)
        # Attempt to preserve some of the formatting of pfSense's config.xml
        elt.text = '\n\t\t\t'
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
                    this_list = value
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
    def element_to_dict(src):
        """ Create XML elt from src """
        res = {}
        for elt in list(src):
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

    def find_alias(self, name, aliastype):
        """ return alias named name, having type aliastype """
        for alias in self.aliases:
            if alias.find('name').text == name and alias.find('type').text == aliastype:
                return alias
        return None

    def is_ip_or_alias(self, address):
        """ return True if address is an ip or an alias """
        # Is it an alias?
        if self.find_alias(address, 'host') is not None or self.find_alias(address, 'network') is not None or self.find_alias(address, 'urltable') is not None:
            return True

        # Is it an IP address?
        try:
            ipaddress.ip_address(unicode(address))
            return True
        except ValueError:
            pass

        # Is it an IP network?
        try:
            ipaddress.ip_network(unicode(address))
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

    @staticmethod
    def uniqid(prefix=''):
        """ return an identifier based on time """
        return prefix + hex(int(time.time()))[2:10] + hex(int(time.time() * 1000000) % 0x100000)[2:7]

    def phpshell(self, command):
        """ Run a command in the php developer shell """
        command = command + "\nexec\nexit"
        # Dummy argument suppresses displaying help message
        return self.module.run_command('/usr/local/sbin/pfSsh.php dummy', data=command)

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
        # Use 'html' to have explicit close tags - 3.4 has short_empty_elements
        # xml_declaration does not appear to be working
        self.tree.write('/tmp/config.xml', xml_declaration=True, method='html')
        shutil.move('/tmp/config.xml', self.config)
        try:
            os.remove('/tmp/config.cache')
        except OSError as exception:
            if exception.errno == 2:
                # suppress "No such file or directory error
                pass
            else:
                raise
