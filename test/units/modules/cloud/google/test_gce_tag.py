import unittest

from ansible.modules.cloud.google.gce_tag import _get_changed_items, _intersect_items, _union_items


class TestGCETag(unittest.TestCase):
    """Unit tests for gce_tag module."""

    def test_union_items(self):
        """
        Combine items in both lists
        removing duplicates.
        """
        listA = [1, 2, 3, 4, 5, 8, 9]
        listB = [1, 2, 3, 4, 5, 6, 7]
        want = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        got = _union_items(listA, listB)
        self.assertEqual(want, got)

    def test_intersect_items(self):
        """
        All unique items from either list.
        """
        listA = [1, 2, 3, 4, 5, 8, 9]
        listB = [1, 2, 3, 4, 5, 6, 7]
        want = [1, 2, 3, 4, 5]
        got = _intersect_items(listA, listB)
        self.assertEqual(want, got)

        # tags removed
        new_tags = ['one', 'two']
        existing_tags = ['two']
        want = ['two']  # only remove the tag that was present
        got = _intersect_items(existing_tags, new_tags)
        self.assertEqual(want, got)

    def test_get_changed_items(self):
        """
        All the items from left list that don't match
        any item from the right list.
        """
        listA = [1, 2, 3, 4, 5, 8, 9]
        listB = [1, 2, 3, 4, 5, 6, 7]
        want = [8, 9]
        got = _get_changed_items(listA, listB)
        self.assertEqual(want, got)

        # simulate new tags added
        tags_to_add = ['one', 'two']
        existing_tags = ['two']
        want = ['one']
        got = _get_changed_items(tags_to_add, existing_tags)
        self.assertEqual(want, got)

        # simulate removing tags
        # specifying one tag on right that doesn't exist
        tags_to_remove = ['one', 'two']
        existing_tags = ['two', 'three']
        want = ['three']
        got = _get_changed_items(existing_tags, tags_to_remove)
        self.assertEqual(want, got)
