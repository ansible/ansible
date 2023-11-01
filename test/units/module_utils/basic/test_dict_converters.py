# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from units.mock.procenv import ModuleTestCase

import builtins

realimport = builtins.__import__


class TestTextifyContainers(ModuleTestCase):
    def test_module_utils_basic_json_dict_converters(self):
        from ansible.module_utils.basic import json_dict_unicode_to_bytes, json_dict_bytes_to_unicode

        test_data = dict(
            item1=u"Fóo",
            item2=[u"Bár", u"Bam"],
            item3=dict(sub1=u"Súb"),
            item4=(u"föo", u"bär", u"©"),
            item5=42,
        )
        res = json_dict_unicode_to_bytes(test_data)
        res2 = json_dict_bytes_to_unicode(res)

        self.assertEqual(test_data, res2)
