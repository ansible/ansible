.. _template:

template
````````

Templates a file out to a remote server.

Templates are processed by the 
`Jinja2 templating language <http://jinja.pocoo.org/docs/>`_ - 
documentation on the template formatting can be found in the 
`Template Designer Documentation <http://jinja.pocoo.org/docs/templates/>`_

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| src                | yes      |         | Path of a Jinja2 formatted template on the local server.  This can be      |
|                    |          |         | a relative or absolute path.                                               |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | Location to render the template on the remote server                       |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| backup             | no       | no      | Create a backup file including the timestamp information so you can        |
|                    |          |         | get the original file back if you somehow clobbered it incorrectly.        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| OTHERS             |          |         | This module also supports all of the arguments to the file module          |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from a playbook::

    template src=/srv/mytemplates/foo.j2 dest=/etc/foo.conf owner=foo group=foo mode=0644
