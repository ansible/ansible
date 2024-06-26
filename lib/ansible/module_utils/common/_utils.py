# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)


"""
Modules in _utils are waiting to find a better home.  If you need to use them, be prepared for them
to move to a different location in the future.
"""
from __future__ import annotations


def get_all_subclasses(cls):
    '''
    Recursively search and find all subclasses of a given class

    :arg cls: A python class
    :rtype: set
    :returns: The set of python classes which are the subclasses of `cls`.

    In python, you can use a class's :py:meth:`__subclasses__` method to determine what subclasses
    of a class exist.  However, `__subclasses__` only goes one level deep.  This function searches
    each child class's `__subclasses__` method to find all of the descendent classes.  It then
    returns an iterable of the descendent classes.
    '''
    # Retrieve direct subclasses
    subclasses = set(cls.__subclasses__())
    to_visit = list(subclasses)
    # Then visit all subclasses
    while to_visit:
        for sc in to_visit:
            # The current class is now visited, so remove it from list
            to_visit.remove(sc)
            # Appending all subclasses to visit and keep a reference of available class
            for ssc in sc.__subclasses__():
                if ssc not in subclasses:
                    to_visit.append(ssc)
                    subclasses.add(ssc)
    return subclasses
