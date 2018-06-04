def str_to_int(str_in):
    if type(str_in) is int:
        return str_in
    elif type(str_in) is str:
        return int(str_in)
    else:
        return None
