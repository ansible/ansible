# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator
from ansible.module_utils.common._collections_compat import Sequence
from ansible.module_utils.six import string_types

"""
Utilities to create module/plugin specs from their documentation.

# example usage:

    #prep
    argpsec = get_options_from_docs(doc.get('options', {}))
    restrictions = get_restrictions_from_doc(doc.get('restrictions', {}))

    # do
    validated = validate_spec(argspec, restrictions, task_params)

    # error handle
    if valided.error_messages:
        raise ActionFail({'msg': 'Validation of arguments failed:\n%s' % '\n'.join(validated.error_messages), 'argument_errors': validatec.error_messages})

    # get info
    final_params = valided.validated_parameters
    no_log_values = valided._no_log_values
    aliases = validated._aliases

'''
example of DOCUMENTATION with requirements:

    options:
         ...jkk
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

        # required_together
       - description: 'a' and 'b' required together
         together: a, b

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
"""

ARGS_DOCS_KEYS = ("aliases", "choices", "default", "elements", "no_log", "required", "type")


def option_to_spec(option, deprecate=None) -> dict:
    """ convert from doc option entry to spec arg definition """

    # use known common keys to copy data
    spec = {name: option[name] for name in ARGS_DOCS_KEYS if name in option}

    # handle suboptions
    if "suboptions" in option:
        add_options_from_doc(spec, option["suboptions"], deprecate)

        for sub in spec["options"].values():
            # check if we need to apply_defults
            if "default" in sub or "fallback" in sub:
                spec["apply_defaults"] = True

    # Use passed-in function to handle deprecations
    if deprecate is not None and 'deprecated' in option:
        deprecate(**option['deprecated'])

    return spec


def restriction_to_spec(r) -> list[list[str]] | None:
    """ read documented restriction and create spec restriction """

    name = None
    rest = None  # normally a list except for 'required_by'
    if 'required' in r:
        if 'by' in r:
            name = 'required_by'
            rest = {r['required']: r['by']}
        elif 'if' in r:
            name = 'required_if'
            rest = [r['if'], r['equals'], r['required']]
    else:
        for ding in ('exclusive', 'together', 'one_of'):
            if ding in r:

                if isinstance(r[ding], string_types):
                    rest = r[ding].spit(',')
                elif not isinstance(r[ding], Sequence):
                    raise TypeError('must be a list!')
                else:
                    rest = r[ding]

                if len(rest) < 2:
                    raise TypeError('must have multiple elements')

                if ding == 'exclusive':
                    name = 'mutually_exclusive'
                else:
                    name = 'required_%s' % ding
                break
            else:
                raise Exception('unknown restriction!')
    return rest


def add_options_from_doc(argspec, options, deprecate=None):
    """ Add option doc entries into argspec """
    for n, o in sorted(options.items()):
        argspec[n] = option_to_spec(o, deprecate)


def get_options_from_doc(options, deprecate=None):
    """ Add option doc entries into argspec """
    argspec = {}
    add_options_from_doc(argspec, options, deprecate)
    return argspec


def add_restrictions_from_doc(restrict_args, restrictions):
    """ add restriction doc entries into argspec """
    for r in restrictions:
        restrict_args.append(restriction_to_spec(r))


def get_restrictions_from_doc(restrictions):
    """ add restriction doc entries into argspec """
    reargs = {}
    add_restrictions_from_doc(reargs, restrictions)
    return reargs


def validate_spec(spec, restrictions, task_args):

    validator = ArgumentSpecValidator(spec, **restrictions)
    return validator.validate(task_args)


def validate_spec_from_plugin(plugin):
    # take plugin object (name?), get docs and process with above
    pass
