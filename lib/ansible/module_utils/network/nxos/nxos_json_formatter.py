# Copyright: (c) 2019, Olivier Blin <olivier.oblin@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class NxosJsonFormatterError(Exception):
    pass


# Nxos JSON formatter.
#
# The nxos JSON outputer return multiple formats for the same data. The regular
# output structure is { "TABLE_x": "ROW_x": [...] } but, for some specific
# cases, it changes:
# * 0 element: missing structure or empty string.
# * 1 element: ROW_x is a dict instead of a list.
# * >1 element: regular format.
# * >1 element alternative: TABLE_x is a list of ROW_x hash.
#   ex: { "TABLE_x": [ {"ROW_x": {...} }, {"ROW_x": {...} } ] }
#
# The TABLE_x.ROW_x stucture can be found on different levels in the nxos JSON
# output. A list of path describes the position where we should find each
# TABLE_x.ROW_x structure.
# With the path "a.*.x":
# * 'a' is the key of the top level dict.
# * '*' indicate to iterate on the values of the 'a' key.
# * 'x', the TABLE_x.ROW_x structure, request a conversion to the regular format:
#   * if TABLE_x.ROW_x structure is missing, it is created.
#   * if TABLE_x.ROW_x structure is invalid, it is rewritten in the regular format.
# The last element of the path is always the TABLE_x.ROW_x structure in a simplified
# writing. Previous elements are the way to reach it.
#
# Examples:
# * ["a"]: Validate the structure {'TABLE_a': {'ROW_a': [...]}}
# * ["a.b"]: Validate the structure {'a': {'TABLE_b': {'ROW_b': [...]}}
# * ["a.*.b"]: Validate the structure {'a': [{'TABLE_b': {'ROW_b': [...]}}, ...]}
# * ["a", "TABLE_a.ROW_a.*.b"]: Validate the structure {'TABLE_a': {'ROW_a': [{'TABLE_b': {'ROW_b': [...]}}, ...]}}
#
# Parameters:
# * nxos_json: Nxos JSON output.
# * all_path: list of path to TABLE_x.ROW_x structures to check.
#
def nxos_json_formatter(nxos_json, all_path):
    # First level case: empty string when no elements
    if nxos_json == '':
        nxos_json = {}

    for struct_path in all_path:
        nxos_json_formatter_recursive(nxos_json, struct_path)

    return nxos_json


# Apply conversion for the requested path.
def nxos_json_formatter_recursive(nxos_json_part, struct_path):
    splitted_path = struct_path.split('.')
    elem = splitted_path.pop(0)
    if elem == '*':
        # Recursive call on each element of the list
        if isinstance(nxos_json_part, list):
            for sub_part in nxos_json_part:
                nxos_json_formatter_recursive(sub_part, '.'.join(splitted_path))
        else:
            raise NxosJsonFormatterError("Expected a list (*), got %s" % (str(type(nxos_json_part))))
    elif len(splitted_path) >= 1:
        # Move forward in the structure
        if isinstance(nxos_json_part, dict):
            if elem in nxos_json_part.keys():
                nxos_json_formatter_recursive(nxos_json_part[elem], '.'.join(splitted_path))
            else:
                raise NxosJsonFormatterError("Missing key '%s'" % (elem))
        else:
            raise NxosJsonFormatterError("Expected a dict with key '%s', got %s" % (elem, str(type(nxos_json_part))))
    else:
        # Convert last element to the format {'TABLE_ELEMENT': {'ROW_ELEMENT': [ ... ]}}
        table = "TABLE_" + elem
        row = "ROW_" + elem
        if isinstance(nxos_json_part, dict):
            if table in nxos_json_part.keys():
                if isinstance(nxos_json_part[table], dict):
                    if isinstance(nxos_json_part[table][row], list):
                        pass
                    else:
                        # 1 element case
                        nxos_json_part[table][row] = [nxos_json_part[table][row]]
                elif isinstance(nxos_json_part[table], list):
                    # >1 element alternative case
                    to_reformat = nxos_json_part[table]
                    nxos_json_part[table] = {}
                    nxos_json_part[table][row] = []

                    for data_instance in to_reformat:
                        # Strict structure check before conversion
                        if not isinstance(data_instance, dict):
                            raise NxosJsonFormatterError("The last element (%s) must be a list of dict, got list of %s" % (table, str(type(data_instance))))
                        elif row not in data_instance.keys():
                            raise NxosJsonFormatterError("The last element (%s) is missing" % (row))
                        elif not isinstance(data_instance[row], dict):
                            raise NxosJsonFormatterError("The last element (%s) must be a dict, got %s" % (row, str(type(data_instance[row]))))
                        else:
                            nxos_json_part[table][row] += [data_instance[row]]
                else:
                    # No other format accepted
                    raise NxosJsonFormatterError("The last element (%s) must be a dict or a list, got %s" % (table, str(type(nxos_json_part[table]))))
            else:
                # 0 element case
                nxos_json_part[table] = {}
                nxos_json_part[table][row] = []
        else:
            raise NxosJsonFormatterError("The last element must be a dict, got %s" % (str(type(nxos_json_part))))
