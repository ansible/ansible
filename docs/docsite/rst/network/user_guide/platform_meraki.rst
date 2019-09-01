.. _meraki_platform_options:

***************************************
Meraki Platform Options
***************************************

Meraki only support supports the ``local`` connection type at this time.

.. contents:: Topics

Connections Available
================================================================================

.. table::
    :class: documentation-table

    ====================  ==========================================
    ..                    Dashboard API
    ====================  ==========================================
    Protocol              HTTP(S)

    Credentials           uses API key from Dashboard

    Connection Settings   ``ansible_connection: localhost``

    Returned Data Format  ``data.``
    ====================  ==========================================


Example Meraki Task
-------------------

.. code-block:: yaml

  meraki_organization:
    auth_key: abc12345
    org_name: YourOrg
    state: present
  delegate_to: localhost
