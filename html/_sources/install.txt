Install
=======


From Yum
--------

Taboot is in the Fedora package repositories. Installing it should be as simple as::

    sudo yum install python-taboot


From Source
-----------

You'll need these dependencies to build/install:

 #. `python <http://www.python.org>`_ - The python programming language along with python-setuptools
 #. `distutils <http://docs.python.org/lib/module-distutils.html>`_ - Python building and packaging library

Building documentation requires some more deps. These are **required**
if you're building RPMs, and optional if you're installing manually:

 #. python-sphinx
 #. asciidoc
 #. libxslt


Building RPMs from source
`````````````````````````

This is the recommended installation method if you're pulling Taboot
from source::

    make rpm
    sudo yum localinstall /path/to/rpm


Installing From source
``````````````````````

I **don't** recommend this. But if you're dead set on installing
directly from source you still can. This calls the python
``distutils`` installer directly::

    sudo make install

If you wish to build and install the optional documentation you'll
need some additional packages so it can be built fully. Install the
documentation with this command::

    sudo make installdocs

Uninstall everything with::

    sudo make uninstall
