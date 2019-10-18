# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class Sentinel:
    """
    Object which can be used to mark whether an entry as being special

    A sentinel value demarcates a value or marks an entry as having a special meaning.  In C, the
    Null byte is used as a sentinel for the end of a string.  In Python, None is often used as
    a Sentinel in optional parameters to mean that the parameter was not set by the user.

    You should use None as a Sentinel value any Python code where None is not a valid entry.  If
    None is a valid entry, though, then you need to create a different value, which is the purpose
    of this class.

    Example of using Sentinel as a default parameter value::

        def confirm_big_red_button(tristate=Sentinel):
            if tristate is Sentinel:
                print('You must explicitly press the big red button to blow up the base')
            elif tristate is True:
                print('Countdown to destruction activated')
            elif tristate is False:
                print('Countdown stopped')
            elif tristate is None:
                print('Waiting for more input')

    Example of using Sentinel to tell whether a dict which has a default value has been changed::

        values = {'one': Sentinel, 'two': Sentinel}
        defaults = {'one': 1, 'two': 2}

        # [.. Other code which does things including setting a new value for 'one' ..]
        values['one'] = None
        # [..]

        print('You made changes to:')
        for key, value in values.items():
            if value is Sentinel:
                continue
            print('%s: %s' % (key, value)
    """

    def __new__(cls):
        """
        Return the cls itself.  This makes both equality and identity True for comparing the class
        to an instance of the class, preventing common usage errors.

        Preferred usage::

            a = Sentinel
            if a is Sentinel:
                print('Sentinel value')

        However, these are True as well, eliminating common usage errors::

            if Sentinel is Sentinel():
                print('Sentinel value')

            if Sentinel == Sentinel():
                print('Sentinel value')
        """
        return cls
