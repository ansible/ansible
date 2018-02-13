# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# mixin classes for testing object compare, total ordering and identity
# (ie, __eq__, __gte__, hash, id)


class DifferentType():
    pass


class EqualityCompare():

    def test_eq(self):
        self.assertTrue(self.one == self.one)
        self.assertFalse(self.one == self.two)

    def test_ne(self):
        self.assertFalse(self.one != self.one)
        self.assertTrue(self.one != self.two)

    def test_eq_different(self):
        self.assertFalse(self.one == self.different)
        self.assertTrue(self.one != self.different)

    def test_eq_none(self):
        # noqa since this compare is a bad idea, but can happen anyway
        self.assertFalse(self.one == None)  # noqa
        self.assertFalse(self.two == None)  # noqa
        self.assertFalse(self.another_one == None)  # noqa

    def test_ne_none(self):
        self.assertNotEqual(self.one, None)
        self.assertNotEqual(self.two, None)
        self.assertNotEqual(self.another_one, None)


class TotalOrdering():
    def test_lt(self):
        self.assertFalse(self.one < self.one)
        self.assertTrue(self.one < self.two)
        self.assertFalse(self.two < self.one)

    def test_gt(self):
        self.assertFalse(self.one > self.one)
        self.assertFalse(self.one > self.two)
        self.assertTrue(self.two > self.one)

    def test_le(self):
        self.assertLessEqual(self.one, self.one)
        self.assertTrue(self.one <= self.one)

        self.assertLessEqual(self.one, self.two)
        self.assertTrue(self.one <= self.two)

        self.assertFalse(self.two <= self.one)

    def test_ge(self):
        self.assertGreaterEqual(self.one, self.one)
        self.assertTrue(self.one >= self.one)

        self.assertFalse(self.one >= self.two)

        self.assertGreaterEqual(self.two, self.one)
        self.assertTrue(self.two >= self.one)


class HashCompare():
    def test_hash_different(self):
        self.assertNotEqual(hash(self.one), hash(self.different))

    def test_hash(self):
        self.assertNotEqual(hash(self.one), hash(self.two))


class IdentityCompare():
    def test_is(self):
        self.assertFalse(self.one is self.two)
        self.assertFalse(self.one is self.another_one)
        self.assertFalse(self.one is self.different)

    def test_not_is(self):
        self.assertTrue(self.one is not self.two)
        self.assertTrue(self.one is not self.another_one)
        self.assertTrue(self.one is not self.different)

    def test_id(self):
        # the ids should never be the same
        self.assertNotEqual(id(self.one), id(self.two))
        self.assertNotEqual(id(self.two), id(self.different))
        self.assertNotEqual(id(self.one), id(self.different))

    def test_is_not_none(self):
        '''Override if you are actually testing None for some reason.

        Or if your object has a legit reason to shared identity with None...'''
        self.assertTrue(self.one is not None)
        self.assertTrue(self.two is not None)
        self.assertTrue(self.another_one is not None)

    def test_is_none(self):
        self.assertFalse(self.one is None)
        self.assertFalse(self.two is None)
        self.assertFalse(self.another_one is None)


class UuidCompare():
    def test_uuid_eq(self):
        self.assertFalse(self.one._uuid == self.two._uuid)
        # self.assertTrue(self.one._uuid == self.another_one._uuid)

    def test_uuid_ne(self):
        self.assertTrue(self.one._uuid != self.two._uuid)
        # self.assertTrue(self.one._uuid != self.another_one._uuid)


class CopyCompare():
    def test_copy_eq(self):
        self.assertEqual(self.one, self.one_copy)

    def test_copy_parent_eq(self):
        self.assertEqual(self.one._parent, self.one_copy._parent)


class CopyExcludeParentCompare():
    def test_copy_eq(self):
        self.assertEqual(self.one, self.one_copy_exclude_parent)

    def test_copy_exclude_parent_eq(self):
        self.assertFalse(self.one._parent == self.one_copy_exclude_parent._parent)

    def test_copy_exclude_parent_ne(self):
        self.assertNotEqual(self.one._parent, self.one_copy_exclude_parent._parent)


class CopyExcludeTasksCompare():
    def test_copy_eq(self):
        self.assertEqual(self.one, self.one_copy_exclude_tasks)

    # FIXME: block compare is not currently based on taskslist. Should it be?
    def test_copy_exclude_tasks_eq(self):
        self.assertEqual(self.one, self.one_copy_exclude_tasks)

    def test_copy_exclude_tasks_ne(self):
        self.assertTrue(self.one != self.one_copy_exclude_tasks)
