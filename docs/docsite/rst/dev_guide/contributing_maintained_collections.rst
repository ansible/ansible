
.. _contributing_maintained_collections:

***********************************************
Contributing to Ansible-maintained Collections
***********************************************

The Ansible team welcomes community contributions to the collections maintained by Red Hat Ansible Engineering. This section describes how to open issue and create PRs with the required testing to speed merging your contributions.

Ansible-maintained collections
=================================


.. raw:: html

  <style>
  /* Style for this single table.  Add delimiters between header columns */
  table#ansible-collection-table  th {
    border-width: 1px;
    border-color: #dddddd /*rgb(225, 228, 229)*/;
    border-style: solid;
    text-align: center;
    padding: 5px;
    background-color: #eeeeee;
  }
  tr, td {
   border-width: 1px;
   border-color: rgb(225, 228, 229);
   border-style: solid;
   text-align: center;
   padding: 5px;

 }
  </style>

  <table id="ansible-collection-table">
    <tr>
      <th colspan="3">Collection details</th>
      <th colspan="4">Test requirements</th>
      <th colspan="2">Developer details</th>
    </tr>
    <tr>
      <th>Ansible collection</th>
      <th>Community collection</th>
      <th>Sponsor</th>
      <th>Sanity</th>
      <th>Unit</th>
      <th>Integration</th>
      <th>CI Platform</th>
      <th>Open to PRs*</th>
      <th>Guidelines</th>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/amazon/aws">amazon.aws</a></td>
      <td><a href="https://galaxy.ansible.com/community/aws">community.aws</a></td>
      <td><a href="https://github.com/ansible/community/tree/master/group-aws">Cloud</a></td>
      <td>✓</td>
      <td>✓</td>
      <td>✓</td>
      <td>Shippable</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/devel/dev_guide/platforms/aws_guidelines.html">AWS guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/ansible/netcommon">ansible.netcommon**</a></td>
      <td><a href="https://galaxy.ansible.com/community/netcommon">community.netcommon</a></td>
      <td><a href="https://github.com/ansible/community/wiki/Network">Network</a></td>
      <td>✓</td>
      <td>✓</td>
      <td>✓</td>
      <td>Zuul</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/devel/network/dev_guide/index.html">Network guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/ansible/posix">ansible.posix</a></td>
      <td><a href="https://galaxy.ansible.com/community/general">community.general</a></td>
      <td>Linux</a></td>
      <td>✓</td>
      <td></td>
      <td></td>
      <td>Shippable</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/latest/dev_guide/index.html">Developer guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/ansible/windows">ansible.windows</a></td>
      <td><a href="https://galaxy.ansible.com/community/windows">community.windows</a></td>
      <td><a href="https://github.com/ansible/community/wiki/Windows">Windows</a></td>
      <td>✓</td>
      <td>✓***</td>
      <td>✓</td>
      <td>Shippable</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_general_windows.html#developing-modules-general-windows">windows guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/ansible/eos">ansible.eos</a></td>
      <td><a href="https://galaxy.ansible.com/community/eos">community.eos</a></td>
      <td><a href="https://github.com/ansible/community/wiki/Network">Network</a></td>
      <td>✓</td>
      <td>✓</td>
      <td>✓</td>
      <td>Zuul</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/devel/network/dev_guide/index.html">Network guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/cisco/asa">cisco.asa</a></td>
      <td><a href="https://galaxy.ansible.com/community/asa">community.asa</a></td>
      <td><a href="https://github.com/ansible/community/wiki/Network">Network</a></td>
      <td>✓</td>
      <td>✓</td>
      <td>✓</td>
      <td>Zuul</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/latest/dev_guide/index.html">Developer guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/cisco/ios">cisco.ios</a></td>
      <td><a href="https://galaxy.ansible.com/community/network">community.network</a></td>
      <td><a href="https://github.com/ansible/community/wiki/Network">Network</a></td>
      <td>✓</td>
      <td>✓</td>
      <td>✓</td>
      <td>Zuul</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/devel/network/dev_guide/index.html">Network guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/cisco/iosxr">cisco.iosxr</a></td>
      <td><a href="https://galaxy.ansible.com/community/network">community.network</a></td>
      <td><a href="https://github.com/ansible/community/wiki/Network">Network</a></td>
      <td>✓</td>
      <td>✓</td>
      <td>✓</td>
      <td>Zuul</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/devel/network/dev_guide/index.html">Network guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/cisco/nxos">cisco.nxos</a></td>
      <td><a href="https://galaxy.ansible.com/community/network">community.network</a></td>
      <td><a href="https://github.com/ansible/community/wiki/Network">Network</a></td>
      <td>✓</td>
      <td>✓</td>
      <td>✓</td>
      <td>Zuul</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/devel/network/dev_guide/index.html">Network guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/ibm/qradar">ibm.qradar</a></td>
      <td><a href="https://galaxy.ansible.com/community/qradar">community.qradar</a></td>
      <td><a href="https://github.com/ansible/community/wiki/Security">Security</a></td>
      <td>✓</td>
      <td></td>
      <td>✓</td>
      <td>Zuul</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/latest/dev_guide/index.html">Developer guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/junipernetworks/junos">junipernetworks.junos</a></td>
      <td><a href="https://galaxy.ansible.com/community/network">community.network</a></td>
      <td><a href="https://github.com/ansible/community/wiki/Network">Network</a></td>
      <td>✓</td>
      <td>✓</td>
      <td>✓</td>
      <td>Zuul</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/devel/network/dev_guide/index.html">Network guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/openvswitch/openvswitch">openvswitch.openvswitch</a></td>
      <td><a href="https://galaxy.ansible.com/community/network">community.network</a></td>
      <td><a href="https://github.com/ansible/community/wiki/Network">Network</a></td>
      <td>✓</td>
      <td>✓</td>
      <td>✓</td>
      <td>Zuul</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/devel/network/dev_guide/index.html">Network guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/splunk/enterprise_security">splunk.enterprise_security</a></td>
      <td><a href="https://galaxy.ansible.com/community/enterprise_security">community.enterprise_security</a></td>
      <td><a href="https://github.com/ansible/community/wiki/Security">Security</a></td>
      <td>✓</td>
      <td></td>
      <td>✓</td>
      <td>Zuul</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/latest/dev_guide/index.html">Developer guide</a></td>
    </tr>
    <tr>
      <td><a href="https://galaxy.ansible.com/vyos/vyos">vyos.vyos</a></td>
      <td><a href="https://galaxy.ansible.com/community/network">community.network</a></td>
      <td><a href="https://github.com/ansible/community/wiki/Network">Network</a></td>
      <td>✓</td>
      <td>✓</td>
      <td>✓</td>
      <td>Zuul</td>
      <td>✓</td>
      <td><a href="https://docs.ansible.com/ansible/devel/network/dev_guide/index.html">Network guide</a></td>
    </tr>
  </table>


.. note::

  \* A ✓ means that all features/defects on existing content may be proposed as GitHub issues and pull requests directly in the GitHub repository for each collection listed above.

  \*\* This collection contains all foundational components for enabling many network and security :ref:`platform <platform_options>` collections. It contains all connection and filter plugins required, and is installed as a dependency automatically from the platform collection.

  \*\*\* Unit tests for Windows PowerShell modules are an exception to testing, but unit tests are valid and required for the remainder of the collection including Ansible-side plugins.


Community Contributor Inclusion Criteria For All Ansible-maintained Collections
===============================================================================

The community is what drives open source innovation, and Red Hat welcomes contributions to its sponsored and maintained collections. The above collections are specifically called out in this document because they are consumed as part of a downstream supported Red Hat product, and therefore the criteria for contribution, testing, and release may be higher than other community collections. More general community collections (such as community.general, community.network, etc.) may have fewer barriers to entry, and may also be a great place for fostering new functionality that may be someday graduated to an above platform collection.

Some situational examples:


1. You have a bugfix pull request against a module in the `arista.eos` collection. This pull request can be raised directly in the collection :ref:`arista.eos GitHub repository itself<https://github.com/ansible-collections/arista.eos>`_. It will be subject to all requirements (see below) prior to being merged.
2. There is a new parsing engine for the Arista EOS platform utilizing a newly developed Ansible Module. This feature request may proceed in one of the following paths:
    1. Place new module in the existing `arista.eos` collection (requires approval from Arista and Red Hat).
    2. Place new module in the `arista` namespace but in a new collection (requires approval from Arista and Red Hat).
    3. Place new module in the `community.network` collection (requires network community approval).
    4. Place new module in a new or existing collection in your own namespace (no approvals required).

    The goal for this new submission is to be well established in the community prior to being graduated to the `arista` namespace, where inclusion and maintenance criteria are much higher. Therefore, Red Hat recommends new content submissions start in either option d) or c) above and then over time possibly be nominated and promoted to option b) or a) with approval.




For submissions to be merged in a collection listed above, the following requirements should be met:



1. It should be in the scope of intent of the collection
2. It should follow the resource module development principles defined below, if applicable (network and/or security domains).
3. Passed sanity, unit and integration tests, if applicable per table above
4. Follow Ansible :ref:`developing_modules`  and :ref:`developing_collections` guidelines
5. All review comments addressed

Network and Security Resource Module Definition (Domain Specific)
==================================================================

Resource modules defined as Ansible module which manages the configuration of logical network function or configuration stanza for eg. interfaces, VLANs etc on a network device in a structured format and supports fetching of the same configuration data that it manages from the network device as Ansible facts in the same structural hierarchical format as defined by Ansible resource module argument specification.

The resource module should have two top-level keys namely config and state.

The config key should define the resource configuration data model as a key-value pair, the type of config option can be dict or list of dict based on the resource managed that is if the device has a single global configuration it should be a dict (eg. global lldp configuration) and if it has multiple instances of configuration it should be of type list with each element in list as dict. (eg. interfaces configuration).

The state key should have values merged, replaced, overridden, deleted, parsed, gathered and rendered.



1. merged: configuration merged with the provided configuration (<span style="text-decoration:underline;">default</span>)
2. replaced: configuration of provided resources will be replaced with the provided configuration
3. overridden: The configuration of the provided resources will be replaced with the provided configuration, extraneous resource instances will be removed
4. deleted: The configuration of the provided resources will be deleted/defaulted.
5. rendered: Will transform the configuration in C(config) option to platform-specific CLI commands which will be returned in the I(rendered) key within the result. For state I(rendered) active connection to the remote host is not required.
6. gathered: will fetch the running configuration from the device and transform it into structured data in the format as per the resource module argspec and the value is returned in the I(gathered) key within the result.
7. parsed: reads the configuration from C(running_config) option and transforms it into JSON format as per the resource module parameters and the value is returned in the I(parsed) key within the result. The value of C(running_config) option should be the same format as the output of show command executed to get configuration of resource on the device. For state, I(parsed) active connection to the remote host is not required.

.. note::

	The states I(rendered), I(gathered) and I(parsed) do not perform any change on the device.

More resources:

:ref:`Network features in 2.9 <https://www.ansible.com/blog/network-features-coming-soon-in-ansible-engine-2.9>`_

Network and Security Resource Module Development (Domain Specific)
==================================================================

The Ansible Engineering team ensures the module design and code pattern is uniform across resources and across platforms to give a vendor-agnostic feel and deliver good quality code. To achieve this we have developed a resource module scaffolding tool :ref:`resource module builder <https://github.com/ansible-network/resource_module_builder>`_.

Though it is not mandatory to use this tool while developing a resource module it highly recommends to use it though. Since this tool is under active development and we strive to ensure the scaffolded code is optimized and reduce module development time it is subject to change in future.

Before writing code for the resource module ensure the model design is shared in the :ref:`resource module models repo <https://github.com/ansible-network/resource_module_models>`_ in form of PR for review.

Integration test
================

See the :ref:`network test details <https://github.com/ansible/community/blob/master/group-network/network_test.rst>`_.


Requirements to be met:


1. Every state should have a testcase, Apat from testcases for every state, additional testcases should be written to test the behavior of the module when empty config is given (empty_config.yaml)
2. Round Trip Testcase should be added. This involves, a merge operation, followed by gather_facts, a merge update with additional config and reverting back to the base config using the previously gathered facts and state as overridden.
3. Wherever applicable, assertions should check after and before dicts against hard coded Source of Truth.

We use Zuul CI to run the integration test. To view, the report click Details on the CI comment in PR.



*   To view failure report
    *   Click on the ansible/check-> details ->  failure job -> Logs -> controller -> ara-report
*   To view ansible run logs (debug test failures)
    *   Click on the ansible/check-> details ->  failure job -> Logs -> controller -> ansible-debug.txt or ansible-debug.html





*   To view logs while the test is running
    *   Check for your PR number in [the :ref:`Zull status board <https://dashboard.zuul.ansible.com/t/ansible/status>`_.
*   To Fix static test failure locally run command **“tox -e black” **inside the root folder of collection.



Unit test
=========

See  :ref:`unit module testing <https://docs.ansible.com/ansible/latest/dev_guide/testing_units_modules.html>`_.

Requirements to be met:



1. Testcases should be written for all the states with all possible combinations of config values.
2. Testcases should be written to test the error conditions ( negative scenarios).
3. The value of ‘changed’ and ‘commands’ keys are checked in every test case.

Unit testcases are run as part of the Zuul CI. Unit test suites are run on the latest python version supported by the CI setup.

The same procedure as the integration tests is followed to view the unit tests reports and logs.
