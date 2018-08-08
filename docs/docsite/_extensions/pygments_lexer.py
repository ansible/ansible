# -*- coding: utf-8 -*-
# pylint: disable=no-self-argument
#
# Copyright 2006-2017 by the Pygments team, see AUTHORS at
# https://bitbucket.org/birkenfeld/pygments-main/raw/7941677dc77d4f2bf0bbd6140ade85a9454b8b80/AUTHORS
# Copyright by Kirill Simonov (original author of YAML lexer).
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

from __future__ import absolute_import, print_function

from pygments.lexer import LexerContext, ExtendedRegexLexer, DelegatingLexer, bygroups, include
from pygments.lexers import DjangoLexer
from pygments import token


class AnsibleYamlLexerContext(LexerContext):
    """Indentation context for the YAML lexer."""

    def __init__(self, *args, **kwds):
        super(AnsibleYamlLexerContext, self).__init__(*args, **kwds)
        self.indent_stack = []
        self.indent = -1
        self.next_indent = 0
        self.block_scalar_indent = None


class AnsibleYamlLexer(ExtendedRegexLexer):
    """
    Lexer for `YAML <http://yaml.org/>`_, a human-friendly data serialization
    language.

    .. versionadded:: 0.11
    """

    name = 'YAML'
    aliases = ['yaml']
    filenames = ['*.yaml', '*.yml']
    mimetypes = ['text/x-yaml']

    def something(token_class):
        """Do not produce empty tokens."""
        def callback(lexer, match, context):
            text = match.group()
            if not text:
                return
            yield match.start(), token_class, text
            context.pos = match.end()
        return callback

    def reset_indent(token_class):
        """Reset the indentation levels."""
        def callback(lexer, match, context):
            text = match.group()
            context.indent_stack = []
            context.indent = -1
            context.next_indent = 0
            context.block_scalar_indent = None
            yield match.start(), token_class, text
            context.pos = match.end()
        return callback

    def save_indent(token_class, start=False):
        """Save a possible indentation level."""
        def callback(lexer, match, context):
            text = match.group()
            extra = ''
            if start:
                context.next_indent = len(text)
                if context.next_indent < context.indent:
                    while context.next_indent < context.indent:
                        context.indent = context.indent_stack.pop()
                    if context.next_indent > context.indent:
                        extra = text[context.indent:]
                        text = text[:context.indent]
            else:
                context.next_indent += len(text)
            if text:
                yield match.start(), token_class, text
            if extra:
                yield match.start() + len(text), token_class.Error, extra
            context.pos = match.end()
        return callback

    def set_indent(token_class, implicit=False):
        """Set the previously saved indentation level."""
        def callback(lexer, match, context):
            text = match.group()
            if context.indent < context.next_indent:
                context.indent_stack.append(context.indent)
                context.indent = context.next_indent
            if not implicit:
                context.next_indent += len(text)
            yield match.start(), token_class, text
            context.pos = match.end()
        return callback

    def set_block_scalar_indent(token_class):
        """Set an explicit indentation level for a block scalar."""
        def callback(lexer, match, context):
            text = match.group()
            context.block_scalar_indent = None
            if not text:
                return
            increment = match.group(1)
            if increment:
                current_indent = max(context.indent, 0)
                increment = int(increment)
                context.block_scalar_indent = current_indent + increment
            if text:
                yield match.start(), token_class, text
                context.pos = match.end()
        return callback

    def parse_block_scalar_empty_line(indent_token_class, content_token_class):
        """Process an empty line in a block scalar."""
        def callback(lexer, match, context):
            text = match.group()
            if (context.block_scalar_indent is None or
                    len(text) <= context.block_scalar_indent):
                if text:
                    yield match.start(), indent_token_class, text
            else:
                indentation = text[:context.block_scalar_indent]
                content = text[context.block_scalar_indent:]
                yield match.start(), indent_token_class, indentation
                yield (match.start() + context.block_scalar_indent,
                       content_token_class, content)
            context.pos = match.end()
        return callback

    def parse_block_scalar_indent(token_class):
        """Process indentation spaces in a block scalar."""
        def callback(lexer, match, context):
            text = match.group()
            if context.block_scalar_indent is None:
                if len(text) <= max(context.indent, 0):
                    context.stack.pop()
                    context.stack.pop()
                    return
                context.block_scalar_indent = len(text)
            else:
                if len(text) < context.block_scalar_indent:
                    context.stack.pop()
                    context.stack.pop()
                    return
            if text:
                yield match.start(), token_class, text
                context.pos = match.end()
        return callback

    def parse_plain_scalar_indent(token_class):
        """Process indentation spaces in a plain scalar."""
        def callback(lexer, match, context):
            text = match.group()
            if len(text) <= context.indent:
                context.stack.pop()
                context.stack.pop()
                return
            if text:
                yield match.start(), token_class, text
                context.pos = match.end()
        return callback

    tokens = {
        # the root rules
        'root': [
            # ignored whitespaces
            (r'[ ]+(?=#|$)', token.Text),
            # line breaks
            (r'\n+', token.Text),
            # a comment
            (r'#[^\n]*', token.Comment.Single),
            # the '%YAML' directive
            (r'^%YAML(?=[ ]|$)', reset_indent(token.Name.Tag), 'yaml-directive'),
            # the %TAG directive
            (r'^%TAG(?=[ ]|$)', reset_indent(token.Name.Tag), 'tag-directive'),
            # document start and document end indicators
            (r'^(?:---|\.\.\.)(?=[ ]|$)', reset_indent(token.Name.Namespace),
             'block-line'),
            # indentation spaces
            (r'[ ]*(?!\s|$)', save_indent(token.Text, start=True),
             ('block-line', 'indentation')),
        ],

        # trailing whitespaces after directives or a block scalar indicator
        'ignored-line': [
            # ignored whitespaces
            (r'[ ]+(?=#|$)', token.Text),
            # a comment
            (r'#[^\n]*', token.Comment.Single),
            # line break
            (r'\n', token.Text, '#pop:2'),
        ],

        # the %YAML directive
        'yaml-directive': [
            # the version number
            (r'([ ]+)([0-9]+\.[0-9]+)',
             bygroups(token.Text, token.Number), 'ignored-line'),
        ],

        # the %YAG directive
        'tag-directive': [
            # a tag handle and the corresponding prefix
            (r'([ ]+)(!|![\w-]*!)'
             r'([ ]+)(!|!?[\w;/?:@&=+$,.!~*\'()\[\]%-]+)',
             bygroups(token.Text, token.Keyword.Type, token.Text, token.Keyword.Type),
             'ignored-line'),
        ],

        # block scalar indicators and indentation spaces
        'indentation': [
            # trailing whitespaces are ignored
            (r'[ ]*$', something(token.Text), '#pop:2'),
            # whitespaces preceeding block collection indicators
            (r'[ ]+(?=[?:-](?:[ ]|$))', save_indent(token.Text)),
            # block collection indicators
            (r'[?:-](?=[ ]|$)', set_indent(token.Punctuation.Indicator)),
            # the beginning a block line
            (r'[ ]*', save_indent(token.Text), '#pop'),
        ],

        # an indented line in the block context
        'block-line': [
            # the line end
            (r'[ ]*(?=#|$)', something(token.Text), '#pop'),
            # whitespaces separating tokens
            (r'[ ]+', token.Text),
            # key with colon
            (r'([^,:?\[\]{}\n]+)(:)(?=[ ]|$)',
             bygroups(token.Name.Tag, set_indent(token.Punctuation, implicit=True))),
            # tags, anchors and aliases,
            include('descriptors'),
            # block collections and scalars
            include('block-nodes'),
            # flow collections and quoted scalars
            include('flow-nodes'),
            # a plain scalar
            (r'(?=[^\s?:,\[\]{}#&*!|>\'"%@`-]|[?:-]\S)',
             something(token.Name.Variable),
             'plain-scalar-in-block-context'),
        ],

        # tags, anchors, aliases
        'descriptors': [
            # a full-form tag
            (r'!<[\w#;/?:@&=+$,.!~*\'()\[\]%-]+>', token.Keyword.Type),
            # a tag in the form '!', '!suffix' or '!handle!suffix'
            (r'!(?:[\w-]+!)?'
             r'[\w#;/?:@&=+$,.!~*\'()\[\]%-]+', token.Keyword.Type),
            # an anchor
            (r'&[\w-]+', token.Name.Label),
            # an alias
            (r'\*[\w-]+', token.Name.Variable),
        ],

        # block collections and scalars
        'block-nodes': [
            # implicit key
            (r':(?=[ ]|$)', set_indent(token.Punctuation.Indicator, implicit=True)),
            # literal and folded scalars
            (r'[|>]', token.Punctuation.Indicator,
             ('block-scalar-content', 'block-scalar-header')),
        ],

        # flow collections and quoted scalars
        'flow-nodes': [
            # a flow sequence
            (r'\[', token.Punctuation.Indicator, 'flow-sequence'),
            # a flow mapping
            (r'\{', token.Punctuation.Indicator, 'flow-mapping'),
            # a single-quoted scalar
            (r'\'', token.String, 'single-quoted-scalar'),
            # a double-quoted scalar
            (r'\"', token.String, 'double-quoted-scalar'),
        ],

        # the content of a flow collection
        'flow-collection': [
            # whitespaces
            (r'[ ]+', token.Text),
            # line breaks
            (r'\n+', token.Text),
            # a comment
            (r'#[^\n]*', token.Comment.Single),
            # simple indicators
            (r'[?:,]', token.Punctuation.Indicator),
            # tags, anchors and aliases
            include('descriptors'),
            # nested collections and quoted scalars
            include('flow-nodes'),
            # a plain scalar
            (r'(?=[^\s?:,\[\]{}#&*!|>\'"%@`])',
             something(token.Name.Variable),
             'plain-scalar-in-flow-context'),
        ],

        # a flow sequence indicated by '[' and ']'
        'flow-sequence': [
            # include flow collection rules
            include('flow-collection'),
            # the closing indicator
            (r'\]', token.Punctuation.Indicator, '#pop'),
        ],

        # a flow mapping indicated by '{' and '}'
        'flow-mapping': [
            # key with colon
            (r'([^,:?\[\]{}\n]+)(:)(?=[ ]|$)',
             bygroups(token.Name.Tag, token.Punctuation)),
            # include flow collection rules
            include('flow-collection'),
            # the closing indicator
            (r'\}', token.Punctuation.Indicator, '#pop'),
        ],

        # block scalar lines
        'block-scalar-content': [
            # line break
            (r'\n', token.Text),
            # empty line
            (r'^[ ]+$',
             parse_block_scalar_empty_line(token.Text, token.Name.Constant)),
            # indentation spaces (we may leave the state here)
            (r'^[ ]*', parse_block_scalar_indent(token.Text)),
            # line content
            (r'[\S\t ]+', token.Name.Constant),
        ],

        # the content of a literal or folded scalar
        'block-scalar-header': [
            # indentation indicator followed by chomping flag
            (r'([1-9])?[+-]?(?=[ ]|$)',
             set_block_scalar_indent(token.Punctuation.Indicator),
             'ignored-line'),
            # chomping flag followed by indentation indicator
            (r'[+-]?([1-9])?(?=[ ]|$)',
             set_block_scalar_indent(token.Punctuation.Indicator),
             'ignored-line'),
        ],

        # ignored and regular whitespaces in quoted scalars
        'quoted-scalar-whitespaces': [
            # leading and trailing whitespaces are ignored
            (r'^[ ]+', token.Text),
            (r'[ ]+$', token.Text),
            # line breaks are ignored
            (r'\n+', token.Text),
            # other whitespaces are a part of the value
            (r'[ ]+', token.Name.Variable),
        ],

        # single-quoted scalars
        'single-quoted-scalar': [
            # include whitespace and line break rules
            include('quoted-scalar-whitespaces'),
            # escaping of the quote character
            (r'\'\'', token.String.Escape),
            # regular non-whitespace characters
            (r'[^\s\']+', token.String),
            # the closing quote
            (r'\'', token.String, '#pop'),
        ],

        # double-quoted scalars
        'double-quoted-scalar': [
            # include whitespace and line break rules
            include('quoted-scalar-whitespaces'),
            # escaping of special characters
            (r'\\[0abt\tn\nvfre "\\N_LP]', token.String),
            # escape codes
            (r'\\(?:x[0-9A-Fa-f]{2}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})',
             token.String.Escape),
            # regular non-whitespace characters
            (r'[^\s"\\]+', token.String),
            # the closing quote
            (r'"', token.String, '#pop'),
        ],

        # the beginning of a new line while scanning a plain scalar
        'plain-scalar-in-block-context-new-line': [
            # empty lines
            (r'^[ ]+$', token.Text),
            # line breaks
            (r'\n+', token.Text),
            # document start and document end indicators
            (r'^(?=---|\.\.\.)', something(token.Name.Namespace), '#pop:3'),
            # indentation spaces (we may leave the block line state here)
            (r'^[ ]*', parse_plain_scalar_indent(token.Text), '#pop'),
        ],

        # a plain scalar in the block context
        'plain-scalar-in-block-context': [
            # the scalar ends with the ':' indicator
            (r'[ ]*(?=:[ ]|:$)', something(token.Text), '#pop'),
            # the scalar ends with whitespaces followed by a comment
            (r'[ ]+(?=#)', token.Text, '#pop'),
            # trailing whitespaces are ignored
            (r'[ ]+$', token.Text),
            # line breaks are ignored
            (r'\n+', token.Text, 'plain-scalar-in-block-context-new-line'),
            # other whitespaces are a part of the value
            (r'[ ]+', token.Literal.Scalar.Plain),
            # regular non-whitespace characters
            (r'(?::(?!\s)|[^\s:])+', token.Literal.Scalar.Plain),
        ],

        # a plain scalar is the flow context
        'plain-scalar-in-flow-context': [
            # the scalar ends with an indicator character
            (r'[ ]*(?=[,:?\[\]{}])', something(token.Text), '#pop'),
            # the scalar ends with a comment
            (r'[ ]+(?=#)', token.Text, '#pop'),
            # leading and trailing whitespaces are ignored
            (r'^[ ]+', token.Text),
            (r'[ ]+$', token.Text),
            # line breaks are ignored
            (r'\n+', token.Text),
            # other whitespaces are a part of the value
            (r'[ ]+', token.Name.Variable),
            # regular non-whitespace characters
            (r'[^\s,:?\[\]{}]+', token.Name.Variable),
        ],

    }

    def get_tokens_unprocessed(self, text=None, context=None):
        if context is None:
            context = AnsibleYamlLexerContext(text, 0)
        return super(AnsibleYamlLexer, self).get_tokens_unprocessed(text, context)


class AnsibleYamlJinjaLexer(DelegatingLexer):
    """
    Subclass of the `DjangoLexer` that highlights unlexed data with the
    `AnsibleYamlLexer`.

    Commonly used in Saltstack salt states.

    .. versionadded:: 2.0
    """

    name = 'YAML+Jinja'
    aliases = ['yaml+jinja']
    filenames = ['*.sls']
    mimetypes = ['text/x-yaml+jinja']

    def __init__(self, **options):
        super(AnsibleYamlJinjaLexer, self).__init__(AnsibleYamlLexer, DjangoLexer, **options)


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
    for lexer in [AnsibleYamlLexer(startinline=True), AnsibleYamlJinjaLexer(startinline=True)]:
        app.add_lexer(lexer.name, lexer)
        for alias in lexer.aliases:
            app.add_lexer(alias, lexer)

    return dict(version=__version__, parallel_read_safe=True)
