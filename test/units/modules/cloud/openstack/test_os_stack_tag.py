import unittest

from ansible.modules.cloud.openstack.os_stack_tag import (_needs_update,
                                                          _add_stack_tags,
                                                          _delete_stack_tags)


class TestOSStackTag(unittest.TestCase):
    """Unit tests for os_stack_tag module."""

    def test_no_needs_update(self):
        """
        Should return false when lists are equal
        """
        listA = ["a", "b", "c", "d"]
        listB = ["a", "b", "c", "d"]
        needs_update = _needs_update(listA, listB)
        self.assertEqual(needs_update, False)

    def test_needs_update(self):
        """
        Should return true when lists are not equal
        """
        listA = ["a", "b", "c", "d"]
        listB = ["a", "c", "d"]
        needs_update = _needs_update(listA, listB)
        self.assertEqual(needs_update, True)

    def test_add_stack_tags(self):
        """
        Should return the union of the lists w/o duplicates
        """
        listA = ["a"]
        listB = ["a", "b", "c", "d"]
        want = ["a", "b", "c", "d"]
        got = _add_stack_tags(listA, listB, purge=False)
        self.assertEqual(set(want), set(got))

    def test_add_stack_tags_with_purge(self):
        """
        Should return only the elements of listB
        """
        listA = ["a", "b", "c", "d"]
        listB = ["a", "e", "f"]
        want = ["a", "e", "f"]
        got = _add_stack_tags(listA, listB, purge=True)
        self.assertEqual(set(want), set(got))

    def test_delete_stack_tags(self):
        """
        Should return all elements of listA that don't exist in listB
        """
        listA = ["a", "b", "c", "d"]
        listB = ["a", "e", "f"]
        want = ["b", "c", "d"]
        got = _delete_stack_tags(listA, listB)
        self.assertEqual(set(want), set(got))
