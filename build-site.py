#!/usr/bin/env python
# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of the Ansible Documentation
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

__docformat__ = 'restructuredtext'

import os
import sys
from sphinx.application import Sphinx
from os import path


class SphinxBuilder(object):
    """
    Creates HTML documentation using Sphinx.
    """

    def __init__(self):
        """
        Run the DocCommand.
        """
        print "Creating html documentation ..."

        try:
            buildername = 'html'

            outdir = path.abspath(path.join('html'))
            # Create the output directory if it doesn't exist
            if not os.access(outdir, os.F_OK):
                os.mkdir(outdir)

            doctreedir = os.path.join('./', '.doctrees')

            confdir = path.abspath('./')
            srcdir = path.abspath('rst')
            freshenv = False

            # Create the builder
            app = Sphinx(srcdir,
                              confdir,
                              outdir,
                              doctreedir,
                              buildername,
                              {},
                              sys.stdout,
                              sys.stderr,
                              freshenv)

            app.builder.build_all()
            # We also have the HTML man pages to handle now as well
            #if os.system("make htmlman"):
            #    print "There was an error while building the HTML man pages."
            #    print "Run 'make htmlman' to recreate the problem."
            #print "Your docs are now in %s" % outdir
        except ImportError, ie:
            print >> sys.stderr, "You don't seem to have the following which"
            print >> sys.stderr, "are required to make documentation:"
            print >> sys.stderr, "\tsphinx.application.Sphinx"
            print >> sys.stderr, "This is usually available from the python-sphinx package"
            print >> sys.stderr, "=== Error message received while attempting to build==="
            print >> sys.stderr, ie
        except Exception, ex:
            print >> sys.stderr, "FAIL! exiting ... (%s)" % ex

    def build_docs(self):
        self.app.builder.build_all()


if __name__ == '__main__':
    docgen = SphinxBuilder()

    if "view" in sys.argv:
        import webbrowser
        if not webbrowser.open('html/index.html'):
            print >> sys.stderr, "Could not open on your webbrowser."
