Module Utils
============

.. contents:: Topics

Module developers quite often need the same functions. The Module Utils contain a collection
of library functions that may be useful to module developers. 

Every Ansible module already contains the 'basic' module::

    from ansible.module_utils.basic import *

But besides the 'basic' module their are quite some others you might want to use.
From the 'urls' module that may replace the requests library to the 'api' module that
gives you an implementation for rate limiting and retrying requests.

The following documentation is very much a work in progress until all modules are documented.

.. _module_utils:

urls
````
.. automodule:: ansible.module_utils.urls

Import::

    from ansible.module_utils.urls import *

.. autofunction:: ansible.module_utils.urls.fetch_url(module, url, data=None, headers=None, method=None, ...)
