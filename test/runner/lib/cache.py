"""Cache for commonly shared data that is intended to be immutable."""

from __future__ import absolute_import, print_function


class CommonCache(object):
    """Common cache."""
    def __init__(self, args):
        """
        :param args: CommonConfig
        """
        self.args = args

    def get(self, key, factory):
        """
        :param key: str
        :param factory: () -> any
        :rtype: any
        """
        if key not in self.args.cache:
            self.args.cache[key] = factory()

        return self.args.cache[key]

    def get_with_args(self, key, factory):
        """
        :param key: str
        :param factory: (CommonConfig) -> any
        :rtype: any
        """

        if key not in self.args.cache:
            self.args.cache[key] = factory(self.args)

        return self.args.cache[key]
