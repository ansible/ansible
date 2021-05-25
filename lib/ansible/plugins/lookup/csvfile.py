# (c) 2013, Jan-Piet Mens <jpmens(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: csvfile
    author: Jan-Piet Mens (@jpmens) <jpmens(at)gmail.com>
    version_added: "1.5"
    short_description: read data from a TSV or CSV file
    description:
      - The csvfile lookup reads the contents of a file in CSV (comma-separated value) format.
        The lookup looks for the row where the first column matches keyname (which can be multiple words)
        and returns the value in the C(col) column (default 1, which indexed from 0 means the second column in the file).
    options:
      col:
        description:  column to return (0 indexed).
        default: "1"
      default:
        description: what to return if the value is not found in the file.
      delimiter:
        description: field separator in the file, for a tab you can specify C(TAB) or C(\\t).
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
"""

EXAMPLES = """
- name:  Match 'Li' on the first column, return the second column (0 based index)
  debug: msg="The atomic number of Lithium is {{ lookup('csvfile', 'Li', file='elements.csv', delimiter=',') }}"

- name: msg="Match 'Li' on the first column, but return the 3rd column (columns start counting after the match)"
  debug: msg="The atomic mass of Lithium is {{ lookup('csvfile', 'Li', file='elements.csv', delimiter=',', col=2) }}"

- name: Define Values From CSV File, this reads file in one go, but you could also use col= to read each in it's own lookup.
  set_fact:
    loop_ip: "{{ csvline[0] }}"
    int_ip: "{{ csvline[1] }}"
    int_mask: "{{ csvline[2] }}"
    int_name: "{{ csvline[3] }}"
    local_as: "{{ csvline[4] }}"
    neighbor_as: "{{ csvline[5] }}"
    neigh_int_ip: "{{ csvline[6] }}"
  vars:
    csvline = "{{ lookup('csvfile', bgp_neighbor_ip, file='bgp_neighbors.csv', delimiter=',') }}"
  delegate_to: localhost
"""

RETURN = """
  _raw:
    description:
      - value(s) stored in file column
    type: list
    elements: str
"""

import codecs
import csv

from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.parsing.splitter import parse_kv
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.six import PY2
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.common._collections_compat import MutableSequence


class CSVRecoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding='utf-8'):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.reader).encode("utf-8")

    next = __next__   # For Python 2


class CSVReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        if PY2:
            f = CSVRecoder(f, encoding)
        else:
            f = codecs.getreader(encoding)(f)

        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def __next__(self):
        row = next(self.reader)
        return [to_text(s) for s in row]

    next = __next__  # For Python 2

    def __iter__(self):
        return self


class LookupModule(LookupBase):

    def read_csv(self, filename, key, delimiter, encoding='utf-8', dflt=None, col=1):

        try:
            f = open(to_bytes(filename), 'rb')
            creader = CSVReader(f, delimiter=to_native(delimiter), encoding=encoding)

            for row in creader:
                if len(row) and row[0] == key:
                    return row[int(col)]
        except Exception as e:
            raise AnsibleError("csvfile: %s" % to_native(e))

        return dflt

    def run(self, terms, variables=None, **kwargs):

        ret = []

        self.set_options(var_options=variables, direct=kwargs)

        # populate options
        paramvals = self.get_options()

        for term in terms:
            kv = parse_kv(term)

            if '_raw_params' not in kv:
                raise AnsibleError('Search key is required but was not found')

            key = kv['_raw_params']

            # parameters override per term using k/v
            try:
                for name, value in kv.items():
                    if name == '_raw_params':
                        continue
                    if name not in paramvals:
                        raise AnsibleAssertionError('%s is not a valid option' % name)

                    self._deprecate_inline_kv()
                    paramvals[name] = value

            except (ValueError, AssertionError) as e:
                raise AnsibleError(e)

            # default is just placeholder for real tab
            if paramvals['delimiter'] == 'TAB':
                paramvals['delimiter'] = "\t"

            lookupfile = self.find_file_in_search_path(variables, 'files', paramvals['file'])
            var = self.read_csv(lookupfile, key, paramvals['delimiter'], paramvals['encoding'], paramvals['default'], paramvals['col'])
            if var is not None:
                if isinstance(var, MutableSequence):
                    for v in var:
                        ret.append(v)
                else:
                    ret.append(var)

        return ret
