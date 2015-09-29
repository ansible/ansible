# (c) 2015, Kevin Carter <kevin.carter@rackspace.com>
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

import datetime
import io
import json
import os
import pwd
import re
import time
import yaml


from ansible.plugins.action import ActionBase
from ansible.utils.unicode import to_bytes, to_unicode
from ansible import constants as C
from ansible import errors


CONFIG_TYPES = {
    'ini': 'return_config_overrides_ini',
    'json': 'return_config_overrides_json',
    'yaml': 'return_config_overrides_yaml'
}


def _convert_2_string(item):
    """Return byte strings for all items.

    This will convert everything within a dict, list or unicode string such
    that the values will be encode('utf-8') where applicable.
    """

    if isinstance(item, dict):
        # Old style dict comprehension for legacy python support
        return dict(
            (_convert_2_string(key), _convert_2_string(value))
            for key, value in item.iteritems()
        )
    elif isinstance(item, list):
        return [_convert_2_string(i) for i in item]
    elif isinstance(item, tuple):
        return tuple([_convert_2_string(i) for i in item])
    elif isinstance(item, set):
        return item
    else:
        try:
            return item.encode('utf-8')
        except AttributeError:
            return str(item)


class MultiKeyDict(dict):
    """Dictionary class which supports duplicate keys.
    This class allows for an item to be added into a standard python dictionary
    however if a key is created more than once the dictionary will convert the
    singular value to a python set. This set type forces all values to be a
    string.
    Example Usage:
    >>> z = MultiKeyDict()
    >>> z['a'] = 1
    >>> z['b'] = ['a', 'b', 'c']
    >>> z['c'] = {'a': 1}
    >>> print(z)
    ... {'a': 1, 'b': ['a', 'b', 'c'], 'c': {'a': 1}}
    >>> z['a'] = 2
    >>> print(z)
    ... {'a': set(['1', '2']), 'c': {'a': 1}, 'b': ['a', 'b', 'c']}
    """
    def __setitem__(self, key, value):
        if key in self:
            if isinstance(self[key], set):
                items = self[key]
                items.add(str(value))
                super(MultiKeyDict, self).__setitem__(key, items)
            else:
                items = [str(value), str(self[key])]
                super(MultiKeyDict, self).__setitem__(key, set(items))
        else:
            return dict.__setitem__(self, key, value)


class ConfigTemplateParser(ConfigParser.RawConfigParser):
    """ConfigParser which supports multi key value.
    The parser will use keys with multiple variables in a set as a multiple
    key value within a configuration file.
    Default Configuration file:
    [DEFAULT]
    things =
        url1
        url2
        url3
    other = 1,2,3
    [section1]
    key = var1
    key = var2
    key = var3
    Example Usage:
    >>> cp = ConfigTemplateParser(dict_type=MultiKeyDict)
    >>> cp.read('/tmp/test.ini')
    ... ['/tmp/test.ini']
    >>> cp.get('DEFAULT', 'things')
    ... \nurl1\nurl2\nurl3
    >>> cp.get('DEFAULT', 'other')
    ... '1,2,3'
    >>> cp.set('DEFAULT', 'key1', 'var1')
    >>> cp.get('DEFAULT', 'key1')
    ... 'var1'
    >>> cp.get('section1', 'key')
    ... {'var1', 'var2', 'var3'}
    >>> cp.set('section1', 'key', 'var4')
    >>> cp.get('section1', 'key')
    ... {'var1', 'var2', 'var3', 'var4'}
    >>> with open('/tmp/test2.ini', 'w') as f:
    ...     cp.write(f)
    Output file:
    [DEFAULT]
    things =
        url1
        url2
        url3
    key1 = var1
    other = 1,2,3
    [section1]
    key = var4
    key = var1
    key = var3
    key = var2
    """
    def _write(self, fp, section, item, entry):
        if section:
            if (item is not None) or (self._optcre == self.OPTCRE):
                fp.write(entry)
        else:
            fp.write(entry)

    def _write_check(self, fp, key, value, section=False):
        if isinstance(value, set):
            for item in value:
                item = str(item).replace('\n', '\n\t')
                entry = "%s = %s\n" % (key, item)
                self._write(fp, section, item, entry)
        else:
            if isinstance(value, list):
                _value = [str(i.replace('\n', '\n\t')) for i in value]
                entry = '%s = %s\n' % (key, ','.join(_value))
            else:
                entry = '%s = %s\n' % (key, str(value).replace('\n', '\n\t'))
            self._write(fp, section, value, entry)

    def write(self, fp):
        if self._defaults:
            fp.write("[%s]\n" % 'DEFAULT')
            for key, value in self._defaults.items():
                self._write_check(fp, key=key, value=value)
            else:
                fp.write("\n")

        for section in self._sections:
            fp.write("[%s]\n" % section)
            for key, value in self._sections[section].items():
                self._write_check(fp, key=key, value=value, section=True)
            else:
                fp.write("\n")

    def _read(self, fp, fpname):
        cursect = None
        optname = None
        lineno = 0
        e = None
        while True:
            line = fp.readline()
            if not line:
                break
            lineno += 1
            if line.strip() == '' or line[0] in '#;':
                continue
            if line.split(None, 1)[0].lower() == 'rem' and line[0] in "rR":
                continue
            if line[0].isspace() and cursect is not None and optname:
                value = line.strip()
                if value:
                    if isinstance(cursect[optname], set):
                        _temp_item = list(cursect[optname])
                        del cursect[optname]
                        cursect[optname] = _temp_item
                    elif isinstance(cursect[optname], (str, unicode)):
                        _temp_item = [cursect[optname]]
                        del cursect[optname]
                        cursect[optname] = _temp_item
                    cursect[optname].append(value)
            else:
                mo = self.SECTCRE.match(line)
                if mo:
                    sectname = mo.group('header')
                    if sectname in self._sections:
                        cursect = self._sections[sectname]
                    elif sectname == 'DEFAULT':
                        cursect = self._defaults
                    else:
                        cursect = self._dict()
                        self._sections[sectname] = cursect
                    optname = None
                elif cursect is None:
                    raise ConfigParser.MissingSectionHeaderError(
                        fpname,
                        lineno,
                        line
                    )
                else:
                    mo = self._optcre.match(line)
                    if mo:
                        optname, vi, optval = mo.group('option', 'vi', 'value')
                        optname = self.optionxform(optname.rstrip())
                        if optval is not None:
                            if vi in ('=', ':') and ';' in optval:
                                pos = optval.find(';')
                                if pos != -1 and optval[pos - 1].isspace():
                                    optval = optval[:pos]
                            optval = optval.strip()
                            if optval == '""':
                                optval = ''
                        cursect[optname] = optval
                    else:
                        if not e:
                            e = ConfigParser.ParsingError(fpname)
                        e.append(lineno, repr(line))
        if e:
            raise e
        all_sections = [self._defaults]
        all_sections.extend(self._sections.values())
        for options in all_sections:
            for name, val in options.items():
                if isinstance(val, list):
                    _temp_item = '\n'.join(val)
                    del options[name]
                    options[name] = _temp_item


class ActionModule(ActionBase):
    TRANSFERS_FILES = True

    def return_config_overrides_ini(self, config_overrides, resultant):
        """Returns string value from a modified config file.

        :param config_overrides: ``dict``
        :param resultant: ``str`` || ``unicode``
        :returns: ``str``
        """
        # If there is an exception loading the RawConfigParser The config obj
        #  is loaded again without the extra option. This is being done to
        #  support older python.
        try:
            config = ConfigTemplateParser(
                allow_no_value=True,
                dict_type=MultiKeyDict
            )
        except Exception:
            config = ConfigTemplateParser(dict_type=MultiKeyDict)

        config_object = io.BytesIO(str(resultant))
        config.readfp(config_object)
        for section, items in config_overrides.items():
            # If the items value is not a dictionary it is assumed that the
            #  value is a default item for this config type.
            if not isinstance(items, dict):
                if isinstance(items, list):
                    items = ','.join(_convert_2_string(items))
                self._option_write(
                    config,
                    'DEFAULT',
                    str(section),
                    items
                )
            else:
                # Attempt to add a section to the config file passing if
                #  an error is raised that is related to the section
                #  already existing.
                try:
                    config.add_section(section.encode('utf-8'))
                except (ConfigParser.DuplicateSectionError, ValueError):
                    pass
                for key, value in items.items():
                    try:
                        self._option_write(config, section, key, value)
                    except ConfigParser.NoSectionError as exp:
                        error_msg = str(exp)
                        error_msg += (
                            ' Try being more explicit with your override'
                            'data. Sections are case sensitive.'
                        )
                        raise errors.AnsibleModuleError(error_msg)
        else:
            config_object.close()

        resultant_bytesio = io.BytesIO()
        try:
            config.write(resultant_bytesio)
            return resultant_bytesio.getvalue()
        finally:
            resultant_bytesio.close()

    @staticmethod
    def _option_write(config, section, key, value):
        config.remove_option(str(section), str(key))
        try:
            if not any(i for i in value.values()):
                value = set(value)
        except AttributeError:
            pass
        if isinstance(value, set):
            config.set(str(section), str(key), value)
        elif isinstance(value, list):
            config.set(str(section), str(key), ','.join(str(i) for i in value))
        else:
            config.set(str(section), str(key), str(value))

    def return_config_overrides_json(self, config_overrides, resultant):
        """Returns config json

        Its important to note that file ordering will not be preserved as the
        information within the json file will be sorted by keys.

        :param config_overrides: ``dict``
        :param resultant: ``str`` || ``unicode``
        :returns: ``str``
        """
        original_resultant = json.loads(resultant)
        merged_resultant = self._merge_dict(
            base_items=original_resultant,
            new_items=config_overrides
        )
        return json.dumps(
            merged_resultant,
            indent=4,
            sort_keys=True
        )

    def return_config_overrides_yaml(self, config_overrides, resultant):
        """Return config yaml.

        :param config_overrides: ``dict``
        :param resultant: ``str`` || ``unicode``
        :returns: ``str``
        """
        original_resultant = yaml.safe_load(resultant)
        merged_resultant = self._merge_dict(
            base_items=original_resultant,
            new_items=config_overrides
        )
        return yaml.safe_dump(
            merged_resultant,
            default_flow_style=False,
            width=1000,
        )

    def _merge_dict(self, base_items, new_items):
        """Recursively merge new_items into base_items.

        :param base_items: ``dict``
        :param new_items: ``dict``
        :returns: ``dict``
        """
        for key, value in new_items.iteritems():
            if isinstance(value, dict):
                base_items[key] = self._merge_dict(
                    base_items.get(key, {}),
                    value
                )
            elif not isinstance(value, int) and (',' in value or '\n' in value):
                base_items[key] = re.split(',|\n', value)
                base_items[key] = [i.strip() for i in base_items[key] if i]
            elif isinstance(value, list):
                if key in base_items and isinstance(base_items[key], list):
                    base_items[key].extend(value)
                else:
                    base_items[key] = value
            else:
                base_items[key] = new_items[key]
        return base_items

    def _load_options_and_status(self, task_vars):
        """Return options and status from module load."""

        config_type = self._task.args.get('config_type')
        if config_type not in ['ini', 'yaml', 'json']:
            return False, dict(
                failed=True,
                msg="No valid [ config_type ] was provided. Valid options are"
                    " ini, yaml, or json."
            )

        # Access to protected method is unavoidable in Ansible
        searchpath = [self._loader._basedir]

        faf = self._task.first_available_file
        if faf:
            task_file = task_vars.get('_original_file', None, 'templates')
            source = self._get_first_available_file(faf, task_file)
            if not source:
                return False, dict(
                    failed=True,
                    msg="could not find src in first_available_file list"
                )
        else:
            # Access to protected method is unavoidable in Ansible
            if self._task._role:
                file_path = self._task._role._role_path
                searchpath.insert(1, C.DEFAULT_ROLES_PATH)
                searchpath.insert(1, self._task._role._role_path)
            else:
                file_path = self._loader.get_basedir()

            user_source = self._task.args.get('src')
            if not user_source:
                return False, dict(
                    failed=True,
                    msg="No user provided [ src ] was provided"
                )
            source = self._loader.path_dwim_relative(
                file_path,
                'templates',
                user_source
            )
            searchpath.insert(1, os.path.dirname(source))

        _dest = self._task.args.get('dest')
        if not _dest:
            return False, dict(
                failed=True,
                msg="No [ dest ] was provided"
            )
        else:
            # Expand any user home dir specification
            user_dest = self._remote_expand_user(_dest)
            if user_dest.endswith(os.sep):
                user_dest = os.path.join(user_dest, os.path.basename(source))

        return True, dict(
            source=source,
            dest=user_dest,
            config_overrides=self._task.args.get('config_overrides', dict()),
            config_type=config_type,
            searchpath=searchpath
        )

    def run(self, tmp=None, task_vars=None):
        """Run the method"""

        try:
            remote_user = task_vars.get('ansible_ssh_user') or self._play_context.remote_user
            if not tmp:
                tmp = self._make_tmp_path(remote_user)
        except TypeError:
            if not tmp:
                tmp = self._make_tmp_path()

        _status, _vars = self._load_options_and_status(task_vars=task_vars)
        if not _status:
            return _vars

        temp_vars = task_vars.copy()
        template_host = temp_vars['template_host'] = os.uname()[1]
        source = temp_vars['template_path'] = _vars['source']
        temp_vars['template_mtime'] = datetime.datetime.fromtimestamp(
            os.path.getmtime(source)
        )

        try:
            template_uid = temp_vars['template_uid'] = pwd.getpwuid(
                os.stat(source).st_uid
            ).pw_name
        except Exception:
            template_uid = temp_vars['template_uid'] = os.stat(source).st_uid

        managed_default = C.DEFAULT_MANAGED_STR
        managed_str = managed_default.format(
            host=template_host,
            uid=template_uid,
            file=to_bytes(source)
        )

        temp_vars['ansible_managed'] = time.strftime(
            managed_str,
            time.localtime(os.path.getmtime(source))
        )
        temp_vars['template_fullpath'] = os.path.abspath(source)
        temp_vars['template_run_date'] = datetime.datetime.now()

        with open(source, 'r') as f:
            template_data = to_unicode(f.read())

        self._templar.environment.loader.searchpath = _vars['searchpath']
        self._templar.set_available_variables(temp_vars)
        resultant = self._templar.template(
            template_data,
            preserve_trailing_newlines=True,
            escape_backslashes=False,
            convert_data=False
        )

        # Access to protected method is unavoidable in Ansible
        self._templar.set_available_variables(
            self._templar._available_variables
        )

        if _vars['config_overrides']:
            type_merger = getattr(self, CONFIG_TYPES.get(_vars['config_type']))
            resultant = type_merger(
                config_overrides=_vars['config_overrides'],
                resultant=resultant
            )

        # Re-template the resultant object as it may have new data within it
        #  as provided by an override variable.
        resultant = self._templar.template(
            resultant,
            preserve_trailing_newlines=True,
            escape_backslashes=False,
            convert_data=False
        )

        # run the copy module
        new_module_args = self._task.args.copy()
        # Access to protected method is unavoidable in Ansible
        transferred_data = self._transfer_data(
            self._connection._shell.join_path(tmp, 'source'),
            resultant
        )
        new_module_args.update(
            dict(
                src=transferred_data,
                dest=_vars['dest'],
                original_basename=os.path.basename(source),
                follow=True,
            ),
        )

        # Remove data types that are not available to the copy module
        new_module_args.pop('config_overrides', None)
        new_module_args.pop('config_type', None)

        # Run the copy module
        return self._execute_module(
            module_name='copy',
            module_args=new_module_args,
            task_vars=task_vars
        )
