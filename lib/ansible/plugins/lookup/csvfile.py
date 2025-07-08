# (c) 2013, Jan-Piet Mens <jpmens(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
    name: csvfile
    author: Jan-Piet Mens (@jpmens) <jpmens(at)gmail.com>
    version_added: "1.5"
    short_description: read data from a TSV or CSV file
    description:
      - The csvfile lookup reads the contents of a file in CSV (comma-separated value) format.
        The lookup looks for the row where the first column matches keyname (which can be multiple words)
        and returns the value in the O(col) column (default 1, which indexed from 0 means the second column in the file).
      - At least one keyname is required, provided as a positional argument(s) to the lookup.
    options:
      col:
        description:  column to return (0 indexed).
        default: 1
        type: int
      keycol:
        description:  column to search in (0 indexed).
        default: 0
        type: int
        version_added: "2.17"
      default:
        description: what to return if the value is not found in the file.
      delimiter:
        description: field separator in the file, for a tab you can specify V(TAB) or V(\\t).
        default: TAB
      file:
        description: name of the CSV/TSV file to open.
        default: ansible.csv
      encoding:
        description: Encoding (character set) of the used CSV file.
        default: utf-8
        version_added: "2.1"
    notes:
      - The default is for TSV files (tab delimited) not CSV (comma delimited) ... yes the name is misleading.
      - As of version 2.11, the search parameter (text that must match the first column of the file) and filename parameter can be multi-word.
      - For historical reasons, in the search keyname, quotes are treated
        literally and cannot be used around the string unless they appear
        (escaped as required) in the first column of the file you are parsing.
    seealso:
      - ref: playbook_task_paths
        description: Search paths used for relative files.
"""

EXAMPLES = """
- name:  Match 'Li' on the first column, return the second column (0 based index)
  ansible.builtin.debug: msg="The atomic number of Lithium is {{ lookup('ansible.builtin.csvfile', 'Li file=elements.csv delimiter=,') }}"

- name: msg="Match 'Li' on the first column, but return the 3rd column (columns start counting after the match)"
  ansible.builtin.debug: msg="The atomic mass of Lithium is {{ lookup('ansible.builtin.csvfile', 'Li file=elements.csv delimiter=, col=2') }}"

# Contents of bgp_neighbors.csv
# 127.0.0.1,10.0.0.1,24,nones,lola,pepe,127.0.0.2
# 128.0.0.1,10.1.0.1,20,notes,lolita,pepito,128.0.0.2
# 129.0.0.1,10.2.0.1,23,nines,aayush,pepete,129.0.0.2

- name: Define values from CSV file, this reads file in one go, but you could also use col= to read each in it's own lookup.
  ansible.builtin.set_fact:
    '{{ columns[item|int] }}': "{{ csvline }}"
  vars:
    csvline: "{{ lookup('csvfile', bgp_neighbor_ip, file='bgp_neighbors.csv', delimiter=',', col=item) }}"
    columns: ['loop_ip', 'int_ip', 'int_mask', 'int_name', 'local_as', 'neighbour_as', 'neight_int_ip']
    bgp_neighbor_ip: '127.0.0.1'
  loop: '{{ range(columns|length|int) }}'
  delegate_to: localhost
  delegate_facts: true

# Contents of people.csv
# # Last,First,Email,Extension
# Smith,Jane,jsmith@example.com,1234

- name: Specify the column (by keycol) in which the string should be searched
  assert:
    that:
    - lookup('ansible.builtin.csvfile', 'Jane', file='people.csv', delimiter=',', col=0, keycol=1) == "Smith"

# Contents of debug.csv
# test1 ret1.1 ret2.1
# test2 ret1.2 ret2.2
# test3 ret1.3 ret2.3

- name: "Lookup multiple keynames in the first column (index 0), returning the values from the second column (index 1)"
  debug:
    msg: "{{ lookup('csvfile', 'test1', 'test2', file='debug.csv', delimiter=' ') }}"

- name: Lookup multiple keynames using old style syntax
  debug:
    msg: "{{ lookup('csvfile', term1, term2) }}"
  vars:
    term1: "test1 file=debug.csv delimiter=' '"
    term2: "test2 file=debug.csv delimiter=' '"
"""

RETURN = """
  _raw:
    description:
      - value(s) stored in file column
    type: list
    elements: str
"""

import csv

from collections.abc import MutableSequence

from ansible.errors import AnsibleError
from ansible.parsing.splitter import parse_kv
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def read_csv(self, filename, key, delimiter, encoding='utf-8', dflt=None, col=1, keycol=0):
        with open(filename, encoding=encoding) as f:
            for row in csv.reader(f, dialect=csv.excel, delimiter=delimiter):
                if row and row[keycol] == key:
                    return row[col]

        return dflt

    def run(self, terms, variables=None, **kwargs):
        ret = []

        self.set_options(var_options=variables, direct=kwargs)

        # populate options
        paramvals = self.get_options()

        if not terms:
            raise AnsibleError('Search key is required but was not found')

        for term in terms:
            kv = parse_kv(term)

            if '_raw_params' not in kv:
                raise AnsibleError('Search key is required but was not found')

            key = kv['_raw_params']

            # parameters override per term using k/v
            reset_params = False
            for name, value in kv.items():
                if name == '_raw_params':
                    continue
                if name not in paramvals:
                    raise ValueError(f'{name!r} is not a valid option')

                self._deprecate_inline_kv()
                self.set_option(name, value)
                reset_params = True

            if reset_params:
                paramvals = self.get_options()

            # default is just placeholder for real tab
            if paramvals['delimiter'] == 'TAB':
                paramvals['delimiter'] = "\t"

            lookupfile = self.find_file_in_search_path(variables, 'files', paramvals['file'])
            var = self.read_csv(lookupfile, key, paramvals['delimiter'], paramvals['encoding'], paramvals['default'], paramvals['col'], paramvals['keycol'])
            if var is not None:
                if isinstance(var, MutableSequence):
                    ret.extend(var)
                else:
                    ret.append(var)

        return ret
