Developing ACI modules
----------------------
This is a brief walk-through of how to create new ACI modules for Ansible.

Imports
.......
The following imports are standard across modules:

.. code-block:: python

    from ansible.module_utils.aci import ACIModule, aci_argument_spec
    from ansible.module_utils.basic import AnsibleModule


Argument Spec
.............
The first line adds the standard connection parameters to the module. After that, the next section will update the ``argument_spec`` dictionary with module specific parameters. The module specific parameters should include:

* the object_id (usually the name)
* configurable properties of the object
* the parent object IDs (all parents up to the root)
* only child classes that are a 1-to-1 relationship (1-to-many/many-to-many require their own module to properly manage)
* state

  + `present` to ensure the object and configs exist; this is also the default

  + `absent` to ensure object does not exist

  + `query` to retrieve information about objects in the class

.. code-block:: python

    def main():
        argument_spec = aci_argument_spec()
        argument_spec.update(
            object_id=dict(type='str', aliases=['name']),
            object_prop1=dict(type='str'),
            object_prop2=dict(type='str', choices=['choice1', 'choice2', 'choice3']),
            object_prop3=dict(type='int'),
            parent_id=dict(type='str'),
            child_object_id=dict(type='str'),
            child_object_prop=dict(type='str'),
            state=dict(type='str', choices=['absent', 'present', 'query'], default='present'),
        )


.. hint:: It is important to point out that all configuration arguments should not have a default value, as that could cause unintended changes to the object.

AnsibleModule
.............
The following section creates an AnsibleModule instance. The module should support check_mode, so we pass the ``argument_spec`` and  ``supports_check_mode`` arguments. Since these modules support querying the APIC for all objects of the module's class, the object/parent IDs should only be required if `state` is present or absent.

.. code-block:: python

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['object_id', 'parent_id']],
            ['state', 'present', ['object_id', 'parent_id']],
        ],
    )


Variable Definition
...................
Once the AnsibleModule object has been initiated, the necessary parameter values should be extracted from ``params`` and any data validation should be done. Usually the only params that need to be extracted are those related to the ACI object configuration and it's child configuration. If you have integer objects that you would like to validate, then the validation should be done here, and the ``ACIModule.payload()`` method will handle the str conversion.

.. code-block:: python

    object_id = object_id
    object_prop1 = module.params['object_prop1']
    object_prop2 = module.params['object_prop2']
    object_prop3 = module.params['object_prop3']
    if object_prop3 is not None and object_prop3 not in range(x, y):
        module.fail_json(msg='Valid object_prop3 values are between x and (y-1)')
    child_object_id = module.params[' child_objec_id']
    child_object_prop = module.params['child_object_prop']
    state = module.params['state']


ACIModule
.........
The ACIModule class handles most of the logic for the ACI modules. The ACIModule extends functionality to the AnsibleModule object, so the module instance must be passed into the class instantiation.

.. code-block:: python

    aci = ACIModule(module)

The ACIModule has six main methods that are used by the modules:

* construct_url
* get_existing
* payload
* git_diff
* post_config
* delete_config

The first two methods are used regardless of what value is passed to the ``state`` parameter.

Construct URL
;;;;;;;;;;;;;
The ``construct_url()`` method is used to dynamically build the appropriate URL to interact with the object, and the appropriate filter string that should be appended to the URL to filter the results.

* When the ``state`` is not ``query``, the URL is the base URL to access the APIC plus the distinguished name to access the object. The filter string will restrict the returned data to just the configuration data.
* When ``state`` is ``query``, the URL and filter string used depends on what parameters are passed to the object. This method handles the complexity so that it is easier to add new modules and so that all modules are consistent in what type of data is returned.

.. note:: Our design goal is to take all ID parameters that have values, and return the most specific data possible. If no ID parameters are supplied by the task, then all objects of the class will be returned. If all ID parameters are passed, then the data for the specific object is returned. If a partial set of ID parameters are passed, then the module will use the IDs that are passed to build the URL and filter strings appropriately.

The ``construct_url()`` method takes 2 required arguments:

* **self** - passed automatically with the class instance
* **root_class** - A dictionary consisting of ``aci_class``, ``aci_rn``, ``target_filter``, and ``module_object`` keys

  + **aci_class**: The name of the class used by the APIC, e.g. ``fvTenant``

  + **aci_rn**: The relative name of the object, e.g. ``tn-ACME``

  + **target_filter**: A dictionary with key-value pairs that make up the query string for selecting a subset of entries, e.g. ``{'name': 'ACME'}``

  + **module_object**: The particular object for this class, e.g. ``ACME``

Example:

.. code-block:: python

    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{0}'.format(tenant),
            target_filter={'name': tenant},
            module_object=tenant,
        ),
    )

Some modules, like ``aci_tenant``, are the root class and so they would not need to pass any additional arguments to the method.

The ``construct_url()`` method takes 4 optional arguments, the first three imitate the root class as described above, but are for child objects:

* subclass_1 - A dictionary consisting of ``aci_class``, ``aci_rn``, ``target_filter``, and ``module_object`` keys

  + Example: Application Profile Class (AP)

* subclass_2 - A dictionary consisting of ``aci_class``, ``aci_rn``, ``target_filter``, and ``module_object`` keys

  + Example: End Point Group (EPG)

* subclass_3 - A dictionary consisting of ``aci_class``, ``aci_rn``, ``target_filter``, and ``module_object`` keys

  + Example: Binding a Contract to an EPG

* child_classes - The list of APIC names for the child classes supported by the modules.

  + This is a list, even if it is a list of one

  + These are the unfriendly names used by the APIC

  + These are used to limit the returned child_classes when possible

  + Example: ``child_classes=['fvRsBDSubnetToProfile', 'fvRsNdPfxPol']``

.. note:: Sometimes the APIC will require special characters ([, ], and -) or will use object metadata in the name ("vlanns" for VLAN pools); the module should handle adding special characters or joining of multiple parameters in order to keep expected inputs simple.

Get Existing
............
Once the URL and filter string have been built, the module is ready to retrieve the existing configuration for the object:

* ``present`` retrieves the configuration to use as a comparison against what was entered in the task. All values that are different than the existing values will be updated.
* ``absent`` uses the existing configuration to see if the item exists and needs to be deleted.
* ``query`` uses this to perform the query for the task and report back the existing data.

.. code-block:: python

    aci.get_existing()


State is Present
................
When the state is present, the module needs to perform a diff against the existing configuration and the task entries. If any value needs to be updated, then the module will make a POST request with only the items that need to be updated. Some modules have children that are in a 1-to-1 relationship with another object; for these cases, the module can be used to manage the child objects.

ACI Payload Method
;;;;;;;;;;;;;;;;;;
The ``aci.payload()`` method is used to build a dictionary of the proposed object configuration. All parameters that were not provided a value in the task will be removed from the dictionary (both for the object and its children). Any parameter that does have a value will be converted to a string and added to the final dictionary object that will be used for comparison against the existing configuration.

The ``aci.payload()`` method takes two required arguments and 1 optional argument, depending on if the module manages child objects.

* ``aci_class`` is the APIC name for the object's class, e.g. ``aci_class='fvBD'``

* ``class_config`` is the appropriate dictionary to be used as the payload for the POST request

  + The keys should match the names used by the APIC.

  + The values should be the corresponding value in ``module.params``; these are the variables defined above

* ``child_configs`` is optional, and is a list of child config dictionaries.

  + The child configs include the full child object dictionary, not just the attributes configuration portion.

  + The configuration portion is built the same way that the object is done.

.. code-block:: python

    aci.payload(
        aci_class=aci_class,
        class_config=dict(
            name=bd,
            descr=description,
            type=bd_type,
        ),
        child_configs=[
            dict(fvRsCtx=dict(attributes=dict(tnFvCtxName=vrf))),
        ],
    )


Get the Config Diff and Make the POST Request
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
The ``get_diff()`` method is used to perform the diff, and takes only one required argument, ``aci_class``.
Example: ``aci.get_diff(aci_class='fvBD')``

The ``post_config()`` method is used to make the POST request to the APIC if needed. This method doesn't take any arguments and handles check mode.
Example: ``aci.post_config()``

Full Example
;;;;;;;;;;;;

.. code-block:: python

    if state == 'present':
        aci.payload(
            aci_class='<object APIC class>',
            class_config=dict(
                name=object_id,
                prop1=object_prop1,
                prop2=object_prop2,
                prop3=object_prop3,
            ),
            child_configs=[
                dict(
                    '<child APIC class>'=dict(
                        attributes=dict(
                            child_key=child_object_id,
                            child_prop=child_object_prop
                        ),
                    ),
                ),
            ],
        )
        
        aci.get_diff(aci_class='<object APIC class>')
        
        aci.post_config()


State is Absent
...............
If the task sets the state to absent, then the ``delete_config()`` method is all that is needed. This method does not take any arguments, and handles check mode.

.. code-block:: python

    elif state == 'absent':
        aci.delete_config()


Module Exit
...........
To have the module exit, call the ACIModule method ``exit_json()``. This method automatically takes care of returning the common return values for you.

.. code-block:: python

        aci.exit_json()

    if __name__ == '__main__':
        main()


Testing ACI library functions
.............................
You can test your ``construct_url()`` and ``payload()`` arguments without accessing APIC hardware by using the following python script:

.. code-block:: python

    #!/usr/bin/python
    import json
    from ansible.module_utils.network.aci.aci import ACIModule
    
    # Just another class mimicking a bare AnsibleModule class for construct_url() and payload() methods
    class AltModule():
        params = dict(
            host='dummy',
            port=123,
            protocol='https',
            state='present',
            output_level='debug',
        )
    
    # A sub-class of ACIModule to overload __init__ (we don't need to log into APIC)
    class AltACIModule(ACIModule):
        def __init__(self):
            self.result = dict(changed=False)
            self.module = AltModule()
            self.params = self.module.params
    
    # Instantiate our version of the ACI module
    aci = AltACIModule()
    
    # Define the variables you need below
    aep = 'AEP'
    aep_domain = 'uni/phys-DOMAIN'
    
    # Below test the construct_url() arguments to see if it produced correct results
    aci.construct_url(
        root_class=dict(
            aci_class='infraAttEntityP',
            aci_rn='infra/attentp-{}'.format(aep),
            target_filter={'name': aep},
            module_object=aep,
        ),
        subclass_1=dict(
            aci_class='infraRsDomP',
            aci_rn='rsdomP-[{}]'.format(aep_domain),
            target_filter={'tDn': aep_domain},
            module_object=aep_domain,
        ),
    )
    
    # Below test the payload arguments to see if it produced correct results
    aci.payload(
        aci_class='infraRsDomP',
        class_config=dict(tDn=aep_domain),
    )
    
    # Print the URL and proposed payload
    print 'URL:', json.dumps(aci.url, indent=4)
    print 'PAYLOAD:', json.dumps(aci.proposed, indent=4)


This will result in:

.. code-block:: yaml

    URL: "https://dummy/api/mo/uni/infra/attentp-AEP/rsdomP-[phys-DOMAIN].json"
    PAYLOAD: {
        "infraRsDomP": {
            "attributes": {
                "tDn": "phys-DOMAIN"
            }
        }
    }

Testing for sanity checks
.........................
You can run from your fork something like:

.. code-block:: bash

    $ ./test/runner/ansible-test sanity --python 2.7 lib/ansible/modules/network/aci/aci_tenant.py


Testing ACI integration tests
.............................
You can run this:

.. code-block:: bash

    $ ./test/runner/ansible-test network-integration --continue-on-error --allow-unsupported --diff -v aci_tenant

.. note:: You may need to add ``--python 2.7`` or ``--python 3.6`` in order to use the correct python version for performing tests.

You may want to edit the used inventory at *./test/integration/inventory.networking* and add something like:

.. code-block:: ini

    [aci:vars]
    aci_hostname=my-apic-1
    aci_username=admin
    aci_password=my-password
    aci_use_ssl=yes
    aci_use_proxy=no
    
    [aci]
    localhost ansible_ssh_host=127.0.0.1 ansible_connection=local


Testing for test coverage
.........................
You can run this:

.. code-block:: bash

    $ ./test/runner/ansible-test integration --python 2.7 --coverage aci_tenant
    $ ./test/runner/ansible-test coverage report
