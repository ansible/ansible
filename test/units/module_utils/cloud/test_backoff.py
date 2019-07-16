import random

from units.compat import unittest
from ansible.module_utils.cloud import _exponential_backoff, \
    _full_jitter_backoff


class ExponentialBackoffStrategyTestCase(unittest.TestCase):
    def test_no_retries(self):
        strategy = _exponential_backoff(retries=0)
        result = list(strategy())
        self.assertEquals(result, [], 'list should be empty')

    def test_exponential_backoff(self):
        strategy = _exponential_backoff(retries=5, delay=1, backoff=2)
        result = list(strategy())
        self.assertEquals(result, [1, 2, 4, 8, 16])

    def test_max_delay(self):
        strategy = _exponential_backoff(retries=7, delay=1, backoff=2, max_delay=60)
        result = list(strategy())
        self.assertEquals(result, [1, 2, 4, 8, 16, 32, 60])

    def test_max_delay_none(self):
        strategy = _exponential_backoff(retries=7, delay=1, backoff=2, max_delay=None)
        result = list(strategy())
        self.assertEquals(result, [1, 2, 4, 8, 16, 32, 64])


class FullJitterBackoffStrategyTestCase(unittest.TestCase):
    def test_no_retries(self):
        strategy = _full_jitter_backoff(retries=0)
        result = list(strategy())
        self.assertEquals(result, [], 'list should be empty')

    def test_full_jitter(self):
        retries = 5
        seed = 1

        r = random.Random(seed)
        expected = [r.randint(0, 2**i) for i in range(0, retries)]

        strategy = _full_jitter_backoff(
            retries=retries, delay=1, _random=random.Random(seed))
        result = list(strategy())

        self.assertEquals(result, expected)
