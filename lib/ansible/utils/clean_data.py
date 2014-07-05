def _clean_data(orig_data, scrub_list):
    ''' remove template tags from a string '''
    data = orig_data
    if isinstance(orig_data, basestring):
        for pattern,replacement in scrub_list:
            data = data.replace(pattern, replacement)
    return data

def clean_data_struct(orig_data, scrub_list=(('{{','{#'), ('}}','#}'), ('{%','{#'), ('%}','#}'))):
    '''
    walk a complex data structure, and use _clean_data() to
    remove any template tags that may exist
    '''
    if isinstance(orig_data, dict):
        data = orig_data.copy()
        for key in data:
            new_key = clean_data_struct(key)
            new_val = clean_data_struct(data[key])
            if key != new_key:
                del data[key]
            data[new_key] = new_val
    elif isinstance(orig_data, list):
        data = orig_data[:]
        for i in range(0, len(data)):
            data[i] = clean_data_struct(data[i])
    elif isinstance(orig_data, basestring):
        data = _clean_data(orig_data, scrub_list)
    else:
        data = orig_data
    return data
