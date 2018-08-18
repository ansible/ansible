from ansible.module_utils.six import string_types


def check_type_str(value):
    if isinstance(value, string_types):
        return value

    # Note: This could throw a unicode error if value's __str__() method
    # returns non-ascii.  Have to port utils.to_bytes() if that happens
    return str(value)
