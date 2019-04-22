:source: cloud/amazon/dms_endpoint.py

:orphan:

.. _dms_endpoint_module:


dms_endpoint -- creates or destroys a data migration services endpoint
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. versionadded:: 2.9

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- creates or destroys a data migration services endpoint, that can be used to replicate data.



Requirements
------------
The below requirements are needed on the host that executes this module.

- python >= 2.6
- boto


Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
                        <th width="100%">Comments</th>
        </tr>
                    <tr>
                                                                <td colspan="1">
                    <b>aws_access_key</b>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>AWS access key. If not set then the value of the AWS_ACCESS_KEY_ID, AWS_ACCESS_KEY or EC2_ACCESS_KEY environment variable is used.</div>
                                                                                        <div style="font-size: small; color: darkgreen"><br/>aliases: ec2_access_key, access_key</div>
                                    </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>aws_region</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>alias for region</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>aws_secret_key</b>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>AWS secret key. If not set then the value of the AWS_SECRET_ACCESS_KEY, AWS_SECRET_KEY, or EC2_SECRET_KEY environment variable is used.</div>
                                                                                        <div style="font-size: small; color: darkgreen"><br/>aliases: ec2_secret_key, secret_key</div>
                                    </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>certificatearn</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Amazon Resource Name (ARN) for the certificate</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>databasename</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Name for the database on the origin or target side</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>debug_botocore_endpoint_logs</b>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                                            </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.8</div>                </td>
                                <td>
                                                                                                                                                                                                                    <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                                                                                                                                                <li><div style="color: blue"><b>no</b>&nbsp;&larr;</div></li>
                                                                                                                                                                                                <li>yes</li>
                                                                                    </ul>
                                                                            </td>
                                                                <td>
                                                                        <div>Use a botocore.endpoint logger to parse the unique (rather than total) &quot;resource:action&quot; API calls made during a task, outputing the set to the resource_actions key in the task results. Use the aws_resource_action callback to output to total list made during a playbook. The ANSIBLE_DEBUG_BOTOCORE_LOGS environment variable may also be used.</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>dmstransfersettings</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>The settings in JSON format for the DMS transfer type of source endpoint</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>dynamodbsettings</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Settings in JSON format for the target Amazon DynamoDB endpoint if source or target is dynamodb</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>ec2_region</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>alias for region</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>ec2_url</b>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Url to use to connect to EC2 or your Eucalyptus cloud (by default the module will use EC2 endpoints). Ignored for modules where region is required. Must be specified for all other modules if region is not used. If not set then the value of the EC2_URL environment variable, if any, is used.</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>elasticsearchsettings</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Settings in JSON format for the target Elasticsearch endpoint</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>endpointidentifier</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>An identifier name for the endpoint</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>endpointtype</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                            <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                                                                                                                                                <li>source</li>
                                                                                                                                                                                                <li>target</li>
                                                                                    </ul>
                                                                            </td>
                                                                <td>
                                                                        <div>Type of endpoint we want to manage</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>enginename</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                            <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                                                                                                                                                <li>mysql</li>
                                                                                                                                                                                                <li>oracle</li>
                                                                                                                                                                                                <li>postgres</li>
                                                                                                                                                                                                <li>mariadb</li>
                                                                                                                                                                                                <li>aurora</li>
                                                                                                                                                                                                <li>redshift</li>
                                                                                                                                                                                                <li>s3</li>
                                                                                                                                                                                                <li>db2</li>
                                                                                                                                                                                                <li>azuredb</li>
                                                                                                                                                                                                <li>sybase</li>
                                                                                                                                                                                                <li>dynamodb</li>
                                                                                                                                                                                                <li>mongodb</li>
                                                                                                                                                                                                <li>sqlserver</li>
                                                                                    </ul>
                                                                            </td>
                                                                <td>
                                                                        <div>Database engine that we want to use, please refer to the AWS DMS for more information on the supported engines and their limitation</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>externaltabledefinition</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>The external table definition</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>extraconnectionattributes</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Extra attributes for the database connection, the AWS documentation states &quot; For more information about extra connection attributes, see the documentation section for your data store.&quot;</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>kinesissettings</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Settings in JSON format for the target Amazon Kinesis Data Streams endpoint</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>kmskeyid</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Encryption key to use to encrypt replication storage and connection information</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>mongodbsettings</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Settings in JSON format for the source MongoDB endpoint</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>password</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Password used to connect to the database this attribute can only be written the AWS API does not return this parameter</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>port</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>TCP port for access to the database</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>profile</b>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Uses a boto profile. Only works with boto &gt;= 2.24.0.</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>region</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>aws region, should be read from the running aws config</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>retries</b>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>number of times we should retry when deleting a resource</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>s3settings</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>S3 buckets settings for the target Amazon S3 endpoint.</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>security_token</b>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>AWS STS security token. If not set then the value of the AWS_SECURITY_TOKEN or EC2_SECURITY_TOKEN environment variable is used.</div>
                                                                                        <div style="font-size: small; color: darkgreen"><br/>aliases: access_token</div>
                                    </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>servername</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Servername that the endpoint will connect to</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>serviceaccessrolearn</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Amazon Resource Name (ARN) for the service access role that you want to use to create the endpoint.</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>sslmode</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                            <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                                                                                                                                                <li><div style="color: blue"><b>none</b>&nbsp;&larr;</div></li>
                                                                                                                                                                                                <li>require</li>
                                                                                                                                                                                                <li>verify-ca</li>
                                                                                                                                                                                                <li>verify-full</li>
                                                                                    </ul>
                                                                            </td>
                                                                <td>
                                                                        <div>Mode used for the ssl connection</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>state</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                            <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                                                                                                                                                <li><div style="color: blue"><b>present</b>&nbsp;&larr;</div></li>
                                                                                                                                                                                                <li>absent</li>
                                                                                    </ul>
                                                                            </td>
                                                                <td>
                                                                        <div>State of the endpoint</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>tags</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>A list of tags to add to the endpoint</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>timeout</b>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>time in seconds we should wait for when deleting a resource</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>username</b>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                                        <div>Username our endpoint will use to connect to the database</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>validate_certs</b>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                                                                                    <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                                                                                                                                                <li>no</li>
                                                                                                                                                                                                <li><div style="color: blue"><b>yes</b>&nbsp;&larr;</div></li>
                                                                                    </ul>
                                                                            </td>
                                                                <td>
                                                                        <div>When set to &quot;no&quot;, SSL certificates will not be validated for boto versions &gt;= 2.6.0.</div>
                                                                                </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <b>wait</b>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                                            </div>
                                    </td>
                                <td>
                                                                                                                                                                                                                    <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                                                                                                                                                <li><div style="color: blue"><b>no</b>&nbsp;&larr;</div></li>
                                                                                                                                                                                                <li>yes</li>
                                                                                    </ul>
                                                                            </td>
                                                                <td>
                                                                        <div>should wait for the object to be deleted when state = absent</div>
                                                                                </td>
            </tr>
                        </table>
    <br/>


Notes
-----

.. note::
   - If parameters are not set within the module, the following environment variables can be used in decreasing order of precedence ``AWS_URL`` or ``EC2_URL``, ``AWS_ACCESS_KEY_ID`` or ``AWS_ACCESS_KEY`` or ``EC2_ACCESS_KEY``, ``AWS_SECRET_ACCESS_KEY`` or ``AWS_SECRET_KEY`` or ``EC2_SECRET_KEY``, ``AWS_SECURITY_TOKEN`` or ``EC2_SECURITY_TOKEN``, ``AWS_REGION`` or ``EC2_REGION``
   - Ansible uses the boto configuration file (typically ~/.boto) if no credentials are provided. See https://boto.readthedocs.io/en/latest/boto_config_tut.html
   - ``AWS_REGION`` or ``EC2_REGION`` can be typically be used to specify the AWS region, when required, but this can also be configured in the boto config file



Examples
--------

.. code-block:: yaml+jinja

    
    # Note: These examples do not set authentication details
    # Endpoint Creation
    - dms_endpoint:
        state: absent
        endpointidentifier: 'testsource'
        endpointtype: source
        enginename: aurora
        username: testing1
        password: testint1234
        servername: testing.domain.com
        port: 3306
        databasename: 'testdb'
        sslmode: none
        wait: false





Status
------




- This module is not guaranteed to have a backwards compatible interface. *[preview]*


- This module is :ref:`maintained by the Ansible Community <modules_support>`. *[community]*





Authors
~~~~~~~

- Rui Moreira (@ruimoreira)


.. hint::
    If you notice any issues in this documentation you can `edit this document <https://github.com/ansible/ansible/edit/devel/lib/ansible/modules/cloud/amazon/dms_endpoint.py?description=%23%23%23%23%23%20SUMMARY%0A%3C!---%20Your%20description%20here%20--%3E%0A%0A%0A%23%23%23%23%23%20ISSUE%20TYPE%0A-%20Docs%20Pull%20Request%0A%0A%2Blabel:%20docsite_pr>`_ to improve it.
