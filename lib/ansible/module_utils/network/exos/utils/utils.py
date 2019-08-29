#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils

def search_obj_in_list(item, lst, key):
    for o in lst:
        if o[key] == item:
            return o
    return None
