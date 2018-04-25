# -*- coding: utf-8 -*-
# (c) 2018, Scott Buchanan <sbuchanan@ri.pn>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

import json
import errno
from subprocess import Popen, PIPE

from ansible.errors import AnsibleLookupError


class OnePass(object):

    def __init__(self, path='op'):
        self._cli_path = path

    @property
    def cli_path(self):
        return self._cli_path

    def assert_logged_in(self):
        try:
            self._run(["get", "account"])
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise AnsibleLookupError("1Password CLI tool not installed in path on control machine")
            raise e
        except AnsibleLookupError:
            raise AnsibleLookupError("Not logged into 1Password: please run 'op signin' first")

    def get_raw(self, item_id, vault=None):
        args = ["get", "item", item_id]
        if vault is not None:
            args += ['--vault={0}'.format(vault)]
        output, dummy = self._run(args)
        return output

    def get_field(self, item_id, field, section=None, vault=None):
        output = self.get_raw(item_id, vault)
        return self._parse_field(output, field, section) if output != '' else ''

    def _run(self, args, expected_rc=0):
        p = Popen([self.cli_path] + args, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        out, err = p.communicate()
        rc = p.wait()
        if rc != expected_rc:
            raise AnsibleLookupError(err)
        return out, err

    def _parse_field(self, data_json, field_name, section_title=None):
        data = json.loads(data_json)
        if section_title is None:
            for field_data in data['details'].get('fields', []):
                if field_data.get('name').lower() == field_name.lower():
                    return field_data.get('value', '')
        for section_data in data['details'].get('sections', []):
            if section_title is not None and section_title.lower() != section_data['title'].lower():
                continue
            for field_data in section_data.get('fields', []):
                if field_data.get('t').lower() == field_name.lower():
                    return field_data.get('v', '')
        return ''
