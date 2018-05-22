========================================
Ansible 2.6 "Heartbreaker" Release Notes
========================================

.. _Ansible 2.6 "Heartbreaker" Release Notes_v2.6.0a1:

v2.6.0a1
========

.. _Ansible 2.6 "Heartbreaker" Release Notes_v2.6.0a1_Release Summary:

Release Summary
---------------

| Release Date: 2018-05-21
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


.. _Ansible 2.6 "Heartbreaker" Release Notes_v2.6.0a1_Minor Changes:

Minor Changes
-------------

- azure_rm_loadbalancer - add support for sku

- azure_rm_publicipaddress - add support for sku

- Added an ``encoding`` option to the ``b64encode`` and ``b64decode`` filters to specify the encoding of the string that is base64 encoded.

- import/include - Cache task_vars to speed up IncludedFile.process_include_results (https://github.com/ansible/ansible/pull/39026)

- PowerShell modules that use Convert-ToSID in Ansible.ModuleUtils.SID.psm1 like win_user_right now accept an actual SID as an input string. This means any local or domain accounts that are named like a SID need to be prefixed with the domain, hostname, or . to ensure it converts to that accounts SID https://github.com/ansible/ansible/issues/38502


.. _Ansible 2.6 "Heartbreaker" Release Notes_v2.6.0a1_Removed Features (previously deprecated):

Removed Features (previously deprecated)
----------------------------------------

- win_chocolatey - removed deprecated upgrade option and choco_* output return values

- win_feature - removed deprecated reboot option

- win_iis_webapppool - removed the ability to supply attributes as a string in favour of a dictionary

- win_package - removed deprecated name option

- win_regedit - removed deprecated support for specifying HKCC as HCCC


.. _Ansible 2.6 "Heartbreaker" Release Notes_v2.6.0a1_Bugfixes:

Bugfixes
--------

- template - Fix for encoding issues when a template path contains non-ascii characters and using the template path in ansible_managed (https://github.com/ansible/ansible/issues/27262)

- copy - fixed copy to only follow symlinks for files in the non-recursive case

- file - fixed the default follow behaviour of file to be true

- copy module - The copy module was attempting to change the mode of files for remote_src=True even if mode was not set as a parameter.  This failed on filesystems which do not have permission bits (https://github.com/ansible/ansible/pull/40099)

- Fix an encoding issue when parsing the examples from a plugins' documentation

- file module - The file module allowed the user to specify src as a parameter when state was not link or hard.  This is documented as only applying to state=link or state=hard but in previous Ansible, this could have an effect in rare cornercases.  For instance, "ansible -m file -a 'state=directory path=/tmp src=/var/lib'" would create /tmp/lib.  This has been disabled and a warning emitted (will change to an error in Ansible-2.10).

- file module - Fix error when running a task which assures a symlink to a nonexistent file exists for the second and subsequent times (https://github.com/ansible/ansible/issues/39558)

- file module - Fix error when recursively assigning permissions and a symlink to a nonexistent file is present in the directory tree (https://github.com/ansible/ansible/issues/39456)

- file module - Eliminate an error if we're asked to remove a file but something removes it while we are processing the request (https://github.com/ansible/ansible/pull/39466)

- Various grafana_* modules - Port away from the deprecated b64encodestring function to the b64encode function instead. https://github.com/ansible/ansible/pull/38388

- import/include - Update TaskInclude _raw_params with the expanded/templated path to file allowing nested includes using host vars in file (https://github.com/ansible/ansible/pull/39365)

- dynamic includes - Don't treat undefined vars for conditional includes as truthy (https://github.com/ansible/ansible/pull/39377)

- import/include - Ensure role handlers have the proper parent, allowing for correct attribute inheritance (https://github.com/ansible/ansible/pull/39426)

- include_role/import_role - Use the computed role name for include_role/import_role so to diffentiate between names computed from host vars (https://github.com/ansible/ansible/pull/39516)

- import_playbook - Pass vars applied to import_playbook into parsing of the playbook as they may be needed to parse the imported plays (https://github.com/ansible/ansible/pull/39521)

- include_role/import_role - Don't overwrite included role handlers with play handlers on parse (https://github.com/ansible/ansible/pull/39563)

- dynamic includes - Improved performance by fixing re-parenting on copy (https://github.com/ansible/ansible/pull/38747)

- dynamic includes - Fix IncludedFile comparison for free strategy (https://github.com/ansible/ansible/pull/37083)

- dynamic includes - Allow inheriting attributes from static parents (https://github.com/ansible/ansible/pull/38827)

- include_role/import_role - improved performance and recursion depth (https://github.com/ansible/ansible/pull/36470)

- include_role/import_role - Fix parameter templating (https://github.com/ansible/ansible/pull/36372)

- dynamic includes - Use the copied and merged task for calculating task vars (https://github.com/ansible/ansible/pull/39762)

- Implement mode=preserve for the template module

- Fix mode=preserve with remote_src=True for the copy module

- Document mode=preserve for both the copy and template module

- pause - ensure ctrl+c interrupt works in all cases (https://github.com/ansible/ansible/issues/35372)

- spwd - With python 3.6 spwd.getspnam returns PermissionError instead of KeyError if user does not have privileges (https://github.com/ansible/ansible/issues/39472)

- template action plugin - fix the encoding of filenames to avoid tracebacks on Python2 when characters that are not present in the user's locale are present. (https://github.com/ansible/ansible/pull/39424)

- user - only change the expiration time when necessary (https://github.com/ansible/ansible/issues/13235)

- win_environment - Fix for issue where the environment value was deleted when a null value or empty string was set - https://github.com/ansible/ansible/issues/40450

- win_file - fix issue where special chars like [ and ] were not being handled correctly https://github.com/ansible/ansible/pull/37901

- win_get_url - fixed a few bugs around authentication and force no when using an FTP URL

- win_template - fix when specifying the dest option as a directory with and without the trailing slash https://github.com/ansible/ansible/issues/39886

- win_updates - Fix typo that hid the download error when a download failed

- win_updates - Fix logic when using a whitelist for multiple updates

- windows become - Show better error messages when the become process fails

- winrm - allow `ansible_user` or `ansible_winrm_user` to override `ansible_ssh_user` when both are defined in an inventory - https://github.com/ansible/ansible/issues/39844

- The yaml callback plugin now allows non-ascii characters to be displayed.

