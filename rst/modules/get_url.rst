.. _get_url:

get_url
```````

Downloads files from http, https, or ftp to the remote server.  The remote server must have direct
access to the remote resource.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| url                | yes      |         | http, https, or ftp URL                                                    |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | absolute path of where to download the file to.  If dest is a directory,   |
|                    |          |         | the basename of the file on the remote server will be used.                |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| OTHERS             | no       |         | all arguments accepted by the file module also work here                   |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    - name: Grab a bunch of jQuery stuff
       action: get_url url=http://code.jquery.com/$item  dest=${jquery_directory} mode=0444
       with_items:
       - jquery.min.js
       - mobile/latest/jquery.mobile.min.js
       - ui/jquery-ui-git.css
