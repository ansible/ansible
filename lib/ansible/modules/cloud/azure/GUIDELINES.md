
# Rules for Azure Ansible facts modules

## Input Parameters

Every facts module should at least contain following options. In most cases these options should be sufficient:

|Option|Description|Optional|
|------|-----------|--------|
|resource_group|Resource group name|YES|
|name|Resource Name|YES|
|tags|Tags that should be matched|YES|

Facts module should allow users to:
- query all the resources in a given subscription (if possible)
- query all the resources in a specific resource group (if possible)
- query specific resource instance
- filter resources by tags (if possible)

## Return value rules

Return values should be a composite of:
- input of the main module
    - structure should be preserved as closely as possible
    - fields should be omited only if impossible or difficult to retrieve
- additional read only fields assigned by the service, for instance:
    - resource **id** field
    - assigned **ip_address**
    - any other fields that may be important to the user, like URLs etc.

Following rules should be followed:
- return structure should have as short name as possible, for instance **servers**
- return structure should always be a **list of dictionaries**, even when single resource is queried
- every dictionary should be as flat as possible, no deep structures
- field names should be in **python_case** rather than camelCase
- field values should be exactly the same as equivalent input values of the main module (preferably both **python_case**)
- return structure should always contain resource **name**
- return structure should always contain **resource_group** name

Return values should be structured as in following example:

```
servers:
  - id: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx/resourceGroups/TestGroup/providers/Microsoft.DBforPostgreSQL/servers/postgreabdud1223
    resource_group: TestGroup
    name: postgreabdud1223
    location: eastus
    sku:
      name: GP_Gen4_2
      tier: GeneralPurpose
      capacity: 2
    version: "9.6"
    user_visible_state: Ready
    fully_qualified_domain_name: postgreabdud1223.postgres.database.azure.com
```

## Documenting Return Values

Facts module should include full documentation of return value, as in following example:

```
RETURN = '''
servers:
    description: A list of dictionaries containing facts for PostgreSQL servers.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx/resourceGroups/TestGroup/providers/Microsoft.DBforPostgreSQL/servers/postgreabdud1223
        resource_group:
            description:
                - Resource group name.
            returned: always
            type: str
            sample: TestGroup
        name:
            description:
                - Resource name.
            returned: always
            type: str
            sample: postgreabdud1223
        location:
            description:
                - The location the resource resides in.
            returned: always
            type: str
            sample: eastus
        sku:
            description:
                - The SKU of the server.
            returned: always
            type: complex
            contains:
                name:
                    description:
                        - The name of the SKU
                    returned: always
                    type: str
                    sample: GP_Gen4_2
                tier:
                    description:
                        - The tier of the particular SKU
                    returned: always
                    type: str
                    sample: GeneralPurpose
                capacity:
                    description:
                        - The scale capacity.
                    returned: always
                    type: int
                    sample: 2
        version:
            description:
                - Server version.
            returned: always
            type: str
            sample: "9.6"
        user_visible_state:
            description:
                - A state of a server that is visible to user.
            returned: always
            type: str
            sample: Ready
        fully_qualified_domain_name:
            description:
                - The fully qualified domain name of a server.
            returned: always
            type: str
            sample: postgreabdud1223.postgres.database.azure.com
'''
```

## Samples

Samples should include all possible combinations of input parameters showing how to:
- query all the resources of given type in an entire subscription
- query all the resources of given type in the resource group
- query specific resource
- filter resources by tags

## Testing

Following rules should apply to tests:
- Do not create a separate test, add **azure_xx_facts** tests to **azure_xx** module tests
- Do not create any additional instances of costly resources just to test facts - one is sufficient
- Test all possible parameter combinations
- Check if all expected return values are present in the structure
- Test if querying unexisting single instance fails correctly
 

