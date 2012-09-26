.. _get_url:

get_url
````````````````````````

.. versionadded:: 0.6


Downloads files from HTTP, HTTPS, or FTP to the remote server. The remote server must have direct access to the remote resource. 


==============  ========== ========== ============================================================
parameter       required   default    comments                                                    
==============  ========== ========== ============================================================ 
url             yes        None       HTTP, HTTPS, or FTP URL
dest            yes        None       absolute path of where to download the file to.If *dest* is a directory, the basename of the file on the remote server will be used. If a directory, *thirsty=yes* must also be set.
thirsty                    no         if ``yes``, will download the file every time and replace the file if the contents change. if ``no``, the file will only be downloaded if the destination does not exist. Generally should be ``yes`` only for small local files. prior to 0.6, acts if ``yes`` by default.
others                                all arguments accepted by the ``file`` module also work here
==============  ========== ========== ============================================================




FIXME: examples!



.. note::


   This module doesn't support proxies or passwords.

   Also see the ``template`` module.


Example action from Ansible :doc:`playbooks`::


    get_url url=http://example.com/path/file.conf dest=/etc/foo.conf mode=0440
  
