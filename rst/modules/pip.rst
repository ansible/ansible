.. _pip:

pip
```

.. versionadded:: 0.7

Manages Python library dependencies.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | no       |         | The name of a Python library to install                                    |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| version            | no       |         | The version number to install of the Python library specified in the       |
|                    |          |         | 'name' parameter                                                           |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| requirements       | no       |         | The path to a pip requirements file                                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| virtualenv         | no       |         | An optional path to a virtualenv directory to install into                 |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | no       | present | 'present', 'absent' or 'latest'                                            |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Please note that `virtualenv <http://www.virtualenv.org/>`_ must be installed on
the remote host if the `virtualenv` parameter is specified.

Examples::

    pip name=flask
    pip name=flask version=0.8
    pip name=flask virtualenv=/srv/webapps/my_app/venv
    pip requirements=/srv/webapps/my_app/src/requirements.txt
    pip requirements=/srv/webapps/my_app/src/requirements.txt virtualenv=/srv/webapps/my_app/venv
