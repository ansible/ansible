from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class BotoServerError(Exception):
    pass


class ClientError(Exception):
    pass


class PartialCredentialsError(Exception):
    pass


class ProfileNotFound(Exception):
    pass


class BotoCoreError(Exception):
    pass
