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
