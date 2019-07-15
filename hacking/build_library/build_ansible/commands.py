# coding: utf-8
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from abc import ABCMeta, abstractmethod, abstractproperty


class Command:
    """
    Subcommands of :program:`build-ansible.py`.

    This defines an interface that all subcommands must conform to.  :program:`build-ansible.py` will
    require that these things are present in order to proceed.
    """
    @staticmethod
    @abstractproperty
    def name():
        """Name of the command.  The same as the string is invoked with"""

    @staticmethod
    @abstractmethod
    def init_parser(add_parser):
        """
        Initialize and register an argparse ArgumentParser

        :arg add_parser: function which creates an ArgumentParser for the main program.

        Implementations should first create an ArgumentParser using `add_parser` and then populate
        it with the command line arguments that are needed.

        .. seealso:
            `add_parser` information in the :py:meth:`ArgumentParser.add_subparsers` documentation.
        """

    @staticmethod
    @abstractmethod
    def main(arguments):
        """
        Run the command

        :arg arguments: The **parsed** command line args

        This is the Command's entrypoint.  The command line args are already parsed but from here
        on, the command can do its work.
        """
