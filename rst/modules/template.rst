.. _template:

template
````````

Templates a file out to a remote server.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| src                | yes      |         | Path of a Jinja2 formatted template on the local server.  This can be      |
|                    |          |         | a relative or absolute path.                                               |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | Location to render the template on the remote server                       |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| OTHERS             |          |         | This module also supports all of the arguments to the file module          |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from a playbook::

    template src=/srv/mytemplates/foo.j2 dest=/etc/foo.conf owner=foo group=foo mode=0644
