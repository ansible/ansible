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


# def opts_docs(cli, name):
def opts_docs(cli_class_name, cli_module_name):
    ''' generate doc structure from options '''

    cli_name = 'ansible-%s' % cli_module_name
    if cli_module_name == 'adhoc':
        cli_name = 'ansible'

    print('cli_class_name: %s' % cli_class_name)
    print('cli_name: %s' % cli_name)
    # WIth no action/subcommand
    # shared opts set
    # instantiate each cli and ask its options
    cli_klass = getattr(__import__("ansible.cli.%s" % cli_module_name,
                                   fromlist=[cli_class_name]), cli_class_name)
    cli = cli_klass([])

    # parse the common options
    try:
        cli.parse()
    except:
        # no options passed, we expect errors
        pass

    # base/common cli info
    docs = {
        'cli': cli_module_name,
        'cli_name': cli_name,
        'usage': cli.parser.usage,
        'short_desc': cli.parser.description,
        'long_desc': trim_docstring(cli.__doc__),
        'actions': {},
    }
    option_info = {'option_names': [],
                   'options': []}

    for extras in ('ARGUMENTS'):
        if hasattr(cli, extras):
            docs[extras.lower()] = getattr(cli, extras)

    common_opts = opt_doc_list(cli)

    shared_opt_names = []
    for opt in common_opts:
        shared_opt_names.extend(opt.get('options', []))

    option_info['options'] = common_opts
    option_info['option_names'] = shared_opt_names

    docs.update(option_info)

    # now for each action/subcommand
    # force populate parser with per action options

    print('cli_class_name: %s type: %s' % (cli_class_name, type(cli_class_name)))

    # use class attrs not the attrs on a instance (not that it matters here...)
    print(getattr(cli_klass, 'VALID_ACTIONS', ()))
    for action in getattr(cli_klass, 'VALID_ACTIONS', ()):

        # instantiate each cli and ask its options
        action_cli_klass = getattr(__import__("ansible.cli.%s" % cli_module_name,
                                              fromlist=[cli_class_name]), cli_class_name)
        # init with args with action added?
        cli = action_cli_klass([])
        cli.args.append(action)

        try:
            cli.parse()
        except:
            # no options passed, we expect errors
            pass

        # FIXME/TODO: needed?
        # avoid dupe errors
        cli.parser.set_conflict_handler('resolve')

        cli.set_action()

        action_info = {'option_names': [],
                       #'uncommon_options': [],
                       'options': []}
        # docs['actions'][action] = {}
        # docs['actions'][action]['name'] = action
        action_info['name'] = action
        action_info['desc'] = trim_docstring(getattr(cli, 'execute_%s' % action).__doc__)

        # docs['actions'][action]['desc'] = getattr(cli, 'execute_%s' % action).__doc__.strip()
        action_doc_list = opt_doc_list(cli)

        uncommon_options = []
        for action_doc in action_doc_list:
            # uncommon_options = []
            print('\naction: %s action_doc: %s' % (action, action_doc))

            for option_alias in action_doc.get('options', []):

                print('option_alias: %s' % option_alias)

                if option_alias in shared_opt_names:
                    continue

                action_info['option_names'].append(option_alias)
                uncommon_options.append(action_doc)

            action_info['options'] = uncommon_options

        #if 'options' not in action_info:
        #    action_info['options'] = action_doc_list

        #if 'uncommon_options' not in docs['actions'][action]:
        #    docs['actions'][action]['uncommon_options'] = []
        #for uncommon_option in uncommon_options:
        #    if uncommon_option not in docs['actions'][action]['uncommon_options']:
        #        docs['actions'][action]['uncommon_options'].append(uncommon_option)

        print('foo')
        # TODO: mv per-action stuff to method, return action_info
        docs['actions'][action] = action_info

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

        cli_name = os.path.splitext(binary)[0]
        print("Found CLI %s" % cli_name)

        if cli_name == 'adhoc':
            cli_class_name = 'AdHocCLI'
            # myclass = 'AdHocCLI'
            output[cli_name] = 'ansible.1.asciidoc.in'
        else:
            # myclass = "%sCLI" % libname.capitalize()
            cli_class_name = "%sCLI" % cli_name.capitalize()
            output[cli_name] = 'ansible-%s.1.asciidoc.in' % cli_name

        # FIXME:
        allvars[cli_name] = opts_docs(cli_class_name, cli_name)

    cli_list = allvars.keys()

    templates = {'man.j2': {'out_dir': '../man/man1/%s',
                            'out_file_format': '%s.1.asciidoc.in'},
                 'cli_rst.j2': {'out_dir': '../docsite/rst/cli/%s',
                                'out_file_format': '%s.rst'}}

    for cli_name in cli_list:

        # template it!
        env = Environment(loader=FileSystemLoader('../templates'))
        for template_file in templates:
            # print('template_file: %s' % template_file)
            # import pdb; pdb.set_trace()  # XXX BREAKPOINT
            template = env.get_template(template_file)

            # add rest to vars
            # pprint.pprint(allvars)
            tvars = allvars[cli_name]
            tvars['cli_list'] = cli_list
            tvars['cli'] = cli_name
            if '-i' in tvars['options']:
                print('uses inventory')

            manpage = template.render(tvars)
            filename = templates[template_file]['out_dir'] % templates[template_file]['out_file_format'] % tvars['cli_name']
            # output[cli_name]
            # print('filename: %s %s' % (filename, os.path.realpath(filename)))
            with open(filename, 'wb') as f:
                f.write(to_bytes(manpage))
                print("Wrote doc to %s" % filename)
