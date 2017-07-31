# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.playbook.taggable import Taggable
from units.mock.loader import DictDataLoader


class TaggableTestObj(Taggable):

    def __init__(self):
        self._loader = DictDataLoader({})
        self.tags = []


class TestTaggable(unittest.TestCase):

    def assert_evaluate_equal(self, test_value, tags, only_tags, skip_tags):
        taggable_obj = TaggableTestObj()
        taggable_obj.tags = tags

        evaluate = taggable_obj.evaluate_tags(only_tags, skip_tags, {})

        self.assertEqual(test_value, evaluate)

    def test_evaluate_tags_tag_in_only_tags(self):
        self.assert_evaluate_equal(True, ['tag1', 'tag2'], ['tag1'], [])

    def test_evaluate_tags_tag_in_skip_tags(self):
        self.assert_evaluate_equal(False, ['tag1', 'tag2'], [], ['tag1'])

    def test_evaluate_tags_special_always_in_object_tags(self):
        self.assert_evaluate_equal(True, ['tag', 'always'], ['random'], [])

    def test_evaluate_tags_tag_in_skip_tags_special_always_in_object_tags(self):
        self.assert_evaluate_equal(False, ['tag', 'always'], ['random'], ['tag'])

    def test_evaluate_tags_special_always_in_skip_tags_and_always_in_tags(self):
        self.assert_evaluate_equal(False, ['tag', 'always'], [], ['always'])

    def test_evaluate_tags_special_tagged_in_only_tags_and_object_tagged(self):
        self.assert_evaluate_equal(True, ['tag'], ['tagged'], [])

    def test_evaluate_tags_special_tagged_in_only_tags_and_object_untagged(self):
        self.assert_evaluate_equal(False, [], ['tagged'], [])

    def test_evaluate_tags_special_tagged_in_skip_tags_and_object_tagged(self):
        self.assert_evaluate_equal(False, ['tag'], [], ['tagged'])

    def test_evaluate_tags_special_tagged_in_skip_tags_and_object_untagged(self):
        self.assert_evaluate_equal(True, [], [], ['tagged'])

    def test_evaluate_tags_special_untagged_in_only_tags_and_object_tagged(self):
        self.assert_evaluate_equal(False, ['tag'], ['untagged'], [])

    def test_evaluate_tags_special_untagged_in_only_tags_and_object_untagged(self):
        self.assert_evaluate_equal(True, [], ['untagged'], [])

    def test_evaluate_tags_special_untagged_in_skip_tags_and_object_tagged(self):
        self.assert_evaluate_equal(True, ['tag'], [], ['untagged'])

    def test_evaluate_tags_special_untagged_in_skip_tags_and_object_untagged(self):
        self.assert_evaluate_equal(False, [], [], ['untagged'])

    def test_evaluate_tags_special_all_in_only_tags(self):
        self.assert_evaluate_equal(True, ['tag'], ['all'], ['untagged'])

    def test_evaluate_tags_special_all_in_skip_tags(self):
        self.assert_evaluate_equal(False, ['tag'], ['tag'], ['all'])

    def test_evaluate_tags_special_all_in_only_tags_and_special_all_in_skip_tags(self):
        self.assert_evaluate_equal(False, ['tag'], ['all'], ['all'])

    def test_evaluate_tags_special_all_in_skip_tags_and_always_in_object_tags(self):
        self.assert_evaluate_equal(True, ['tag', 'always'], [], ['all'])

    def test_evaluate_tags_special_all_in_skip_tags_and_special_always_in_skip_tags_and_always_in_object_tags(self):
        self.assert_evaluate_equal(False, ['tag', 'always'], [], ['all', 'always'])

    def test_evaluate_tags_accepts_lists(self):
        self.assert_evaluate_equal(True, ['tag1', 'tag2'], ['tag2'], [])

    def test_evaluate_tags_accepts_strings(self):
        self.assert_evaluate_equal(True, 'tag1,tag2', ['tag2'], [])

    def test_evaluate_tags_with_repeated_tags(self):
        self.assert_evaluate_equal(False, ['tag', 'tag'], [], ['tag'])
