# Copyright (c) 2019, Matt Martz <matt@sivel.net>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)


class AnsibleWarning(Warning):
    def __init__(self, msg):
        self.msg = msg
        super(AnsibleWarning, self).__init__(msg)


class AnsibleDeprecationWarning(DeprecationWarning):
    def __init__(self, msg, version=None):
        self.version = version
        self.msg = msg
        super(AnsibleDeprecationWarning, self).__init__(msg)
