.. note::

    Ansible 2.0 has deprecated the “ssh” from ``ansible_ssh_user``, ``ansible_ssh_host``, and ``ansible_ssh_port`` to become ``ansible_user``, ``ansible_host``, and ``ansible_port``. If you are using a version of Ansible prior to 2.0,  you should continue using the older style variables (``ansible_ssh_*``). These shorter variables are ignored, without warning, in older versions of Ansible. 
    BTW, please pay attention to the older style variables (``ansible_ssh_*``): ansible_ssh_password doesn't exist, should be ansible_ssh_pass. 
