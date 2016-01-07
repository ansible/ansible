# This script wraps the `setup.py register` command with creating a temporary file to use in the package's long_description field.
# It should be used for release to PyPI instead of `setup.py register`

# Note that this script requires Pandoc to be installed, as well as the Python package pyandoc
# http://pandoc.org/
# pip install pyandoc

import pandoc
import os

pandoc.core.PANDOC_PATH = 'pandoc'

doc = pandoc.Document()
doc.markdown = open('README.md').read()
f = open('README.txt','w+')
f.write(doc.rst)
f.close()
os.system("setup.py register")
os.remove('README.txt')
