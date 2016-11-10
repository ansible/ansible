#!/usr/bin/env python

# A helper script that patches the simple usage of "type(foo) == bar" in modules.

import os
import re
import shutil
import sys
import subprocess
import tempfile

# basic matcher for instances of type()
TYPE_REGEX = re.compile(r'.*\stype\(.*')
# each of these regexes identifies the different possible operators
r1 = re.compile(r'.*\stype\(.*\)\s+is\s+(int|bool|str|dict|list|tuple|MethodType|vim\..*):')
r2 = re.compile(r'.*\stype\(.*\)\s+is\snot\s+(int|bool|str|dict|list|tuple|MethodType|vim\..*):')
r3 = re.compile(r'.*\stype\(.*\)\s+==\s+(int|bool|str|dict|list|tuple|MethodType|vim\..*):')
r4 = re.compile(r'.*\stype\(.*\)\s+!=\s+(int|bool|str|dict|list|tuple|MethodType|vim\..*):')
r5 = re.compile(r'.*\stype\(.*\)\s+is\s+not\s+(int|bool|str|dict|list|tuple|MethodType|vim\..*):')

def run_command(args):
    p = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
    (so, se) = p.communicate()
    return (p.returncode, so, se)

def find_modules(basepath):
    cmd = 'find %s -type f -name "*.py"' % basepath
    (rc, so, se) = run_command(cmd)
    files = [x.strip() for x in so.split('\n') if x.strip()]
    files = [x for x in files if not x.endswith('__init__.py')]
    files = [x for x in files if not '.git' in x]
    files = [x for x in files if not '/test/' in x]
    return files

def isbad(rawtext):
    flag = False
    lines = rawtext.split('\n')
    for idx,x in enumerate(lines):
        if TYPE_REGEX.match(x):
            flag = True
            break
    return flag

def create_fix(rawtext, oldfile, newfile):

    ## FIX
    #         if type(tags) is str:
    #     elif type(value_in)  is list:
    #     elif isinstance(value_in)  is list, elif type(value_in)  is list):
    #        elif type(value) == bool

    ## WONTFIX
    #        module.fail_json(msg='Invalid rule parameter type [%s].' % type(rule))
    #     p = type('Params', (), module.params)

    # Match each different operator and split the components accordingly
    diff = None
    lines = [x for x in rawtext.split('\n')]
    for idx,x in enumerate(lines):
        if TYPE_REGEX.match(x):
            print('\t#%s%s' % (idx,x))
            x2 = None
            if r1.match(x):
                start = x.find('type(')
                isidx = x.find(') is ')
                padding = x[:start]
                val = x[start+5:isidx]
                etype = x[isidx+5:-1]
                x2 = '%sisinstance(%s, %s):' % (padding, val, etype)
            elif r2.match(x):
                start = x.find('type(')
                isidx = x.find(') is not')
                padding = x[:start]
                val = x[start+5:isidx]
                etype = x[isidx+9:-1]
                x2 = '%snot isinstance(%s, %s):' % (padding, val, etype)
            elif r3.match(x):
                start = x.find('type(')
                isidx = x.find(') == ')
                padding = x[:start]
                val = x[start+5:isidx]
                etype = x[isidx+5:-1]
                x2 = '%sisinstance(%s, %s):' % (padding, val, etype)
            elif r4.match(x):
                start = x.find('type(')
                isidx = x.find(') != ')
                padding = x[:start]
                val = x[start+5:isidx]
                etype = x[isidx+5:-1]
                x2 = '%sisinstance(%s, %s):' % (padding, val, etype)
            elif r5.match(x):
                start = x.find('type(')
                isidx = x.find(') is not')
                padding = x[:start]
                val = x[start+5:isidx]
                etype = x[isidx+5:-1]
                x2 = '%sisinstance(%s, %s):' % (padding, val, etype)

            else:
                print('NO MATCH ON %s' % x)
                import epdb; epdb.st()

            print('\t#%s%s' % (idx,x2))
            if x2:
                lines[idx] = x2

    # Create a patch with the new revisions
    newtxt = '\n'.join(lines)
    if newtxt != rawtext:
        with open(newfile, 'wb') as f:
            f.write(newtxt)
        diffcmd = 'diff %s %s' % (oldfile, newfile)
        (rc, so, se) = run_command(diffcmd)
        print(str(so) + str(se))

        # Copy the changed file over if the user accepts
        choice = raw_input('Does this look good? (y|n)')
        if choice == 'y':
            shutil.move(newfile, oldfile)

    return diff    

def main():
    print(sys.argv)
    mfiles = find_modules(sys.argv[1])

    total = len(mfiles) - 1
    for idm,mfile in enumerate(mfiles):
        print("CHECKING (%s|%s) %s" % (idm, total, mfile))
        with open(mfile, 'rb') as f:
            rawtext = f.read()
        flag = isbad(rawtext)
        print('\tflagged=%s' % flag)

        if flag:
            tfo,tfn = tempfile.mkstemp()
            create_fix(rawtext, mfile, tfn)

if __name__ == "__main__":
    main()
    
