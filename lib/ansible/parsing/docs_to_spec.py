ARGS_DOCS_KEYS = ("aliases", "choices", "default", "elements", "required", "type")


def option_to_spec(option):

    # use known common keys to copy data
    spec = {name: option[name] for name in ARGS_DOCS_KEYS if name in option}

    # handle suboptions
    if "suboptions" in option:
        add_options(spec, option["suboptions"])

        for sub in spec["options"].values():
            # check if we need to apply_defults
            if "default" in sub or "fallback" in sub:
                spec["apply_defaults"] = True

    #TODO: handle deprecations:
    return spec


def restriction_to_spec(r):

    name = None
    rest = None # normally a list except for 'required_by'
    if 'required' in r:
        if 'by' in r:
            name='required_by'
            rest = {r['required']: r['by']}
        elif 'if' in r:
            name='required_if'
            rest = [r['if'], r['equals'], r['required']]
    else:
        for ding in ('exclusive', 'toghether', 'one_of'):
            if ding in r:
                if not isinstance(r[ding], Sequence):
                    raise AnsibleError('must be a list!')
                rest  = r[ding]

                if ding == 'exclusive':
                    name = 'mutually_exclusive'
                else:
                    name = 'required_%s' % ding
                break
            else:
                raise AnsibleError('unknown restriction!')

    return {name: rest}


    # use known common keys to copy data
def add_options(argspec, options):
    for n, o in sorted(options.items()):
        argspec[n] = option_to_spec(o)


def add_restrictions(restrict_spec, restrictions):
    for r in restrictions:
        restrict_spec.append(restriction_to_spec(r))


#argspec = {}
#add_options(argspec, doc['docs']['options'])
#
#restrictions = {}
#add_restrictions(restrictions, doc['docs']['restrictions'])
#
#attributes = {}
#add_attributes(attributes, doc['ATTRIBUTES'])

'''
options:
     ...
notes:
     ...
requirements:
     ...
restrictions:
    # mutually_exclusive
   - description: You cannot use 'a' and 'b' at the same time
     exclusive: a, b
   - description: You cannot use 'c' and 'x' at the same time
     exclusive: c, x

    # required_toghether
   - description: 'a' and 'b' required toghether
     toghether: a, b

    # required_one_of
   - description: at least one of a or b is required
     one_of: a, b

     # required_if
   - description: if x is set to y, a,b and c are required
     required: [a,b,c]
     if: x
     equals: y

     # required_by
   - required: x
     description: x is required if b or c are set
     by: [b,c]
'''
