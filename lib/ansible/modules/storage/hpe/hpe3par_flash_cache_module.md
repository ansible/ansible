source

:   storage/hpe/hpe3par\_flash\_cache.py

hpe3par\_flash\_cache - Manage HPE 3PAR Flash Cache
===================================================

Synopsis
--------

-   Create and delete Flash Cache on HPE 3PAR.

### Requirements

The below requirements are needed on the host that executes this module.

-   3PAR OS - 3.2.2 MU6, 3.3.1 MU1
-   Ansible - 2.4
-   hpe3par\_sdk 1.0.0
-   WSAPI service should be enabled on the 3PAR storage array.

Parameters
----------

<table  border=0 cellpadding=0 class="documentation-table">
            <tr>
        <th class="head"><div class="cell-border">Parameter</div></th>
        <th class="head"><div class="cell-border">Choices/<font color="blue">Defaults</font></div></th>
                    <th class="head" width="100%"><div class="cell-border">Comments</div></th>
    </tr>
                <tr class="return-value-column">
                            <td>
                <div class="outer-elbow-container">
                                            <div class="elbow-key">
                        <b>mode</b>
                                                                            </div>
                </div>
            </td>
                            <td>
                <div class="cell-border">
                                                                                                                                                                                        </div>
            </td>
                                                            <td>
                <div class="cell-border">
                                                                                <div>Simulator 1, Real 2 (default)</div>
                                                                                            </div>
            </td>
        </tr>
                            <tr class="return-value-column">
                            <td>
                <div class="outer-elbow-container">
                                            <div class="elbow-key">
                        <b>size_in_gib</b>
                                                                            </div>
                </div>
            </td>
                            <td>
                <div class="cell-border">
                                                                                                                                                                                        </div>
            </td>
                                                            <td>
                <div class="cell-border">
                                                                                <div>Specifies the node pair size of the Flash Cache on the system.</div>
                                                                                            </div>
            </td>
        </tr>
                            <tr class="return-value-column">
                            <td>
                <div class="outer-elbow-container">
                                            <div class="elbow-key">
                        <b>state</b>
                        <br/><div style="font-size: small; color: red">required</div>                                                    </div>
                </div>
            </td>
                            <td>
                <div class="cell-border">
                                                                                                                                                <ul><b>Choices:</b>
                                                                                                                                                                                <li>present</li>
                                                                                                                                                                                                                    <li>absent</li>
                                                                                            </ul>
                                                                                        </div>
            </td>
                                                            <td>
                <div class="cell-border">
                                                                                <div>Whether the specified Flash Cache should exist or not.</div>
                                                                                            </div>
            </td>
        </tr>
                            <tr class="return-value-column">
                            <td>
                <div class="outer-elbow-container">
                                            <div class="elbow-key">
                        <b>storage_system_ip</b>
                        <br/><div style="font-size: small; color: red">required</div>                                                    </div>
                </div>
            </td>
                            <td>
                <div class="cell-border">
                                                                                                                                                                                        </div>
            </td>
                                                            <td>
                <div class="cell-border">
                                                                                <div>The storage system IP address.</div>
                                                                                            </div>
            </td>
        </tr>
                            <tr class="return-value-column">
                            <td>
                <div class="outer-elbow-container">
                                            <div class="elbow-key">
                        <b>storage_system_name</b>
                                                                            </div>
                </div>
            </td>
                            <td>
                <div class="cell-border">
                                                                                                                                                                                        </div>
            </td>
                                                            <td>
                <div class="cell-border">
                                                                                <div>The storage system name.</div>
                                                                                            </div>
            </td>
        </tr>
                            <tr class="return-value-column">
                            <td>
                <div class="outer-elbow-container">
                                            <div class="elbow-key">
                        <b>storage_system_password</b>
                        <br/><div style="font-size: small; color: red">required</div>                                                    </div>
                </div>
            </td>
                            <td>
                <div class="cell-border">
                                                                                                                                                                                        </div>
            </td>
                                                            <td>
                <div class="cell-border">
                                                                                <div>The storage system password.</div>
                                                                                            </div>
            </td>
        </tr>
                            <tr class="return-value-column">
                            <td>
                <div class="outer-elbow-container">
                                            <div class="elbow-key">
                        <b>storage_system_username</b>
                        <br/><div style="font-size: small; color: red">required</div>                                                    </div>
                </div>
            </td>
                            <td>
                <div class="cell-border">
                                                                                                                                                                                        </div>
            </td>
                                                            <td>
                <div class="cell-border">
                                                                                <div>The storage system user name.</div>
                                                                                            </div>
            </td>
        </tr>
                    </table>
<br/>
Examples
--------

``` {.sourceCode .yaml}
- name: Create Flash Cache
  hpe3par_flash_cache:
    storage_system_ip="{{ storage_system_ip }}"
    storage_system_username="{{ storage_system_username }}"
    storage_system_password="{{ storage_system_password }}"
    state=present
    size_in_gib="{{ size_in_gib }}"

- name: Delete Flash Cache
  hpe3par_flash_cache:
    storage_system_ip="{{ storage_system_ip }}"
    storage_system_username="{{ storage_system_username }}"
    storage_system_password="{{ storage_system_password }}"
    state=absent
```

Status
------

This module is flagged as **preview** which means that it is not
guaranteed to have a backwards compatible interface.

### Author

-   Farhan Nomani (<nomani@hpe.com>)

> **hint**
>
> If you notice any issues in this documentation you can [edit this
> document](https://github.com/ansible/ansible/edit/devel/lib/ansible/modules/storage/hpe/hpe3par_flash_cache.py?description=%3C!---%20Your%20description%20here%20--%3E%0A%0A+label:%20docsite_pr)
> to improve it.
