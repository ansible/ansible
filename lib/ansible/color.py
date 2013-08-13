# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import os
import sys
import constants
import yaml

ANSIBLE_COLOR=True
if constants.ANSIBLE_NOCOLOR:
    ANSIBLE_COLOR=False
elif not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
    ANSIBLE_COLOR=False
else:
    try:
        import curses
        curses.setupterm()
        if curses.tigetnum('colors') < 0:
            ANSIBLE_COLOR=False
    except ImportError:
        # curses library was not found
        pass
    except curses.error:
        # curses returns an error (e.g. could not find terminal)
        ANSIBLE_COLOR=False

if os.getenv("ANSIBLE_FORCE_COLOR") is not None:
        ANSIBLE_COLOR=True

# --- begin "pretty"
#
# pretty - A miniature library that provides a Python print and stdout
# wrapper that makes colored terminal text easier to use (eg. without
# having to mess around with ANSI escape sequences). This code is public
# domain - there is no license except that you must leave this header.
#
# Copyright (C) 2008 Brian Nez <thedude at bri1 dot com>
#
# http://nezzen.net/2008/06/23/colored-text-in-python-using-ansi-escape-sequences/

FG_CODES = {
    'black'     : '0;30', 'bright gray'   : '0;37',
    'blue'      : '0;34', 'white'         : '1;37',
    'green'     : '0;32', 'bright blue'   : '1;34',
    'cyan'      : '0;36', 'bright green'  : '1;32',
    'red'       : '0;31', 'bright cyan'   : '1;36',
    'purple'    : '0;35', 'bright red'    : '1;31',
    'yellow'    : '0;33', 'bright purple' : '1;35',
    'dark gray' : '1;30', 'bright yellow' : '1;33',
    'normal'    : '0'
}
BG_CODES = {
    'black'  : '0m',
    'gray'   : '40m',
    'red'    : '41m',
    'green'  : '42m',
    'yellow' : '43m',
    'blue'   : '44m',
    'purple' : '45m',
    'cyan'   : '46m',
    'white'  : '47m'
}
CLEAR_CODE="\033[0m"

def color_code(fg, bg=None):
    code = "\033[" + FG_CODES[fg] + 'm'
    if bg:
        code += "\033["+BG_CODES[bg]
    return code
def stringc(text, color, background_color=None):
    """String in color."""

    if ANSIBLE_COLOR:
        return color_code(color,background_color) + text + color_code("normal")
    else:
        return text


# --- end "pretty"



# ---  begin "yamlc"
# yamlc - The function is based on a heavily minimized adaptation from the
# example at http://pyyaml.org/browser/pyyaml/trunk/examples/yaml-hl/yaml_hl.py


YAML_TOKENS = {
    "BlockEnd"          : None,
    "FlowSequenceStart" : None,
    "FlowMappingStart"  : None,
    "FlowSequenceEnd"   : None,
    "FlowMappingEnd"    : None,
    "BlockMappingStart" : color_code("red"),
    "Key"               : color_code("white"),
    "Value"             : color_code("yellow"),
    "BlockEntry"        : color_code("red"),
    "Alias"             : CLEAR_CODE,
    "Anchor"            : CLEAR_CODE,
    "Scalar"            : color_code("green"),
    "Tag"               : CLEAR_CODE,
}
YAML_SUBSTITUTIONS = {}
for code in YAML_TOKENS:
    cls = getattr(yaml, code+"Token")
    YAML_SUBSTITUTIONS[cls] = YAML_TOKENS[code]

def yamlc(data):
    """ return a syntax highlighted version of a yaml document """
    if ANSIBLE_COLOR:
        tokens = yaml.scan(data)
        markers = []
        for token in tokens:
            cls = token.__class__
            if cls in YAML_SUBSTITUTIONS:
                code = YAML_SUBSTITUTIONS[cls]
                markers.append([token.start_mark.index, code])
                markers.append([token.end_mark.index,CLEAR_CODE if code else None])
            else:
                markers.append([token.start_mark.index,None])
                markers.append([token.end_mark.index,None])
        markers.sort()
        markers = markers[::-1]
        pos = len(data)
        chunks = []
        for idx, sub in markers:
            if idx < pos:
                chunk = data[idx:pos]
                chunks.append(chunk)
            pos = idx
            if sub:
                chunks.append(sub)
        chunks.reverse()

        return u''.join(chunks).encode('utf-8')
    else:
        return data

# ---  end "yamlc"
