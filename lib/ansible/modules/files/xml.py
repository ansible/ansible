#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# xml - Manage bits and pieces of XML files
#
# Copyright 2014, Red Hat, Inc.
# Tim Bielawa <tbielawa@redhat.com>
# Magnus Hedemark <mhedemar@redhat.com>
#
# This software may be freely redistributed under the terms of the GNU
# general public license version 2.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = '''
---
module: xml
short_description: Manage bits and pieces of XML files or strings
description:
  - A CRUD-like interface to managing bits of XML files. You might also be interested in a brief tutorial, U(http://www.w3schools.com/xpath/). Note that module this does not handle complicated xpath expressions. So limit xpath selectors to simple expressions.
version_added: "1.0"
options:
  path:
    description:
      - Path to the file to operate on. File must exist ahead of time.
    required: true unless xmlstring is given
    default: null
    choices: []
    aliases: ['dest', 'file']
  xmlstring:
    description:
      - A string containing XML on which to operate.
    required: true unless file is given
    default: null
    choices: []
  xpath:
    description:
      - A valid XPath expression describing the item(s) you want to manipulate. Operates on the document root, C(/), by default.
    required: false
    default: /
    choices: []
  namespaces:
    description:
      - The namespace prefix:uri mapping for the XPath expression. Needs to be a *map*, not a list of items.
    required: false
    default: null
    choices: []
  ensure:
    description:
      - Set or remove an xpath selection (node(s), attribute(s))
    required: false
    default: present
    choices:
      - "absent"
      - "present"
  value:
    description:
      - Desired state of the selected attribute. Either a string, or to unset a value, the Python C(None) keyword (YAML Equivalent, C(null)).
    required: false
    default: Elements default to no value (but present). Attributes default to an empty string.
    choices: []
  add_children:
    description:
      - 'Add additional child-element(s) to a selected element. Child elements must be given in a list and each item may be either a string (ex: C(children=ansible) to add an empty C(<ansible/>) child element), or a hash where the key is an element name and the value is the element value.'
    required: false
    default: null
    choices: []
  set_children:
    description:
      - 'Set the the child-element(s) of a selected element. Removes any existing children. Child elements must be specified as in C(add_children).'
    required: false
    default: null
    choices: []
  count:
    description:
      - "Search for a given C(xpath) and provide the count of any matches"
    required: false
    default: null
    choices: []
  print_match:
    description:
      - "Search for a given C(xpath) and print out any matches"
    required: false
    default: null
    choices: []
  pretty_print:
    description:
      - "Pretty print output XML"
    required: false
    default: false
    choices: []
  content:
    description:
      - "Search for a given C(xpath) and get content"
    required: false
    default: false
    choices:
      - "attribute"
      - "text"
  input_type:
    description:
      - "Type of input for add_children and set_children"
    required: false
    default: "yaml"
    choices:
      - "yaml"
      - "xml"
requirements:
    - The remote end must have the Python C(lxml) library installed
author: Tim Bielawa, Magnus Hedemark
'''


from io import BytesIO
from lxml import etree
try:
    import json
except:
    import simplejson as json
import lxml
import sys, os, re, traceback

def print_match(module, tree, xpath, namespaces):
    match = tree.xpath(xpath, namespaces=namespaces)
    match_xpaths = []
    for m in match:
        match_xpaths.append(tree.getpath(m))
    match_str = json.dumps(match_xpaths)
    msg = "selector '%s' match: %s" % (xpath, match_str)
    finish(module, tree, xpath, namespaces, changed=False, msg=msg)

def count(module, tree, xpath, namespaces):
    """ Return the count of nodes matching the xpath """
    hits = tree.xpath("count(/%s)" % xpath, namespaces=namespaces)
    finish(module, tree, xpath, namespaces, changed=False, msg=int(hits), hitcount=int(hits))

def is_node(tree, xpath, namespaces):
    """ Test if a given xpath matches anything and if that match is a node.

    For now we just assume you're only searching for one specific thing."""
    if xpath_matches(tree, xpath, namespaces):
        # OK, it found something
        match = tree.xpath(xpath, namespaces=namespaces)
        if type(match[0]) == lxml.etree._Element:
            return True

    return False

def is_attribute(tree, xpath, namespaces):
    """ Test if a given xpath matches and that match is an attribute

An xpath attribute search will only match one item"""
    if xpath_matches(tree, xpath, namespaces):
        match = tree.xpath(xpath, namespaces=namespaces)
        if type(match[0]) == lxml.etree._ElementStringResult:
            return True
    return False

def xpath_matches(tree, xpath, namespaces):
    """ Test if a node exists """
    if tree.xpath(xpath, namespaces=namespaces):
        return True
    else:
        return False

def delete_xpath_target(module, tree, xpath, namespaces):
    """ Delete an attribute or element from a tree """
    try:
        for result in tree.xpath(xpath, namespaces=namespaces):
            if not module.check_mode:
                # Get the xpath for this result
                if is_attribute(tree, xpath, namespaces):
                    # Delete an attribute
                    parent = result.getparent()
                    # Pop this attribute match out of the parent
                    # node's 'attrib' dict by using this match's
                    # 'attrname' attribute for the key
                    parent.attrib.pop(result.attrname)
                elif is_node(tree, xpath, namespaces):
                    # Delete an element
                    result.getparent().remove(result)
    except Exception, e:
        abort(module, "Couldn't delete xpath target: %s (%s)" % (xpath, str(e)))
    else:
        finish(module, tree, xpath, namespaces, changed=True)

def set_target_children_inner(module, tree, xpath, namespaces, children, type):
    matches = tree.xpath(xpath, namespaces=namespaces)

    # Create a list of our new children
    children = children_to_nodes(module, children, type)
    children_as_string = [lxml.etree.tostring(c) for c in children]

    changed = False

    def replace_children_of(match):
        if not module.check_mode:
            for element in match.getchildren():
                match.remove(element)
            match.extend(children)

    # xpaths always return matches as a list, so....
    for match in matches:
        # Check if elements differ
        if len(match.getchildren()) == len(children):
            for idx, element in enumerate(match.getchildren()):
                if lxml.etree.tostring(element) != children_as_string[idx]:
                    replace_children_of(match)
                    changed = True
                    break
        else:
            replace_children_of(match)
            changed = True

    return changed

def set_target_children(module, tree, xpath, namespaces, children, type):
    changed = set_target_children_inner(module, tree, xpath, namespaces, children, type)
    # Write it out
    finish(module, tree, xpath, namespaces, changed=changed)

def add_target_children(module, tree, xpath, namespaces, children, type):
    if is_node(tree, xpath, namespaces):
        new_kids = children_to_nodes(module, children, type)
        for node in tree.xpath(xpath, namespaces=namespaces):
            if not module.check_mode: node.extend(new_kids)
        finish(module, tree, xpath, namespaces, changed=True)
    else:
        finish(module, tree, xpath, namespaces)

_ident = "[a-zA-Z-][a-zA-Z0-9_\-\.]*"
_nsIdent = _ident +"|"+_ident+":"+_ident
_xpstr = "('(?:.*)'|\"(?:.*)\")" # Note: we can't reasonably support the 'if you need to put both ' and " in a string, concatenate
                               # strings wrapped by the other delimiter' XPath trick, especially as simple XPath.

_re_splitSimpleLast = re.compile("^(.*)/("+_nsIdent+")$")
_re_splitSimpleLastEqValue = re.compile("^(.*)/("+_nsIdent+")/text\\(\\)="+_xpstr+"$")
_re_splitSimpleAttrLast = re.compile("^(.*)/(@(?:"+_nsIdent+"))$")
_re_splitSimpleAttrLastEqValue = re.compile("^(.*)/(@(?:"+_nsIdent+"))="+_xpstr+"$")

_re_splitSubLast = re.compile("^(.*)/("+_nsIdent+")\\[(.*)\\]$")

_re_splitOnlyEqValue = re.compile("^(.*)/text\\(\\)="+_xpstr+"$")

def _extract_xpstr(g):
    return g[1:-1]

def split_xpath_last(xpath):
    """split an XPath of the form /foo/bar/baz into /foo/bar and baz"""
    xpath = xpath.strip()
    m = _re_splitSimpleLast.match(xpath)
    if m:
        return (m.group(1), [(m.group(2), None)]) # requesting an element to exist
    m = _re_splitSimpleLastEqValue.match(xpath)
    if m:
        return (m.group(1), [(m.group(2), _extract_xpstr(m.group(3)))]) # requesting an element to exist with an inner text

    m = _re_splitSimpleAttrLast.match(xpath)
    if m:
        return (m.group(1), [(m.group(2), None)]) # requesting an attribute to exist
    m = _re_splitSimpleAttrLastEqValue.match(xpath)
    if m:
        return (m.group(1), [(m.group(2), _extract_xpstr(m.group(3)))]) # requesting an attribute to exist with a value

    m = _re_splitSubLast.match(xpath)
    if m:
        content = map(lambda x: x.strip(), m.group(3).split(" and "))

        return (m.group(1),  [('/'+m.group(2), content )] )

    m = _re_splitOnlyEqValue.match(xpath)
    if m:
        return (m.group(1), [("", _extract_xpstr(m.group(2)))]) # requesting a change of inner text
    return (xpath, [])

def nsnameToClark(name, namespaces):
    if ":" in name:
        (nsname, rawname) = name.split(":")
        return "{{{0}}}{1}".format(namespaces[nsname], rawname)
    else:
        # no namespace name here
        return name

def check_or_make_target(module, tree, xpath, namespaces):
    (inner_xpath, changes) = split_xpath_last(xpath)
    if (inner_xpath == xpath) or (changes == None):
        abort(module, "Can't process Xpath " + xpath + " in order to spawn nodes! tree is " + etree.tostring(tree, pretty_print=True))
        return False

    changed = False

    if not is_node(tree, inner_xpath, namespaces):
        changed = check_or_make_target(module, tree, inner_xpath, namespaces)

    if is_node(tree, inner_xpath, namespaces) and changes: # we test again after calling check_or_make_target
        for (eoa, eoa_value) in changes:
            if eoa and eoa[0] != '@' and eoa[0] != '/':
                # implicitly creating an element
                new_kids = children_to_nodes(module, [nsnameToClark(eoa, namespaces)], "yaml")
                if eoa_value:
                    for nk in new_kids:
                        nk.text = eoa_value

                for node in tree.xpath(inner_xpath, namespaces=namespaces):
                    if not module.check_mode: node.extend(new_kids)
                    changed = True
                #abort(module, "now tree=" + etree.tostring(tree, pretty_print=True))
            elif eoa and eoa[0] == '/':
                element = eoa[1:]
                new_kids = children_to_nodes(module, [nsnameToClark(element, namespaces)], "yaml")
                for node in tree.xpath(inner_xpath, namespaces=namespaces):
                    if not module.check_mode: node.extend(new_kids)
                    for nk in new_kids:
                        for subexpr in eoa_value:
                            #abort(module, "element="+element+" subexpr="+str(subexpr)+" node="+etree.tostring(node, pretty_print=True)+
                            #    " now tree=" + etree.tostring(tree, pretty_print=True))
                            check_or_make_target(module, nk, "./"+subexpr, namespaces)
                    changed = True

                #abort(module, "now tree=" + etree.tostring(tree, pretty_print=True))
            elif eoa == "":
                for node in tree.xpath(inner_xpath, namespaces=namespaces):
                    if (node.text != eoa_value):
                        node.text = eoa_value
                        changed = True

            elif eoa and eoa[0] == '@':
                attribute = nsnameToClark(eoa[1:], namespaces)

                for element in tree.xpath(inner_xpath, namespaces=namespaces):
                    changing = (not element.attrib.has_key(attribute)) or (element.attrib.get(attribute) != eoa_value)

                    if not module.check_mode and changing:
                        changed = changed or changing
                        if eoa_value is None:
                            value = ""
                        else:
                            value = eoa_value
                        element.attrib[attribute] = value

                    #abort(module, "arf "+xpath+"  changing="+str(changing)+"  as curval="+str(element.get(attribute))+" changed tree=" + etree.tostring(tree, pretty_print=True))


            else:
                abort(module, "unknown tree transformation=" + etree.tostring(tree, pretty_print=True))

    return changed


def ensure_xpath_exists(module, tree, xpath, namespaces):
    changed = False

    if not is_node(tree, xpath, namespaces):
        changed = check_or_make_target(module, tree, xpath, namespaces)

    finish(module, tree, xpath, namespaces, changed)

def set_target_inner(module, tree, xpath, namespaces, attribute, value):
    changed = False

    try:
        if not is_node(tree, xpath, namespaces):
            changed = check_or_make_target(module, tree, xpath, namespaces)
    except Exception, e:
        abort(module, "Xpath " + xpath + " causes a failure: "+str(e)+ "\n" + traceback.format_exc(e)+"\n  -- tree is " + etree.tostring(tree, pretty_print=True))

    if not is_node(tree, xpath, namespaces):
        abort(module, "Xpath " + xpath + " does not reference a node! tree is " + etree.tostring(tree, pretty_print=True))

    for element in tree.xpath(xpath, namespaces=namespaces):
        if not attribute:
            changed = changed or (element.text != value)
            if not module.check_mode and (element.text != value): element.text = value
        else:
            changed = changed or (element.get(attribute) != value)
            if ":" in attribute:
                attr_ns, attr_name = attribute.split(":")
                attribute = "{{{0}}}{1}".format(namespaces[attr_ns], attr_name)
            if not module.check_mode and (element.get(attribute) != value): element.set(attribute, value)

    return changed

def set_target(module, tree, xpath, namespaces, attribute, value):
    changed = set_target_inner(module, tree, xpath, namespaces, attribute, value)
    finish(module, tree, xpath, namespaces, changed)

def pretty(module, tree):
    xml_string = etree.tostring(tree, xml_declaration=True, encoding='UTF-8', pretty_print=module.params['pretty_print'])
    changed = False

    if module.params['path']:
        xml_file = os.path.expanduser(module.params['path'])

        xml_content = open(xml_file)
        try:
            if xml_string != xml_content.read():
                changed = True
                tree.write(xml_file, xml_declaration=True, encoding='UTF-8', pretty_print=module.params['pretty_print'])
        finally:
            xml_content.close()

        module.exit_json(changed=changed)

    if module.params['xmlstring']:
        if xml_string != module.params['xmlstring']:
            changed = True

        module.exit_json(changed=changed, xmlstring=xml_string)

def get_element_text(module, tree, xpath, namespaces):
    if not is_node(tree, xpath, namespaces):
        abort(module, "Xpath " + xpath + " does not reference a node!")

    elements = []
    for element in tree.xpath(xpath, namespaces=namespaces):
        elements.append({element.tag: element.text})

    finish(module, tree, xpath, namespaces, changed=False, msg=len(elements), hitcount=len(elements), matches=elements)

def get_element_attr(module, tree, xpath, namespaces):
    if not is_node(tree, xpath, namespaces):
        abort(module, "Xpath " + xpath + " does not reference a node!")

    elements = []
    for element in tree.xpath(xpath, namespaces=namespaces):
        child = {}
        for key in element.keys():
            value = element.get(key)
            child.update({key: value})
        elements.append({element.tag: child})

    finish(module, tree, xpath, namespaces, changed=False, msg=len(elements), hitcount=len(elements), matches=elements)

def child_to_element(module, child, in_type):
    if in_type == 'xml':
        infile = BytesIO(child.encode('utf-8'))

        try:
            parser = etree.XMLParser()
            node = etree.parse(infile, parser)
            return node.getroot()
        except etree.XMLSyntaxError, e:
            module.fail_json(
                msg="Error while parsing child element: %s" %
                str(e))
    elif in_type == 'yaml':
        ch_type = type(child)
        if ch_type == str or ch_type == unicode:
            return etree.Element(child)
        elif ch_type == dict:
            if len(child) > 1:
                abort(module, "Can only create children from hashes with one key")

            (key, value) = child.items()[0]
            if type(value) == dict:
                children = value.pop('_', None)

                node = etree.Element(key, value)

                if children is not None:
                    if type(children) != list:
                        abort(module, "Invalid children type: %s, must be list." % str(type(children)))

                    subnodes = children_to_nodes(module, children)
                    node.extend(subnodes)
            else:
                node = etree.Element(key)
                node.text = value
            return node
        else:
            abort(module, "Invalid child type: %s. Children must be either strings or hashes." % str(ch_type))
    else:
        abort(module, "Invalid child input type: %s. Type must be either xml or yaml." % in_type)

def children_to_nodes(module=None, children=[], type='yaml'):
    """turn a str/hash/list of str&hash into a list of elements"""
    return [child_to_element(module, child, type) for child in children]

def abort(m, msg):
    m.fail_json(msg=msg)

def finish(m, tree, xpath, namespaces, changed=False, msg="", hitcount=0, matches=[]):
    if not changed:
        m.exit_json(changed=changed,actions={"xpath": xpath, "namespaces": namespaces, "ensure": m.params['ensure']}, msg=msg, count=hitcount, matches=matches)

    if m.params['path']:
        xml_file = os.path.expanduser(m.params['path'])
        tree.write(xml_file, xml_declaration=True, encoding='UTF-8', pretty_print=m.params['pretty_print'])
        m.exit_json(changed=changed,actions={"xpath": xpath, "namespaces": namespaces, "ensure": m.params['ensure']}, msg=msg, count=hitcount, matches=matches)

    if m.params['xmlstring']:
        xml_string = etree.tostring(tree, xml_declaration=True, encoding='UTF-8', pretty_print=m.params['pretty_print'])
        m.exit_json(changed=changed,actions={"xpath": xpath, "namespaces": namespaces, "ensure": m.params['ensure']}, msg=msg, count=hitcount, matches=matches, xmlstring=xml_string)

def decode(value):
    # Convert value to unicode to use with lxml
    if not value or isinstance(value, unicode):
        return value
    elif isinstance(value, str):
        return value.decode('utf-8')
    elif isinstance(value, list):
        return [decode(v) for v in value]
    elif isinstance(value, dict):
        return dict((key, decode(val)) for key, val in value.iteritems())
    else:
        raise AttributeError('Undecodable value: type=%s, value=%s' %
                             (type(value), value))

def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=False, aliases=['dest', 'file']),
            xmlstring=dict(required=False, default=''),
            xpath=dict(required=False, default='/'),
            namespaces=dict(required=False, default={}, type='dict'),
            ensure=dict(required=False, default='present', choices=['absent', 'present']),
            value=dict(required=False, default=None),
            attribute=dict(required=False, default=None),
            add_children=dict(required=False, default=None, type='list'),
            set_children=dict(required=False, default=None, type='list'),
            count=dict(required=False, default=None, type='bool'),
            print_match=dict(required=False, default=None, type='bool'),
            pretty_print=dict(required=False, default=False, type='bool'),
            content=dict(required=False, default=None, choices=['attribute', 'text']),
            input_type=dict(required=False, default='yaml', choices=['yaml', 'xml'])
        ),
        supports_check_mode=True,
        mutually_exclusive = [
            ['value','set_children'],
            ['value','add_children'],
            ['set_children', 'add_children'],
            ['path', 'xmlstring'],
            ['content','set_children'],
            ['content','add_children'],
            ['content','value'],
        ]
    )

    xml_file = os.path.expanduser(module.params['path'])
    xml_string = module.params['xmlstring']
    xpath = module.params['xpath']
    namespaces = module.params['namespaces']
    ensure = module.params['ensure']
    value = decode(module.params['value'])
    attribute = module.params['attribute']
    set_children = decode(module.params['set_children'])
    add_children = decode(module.params['add_children'])
    pretty_print = module.params['pretty_print']
    content = module.params['content']
    input_type = module.params['input_type']

    ##################################################################
    # Check if the file exists
    # No: abort
    if xml_string:
        infile = BytesIO(xml_string.encode('utf-8'))
    elif os.path.isfile(xml_file):
        infile = file(xml_file, 'r')
    else:
        module.fail_json(
            msg="The target XML source does not exist: %s" %
            xml_file)

    # Try to parse in the target XML file
    try:
        parser = etree.XMLParser(remove_blank_text=pretty_print)
        x = etree.parse(infile, parser)
    except etree.XMLSyntaxError, e:
        module.fail_json(
            msg="Error while parsing file: %s" %
            str(e))

    if module.params['print_match']:
        print_match(module, x, xpath, namespaces)

    if module.params['count']:
        count(module, x, xpath, namespaces)

    if content == 'attribute':
        get_element_attr(module, x, xpath, namespaces)
    elif module.params['content'] == 'text':
        get_element_text(module, x, xpath, namespaces)

    # module.fail_json(msg="OK. Well, etree parsed the xml file...")

    # module.exit_json(what_did={"foo": "bar"}, changed=True)

    ##################################################################
    # File exists:
    # Ensure:
    if ensure == 'absent':
        # - absent: delete xpath target
        delete_xpath_target(module, x, xpath, namespaces)
        # Exit
    # - present: carry on

    ##################################################################
    # children && value both set?: should have already aborted by now
    ##################################################################

    ##################################################################
    # add_children && set_children both set?: should have already aborted by now
    ##################################################################

    ##################################################################
    # set_children set?
    # Yes: Set children of target
    if module.params['set_children']:
        set_target_children(module, x, xpath, namespaces, set_children, input_type)

    ##################################################################
    # add_children set?
    # Yes: Add children to target
    if module.params['add_children']:
        add_target_children(module, x, xpath, namespaces, add_children, input_type)

    # No?: Carry on

    ##################################################################
    # Is the xpath target an attribute selector?
    # Yes: Set the attribute, exit
    if module.params['value'] is not None:
        set_target(module, x, xpath, namespaces, attribute, value)

    ##################################################################
    # Format the xml only?
    if module.params['pretty_print']:
        pretty(module, x)

    ensure_xpath_exists(module, x, xpath, namespaces)
    #abort(module, "don't know what to do")

######################################################################
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
