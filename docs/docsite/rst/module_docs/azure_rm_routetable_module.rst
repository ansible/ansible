.. _azure_rm_routetable:


azure_rm_routetable - Manage Azure route tables.
++++++++++++++++++++++++++++++++++++++++++++++++



.. contents::
   :local:
   :depth: 2


Synopsis
--------


* Create, update or delete a route tables. Allows setting and updating the available routes with cidr, type, and destination



Requirements (on host that executes module)
-------------------------------------------

  * python >= 2.7
  * azure >= 2.0.0


Options
-------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
                <tr>
            <th class="head"><div class="cell-border">parameter</div></th>
            <th class="head"><div class="cell-border">required</div></th>
            <th class="head"><div class="cell-border">default</div></th>
            <th class="head"><div class="cell-border">choices</div></th>
                        <th class="head"><div class="cell-border">comments</div></th>
        </tr>
                    <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            profile<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border"></div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>Security profile found in ~/.azure/credentials file.</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            resource_group<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">yes</div></td>
                                <td><div class="cell-border"></div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>name of resource group.</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            tags<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border"></div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>Dictionary of string:string pairs to assign as metadata to the object. Metadata tags on the object will be updated with any provided values. To remove tags set append_tags option to false.
    </div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            ad_user<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border"></div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>Active Directory username. Use when authenticating with an Active Directory user rather than service principal.</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            client_id<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border"></div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>Azure client ID. Use when authenticating with a Service Principal.</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            purge_routes<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border"></div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>Use with state present to remove any existing routes and replace with defined routes</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            password<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border"></div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>Active Directory user password. Use when authenticating with an Active Directory user rather than service principal.</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            tenant<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border"></div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>Azure tenant ID. Use when authenticating with a Service Principal.</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            name<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">yes</div></td>
                                <td><div class="cell-border"></div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>name of the virtual network.</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            append_tags<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border">True</div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>Use to control if tags field is canonical or just appends to existing tags. When canonical, any tags not found in the tags parameter will be removed from the object's metadata.</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            cloud_environment<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border">AzureCloud</div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>For cloud environments other than the US public cloud, the environment name (as defined by Azure Python SDK, eg, <code>AzureChinaCloud</code>, <code>AzureUSGovernment</code>), or a metadata discovery endpoint URL (required for Azure Stack). Can also be set via credential file profile or the <code>AZURE_CLOUD_ENVIRONMENT</code> environment variable.</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            secret<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border"></div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>Azure client secret. Use when authenticating with a Service Principal.</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            state<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border">present</div></td>
                                <td>
                    <div class="cell-border">
                                                                                    <ul>
                                                                            <li>absent</li>
                                                                            <li>present</li>
                                                                    </ul>
                                                                        </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>Assert the state of the virtual network. Use 'present' to create or update and 'absent' to delete.</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            location<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border">resource_group location</div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>Valid azure location. Defaults to location of the resource group.</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            routes<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border"></div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>A list of hashes which has address_prefix, next_hop_type, and next_hop_ip_address set to populate the routes in the route table</div>
                                                                                                </div>
                </td>
            </tr>
                                <tr class="return-value-column">
                                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            subscription_id<br/><div style="font-size: small;"></div>
                        </div>
                    <div class="outer-elbow-container">
                </td>
                                <td><div class="cell-border">no</div></td>
                                <td><div class="cell-border"></div></td>
                                <td>
                    <div class="cell-border">
                                                                                                </div>
                </td>
                                                                <td>
                    <div class="cell-border">
                                                                                    <div>Your Azure subscription Id.</div>
                                                                                                </div>
                </td>
            </tr>
                        </table>
    </br>

Examples
--------

.. code-block:: yaml

    
        - name: Create a virtual network
          azure_rm_routetable:
            name: foobar
            resource_group: Testing
            routes:
                -
                    name: "My Route Table"
                    address_prefix: "10.0.0.0/16"
                    next_hop_type: "VirtualAppliance"
                    next_hop_ip_address: "1.2.3.4"
            tags:
                testing: testing
                delete: on-exit

        - name: Delete a route table
          azure_rm_routetable:
            name: foobar
            resource_group: Testing
            state: absent


Return Values
-------------

Common return values are documented :ref:`here <common_return_values>`, the following are the fields unique to this {{plugin_type}}:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th class="head"><div class="cell-border">name</div></th>
            <th class="head"><div class="cell-border">description</div></th>
            <th class="head"><div class="cell-border">returned</div></th>
            <th class="head"><div class="cell-border">type</div></th>
            <th class="head"><div class="cell-border">sample</div></th>
        </tr>
                    <tr class="return-value-column">
                <td>
                    <div class="outer-elbow-container">
                                                <div class="elbow-key">
                            state
                        </div>
                    </div>
                </td>
                <td>
                                            <div class="cell-border">Current state of the route table</div>
                                    </td>
                <td align=center><div class="cell-border">always</div></td>
                <td align=center><div class="cell-border">dict</div></td>
                <td align=center><div class="cell-border">{'name': 'my_route_table', 'tags': None, 'provisioning_state': 'Succeeded', 'etag': 'W/&quot;0712e87c-f02f-4bb3-8b9e-2da0390a3886&quot;', 'location': 'eastus', 'routes': [{'next_hop_type': 'VirtualAppliance', 'name': 'myrt', 'etag': 'W/&quot;0712e87c-f02f-4bb3-8b9e-2da0390a3886&quot;', 'next_hop_ip_address': '1.2.3.4', 'address_prefix': '10.0.0.0/16', 'id': '/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/routeTables/myrt/routes/my_route_name', 'provisioning_state': 'Succeeded'}], 'type': 'Microsoft.Network/routeTables', 'id': '/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/routet/Testing/providers/Microsoft.Network/routeTables/myrt'}</div></td>
            </tr>
                        </table>
    </br></br>


Notes
-----

.. note::
    - For authentication with Azure you can pass parameters, set environment variables or use a profile stored in ~/.azure/credentials. Authentication is possible using a service principal or Active Directory user. To authenticate via service principal, pass subscription_id, client_id, secret and tenant or set environment variables AZURE_SUBSCRIPTION_ID, AZURE_CLIENT_ID, AZURE_SECRET and AZURE_TENANT.
    - To authenticate via Active Directory user, pass ad_user and password, or set AZURE_AD_USER and AZURE_PASSWORD in the environment.
    - Alternatively, credentials can be stored in ~/.azure/credentials. This is an ini file containing a [default] section and the following keys: subscription_id, client_id, secret and tenant or subscription_id, ad_user and password. It is also possible to add additional profiles. Specify the profile by passing profile or setting AZURE_PROFILE in the environment.


Author
~~~~~~

    * Thomas Vachon (@TomVachon)




Status
~~~~~~

This module is flagged as **preview** which means that it is not guaranteed to have a backwards compatible interface.



If you want to help with development, please read :doc:`../../community`,
:doc:`../../dev_guide/testing` and :doc:`../../dev_guide/developing_modules`.