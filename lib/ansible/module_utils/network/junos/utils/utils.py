#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils
from ansible.module_utils._text import to_text

try:
    from ncclient.xml_ import to_ele, to_xml, new_ele, sub_ele
    HAS_NCCLIENT = True
except (ImportError, AttributeError):
    HAS_NCCLIENT = False


def build_root_xml_node(tag):
    return new_ele(tag)


def build_child_xml_node(parent, tag, text=None, attrib=None):
    element = sub_ele(parent, tag)
    if text:
        element.text = to_text(text)
    if attrib:
        element.attrib.update(attrib)
    return element


def build_subtree(parent, path):
    element = parent
    for field in path.split('/'):
        sub_element = build_child_xml_node(element, field)
        element = sub_element
    return element


def _handle_field_replace(root, field, have, want, tag=None):
    tag = field if not tag else tag
    want_value = want.get(field) if want else None
    have_value = have.get(field) if have else None
    if have_value:
        if want_value:
            if want_value != have_value:
                build_child_xml_node(root, tag, want_value)
        else:
            build_child_xml_node(root, tag, None, {'delete': 'delete'})
    elif want_value:
        build_child_xml_node(root, tag, want_value)
