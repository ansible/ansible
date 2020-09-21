# -*- coding: utf-8 -*-
#
# documentation build configuration file, created by
# sphinx-quickstart on Sat Sep 27 13:23:22 2008-2009.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# The contents of this file are pickled, so don't put values in the namespace
# that aren't pickleable (module imports are okay, they're removed
# automatically).
#
# All configuration values have a default value; values that are commented out
# serve to show the default value.

import sys
import os

# pip install sphinx_rtd_theme
# import sphinx_rtd_theme
# html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# If your extensions are in another directory, add it here. If the directory
# is relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
# sys.path.append(os.path.abspath('some/directory'))
#
sys.path.insert(0, os.path.join('ansible', 'lib'))
sys.path.append(os.path.abspath(os.path.join('..', '_extensions')))

# We want sphinx to document the ansible modules contained in this repository,
# not those that may happen to be installed in the version
# of Python used to run sphinx.  When sphinx loads in order to document,
# the repository version needs to be the one that is loaded:
sys.path.insert(0, os.path.abspath(os.path.join('..', '..', '..', 'lib')))

VERSION = '2.9'
AUTHOR = 'Ansible, Inc'


# General configuration
# ---------------------

# Add any Sphinx extension module names here, as strings.
# They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
# TEST: 'sphinxcontrib.fulltoc'
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 'pygments_lexer', 'notfound.extension']

# Later on, add 'sphinx.ext.viewcode' to the list if you want to have
# colorized code generated too for references.


# Add any paths that contain templates here, relative to this directory.
templates_path = ['.templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General substitutions.
project = 'Ansible'
copyright = "2019 Red Hat, Inc."

# The default replacements for |version| and |release|, also used in various
# other places throughout the built documents.
#
# The short X.Y version.
version = VERSION
# The full version, including alpha/beta/rc tags.
release = VERSION

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
# unused_docs = []

# List of directories, relative to source directories, that shouldn't be
# searched for source files.
# exclude_dirs = []

# A list of glob-style patterns that should be excluded when looking
# for source files.
# OBSOLETE - removing this - dharmabumstead 2018-02-06
# exclude_patterns = ['modules']

# The reST default role (used for this markup: `text`) to use for all
# documents.
# default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
# add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
# add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

highlight_language = 'YAML+Jinja'

# Substitutions, variables, entities, & shortcuts for text which do not need to link to anything.
# For titles which should be a link, use the intersphinx anchors set at the index, chapter, and section levels, such as  qi_start_:
# |br| is useful for formatting fields inside of tables
# |_| is a nonbreaking space; similarly useful inside of tables
rst_epilog = """
.. |br| raw:: html

   <br>
.. |_| unicode:: 0xA0
    :trim:
"""


# Options for HTML output
# -----------------------

html_theme_path = ['../_themes']
html_theme = 'sphinx_rtd_theme'
html_short_title = 'Ansible Documentation'
html_show_sphinx = False

html_theme_options = {
    'canonical_url': "https://docs.ansible.com/ansible/latest/",
    'vcs_pageview_mode': 'edit'
}

html_context = {
    'display_github': 'True',
    'github_user': 'ansible',
    'github_repo': 'ansible',
    'github_version': 'devel/docs/docsite/rst/',
    'github_module_version': 'devel/lib/ansible/modules/',
    'github_root_dir': 'devel/lib/ansible',
    'github_cli_version': 'devel/lib/ansible/cli/',
    'current_version': version,
    'latest_version': '2.10',
    # list specifically out of order to make latest work
    'available_versions': ('latest', '2.9', '2.9_ja', '2.8', 'devel'),
    'css_files': ('_static/ansible.css',  # overrides to the standard theme
                  ),
}

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
# html_style = 'solar.css'

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = 'Ansible Documentation'

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = None

# The name of an image file (within the static path) to place at the top of
# the sidebar.
# html_logo =

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
# html_favicon = 'favicon.ico'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['../_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {}

# If false, no module index is generated.
# html_use_modindex = True

# If false, no index is generated.
# html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, the reST sources are included in the HTML build as _sources/<name>.
html_copy_source = False

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = 'https://docs.ansible.com/ansible/latest'

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'Poseidodoc'

# Configuration for sphinx-notfound-pages
# with no 'notfound_template' and no 'notfound_context' set,
# the extension builds 404.rst into a location-agnostic 404 page
#
# default is `en` - using this for the sub-site:
notfound_default_language = "ansible"
# default is `latest`:
# setting explicitly - docsite serves up /ansible/latest/404.html
# so keep this set to `latest` even on the `devel` branch
# then no maintenance is needed when we branch a new stable_x.x
notfound_default_version = "latest"
# makes default setting explicit:
notfound_no_urls_prefix = False

# Options for LaTeX output
# ------------------------

# The paper size ('letter' or 'a4').
# latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
# latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class
# [howto/manual]).
latex_documents = [
    ('index', 'ansible.tex', 'Ansible 2.2 Documentation', AUTHOR, 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# Additional stuff for the LaTeX preamble.
# latex_preamble = ''

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_use_modindex = True

autoclass_content = 'both'

intersphinx_mapping = {'python': ('https://docs.python.org/2/', (None, '../python2-2.7.13.inv')),
                       'python3': ('https://docs.python.org/3/', (None, '../python3-3.6.2.inv')),
                       'jinja2': ('http://jinja.pocoo.org/docs/', (None, '../jinja2-2.9.7.inv'))}
