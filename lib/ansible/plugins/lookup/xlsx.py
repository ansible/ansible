#!/usr/bin.python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Mathieu Dirkx <mathieudirkx@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/glp-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: xlsx
    author: Mathieu Dirkx <mathieu.dirkx@gmail.com>
    version_added: "2.13"
    short_description: Use content of one XLSX worksheet.
    description:
        - This lookup retuns all data in an XLSX worksheet as a list of dicts.
          Each line in the file is a dict. All dicts in the list are in the
          same order as in the file.
        - Unless header is set to None, the values at the line specified by
          header are used as the keys for the dict. If header is set to None the
          the column index is used as the keys for the dict.
          Column A=0, Column B=1, etc.
    options:
      _terms:
        description: Path of the XLSX file. HTTP(S) sources allowed
        required: True
        type: path
      sheet_name:
        description: Name of the worksheet in the file.
        type: string
        required: True
      header:
        description: Line containing the headers. Set to None if there is no
                     header line.
        type: int
        required: False
        default: 1
    requirements:
      - pandas>=1.3.0
      - openpyxl>=3.0.0
    notes:
      - Password protected download sources are not supported.
      - Only use XLSX files you trust.
"""

EXAMPLES = """
- name: The content of attachment {{ sys_id }}
  debug:
    var: "{{ lookup('xlsx', 'http://www.service-now.com/api/now/v1/attachment/'sys_id, sheet_name="Sheet1") }}"

- name: Create VM's
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    folder: /dev
    name: "{{ item.hostname }}"
    state: poweredon
    guest_id: "{{ item.os }}"
    disk:
    - size_gb: "{{ item.os_disk }}"
      type: thin
    hardware:
      memory_mb: "{{ item.memory }}"
      num_cpus: "{{ item.cpu }}"
    networks:
    - ip: "{{ item.ip }}"
      netmask: "{{ item.netmask }}"
      device_type: vmxnet3
    wait_for_ip_address: true
  loop: "{{ lookup('/mount/share1/myproject/k8s/dev.xlsx', header=1, sheet_name='dev') }}"
"""

RETURN = """
  _raw:
    description:
      - Content of worksheet of XLSX file as a list of dicts.
    returned: "success"
    type: "list"
    elements: "dict"
    sample: [{'name': 'Laptop-1', 'owner': 'Jone Doe'},{'name': 'Laptop-2', 'owner': 'Jane Doe']
"""

from ansible.errors import (AnsibleError,
                            AnsibleLookupError,
                            AnsibleFileNotFound,
                            AnsibleOptionsError,
                            AnsibleParserError)
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_text
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.basic import missing_required_lib
from ansible.utils.display import Display
from zipfile import BadZipFile
import traceback
PANDAS_IMP_ERR = None
try:
    from pandas import read_excel
    HAS_PANDAS = True
except ModuleNotFoundError:
    HAS_PANDAS = False
    PANDAS_IMP_ERR = traceback.format_exc()

display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = []
        self.set_options(var_options=variables, direct=kwargs)
        header = self.get_option("header", 1)
        sheet_name = self.get_option("sheet_name")

        display.debug(f"File lookup terms: {terms}")
        display.debug(f"header: {header}")
        display.debug(f"sheet_name: {sheet_name}")

        try:
            data = read_excel(io=terms[0],
                              header=header,
                              sheet_name=sheet_name,
                              engine='openpyxl')
        except FileNotFoundError as e:
            raise AnsibleFileNotFound(f"{terms[0]} not found.")
        except BadZipFile as e:
            raise AnsibleLookupError(f"{terms[0]} not a valid XLSX file.\n\
                                       {to_native(e)}")
        except ValueError as e:
            raise AnsibleLookupError(f"{to_native(e)}")
        except SyntaxError as e:
            raise AnsibleOptionsError(f"Syntax error.\n{to_native(e)}")
        except Exception as e:
            raise AnsibleError(f"Error reading {terms[0]}.\n{to_native(e)}")

        try:
            ret = data.to_dict(orient="records")
        except Exception as e:
            raise AnsibleError(f"Error converting file.\n{to_native(e)}")

        return ret


def main():
    if not PANDAS_LIB:
        module_fail_json(msg=missing_required_lib("pandas"),
                         exception=PANDAS_IMP_ERR)


if __name__ == '__main__':
    main()
