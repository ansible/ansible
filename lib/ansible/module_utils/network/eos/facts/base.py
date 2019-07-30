#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos facts base class
this contains methods common to all facts subsets
"""

import re
from copy import deepcopy
from ansible.module_utils.six import iteritems


class FactsBase(object):
    """
    The eos facts base class
    """
    generated_spec = {}
    ansible_facts = {'ansible_network_resources': {}}

    def __init__(self, argspec, subspec=None, options=None):
        spec = deepcopy(argspec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = self.generate_dict(facts_argument_spec)

    def generate_dict(self, spec):
        """
        Generate dictionary which is in sync with argspec

        :param spec: A dictionary which the argspec of module
        :rtype: A dictionary
        :returns: A dictionary in sync with argspec with default value
        """
        obj = {}
        if not spec:
            return obj

        for key, val in iteritems(spec):
            if 'default' in val:
                dct = {key: val['default']}
            elif 'type' in val and val['type'] == 'dict':
                dct = {key: self.generate_dict(val['options'])}
            else:
                dct = {key: None}
            obj.update(dct)
        return obj

    @staticmethod
    def parse_conf_arg(cfg, arg):
        """
        Parse config based on argument

        :param cfg: A text string which is a line of configuration.
        :param arg: A text string which is to be matched.
        :rtype: A text string
        :returns: A text string if match is found
        """
        match = re.search(r'%s (.+)(\n|$)' % arg, cfg, re.M)
        if match:
            result = match.group(1).strip()
        else:
            result = None
        return result

    @staticmethod
    def parse_conf_cmd_arg(cfg, cmd, res1, res2=None):
        """
        Parse config based on command

        :param cfg: A text string which is a line of configuration.
        :param cmd: A text string which is the command to be matched
        :param res1: A text string to be returned if the command is present
        :param res2: A text string to be returned if the negate command
                     is present
        :rtype: A text string
        :returns: A text string if match is found
        """
        match = re.search(r'\n\s+%s(\n|$)' % cmd, cfg)
        if match:
            return res1
        if res2 is not None:
            match = re.search(r'\n\s+no %s(\n|$)' % cmd, cfg)
            if match:
                return res2
        return None

    def generate_final_config(self, cfg_dict):
        """
        Generate final config dictionary

        :param cfg_dict: A dictionary parsed in the facts system
        :rtype: A dictionary
        :returns: A dictionary by eliminating keys that have null values
        """
        final_cfg = {}
        if not cfg_dict:
            return final_cfg

        for key, val in iteritems(cfg_dict):
            dct = None
            if isinstance(val, dict):
                child_val = self.generate_final_config(val)
                if child_val:
                    dct = {key: child_val}
            elif val not in [None, [], {}, (), '']:
                dct = {key: val}
            if dct:
                final_cfg.update(dct)
        return final_cfg
