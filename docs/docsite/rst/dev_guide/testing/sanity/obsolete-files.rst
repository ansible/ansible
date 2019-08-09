obsolete-files
==============

Directories in the Ansible source tree are sometimes made obsolete.
Files should not exist in these directories.
The new location (if any) is dependent on which directory has been made obsolete.

Below are some of the obsolete directories and their new locations:

- All of ``test/runner/`` is now under ``test/lib/ansible_test/`` instead. The organization of files in the new directory has changed.
- Most subdirectories of ``test/sanity/`` (with some exceptions) are now under ``test/lib/ansible_test/_data/sanity/`` instead.

This error occurs most frequently for open pull requests which add or modify files in directories which are now obsolete.
Make sure the branch you are working from is current so that changes can be made in the correct location.
