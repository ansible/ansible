# -*- coding: utf-8 -*-
# pylint: disable=no-self-argument
#
# Copyright 2006-2017 by the Pygments team, see AUTHORS at
# https://bitbucket.org/birkenfeld/pygments-main/raw/7941677dc77d4f2bf0bbd6140ade85a9454b8b80/AUTHORS
# Copyright by Norman Richards (original author of JSON lexer).
#
# Licensed under BSD license:
#
# Copyright (c) 2006-2017 by the respective authors (see AUTHORS file).
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from pygments.lexer import LexerContext, ExtendedRegexLexer, DelegatingLexer, RegexLexer, bygroups, include
from pygments.lexers import DiffLexer
from pygments import token

import re


class AnsibleOutputPrimaryLexer(RegexLexer):
    name = 'Ansible-output-primary'

    # The following definitions are borrowed from Pygment's JSON lexer.
    # It has been originally authored by Norman Richards.

    # integer part of a number
    int_part = r'-?(0|[1-9]\d*)'

    # fractional part of a number
    frac_part = r'\.\d+'

    # exponential part of a number
    exp_part = r'[eE](\+|-)?\d+'

    tokens = {
        # #########################################
        # # BEGIN: states from JSON lexer #########
        # #########################################
        'whitespace': [
            (r'\s+', token.Text),
        ],

        # represents a simple terminal value
        'simplevalue': [
            (r'(true|false|null)\b', token.Keyword.Constant),
            (('%(int_part)s(%(frac_part)s%(exp_part)s|'
              '%(exp_part)s|%(frac_part)s)') % vars(),
             token.Number.Float),
            (int_part, token.Number.Integer),
            (r'"(\\\\|\\"|[^"])*"', token.String),
        ],


        # the right hand side of an object, after the attribute name
        'objectattribute': [
            include('value'),
            (r':', token.Punctuation),
            # comma terminates the attribute but expects more
            (r',', token.Punctuation, '#pop'),
            # a closing bracket terminates the entire object, so pop twice
            (r'\}', token.Punctuation, '#pop:2'),
        ],

        # a json object - { attr, attr, ... }
        'objectvalue': [
            include('whitespace'),
            (r'"(\\\\|\\"|[^"])*"', token.Name.Tag, 'objectattribute'),
            (r'\}', token.Punctuation, '#pop'),
        ],

        # json array - [ value, value, ... }
        'arrayvalue': [
            include('whitespace'),
            include('value'),
            (r',', token.Punctuation),
            (r'\]', token.Punctuation, '#pop'),
        ],

        # a json value - either a simple value or a complex value (object or array)
        'value': [
            include('whitespace'),
            include('simplevalue'),
            (r'\{', token.Punctuation, 'objectvalue'),
            (r'\[', token.Punctuation, 'arrayvalue'),
        ],
        # #########################################
        # # END: states from JSON lexer ###########
        # #########################################

        'host-postfix': [
            (r'\n', token.Text, '#pop:3'),
            (r'( )(=>)( )(\{)',
                bygroups(token.Text, token.Punctuation, token.Text, token.Punctuation),
                'objectvalue'),
        ],

        'host-error': [
            (r'(?:(:)( )(UNREACHABLE|FAILED)(!))?',
                bygroups(token.Punctuation, token.Text, token.Keyword, token.Punctuation),
                'host-postfix'),
            (r'', token.Text, 'host-postfix'),
        ],

        'host-name': [
            (r'(\[)([^ \]]+)(?:( )(=>)( )([^\]]+))?(\])',
                bygroups(token.Punctuation, token.Name.Variable, token.Text, token.Punctuation, token.Text, token.Name.Variable, token.Punctuation),
                'host-error')
        ],

        'host-result': [
            (r'\n', token.Text, '#pop'),
            (r'( +)(ok|changed|failed|skipped|unreachable)(=)([0-9]+)',
                bygroups(token.Text, token.Keyword, token.Punctuation, token.Number.Integer)),
        ],

        'root': [
            (r'(PLAY|TASK|PLAY RECAP)(?:( )(\[)([^\]]+)(\]))?( )(\*+)(\n)',
                bygroups(token.Keyword, token.Text, token.Punctuation, token.Literal, token.Punctuation, token.Text, token.Name.Variable, token.Text)),
            (r'(fatal|ok|changed|skipping)(:)( )',
                bygroups(token.Keyword, token.Punctuation, token.Text),
                'host-name'),
            (r'(\[)(WARNING)(\]:)([^\n]+)',
                bygroups(token.Punctuation, token.Keyword, token.Punctuation, token.Text)),
            (r'([^ ]+)( +)(:)',
                bygroups(token.Name, token.Text, token.Punctuation),
                'host-result'),
            (r'(\tto retry, use: )(.*)(\n)', bygroups(token.Text, token.Literal.String, token.Text)),
            (r'.*\n', token.Other),
        ],
    }


class AnsibleOutputLexer(DelegatingLexer):
    name = 'Ansible-output'
    aliases = ['ansible-output']

    def __init__(self, **options):
        super(AnsibleOutputLexer, self).__init__(DiffLexer, AnsibleOutputPrimaryLexer, **options)


# ####################################################################################################
# # Sphinx plugin ####################################################################################
# ####################################################################################################

__version__ = "0.1.0"
__license__ = "BSD license"
__author__ = "Felix Fontein"
__author_email__ = "felix@fontein.de"


def setup(app):
    """ Initializer for Sphinx extension API.
        See http://www.sphinx-doc.org/en/stable/extdev/index.html#dev-extensions.
    """
    for lexer in [
        AnsibleOutputLexer(startinline=True)
    ]:
        app.add_lexer(lexer.name, lexer)
        for alias in lexer.aliases:
            app.add_lexer(alias, lexer)

    return dict(version=__version__, parallel_read_safe=True)
