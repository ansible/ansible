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
import yaml
import json
from ansible import errors
import ansible.constants as C
import time
import subprocess
import datetime
import pwd
import ast
import traceback

from ansible.utils.string_functions import count_newlines_from_end
from ansible.utils import to_bytes, to_unicode

class Globals(object):

    FILTERS = None

    def __init__(self):
        pass

def _get_filters():
    ''' return filter plugin instances '''

    if Globals.FILTERS is not None:
        return Globals.FILTERS

    from ansible import utils
    plugins = [ x for x in utils.plugins.filter_loader.all()]
    filters = {}
    for fp in plugins:
        filters.update(fp.filters())
    Globals.FILTERS = filters

    return Globals.FILTERS

def _get_extensions():
    ''' return jinja2 extensions to load '''

    '''
    if some extensions are set via jinja_extensions in ansible.cfg, we try
    to load them with the jinja environment
    '''
    jinja_exts = []
    if C.DEFAULT_JINJA2_EXTENSIONS:
        '''
        Let's make sure the configuration directive doesn't contain spaces
        and split extensions in an array
        '''
        jinja_exts = C.DEFAULT_JINJA2_EXTENSIONS.replace(" ", "").split(',')

    return jinja_exts

class Flags:
    LEGACY_TEMPLATE_WARNING = False

# TODO: refactor this file

FILTER_PLUGINS = None
_LISTRE = re.compile(r"(\w+)\[(\d+)\]")
JINJA2_OVERRIDE = '#jinja2:'
JINJA2_ALLOWED_OVERRIDES = ['trim_blocks', 'lstrip_blocks', 'newline_sequence', 'keep_trailing_newline']

def lookup(name, *args, **kwargs):
    from ansible import utils
    instance = utils.plugins.lookup_loader.get(name.lower(), basedir=kwargs.get('basedir',None))
    tvars = kwargs.get('vars', None)

    wantlist = kwargs.pop('wantlist', False)

    if instance is not None:
        try:
            ran = instance.run(*args, inject=tvars, **kwargs)
        except errors.AnsibleError:
            raise
        except jinja2.exceptions.UndefinedError, e:
            raise errors.AnsibleUndefinedVariable("One or more undefined variables: %s" % str(e))
        except Exception, e:
            raise errors.AnsibleError('Unexpected error in during lookup: %s' % e)
        if ran and not wantlist:
            ran = ",".join(ran)
        return ran
    else:
        raise errors.AnsibleError("lookup plugin (%s) not found" % name)

def template(basedir, varname, templatevars, lookup_fatal=True, depth=0, expand_lists=True, convert_bare=False, fail_on_undefined=False, filter_fatal=True):
    ''' templates a data structure by traversing it and substituting for other data structures '''
    from ansible import utils

    try:
        if convert_bare and isinstance(varname, basestring):
            first_part = varname.split(".")[0].split("[")[0]
            if first_part in templatevars and '{{' not in varname and '$' not in varname:
                varname = "{{%s}}" % varname

        if isinstance(varname, basestring):
            if '{{' in varname or '{%' in varname:
                try:
                    varname = template_from_string(basedir, varname, templatevars, fail_on_undefined)
                except errors.AnsibleError, e:
                    raise errors.AnsibleError("Failed to template %s: %s" % (varname, str(e)))

                if (varname.startswith("{") and not varname.startswith("{{")) or varname.startswith("["):
                    eval_results = utils.safe_eval(varname, locals=templatevars, include_exceptions=True)
                    if eval_results[1] is None:
                        varname = eval_results[0]

            return varname

        elif isinstance(varname, (list, tuple)):
            return [template(basedir, v, templatevars, lookup_fatal, depth, expand_lists, convert_bare, fail_on_undefined, filter_fatal) for v in varname]
        elif isinstance(varname, dict):
            d = {}
            for (k, v) in varname.iteritems():
                d[k] = template(basedir, v, templatevars, lookup_fatal, depth, expand_lists, convert_bare, fail_on_undefined, filter_fatal)
            return d
        else:
            return varname
    except errors.AnsibleFilterError:
        if filter_fatal:
            raise
        else:
            return varname


class _jinja2_vars(object):
    '''
    Helper class to template all variable content before jinja2 sees it.
    This is done by hijacking the variable storage that jinja2 uses, and
    overriding __contains__ and __getitem__ to look like a dict. Added bonus
    is avoiding duplicating the large hashes that inject tends to be.
    To facilitate using builtin jinja2 things like range, globals are handled
    here.
    extras is a list of locals to also search for variables.
    '''

    def __init__(self, basedir, vars, globals, fail_on_undefined, *extras):
        self.basedir = basedir
        self.vars = vars
        self.globals = globals
        self.fail_on_undefined = fail_on_undefined
        self.extras = extras

    def __contains__(self, k):
        if k in self.vars:
            return True
        for i in self.extras:
            if k in i:
                return True
        if k in self.globals:
            return True
        return False

    def __getitem__(self, varname):
        from ansible.runner import HostVars
        if varname not in self.vars:
            for i in self.extras:
                if varname in i:
                    return i[varname]
            if varname in self.globals:
                return self.globals[varname]
            else:
                raise KeyError("undefined variable: %s" % varname)
        var = self.vars[varname]
        # HostVars is special, return it as-is, as is the special variable
        # 'vars', which contains the vars structure
        var = to_unicode(var, nonstring="passthru")
        if isinstance(var, dict) and varname == "vars" or isinstance(var, HostVars):
            return var
        else:
            return template(self.basedir, var, self.vars, fail_on_undefined=self.fail_on_undefined)

    def add_locals(self, locals):
        '''
        If locals are provided, create a copy of self containing those
        locals in addition to what is already in this variable proxy.
        '''
        if locals is None:
            return self
        return _jinja2_vars(self.basedir, self.vars, self.globals, self.fail_on_undefined, locals, *self.extras)

class J2Template(jinja2.environment.Template):
    '''
    This class prevents Jinja2 from running _jinja2_vars through dict()
    Without this, {% include %} and similar will create new contexts unlike
    the special one created in template_from_file. This ensures they are all
    alike, except for potential locals.
    '''
    def new_context(self, vars=None, shared=False, locals=None):
        return jinja2.runtime.Context(self.environment, vars.add_locals(locals), self.name, self.blocks)

def template_from_file(basedir, path, vars, vault_password=None):
    ''' run a file through the templating engine '''

    fail_on_undefined = C.DEFAULT_UNDEFINED_VAR_BEHAVIOR

    from ansible import utils
    realpath = utils.path_dwim(basedir, path)
    loader=jinja2.FileSystemLoader([basedir,os.path.dirname(realpath)])

    def my_lookup(*args, **kwargs):
        kwargs['vars'] = vars
        return lookup(*args, basedir=basedir, **kwargs)
    def my_finalize(thing):
        return thing if thing is not None else ''

    environment = jinja2.Environment(loader=loader, trim_blocks=True, extensions=_get_extensions())
    environment.filters.update(_get_filters())
    environment.globals['lookup'] = my_lookup
    environment.globals['finalize'] = my_finalize
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
            key = key.strip()
            if key in JINJA2_ALLOWED_OVERRIDES:
                setattr(environment, key, ast.literal_eval(val.strip()))


    environment.template_class = J2Template
    try:
        t = environment.from_string(data)
    except TemplateSyntaxError, e:
        # Throw an exception which includes a more user friendly error message
        values = {'name': realpath, 'lineno': e.lineno, 'error': str(e)}
        msg = 'file: %(name)s, line number: %(lineno)s, error: %(error)s' % \
               values
        error = errors.AnsibleError(msg)
        raise error
    vars = vars.copy()
    try:
        template_uid = pwd.getpwuid(os.stat(realpath).st_uid).pw_name
    except:
        template_uid = os.stat(realpath).st_uid
    vars['template_host']   = os.uname()[1]
    vars['template_path']   = realpath
    vars['template_mtime']  = datetime.datetime.fromtimestamp(os.path.getmtime(realpath))
    vars['template_uid']    = template_uid
    vars['template_fullpath'] = os.path.abspath(realpath)
    vars['template_run_date'] = datetime.datetime.now()

    managed_default = C.DEFAULT_MANAGED_STR
    managed_str = managed_default.format(
        host = vars['template_host'],
        uid  = vars['template_uid'],
        file = to_bytes(vars['template_path'])
    )
    vars['ansible_managed'] = time.strftime(
        managed_str,
        time.localtime(os.path.getmtime(realpath))
    )

    # This line performs deep Jinja2 magic that uses the _jinja2_vars object for vars
    # Ideally, this could use some API where setting shared=True and the object won't get
    # passed through dict(o), but I have not found that yet.
    try:
        res = jinja2.utils.concat(t.root_render_func(t.new_context(_jinja2_vars(basedir, vars, t.globals, fail_on_undefined), shared=True)))
    except jinja2.exceptions.UndefinedError, e:
        raise errors.AnsibleUndefinedVariable("One or more undefined variables: %s" % str(e))
    except jinja2.exceptions.TemplateNotFound, e:
        # Throw an exception which includes a more user friendly error message
        # This likely will happen for included sub-template. Not that besides
        # pure "file not found" it may happen due to Jinja2's "security"
        # checks on path.
        values = {'name': realpath, 'subname': str(e)}
        msg = 'file: %(name)s, error: Cannot find/not allowed to load (include) template %(subname)s' % \
               values
        error = errors.AnsibleError(msg)
        raise error

    # The low level calls above do not preserve the newline
    # characters at the end of the input data, so we use the
    # calculate the difference in newlines and append them 
    # to the resulting output for parity
    res_newlines  = count_newlines_from_end(res)
    data_newlines = count_newlines_from_end(data)
    if data_newlines > res_newlines:
        res += '\n' * (data_newlines - res_newlines)

    if isinstance(res, unicode):
        # do not try to re-template a unicode string
        result = res
    else:
        result = template(basedir, res, vars)

    return result

def template_from_string(basedir, data, vars, fail_on_undefined=False):
    ''' run a string through the (Jinja2) templating engine '''

    try:
        if type(data) == str:
            data = unicode(data, 'utf-8')

        def my_finalize(thing):
            return thing if thing is not None else ''

        environment = jinja2.Environment(trim_blocks=True, undefined=StrictUndefined, extensions=_get_extensions(), finalize=my_finalize)
        environment.filters.update(_get_filters())
        environment.template_class = J2Template

        if '_original_file' in vars:
            basedir = os.path.dirname(vars['_original_file'])
            filesdir = os.path.abspath(os.path.join(basedir, '..', 'files'))
            if os.path.exists(filesdir):
                basedir = filesdir

        # 6227
        if isinstance(data, unicode):
            try:
                data = data.decode('utf-8')
            except UnicodeEncodeError, e:
                pass

        try:
            t = environment.from_string(data)
        except TemplateSyntaxError, e:
            raise errors.AnsibleError("template error while templating string: %s" % str(e))
        except Exception, e:
            if 'recursion' in str(e):
                raise errors.AnsibleError("recursive loop detected in template string: %s" % data)
            else:
                return data

        def my_lookup(*args, **kwargs):
            kwargs['vars'] = vars
            return lookup(*args, basedir=basedir, **kwargs)

        t.globals['lookup'] = my_lookup
        t.globals['finalize'] = my_finalize
        jvars =_jinja2_vars(basedir, vars, t.globals, fail_on_undefined)
        new_context = t.new_context(jvars, shared=True)
        rf = t.root_render_func(new_context)
        try:
            res = jinja2.utils.concat(rf)
        except TypeError, te:
            if 'StrictUndefined' in str(te):
                raise errors.AnsibleUndefinedVariable(
                    "Unable to look up a name or access an attribute in template string. " + \
                    "Make sure your variable name does not contain invalid characters like '-'."
                )
            else:
                raise errors.AnsibleError("an unexpected type error occurred. Error was %s" % te)
        return res
    except (jinja2.exceptions.UndefinedError, errors.AnsibleUndefinedVariable):
        if fail_on_undefined:
            raise
        else:
            return data

