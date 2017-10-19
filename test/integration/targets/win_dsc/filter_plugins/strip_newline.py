# (c) 2017 Red Hat, Inc.
#
# This file is part of Ansible


class FilterModule(object):
    def filters(self):
        return {
            'strip_newline': self.strip_newline
        }

    def strip_newline(self, value):
        # will convert \r\n and \n to just \n
        split_lines = value.splitlines()

        return "\n".join(split_lines)
