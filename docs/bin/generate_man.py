#!/usr/bin/env python

import os
import sys

from jinja2 import Environment, FileSystemLoader

from ansible.module_utils._text import to_bytes


# from https://www.python.org/dev/peps/pep-0257/
def trim_docstring(docstring):
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxint
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxint:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


def get_options(optlist):
    ''' get actual options '''

    opts = []
    for opt in optlist:
        res = {
            'desc': opt.help,
            'options': opt._short_opts + opt._long_opts
        }
        if opt.action == 'store':
            res['arg'] = opt.dest.upper()
        opts.append(res)

    return opts


def opt_doc_list(cli):
    ''' iterate over options lists '''

    results = []
    for optg in cli.parser.option_groups:
        results.extend(get_options(optg.option_list))

    results.extend(get_options(cli.parser.option_list))

    return results


import pprint
def opts_docs(cli, name):
    ''' generate doc structure from options '''
    if name == 'adhoc':
        cli_name = 'ansible'
    else:
        cli_name = 'ansible-%s' % name

    # cli info
    docs = {
        'cli': name,
        'cli_name': cli_name,
        'usage': cli.parser.usage,
        'short_desc': cli.parser.description,
        'long_desc': trim_docstring(cli.__doc__),
        'actions': {'foo': 1232},
    }

    # shared opts set
    common_opts = opt_doc_list(cli)

    shared_opt_names = []
    for opt in common_opts:
        shared_opt_names.extend(opt.get('options', []))

    # force populate parser with per action options
    if cli.VALID_ACTIONS:
        docs['actions'] = {}
        # avoid dupe errors
        cli.parser.set_conflict_handler('resolve')
        for action in cli.VALID_ACTIONS:
            cli.args.append(action)
            cli.set_action()
            docs['actions'][action] = {}
            docs['actions'][action]['name'] = action
            docs['actions'][action]['desc'] = trim_docstring(getattr(cli, 'execute_%s' % action).__doc__)
            #docs['actions'][action]['desc'] = getattr(cli, 'execute_%s' % action).__doc__.strip()
            action_doc_list = opt_doc_list(cli)

            uncommon_options = []
            for action_doc in action_doc_list:
                uncommon_options = []
                print('\naction: %s action_doc: %s' % (action, action_doc))
                for option_alias in action_doc.get('options', []):
                    print('option_alias: %s' % option_alias)
                    if option_alias in shared_opt_names:
                        continue
                    if 'option_names' not in docs['actions'][action]:
                        docs['actions'][action]['option_names'] = []
                    docs['actions'][action]['option_names'].append(option_alias)
                    uncommon_options.append(action_doc)

                if 'uncommon_options' not in docs['actions'][action]:
                    docs['actions'][action]['uncommon_options'] = []
                docs['actions'][action]['uncommon_options'] = uncommon_options

            if 'options' not in docs['actions'][action]:
                docs['actions'][action]['options'] = action_doc_list
            #if 'uncommon_options' not in docs['actions'][action]:
            #    docs['actions'][action]['uncommon_options'] = []
            #for uncommon_option in uncommon_options:
            #    if uncommon_option not in docs['actions'][action]['uncommon_options']:
            #        docs['actions'][action]['uncommon_options'].append(uncommon_option)

    docs['options'] = opt_doc_list(cli)
    print('\n\n')
    pprint.pprint(docs)

    return docs


if __name__ == '__main__':

    template_file = 'man.j2'

    # need to be in right dir
    os.chdir(os.path.dirname(__file__))

    allvars = {}
    output = {}
    cli_list = []
    for binary in os.listdir('../../lib/ansible/cli'):

        if not binary.endswith('.py'):
            continue
        elif binary == '__init__.py':
            continue

        libname = os.path.splitext(binary)[0]
        print("Found CLI %s" % libname)

        if libname == 'adhoc':
            myclass = 'AdHocCLI'
            output[libname] = 'ansible.1.asciidoc.in'
        else:
            myclass = "%sCLI" % libname.capitalize()
            output[libname] = 'ansible-%s.1.asciidoc.in' % libname

        # instantiate each cli and ask its options
        mycli = getattr(__import__("ansible.cli.%s" % libname, fromlist=[myclass]), myclass)
        cli_object = mycli([])
        try:
            cli_object.parse()
        except:
            # no options passed, we expect errors
            pass

        allvars[libname] = opts_docs(cli_object, libname)

        for extras in ('ARGUMENTS'):
            if hasattr(cli_object, extras):
                allvars[libname][extras.lower()] = getattr(cli_object, extras)

    cli_list = allvars.keys()

    templates = {'man.j2': {'out_dir': '../man/man1/%s',
                            'out_file_format': '%s.1.asciidoc.in'},
                 'cli_rst.j2': {'out_dir': '../docsite/rst/cli/%s',
                                'out_file_format': '%s.rst'}}

    for libname in cli_list:

        # template it!
        env = Environment(loader=FileSystemLoader('../templates'))
        for template_file in templates:
            # print('template_file: %s' % template_file)
            # import pdb; pdb.set_trace()  # XXX BREAKPOINT
            template = env.get_template(template_file)

            # add rest to vars
            # pprint.pprint(allvars)
            tvars = allvars[libname]
            tvars['cli_list'] = cli_list
            tvars['cli'] = libname
            if '-i' in tvars['options']:
                print('uses inventory')

            manpage = template.render(tvars)
            filename = templates[template_file]['out_dir'] % templates[template_file]['out_file_format'] % tvars['cli_name']
            # output[libname]
            # print('filename: %s %s' % (filename, os.path.realpath(filename)))
            with open(filename, 'wb') as f:
                f.write(to_bytes(manpage))
                print("Wrote doc to %s" % filename)
