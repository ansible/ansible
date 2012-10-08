.. _nagios:

nagios
``````````````````````````````

.. versionadded:: 0.7

The ``nagios`` module has two basic functions: scheduling downtime and toggling alerts for services or hosts. 
All actions require the ``host`` parameter to be given explicitly. In playbooks you can use the ``$inventory_hostname`` variable to refer to the host the playbook is currently running on. 
You can specify multiple services at once by separating them with commas, .e.g., ``services=httpd,nfs,puppet``. 
When specifying what service to handle there is a special service value, *host*, which will handle alerts/downtime for the *host itself*, e.g., ``service=host``. This keyword may not be given with other services at the same time. *Setting alerts/downtime for a host does not affect alerts/downtime for any of the services running on it.* 
When using the ``nagios`` module you will need to specify your nagios server using the ``delegate_to`` parameter. 

.. raw:: html

    <table>
    <tr>
    <th class="head">parameter</th>
    <th class="head">required</th>
    <th class="head">default</th>
    <th class="head">choices</th>
    <th class="head">comments</th>
    </tr>
        <tr>
    <td>action</td>
    <td>yes</td>
    <td></td>
    <td><ul><li>downtime</li><li>enable_alerts</li><li>disable_alerts</li><li>silence</li><li>unsilence</li></ul></td>
    <td>Action to take.</td>
    </tr>
        <tr>
    <td>host</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Host to operate on in Nagios.</td>
    </tr>
        <tr>
    <td>author</td>
    <td>no</td>
    <td>Ansible</td>
    <td><ul></ul></td>
    <td>Author to leave downtime comments as. - Only useable with the <code>downtime</code> action.</td>
    </tr>
        <tr>
    <td>services</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>What to manage downtime/alerts for. Separate multiple services with commas.<code>service</code> is an alias for <code>services</code>.<b>Required</b> option when using the <code>downtime</code>, <code>enable_alerts</code>, and <code>disable_alerts</code> actions.</td>
    </tr>
        <tr>
    <td>minutes</td>
    <td>no</td>
    <td>30</td>
    <td><ul></ul></td>
    <td>Minutes to schedule downtime for.Only useable with the <code>downtime</code> action.</td>
    </tr>
        <tr>
    <td>cmdfile</td>
    <td>no</td>
    <td>auto-detected</td>
    <td><ul></ul></td>
    <td>Path to the nagios <em>command file</em> (FIFO pipe).Only required if auto-detection fails.</td>
    </tr>
        </table>

.. raw:: html

    <p>set 30 minutes of apache downtime</p>    <p><pre>
    nagios action=downtime minutes=30 service=httpd host=$inventory_hostname
    </pre></p>
    <p>schedule an hour of HOST downtime</p>    <p><pre>
    nagios action=downtime minutes=60 service=host host=$inventory_hostname
    </pre></p>
    <p>schedule downtime for a few services</p>    <p><pre>
    nagios action=downtime services=frob,foobar,qeuz host=$inventory_hostname
    </pre></p>
    <p>enable SMART disk alerts</p>    <p><pre>
    nagios action=enable_alerts service=smart host=$inventory_hostname
    </pre></p>
    <p>two services at once: disable httpd and nfs alerts</p>    <p><pre>
    nagios action=disable_alerts service=httpd,nfs host=$inventory_hostname
    </pre></p>
    <p>disable HOST alerts</p>    <p><pre>
    nagios action=disable_alerts service=host host=$inventory_hostname
    </pre></p>
    <p>silence ALL alerts</p>    <p><pre>
    nagios action=silence host=$inventory_hostname
    </pre></p>
    <p>unsilence all alerts</p>    <p><pre>
    nagios action=unsilence host=$inventory_hostname
    </pre></p>
    <br/>

