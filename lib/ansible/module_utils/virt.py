# Copyright: (c) 2019, Chris Redit, github.com/chrisred
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.six import string_types
from collections import defaultdict
import traceback

LXML_IMPORT_ERROR = None
try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    LXML_IMPORT_ERROR = traceback.format_exc()
    HAS_LXML = False


class Config():
    '''Represents the XML configuration of a libvirt resource. This should provide a simple interface
    for accessing the configuration.'''
    def __init__(self, module, xml):
        if not HAS_LXML:
            module.fail_json(msg=missing_required_lib('lxml'), exception=LXML_IMPORT_ERROR)

        try:
            self._etree = etree.fromstring(xml)
        except etree.XMLSyntaxError as e:
            module.fail_json(
                msg='Error parsing libvirt XML config. ' + str(e),
                exception=traceback.format_exc()
            )

    def __str__(self):
        return etree.tostring(self._etree, encoding='utf-8')


def etree_to_dict(element):
    '''Convert an ElementTree object into a dictonary. The tag/attribute/text content of the XML
    document is converted (in most cases) into key/value pairs in the resulting dictonary. For
    duplicate tag names a list of dictionaries is generated.'''
    parent = {element.tag: {} if element.attrib else ''}
    children = list(element)
    if children:
        # create default dict using a list to deal with duplicate tags
        dd = defaultdict(list)
        for child in map(etree_to_dict, children):
            for k, v in child.items():
                # Append each child item to the list in the defaultdict, duplicate keys/tags get
                # grouped together in the same list.
                dd[k].append(v)
        # Add the child dicts to the parent, the one item lists have the only value added,
        # otherwise the whole list is added representing multiple elements with the same tag.
        parent = {element.tag: dict([(k, v[0] if len(v) == 1 else v) for k, v in dd.items()])}
    if element.attrib:
        parent[element.tag].update(('@' + k, v) for k, v in element.attrib.items())
    if element.text:
        text = element.text.strip()
        if children or element.attrib:
            if text:
                parent[element.tag]['#' + element.tag] = text
        else:
            # add only a text string if this is all the element contains
            parent[element.tag] = text
    return parent


def flatten_dict(d, parent_key='', seperator='_'):
    '''Convert nested dictonaries into a single "flat" dictonary by generating new concatenated keys
    that combine the nested dictonaries into one. This will also handle list objects contained in the
    dictonaries.'''
    items = list()
    for k, v in d.items():
        # modify some of the key names to make the flattened key cleaner
        if k[:1] == '#':
            new_key = parent_key if parent_key else k[1:]
        elif k[:1] == '@':
            new_key = parent_key + seperator + k[1:] if parent_key else k[1:]
        else:
            new_key = parent_key + seperator + k if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, seperator=seperator).items())
        elif isinstance(v, list):
            # Process a list of dicts, this occurs when there are elements with duplicate names
            # in the source XML docuemnt the dictionary was generated from. If the duplicates are
            # elements containing only a text node this can also be a list of strings.
            items.append((new_key, [flatten_dict(i) if isinstance(i, dict) else i for i in v]))
        else:
            items.append((new_key, v))
    return dict(items)


def get_facts(config, wanted):
    '''Access the properties of a Config object selected by the "wanted" parameter and process them to
    be returned as facts. ElementTree objects are converted to dictonaries and flattened so that clean
    JSON output can be generated.'''
    facts = dict()
    for key in wanted:
        config_item = getattr(config, key)
        if isinstance(config_item, string_types) or isinstance(config_item, int):
            facts[key] = config_item
        elif isinstance(config_item, list):
            new_items = list()
            for item in config_item:
                if isinstance(item, etree._Element):
                    # The first key in the output from etree_to_dict is the tag name for the current
                    # element. This is not required as we use the oft identical property name from the
                    # Config object, so select only the value here.
                    item_value = list(etree_to_dict(item).values())[0]
                    # An empty element selected by a property of the Config object won't return a dict
                    # as it's value. Only run flatten_dict if we have a dict.
                    if isinstance(item_value, dict):
                        new_items.append(flatten_dict(item_value))
                    else:
                        new_items.append(item_value)
                else:
                    raise TypeError('Unexpected type when reading config property list.')
            facts[key] = new_items
        elif isinstance(config_item, etree._Element):
            key_value = list(etree_to_dict(config_item).values())[0]
            facts[key] = flatten_dict(key_value) if isinstance(key_value, dict) else key_value
        else:
            facts[key] = None
    return facts
