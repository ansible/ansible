.. _win_guide_index:

########################
Using Ansible on Windows
########################

.. note::

    **Making Open Source More Inclusive**

    Red Hat is committed to replacing problematic language in our code, documentation, and web properties. We are beginning with these four terms: master, slave, blacklist, and whitelist. We ask that you open an issue or pull request if you come upon a term that we have missed. For more details, see `our CTO Chris Wright's message <https://www.redhat.com/en/blog/making-open-source-more-inclusive-eradicating-problematic-language>`_.

Welcome to the Ansible guide for Microsoft Windows.
This guide shows you how to set up Ansible on a Windows host, configure WinRM for Ansible, perform operations, and tune performance.
Additionally, because Windows is not a POSIX-compliant operating system, Ansible interacts with Windows hosts differently to Linux/Unix hosts.
You can find information about those differences, and everything you need to know about using Ansible on Windows, in this guide.

.. toctree::
   :maxdepth: 2
   
   windows_setup
   windows_usage
   windows_winrm
   windows_dsc
   windows_performance
   windows_faq