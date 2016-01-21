# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors.yaml_strings import ( YAML_POSITION_DETAILS,
        YAML_COMMON_UNQUOTED_VARIABLE_ERROR,
        YAML_COMMON_DICT_ERROR,
        YAML_COMMON_UNQUOTED_COLON_ERROR,
        YAML_COMMON_PARTIALLY_QUOTED_LINE_ERROR,
        YAML_COMMON_UNBALANCED_QUOTES_ERROR )

from ansible.utils.unicode import to_unicode, to_str


class AnsibleError(Exception):
    '''
    This is the base class for all errors raised from Ansible code,
    and can be instantiated with two optional parameters beyond the
    error message to control whether detailed information is displayed
    when the error occurred while parsing a data file of some kind.

    Usage:

        raise AnsibleError('some message here', obj=obj, show_content=True)

    Where "obj" is some subclass of ansible.parsing.yaml.objects.AnsibleBaseYAMLObject,
    which should be returned by the DataLoader() class.
    '''

    def __init__(self, message="", obj=None, show_content=True):
        # we import this here to prevent an import loop problem,
        # since the objects code also imports ansible.errors
        from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject

        self._obj = obj
        self._show_content = show_content
        if obj and isinstance(obj, AnsibleBaseYAMLObject):
            extended_error = self._get_extended_error()
            if extended_error:
                self.message = '%s\n\n%s' % (to_str(message), to_str(extended_error))
        else:
            self.message = '%s' % to_str(message)

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message

    def _get_error_lines_from_file(self, file_name, line_number):
        '''
        Returns the line in the file which coresponds to the reported error
        location, as well as the line preceding it (if the error did not
        occur on the first line), to provide context to the error.
        '''

        target_line = ''
        prev_line = ''

        with open(file_name, 'r') as f:
            lines = f.readlines()

            target_line = lines[line_number]
            if line_number > 0:
                prev_line = lines[line_number - 1]

        return (target_line, prev_line)

    def _get_extended_error(self):
        '''
        Given an object reporting the location of the exception in a file, return
        detailed information regarding it including:

          * the line which caused the error as well as the one preceding it
          * causes and suggested remedies for common syntax errors

        If this error was created with show_content=False, the reporting of content
        is suppressed, as the file contents may be sensitive (ie. vault data).
        '''

        error_message = ''

        try:
            (src_file, line_number, col_number) = self._obj.ansible_pos
            error_message += YAML_POSITION_DETAILS % (src_file, line_number, col_number)
            if src_file not in ('<string>', '<unicode>') and self._show_content:
                (target_line, prev_line) = self._get_error_lines_from_file(src_file, line_number - 1)
                target_line = to_unicode(target_line)
                prev_line = to_unicode(prev_line)
                if target_line:
                    stripped_line = target_line.replace(" ","")
                    arrow_line    = (" " * (col_number-1)) + "^ here"
                    #header_line   = ("=" * 73)
                    error_message += "\nThe offending line appears to be:\n\n%s\n%s\n%s\n" % (prev_line.rstrip(), target_line.rstrip(), arrow_line)

                    # common error/remediation checking here:
                    # check for unquoted vars starting lines
                    if ('{{' in target_line and '}}' in target_line) and ('"{{' not in target_line or "'{{" not in target_line):
                        error_message += YAML_COMMON_UNQUOTED_VARIABLE_ERROR
                    # check for common dictionary mistakes
                    elif ":{{" in stripped_line and "}}" in stripped_line:
                        error_message += YAML_COMMON_DICT_ERROR
                    # check for common unquoted colon mistakes
                    elif len(target_line) and len(target_line) > 1 and len(target_line) > col_number and target_line[col_number] == ":" and target_line.count(':') > 1:
                        error_message += YAML_COMMON_UNQUOTED_COLON_ERROR
                    # otherwise, check for some common quoting mistakes
                    else:
                        parts = target_line.split(":")
                        if len(parts) > 1:
                            middle = parts[1].strip()
                            match = False
                            unbalanced = False

                            if middle.startswith("'") and not middle.endswith("'"):
                                match = True
                            elif middle.startswith('"') and not middle.endswith('"'):
                                match = True

                            if len(middle) > 0 and middle[0] in [ '"', "'" ] and middle[-1] in [ '"', "'" ] and target_line.count("'") > 2 or target_line.count('"') > 2:
                                unbalanced = True

                            if match:
                                error_message += YAML_COMMON_PARTIALLY_QUOTED_LINE_ERROR
                            if unbalanced:
                                error_message += YAML_COMMON_UNBALANCED_QUOTES_ERROR

        except (IOError, TypeError):
            error_message += '\n(could not open file to display line)'
        except IndexError:
            error_message += '\n(specified line no longer in file, maybe it changed?)'

        return error_message

class AnsibleOptionsError(AnsibleError):
    ''' bad or incomplete options passed '''
    pass

class AnsibleParserError(AnsibleError):
    ''' something was detected early that is wrong about a playbook or data file '''
    pass

class AnsibleInternalError(AnsibleError):
    ''' internal safeguards tripped, something happened in the code that should never happen '''
    pass

class AnsibleRuntimeError(AnsibleError):
    ''' ansible had a problem while running a playbook '''
    pass

class AnsibleModuleError(AnsibleRuntimeError):
    ''' a module failed somehow '''
    pass

class AnsibleConnectionFailure(AnsibleRuntimeError):
    ''' the transport / connection_plugin had a fatal error '''
    pass

class AnsibleFilterError(AnsibleRuntimeError):
    ''' a templating failure '''
    pass

class AnsibleLookupError(AnsibleRuntimeError):
    ''' a lookup failure '''
    pass

class AnsibleCallbackError(AnsibleRuntimeError):
    ''' a callback failure '''
    pass

class AnsibleUndefinedVariable(AnsibleRuntimeError):
    ''' a templating failure '''
    pass

class AnsibleFileNotFound(AnsibleRuntimeError):
    ''' a file missing failure '''
    pass
