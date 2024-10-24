#!/usr/bin/env python

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# This file is part of Ansible, a free software under the GNU General Public License

# This script is for testing Ansible modules without going through the entire Ansible engine.
# It helps developers test modules directly. Example usage is provided in the comments above.

from __future__ import annotations

import glob
import optparse
import os
import subprocess
import sys
import traceback
import shutil
from pathlib import Path

from ansible.release import __version__
import ansible.utils.vars as utils_vars
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.utils.jsonify import jsonify
from ansible.parsing.splitter import parse_kv
from ansible.plugins.loader import init_plugin_loader
from ansible.executor import module_common
import ansible.constants as C
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.template import Templar

import json


## Parse command-line arguments for testing the Ansible module
def parse():
    """parse command line

    :return : (options, args)"""
    parser = optparse.OptionParser()

    parser.usage = "%prog -[options] (-h for help)"

    parser.add_option('-m', '--module-path', dest='module_path',
                      help="REQUIRED: full path of module source to execute")
    parser.add_option('-a', '--args', dest='module_args', default="",
                      help="module argument string")
    parser.add_option('-D', '--debugger', dest='debugger',
                      help="path to python debugger (e.g. /usr/bin/pdb)")
    parser.add_option('-I', '--interpreter', dest='interpreter',
                      help="path to interpreter to use for this module"
                      " (e.g. ansible_python_interpreter=/usr/bin/python)",
                      metavar='INTERPRETER_TYPE=INTERPRETER_PATH',
                      default="ansible_python_interpreter=%s" %
                      (sys.executable if sys.executable else '/usr/bin/python'))
    parser.add_option('-c', '--check', dest='check', action='store_true',
                      help="run the module in check mode")
    parser.add_option('-n', '--noexecute', dest='execute', action='store_false',
                      default=True, help="do not run the resulting module")
    parser.add_option('-o', '--output', dest='filename',
                      help="Filename for resulting module",
                      default="~/.ansible_module_generated")
    options, args = parser.parse_args()
    if not options.module_path:
        parser.print_help()
        sys.exit(1)
    else:
        return options, args


## Write module arguments to a file (old-style module's use)
def write_argsfile(argstring, json=False):
    """ Write args to a file for old-style module's use. """
    argspath = Path("~/.ansible_test_module_arguments").expanduser()
    if json:
        args = parse_kv(argstring)
        argstring = jsonify(args)
    argspath.write_text(argstring)
    return argspath


## Get the interpreters for running the module, ensuring proper format
def get_interpreters(interpreter):
    result = dict()
    if interpreter:
        if '=' not in interpreter:
            print("interpreter must by in the form of ansible_python_interpreter=/usr/bin/python")
            sys.exit(1)
        interpreter_type, interpreter_path = interpreter.split('=')
        if not interpreter_type.startswith('ansible_'):
            interpreter_type = 'ansible_%s' % interpreter_type
        if not interpreter_type.endswith('_interpreter'):
            interpreter_type = '%s_interpreter' % interpreter_type
        result[interpreter_type] = interpreter_path
    return result


## Simulate Ansible's process to set up the module for testing
def boilerplate_module(modfile, args, interpreters, check, destfile):
    """ simulate what ansible does with new style modules """
    loader = DataLoader()

    complex_args = {}

    # default selinux fs list is pass in as _ansible_selinux_special_fs arg
    complex_args['_ansible_selinux_special_fs'] = C.DEFAULT_SELINUX_SPECIAL_FS
    complex_args['_ansible_tmpdir'] = C.DEFAULT_LOCAL_TMP
    complex_args['_ansible_keep_remote_files'] = C.DEFAULT_KEEP_REMOTE_FILES
    complex_args['_ansible_version'] = __version__

    # Load arguments if they are in YAML/JSON format
    if args.startswith("@"):
        complex_args = utils_vars.combine_vars(complex_args, loader.load_from_file(args[1:]))
        args = ''
    elif args.startswith("{"):
        complex_args = utils_vars.combine_vars(complex_args, loader.load(args))
        args = ''

    # Add parsed arguments to the module execution
    if args:
        parsed_args = parse_kv(args)
        complex_args = utils_vars.combine_vars(complex_args, parsed_args)

    task_vars = interpreters

    if check:
        complex_args['_ansible_check_mode'] = True

    modname = os.path.basename(modfile)
    modname = os.path.splitext(modname)[0]
    (module_data, module_style, shebang) = module_common.modify_module(
        modname,
        modfile,
        complex_args,
        Templar(loader=loader),
        task_vars=task_vars
    )

    if module_style == 'new' and '_ANSIBALLZ_WRAPPER = True' in to_native(module_data):
        module_style = 'ansiballz'

    modfile2_path = os.path.expanduser(destfile)
    print("* including generated source, if any, saving to: %s" % modfile2_path)
    if module_style not in ('ansiballz', 'old'):
        print("* this may offset any line numbers in tracebacks/debuggers!")
    with open(modfile2_path, 'wb') as modfile2:
        modfile2.write(module_data)
    modfile = modfile2_path

    return (modfile2_path, modname, module_style)


## Extract and setup an AnsiBallZ module for execution
def ansiballz_setup(modfile, modname, interpreters):
    os.system("chmod +x %s" % modfile)

    if 'ansible_python_interpreter' in interpreters:
        command = [interpreters['ansible_python_interpreter']]
    else:
        command = []
    command.extend([modfile, 'explode'])

    cmd = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = cmd.communicate()
    out, err = to_text(out, errors='surrogate_or_strict'), to_text(err)
    lines = out.splitlines()
    if len(lines) != 2 or 'Module expanded into' not in lines[0]:
        print("*" * 35)
        print("INVALID OUTPUT FROM ANSIBALLZ MODULE WRAPPER")
        print(out)
        sys.exit(err)
    debug_dir = lines[1].strip()

    core_dirs = glob.glob(os.path.join(debug_dir, 'ansible/modules'))
    collection_dirs = glob.glob(os.path.join(debug_dir, 'ansible_collections/*/*/plugins/modules'))

    # Find and return the module
    for module_dir in core_dirs + collection_dirs:
        for dirname, directories, filenames in os.walk(module_dir):
            for filename in filenames:
                if filename == modname + '.py':
                    modfile = os.path.join(dirname, filename)
                    break

    argsfile = os.path.join(debug_dir, 'args')

    print("* ansiballz module detected; extracted module source to: %s" % debug_dir)
    return modfile, argsfile


## Execute the test on the module, running it and piping its output
def runtest(modfile, argspath, modname, module_style, interpreters):
    """Test run a module, piping it's output for reporting."""
    invoke = ""
    if module_style == 'ansiballz':
        modfile, argspath = ansiballz_setup(modfile, modname, interpreters)
        if 'ansible_python_interpreter' in interpreters:
            invoke = "%s " % interpreters['ansible_python_interpreter']

    os.system("chmod +x %s" % modfile)

    invoke = "%s%s" % (invoke, modfile)
    if argspath is not None:
        invoke = "%s %s" % (invoke, argspath)

    cmd = subprocess.Popen(invoke, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = cmd.communicate()
    out, err = to_text(out), to_text(err)

    try:
        print("*" * 35)
        print("RAW OUTPUT")
        print(out)
        print(err)
        results = json.loads(out)
    except Exception:
        print("*" * 35)
        print("INVALID OUTPUT FORMAT")
        print(out)
        traceback.print_exc()
        sys.exit(1)

    print("*" * 35)
    print("PARSED OUTPUT")
    print(jsonify(results, format=True))


## Debug the module with an interactive console debugger
def rundebug(debugger, modfile, argspath, modname, module_style, interpreters):
    """Run interactively with console debugger."""

    if module_style == 'ansiballz':
        modfile, argspath = ansiballz_setup(modfile, modname, interpreters)

    if argspath is not None:
        subprocess.call("%s %s %s" % (debugger, modfile, argspath), shell=True)
    else:
        subprocess.call("%s %s" % (debugger, modfile), shell=True)


if __name__ == '__main__':
    options, args = parse()
    interpreters = get_interpreters(options.interpreter)
    argspath = write_argsfile(options.module_args)

    modfile, modname, module_style = boilerplate_module(
        options.module_path,
        options.module_args,
        interpreters,
        options.check,
        options.filename
    )

    if options.debugger:
        rundebug(
            options.debugger,
            modfile,
            argspath,
            modname,
            module_style,
            interpreters
        )
    elif options.execute:
        runtest(
            modfile,
            argspath,
            modname,
            module_style,
            interpreters
        )
