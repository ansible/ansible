# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import codecs
import jinja2
from jinja2.runtime import StrictUndefined
from jinja2.exceptions import TemplateSyntaxError
from ansible import errors
import ansible.constants as C
import time
import datetime
import pwd
import ast
import plugins
import filesystem

FILTER_PLUGINS = None
_LISTRE = re.compile(r"(\w+)\[(\d+)\]")
JINJA2_OVERRIDE='#jinja2:'

class Globals(object):

    FILTERS = None

    def __init__(self):
        pass

def _get_filters():
    ''' return filter plugin instances '''

    if Globals.FILTERS is not None:
        return Globals.FILTERS

    my_plugins = [ x for x in plugins.filter_loader.all()]
    filters = {}
    for fp in my_plugins:
        filters.update(fp.filters())
    Globals.FILTERS = filters

    return Globals.FILTERS

def _get_extensions():
    ''' return jinja2 extensions to load '''
    # if some extensions are set via jinja_extensions in ansible.cfg, we try
    # to load them with the jinja environment
    jinja_exts = []
    if C.DEFAULT_JINJA2_EXTENSIONS:
        # Let's make sure the configuration directive doesn't contain spaces
        # and split extensions in an array
        jinja_exts = C.DEFAULT_JINJA2_EXTENSIONS.replace(" ", "").split(',')
    return jinja_exts

def lookup(name, *args, **kwargs):
    instance = plugins.lookup_loader.get(name.lower(), basedir=kwargs.get('basedir',None))
    vars = kwargs.get('vars', None)

    if instance is not None:
        ran = instance.run(*args, inject=vars, **kwargs)
        return ",".join(ran)
    else:
        raise errors.AnsibleError("lookup plugin (%s) not found" % name)

def _legacy_varFindLimitSpace(basedir, vars, space, part, lookup_fatal, depth, expand_lists):
    ''' limits the search space of space to part

    basically does space.get(part, None), but with
    templating for part and a few more things

    DEPRECATED
    LEGACY VARIABLES ARE SLATED FOR REMOVAL IN ANSIBLE 1.5
    use {{ foo }} INSTEAD
    '''

    if not C.DEFAULT_LEGACY_PLAYBOOK_VARIABLES:
        raise Exception("we should not be here")

    # Previous part couldn't be found, nothing to limit to
    if space is None:
        return space
    # A part with escaped .s in it is compounded by { and }, remove them
    if part[0] == '{' and part[-1] == '}':
        part = part[1:-1]
    # Template part to resolve variables within (${var$var2})
    part = legacy_varReplace(basedir, part, vars, lookup_fatal=lookup_fatal, depth=depth + 1, expand_lists=expand_lists)

    # Now find it
    if part in space:
        space = space[part]
    elif "[" in part:
        m = _LISTRE.search(part)
        if not m:
            return None
        else:
            try:
                space = space[m.group(1)][int(m.group(2))]
            except (KeyError, IndexError):
                return None
    else:
        return None

    # if space is a string, check if it's a reference to another variable
    if isinstance(space, basestring):
        space = template(basedir, space, vars, lookup_fatal=lookup_fatal, depth=depth + 1, expand_lists=expand_lists)

    return space

def _legacy_varFind(basedir, text, vars, lookup_fatal, depth, expand_lists):
    ''' Searches for a variable in text and finds its replacement in vars

    The variables can have two formats;
    - simple, $ followed by alphanumerics and/or underscores
    - complex, ${ followed by alphanumerics, underscores, periods, braces and brackets, ended by a }

    Examples:
    - $variable: simple variable that will have vars['variable'] as its replacement
    - ${variable.complex}: complex variable that will have vars['variable']['complex'] as its replacement
    - $variable.complex: simple variable, identical to the first, .complex ignored

    Complex variables are broken into parts by separating on periods, except if enclosed in {}.
    ${variable.{fully.qualified.domain}} would be parsed as two parts, variable and fully.qualified.domain,
    whereas ${variable.fully.qualified.domain} would be parsed as four parts.

    Returns a dict(replacement=<value in vars>, start=<index into text where the variable stated>,
        end=<index into text where the variable ends>)
    or None if no variable could be found in text. If replacement is None, it should be replaced with the
    original data in the caller.

    DEPRECATED
    LEGACY VARIABLES ARE SLATED FOR REMOVAL IN ANSIBLE 1.5
    use {{ foo }} INSTEAD
    '''

    # short circuit this whole function if we have specified we don't want
    # legacy var replacement
    if not C.DEFAULT_LEGACY_PLAYBOOK_VARIABLES:
        raise Exception("we should not be here")

    start = text.find("$")
    if start == -1:
        return None
    # $ as last character
    if start + 1 == len(text):
        return None
    # Escaped var
    if start > 0 and text[start - 1] == '\\':
        return {'replacement': '$', 'start': start - 1, 'end': start + 1}

    var_start = start + 1
    if text[var_start] == '{':
        is_complex = True
        brace_level = 1
        var_start += 1
    else:
        is_complex = False
        brace_level = 1

    # is_lookup is true for $FILE(...) and friends
    is_lookup = False
    lookup_plugin_name = None
    end = var_start

    # part_start is an index of where the current part started
    part_start = var_start
    space = vars

    while end < len(text) and (((is_lookup or is_complex) and brace_level > 0) or (not is_complex and not is_lookup)):

        if text[end].isalnum() or text[end] == '_':
            pass
        elif not is_complex and not is_lookup and text[end] == '(' and text[part_start:end].isupper():
            is_lookup = True
            lookup_plugin_name = text[part_start:end]
            part_start = end + 1
        elif is_lookup and text[end] == '(':
            brace_level += 1
        elif is_lookup and text[end] == ')':
            brace_level -= 1
        elif is_lookup:
            # lookups are allowed arbitrary contents
            pass
        elif is_complex and text[end] == '{':
            brace_level += 1
        elif is_complex and text[end] == '}':
            brace_level -= 1
        elif is_complex and text[end] in ('$', '[', ']', '-'):
            pass
        elif is_complex and text[end] == '.':
            if brace_level == 1:
                space = _legacy_varFindLimitSpace(basedir, vars, space, text[part_start:end], lookup_fatal, depth, expand_lists)
                part_start = end + 1
        else:
            # This breaks out of the loop on non-variable name characters
            break
        end += 1

    var_end = end

    # Handle "This has $ in it"
    if var_end == part_start:
        return {'replacement': None, 'start': start, 'end': end}

    # Handle lookup plugins
    if is_lookup:
        # When basedir is None, handle lookup plugins later
        if basedir is None:
            return {'replacement': None, 'start': start, 'end': end}
        var_end -= 1
        args = text[part_start:var_end]
        if lookup_plugin_name == 'LOOKUP':
            lookup_plugin_name, args = args.split(",", 1)
            args = args.strip()
        # args have to be templated
        args = legacy_varReplace(basedir, args, vars, lookup_fatal, depth + 1, True)
        if isinstance(args, basestring) and args.find('$') != -1:
            # unable to evaluate something like $FILE($item) at this point, try to evaluate later
            return None


        instance = plugins.lookup_loader.get(lookup_plugin_name.lower(), basedir=basedir)
        if instance is not None:
            try:
                replacement = instance.run(args, inject=vars)
                if expand_lists:
                    replacement = ",".join([unicode(x) for x in replacement])
            except:
                if not lookup_fatal:
                    replacement = None
                else:
                    raise

        else:
            replacement = None
        return dict(replacement=replacement, start=start, end=end)

    if is_complex:
        var_end -= 1
        if text[var_end] != '}' or brace_level != 0:
            return None
    space = _legacy_varFindLimitSpace(basedir, vars, space, text[part_start:var_end], lookup_fatal, depth, expand_lists)
    return dict(replacement=space, start=start, end=end)

def legacy_varReplace(basedir, raw, vars, lookup_fatal=True, depth=0, expand_lists=False):
    ''' Perform variable replacement of $variables in string raw using vars dictionary
    
    DEPRECATED
    LEGACY VARIABLES ARE SLATED FOR REMOVAL IN ANSIBLE 1.5
    use {{ foo }} INSTEAD
    '''

    if not C.DEFAULT_LEGACY_PLAYBOOK_VARIABLES:
        raise Exception("we should not be here")

    # this code originally from yum (and later modified a lot)

    orig = raw

    if not isinstance(raw, unicode):
        raw = raw.decode("utf-8")

    #if (depth > 20):
    #    raise errors.AnsibleError("template recursion depth exceeded")

    done = [] # Completed chunks to return

    while raw:
        m = _legacy_varFind(basedir, raw, vars, lookup_fatal, depth, expand_lists)
        if not m:
            done.append(raw)
            break

        # Determine replacement value (if unknown variable then preserve
        # original)

        replacement = m['replacement']
        if expand_lists and isinstance(replacement, (list, tuple)):
            replacement = ",".join([str(x) for x in replacement])
        if isinstance(replacement, (str, unicode)):
            replacement = legacy_varReplace(basedir, replacement, vars, lookup_fatal, depth=depth+1, expand_lists=expand_lists)
        if replacement is None:
            replacement = raw[m['start']:m['end']]

        start, end = m['start'], m['end']
        done.append(raw[:start])          # Keep stuff leading up to token
        done.append(unicode(replacement)) # Append replacement value
        raw = raw[end:]                   # Continue with remainder of string

    result = ''.join(done)

    previous_old_style_vars = orig.count('$')
    new_old_style_vars = result.count('$')
    if previous_old_style_vars != new_old_style_vars:
        from ansible import utils
        utils.deprecated("Legacy variable substitution, such as using ${foo} or $foo instead of {{ foo }} is currently valid but will be phased out and has been out of favor since version 1.2. This is the last of legacy features on our deprecation list. You may continue to use this if you have specific needs for now","1.5")
    return result

def fix_ds(basedir, vars, original, depth=0):
    ''' used to massage the input dictionary to avoid surprises later and minimize more complex recursive problems '''
    while (depth < 20):
        depth = depth + 1 
        vars2 = _fix_ds(basedir, vars, original, depth=depth)
        if vars2 == vars:
            return vars
        vars = vars2
    return vars

def _fix_ds(basedir, vars, original, depth=0):
    if isinstance(vars, dict):
        return dict([ (k, fix_ds(basedir, v, original, depth=depth+1)) for (k,v) in vars.iteritems() ])
    if isinstance(vars, (dict, tuple)):
        return [ fix_ds(basedir, x,original, depth=depth+1) for x in vars ]
    if isinstance(vars, basestring) and "{{" in vars and not "|" in vars and not "lookup(" in vars:
        return lightweight_var_template(basedir, vars, original)
    return vars

def lightweight_var_template(basedir, input, vars):
    return template_from_string(basedir, input, vars, fail_on_undefined=False, lookups=True, filters=True)

def template(basedir, input_value, vars, lookup_fatal=True, depth=-1, expand_lists=True, convert_bare=False, fail_on_undefined=False, filter_fatal=True, lookups=True):

    vars = fix_ds(basedir, vars, vars.copy())

    last_time = input_value
    result = None
    changed = True
    while changed:
        result = _template(
            basedir, 
            last_time, 
            vars, 
            lookup_fatal=lookup_fatal, 
            depth=depth, 
            expand_lists=expand_lists, 
            convert_bare=convert_bare, 
            fail_on_undefined=fail_on_undefined,
            filter_fatal=filter_fatal,
            lookups=lookups,
        )
        if last_time == result:
            changed = False
        last_time = result
        depth = depth + 1
        if depth > 20:
            raise errors.AnsibleError("template recursion depth exceeded")
    return result 

def _template(basedir, varname, vars, lookup_fatal=True, depth=0, expand_lists=True, convert_bare=False, fail_on_undefined=False, filter_fatal=True, lookups=True):
    ''' templates a data structure by traversing it and substituting for other data structures '''

    try:
        if convert_bare and isinstance(varname, basestring):
            first_part = varname.split(".")[0].split("[")[0]
            if first_part in vars and '{{' not in varname and '$' not in varname:
                varname = "{{%s}}" % varname
    
        if isinstance(varname, basestring):
            if '{{' in varname or '{%' in varname:
                varname = template_from_string(basedir, varname, vars, fail_on_undefined, lookups=lookups)
    
            if not C.DEFAULT_LEGACY_PLAYBOOK_VARIABLES:
                return varname
 
            if not '$' in varname:
                return varname
            m = _legacy_varFind(basedir, varname, vars, lookup_fatal, depth, expand_lists)
            if not m:
                return varname
            if m['start'] == 0 and m['end'] == len(varname):
                if m['replacement'] is not None:
                    return template(basedir, m['replacement'], vars, lookup_fatal, depth, expand_lists)
                else:
                    return varname
            else:
                return legacy_varReplace(basedir, varname, vars, lookup_fatal, depth, expand_lists)

        elif isinstance(varname, (list, tuple)):
            return [ template(basedir, v, vars, lookup_fatal, depth, expand_lists, fail_on_undefined=fail_on_undefined) for v in varname]
        elif isinstance(varname, dict):
            return dict([
                (k, template(
                     basedir, v, vars, lookup_fatal, depth, expand_lists, fail_on_undefined=fail_on_undefined)
                ) for (k,v) in varname.iteritems() 
            ])
        else:
            return varname

    except errors.AnsibleFilterError:
        if filter_fatal:
            raise
        else:
            return varname

def template_from_file(basedir, path, vars):
    ''' run a file through the templating engine '''

    fail_on_undefined = C.DEFAULT_UNDEFINED_VAR_BEHAVIOR

    realpath = filesystem.path_dwim(basedir, path)
    loader=jinja2.FileSystemLoader([basedir,os.path.dirname(realpath)])

    def my_lookup(*args, **kwargs):
        kwargs['vars'] = vars
        return lookup(*args, basedir=basedir, **kwargs)

    environment = jinja2.Environment(loader=loader, trim_blocks=True, extensions=_get_extensions())
    environment.filters.update(_get_filters())
    environment.globals['lookup'] = my_lookup
    if fail_on_undefined:
        environment.undefined = StrictUndefined

    try:
        data = codecs.open(realpath, encoding="utf8").read()
    except UnicodeDecodeError:
        raise errors.AnsibleError("unable to process as utf-8: %s" % realpath)
    except:
        raise errors.AnsibleError("unable to read %s" % realpath)


    # Get jinja env overrides from template
    if data.startswith(JINJA2_OVERRIDE):
        eol = data.find('\n')
        line = data[len(JINJA2_OVERRIDE):eol]
        data = data[eol+1:]
        for pair in line.split(','):
            (key,val) = pair.split(':')
            setattr(environment,key.strip(),ast.literal_eval(val.strip()))

    vars = vars.copy()
    try:
        template_uid = pwd.getpwuid(os.stat(realpath).st_uid).pw_name
    except:
        template_uid = os.stat(realpath).st_uid

    vars.update(dict(
       template_host     = os.uname()[1],
       template_path     = realpath,
       template_mtime    = datetime.datetime.fromtimestamp(os.path.getmtime(realpath)),
       template_uid      = template_uid,
       template_fullpath = os.path.abspath(realpath),
       template_run_date = datetime.datetime.now(),
    ))

    managed_default = C.DEFAULT_MANAGED_STR
    managed_str = managed_default.format(
        host = vars['template_host'],
        uid  = vars['template_uid'],
        file = vars['template_path']
    )
    vars['ansible_managed'] = time.strftime(
        managed_str,
        time.localtime(os.path.getmtime(realpath))
    )

    # this double template pass is here to detect errors while we still have context
    # actual recursion is handled by the mainline template function further down
    try:
        t = environment.from_string(data)
        res = t.render(vars)
    except jinja2.exceptions.UndefinedError, e:
        raise errors.AnsibleUndefinedVariable("One or more undefined variables: %s" % str(e))
    except TemplateSyntaxError, e:
        # Throw an exception which includes a more user friendly error message
        values = dict(name=realpath, lineno=e.lineno, error=str(e)) 
        msg = 'file: %(name)s, line number: %(lineno)s, error: %(error)s' % values
        error = errors.AnsibleError(msg)
        raise error

    if data.endswith('\n') and not res.endswith('\n'):
        res = res + '\n'
    return template(basedir, res, vars) 

def template_from_string(basedir, data, vars, fail_on_undefined=False, lookups=True, filters=True):
    ''' run a string through the (Jinja2) templating engine '''
    
    def my_lookup(*args, **kwargs):
        kwargs['vars'] = vars
        return lookup(*args, basedir=basedir, **kwargs)

    if type(data) == str:
        data = unicode(data, 'utf-8')
    environment = jinja2.Environment(trim_blocks=True, undefined=StrictUndefined, extensions=_get_extensions())

    if filters:
        environment.filters.update(_get_filters())

    if '_original_file' in vars:
        basedir = os.path.dirname(vars['_original_file'])
        filesdir = os.path.abspath(os.path.join(basedir, '..', 'files'))
        if os.path.exists(filesdir):
            basedir = filesdir

    # TODO: may need some way of using lookup plugins here seeing we aren't calling
    # the legacy engine, lookup() as a function, perhaps?

    if type(data) == str:
        data = unicode(data, 'utf-8')
    environment = jinja2.Environment(trim_blocks=True, undefined=StrictUndefined, extensions=_get_extensions())
    environment.filters.update(_get_filters())

    if '_original_file' in vars:
        basedir = os.path.dirname(vars['_original_file'])
        filesdir = os.path.abspath(os.path.join(basedir, '..', 'files'))
        if os.path.exists(filesdir):
            basedir = filesdir

    # TODO: may need some way of using lookup plugins here seeing we aren't calling
    # the legacy engine, lookup() as a function, perhaps?

    try:
        t = environment.from_string(data.decode('utf-8'))
    except Exception, e:
        if 'recursion' in str(e):
            raise errors.AnsibleError("recursive loop detected in template string: %s" % data)
        else:
            return data

    if lookups:
        t.globals['lookup'] = my_lookup

    try:
        return t.render(vars)
    except jinja2.exceptions.UndefinedError:
        if fail_on_undefined:
            raise
        else:
            return data

