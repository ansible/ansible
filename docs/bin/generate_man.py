#!/usr/bin/env python

import os
import sys

from jinja2 import Environment, FileSystemLoader

from ansible.module_utils._text import to_bytes


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


def opts_docs(cli, name):
    ''' generate doc structure from options '''

    # cli name
    if '-' in name:
        name = name.split('-')[1]
    else:
        name = 'adhoc'

    # cli info
    docs = {
        'cli': name,
        'usage': cli.parser.usage,
        'short_desc': cli.parser.description,
        'long_desc': cli.__doc__,
    }

    # force populate parser with per action options
    if cli.VALID_ACTIONS:
        docs['actions'] = {}
        # avoid dupe errors
        cli.parser.set_conflict_handler('resolve')
        for action in cli.VALID_ACTIONS:
            cli.args.append(action)
            cli.set_action()
            docs['actions'][action] = getattr(cli, 'execute_%s' % action).__doc__

    docs['options'] = opt_doc_list(cli)

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
    for libname in cli_list:

        # template it!
        env = Environment(loader=FileSystemLoader('../templates'))
        template = env.get_template('man.j2')

        # add rest to vars
        tvars = allvars[libname]
        tvars['cli_list'] = cli_list
        tvars['cli'] = libname
        if '-i' in tvars['options']:
            print('uses inventory')

        manpage = template.render(tvars)
        filename = '../man/man1/%s' % output[libname]
        with open(filename, 'wb') as f:
            f.write(to_bytes(manpage))
            print("Wrote man docs to %s" % filename)
