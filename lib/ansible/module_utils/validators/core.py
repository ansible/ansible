import json
import os

from ansible.module_utils.basic import jsonify, human_to_bytes, safe_eval
from ansible.module_utils.six import string_types, binary_type, text_type


def check_type_str(value):
    if isinstance(value, string_types):
        return value

    # Note: This could throw a unicode error if value's __str__() method
    # returns non-ascii.  Have to port utils.to_bytes() if that happens
    return str(value)


def check_type_list(value):
    if isinstance(value, list):
        return value

    if isinstance(value, string_types):
        return value.split(",")
    elif isinstance(value, int) or isinstance(value, float):
        return [str(value)]

    raise TypeError('%s cannot be converted to a list' % type(value))


def check_type_dict(value):
    if isinstance(value, dict):
        return value

    if isinstance(value, string_types):
        if value.startswith("{"):
            try:
                return json.loads(value)
            except:
                (result, exc) = safe_eval(value, dict(), include_exceptions=True)
                if exc is not None:
                    raise TypeError('unable to evaluate string as dictionary')
                return result
        elif '=' in value:
            fields = []
            field_buffer = []
            in_quote = False
            in_escape = False
            for c in value.strip():
                if in_escape:
                    field_buffer.append(c)
                    in_escape = False
                elif c == '\\':
                    in_escape = True
                elif not in_quote and c in ('\'', '"'):
                    in_quote = c
                elif in_quote and in_quote == c:
                    in_quote = False
                elif not in_quote and c in (',', ' '):
                    field = ''.join(field_buffer)
                    if field:
                        fields.append(field)
                    field_buffer = []
                else:
                    field_buffer.append(c)

            field = ''.join(field_buffer)
            if field:
                fields.append(field)
            return dict(x.split("=", 1) for x in fields)
        else:
            raise TypeError("dictionary requested, could not parse JSON or key=value")

    raise TypeError('%s cannot be converted to a dict' % type(value))


def check_type_bool(self, value):
    if isinstance(value, bool):
        return value

    if isinstance(value, string_types) or isinstance(value, int):
        return self.boolean(value)

    raise TypeError('%s cannot be converted to a bool' % type(value))


def check_type_int(value):
    if isinstance(value, int):
        return value

    if isinstance(value, string_types):
        return int(value)

    raise TypeError('%s cannot be converted to an int' % type(value))


def check_type_float(value):
    if isinstance(value, float):
        return value

    if isinstance(value, (binary_type, text_type, int)):
        return float(value)

    raise TypeError('%s cannot be converted to a float' % type(value))


def check_type_path(value):
    value = check_type_str(value)
    return os.path.expanduser(os.path.expandvars(value))


def check_type_jsonarg(value):
    # Return a jsonified string.  Sometimes the controller turns a json
    # string into a dict/list so transform it back into json here
    if isinstance(value, (text_type, binary_type)):
        return value.strip()
    else:
        if isinstance(value, (list, tuple, dict)):
            return jsonify(value)
    raise TypeError('%s cannot be converted to a json string' % type(value))


def check_type_raw(value):
    return value


def check_type_bytes(value):
    try:
        human_to_bytes(value)
    except ValueError:
        raise TypeError('%s cannot be converted to a Byte value' % type(value))


def check_type_bits(value):
    try:
        human_to_bytes(value, isbits=True)
    except ValueError:
        raise TypeError('%s cannot be converted to a Bit value' % type(value))
