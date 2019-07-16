# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class AnsibleModuleException(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class ExitJsonException(AnsibleModuleException):
    pass


class FailJsonException(AnsibleModuleException):
    pass


class FakeAnsibleModule:
    def __init__(self, params=None, check_mode=False):
        self.params = params
        self.check_mode = check_mode

    def exit_json(self, *args, **kwargs):
        raise ExitJsonException(*args, **kwargs)

    def fail_json(self, *args, **kwargs):
        raise FailJsonException(*args, **kwargs)
