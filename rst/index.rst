
Introducing Ansible
```````````````````

Ansible is a radically simple model-driven configuration management, deployment, 
and command execution framework.  Other tools in this space have been too complicated for too long, 
require too much bootstrapping, and have too much learning curve.  By comparison, Ansible is dead simple 
and painless to extend. Puppet and Chef have about 60k lines of code.  Ansible's core is a little over 2000 lines.

Ansible isn't just for configuration management -- it's also great for ad-hoc tasks, quickly firing off commands against nodes, and it excels at complex multi-tier deployment tasks, being designed for that purpose from day one.  

Systems management doesn't have to be complicated.  We've learned well from the "Infrastructure is Code" movement.  
Infrastructure should be easy and powerful to command, but it should not look like code, lest it acquire the disadvantages of a software project -- bugs, complexity, and overhead.  Infrastructure configurations should be simple, easy to develop, and easy to audit.  This is Ansible's philosophy and the main reason it's different.  Read on, though, and we'll tell you more.

+---------------------------------------------------------------------+
| Key Features                                                        |
+=====================================================================+
| Dead simple setup                                                   |
+---------------------------------------------------------------------+
| Can be easily run from a checkout, no installation required         |
+---------------------------------------------------------------------+
| No agents or software to install on managed machines                |
+---------------------------------------------------------------------+
| Ultra-secure; uses existing SSHd out of the box                     |
+---------------------------------------------------------------------+
| Connect as any user, not just root, and sudo as needed              |
+---------------------------------------------------------------------+
| Super fast & parallel by default                                    |
+---------------------------------------------------------------------+
| Supports Kerberized SSH, jump hosts, forwarding, etc                | 
+---------------------------------------------------------------------+
| Modules are idempotent, but you can also easily use shell commands  |
+---------------------------------------------------------------------+
| Modules can be written in ANY language                              |
+---------------------------------------------------------------------+
| Awesome API for creating very powerful distributed applications     |
+---------------------------------------------------------------------+
| Pluggable transports (SSH is just the default)                      |
+---------------------------------------------------------------------+
| Can draw inventory data from external sources like EC2 and Cobbler  |
+---------------------------------------------------------------------+
| The easiest config management system to use, ever.                  |
+---------------------------------------------------------------------+

Architecture
````````````

.. image:: http://ansible.github.com/ansible_arch2.jpg
  :alt: "Architecture Diagram"
  :width: 800
  :align: center

+--------------------------------------------------------------------------------------------------------+
| Tell Me More                                                                                           |
+====================================+===================================================================+
| Multi-node control & orchestration | Ansible is especially strong at expressing complex multi-node     |
|                                    | deployment processes, executing ordered sequences on              |
|                                    | different sets of nodes through :doc:`playbooks`. Performing      |
|                                    | steps on all your webservers, then some steps on your database    |
|                                    | servers, and then some steps on monitoring servers -- all the     |
|                                    | while sharing variables between them is trivial.                  |
+------------------------------------+-------------------------------------------------------------------+
| Doesn't choose sides in the        | Modules can be written in Bash, Perl, Python, Ruby, whatever.     |
| language war                       | Playbooks are not a programming language, but a data format.      |
+------------------------------------+-------------------------------------------------------------------+
| Infrastructure Is Not Code,        | Playbooks are not a programming language, they are designed to be |
| Infrastructure Is Data             | super-easy to write, and easy to audit by non-developers.  You    |
|                                    | will be able to skim and very quickly understand your entire      |
|                                    | configuration policy.                                             |
+------------------------------------+-------------------------------------------------------------------+
| Three In One                       | Ansible handles multiple command and control                      |
|                                    | problems in one tool.  You don't need to use  a config tool, a    |
|                                    | deployment tool, and yet another ad-hoc parallel task execution   |
|                                    | tool -- Ansible will do all three.                                |
+------------------------------------+-------------------------------------------------------------------+  
| Lower Attack Surface, No Agents    | Ansible is very secure.  Ansible uses SSH as a transport,         |
|                                    | resulting in a much lower attack surface, and requires no agents  |
|                                    | to be running on managed machines.  If a central server           |
|                                    | containing your playbooks are comprimised, your nodes are not --  |
|                                    | which is NOT the case of most other tools, which can, more or     |
|                                    | less, turn into a botnet. Our security approach is to avoid       |
|                                    | writing custom crypto code altogether, and rely on the most       |
|                                    | secure part of the Linux/Unix subsystem that your machines are    |
|                                    | already using -- openssh.                                         |  
+------------------------------------+-------------------------------------------------------------------+  

+-----------------------------------------------------------------------------------------------------------+
| Community                                                                                                 |
+===========================================================================================================+
| Your ideas and contributions are welcome.  We're also happy to help                                       |
| you with questions about Ansible.                                                                         |
+------------------------+----------------------------------------------------------------------------------+
| Get the source         | Visit the `project page <https://github.com/ansible/ansible>`_ on Github         |
+------------------------+----------------------------------------------------------------------------------+
| File a bug             | View the `issue tracker <https://github.com/ansible/ansible/issues>`_            |
+------------------------+----------------------------------------------------------------------------------+
| Spread the word        | Watch slides on `Speakerdeck <http://speakerdeck.com/u/mpdehaan/p/ansible>`_     |
+------------------------+----------------------------------------------------------------------------------+
| Join the mailing list  | Visit the `Google Group <http://groups.google.com/group/ansible-project>`_       |
+------------------------+----------------------------------------------------------------------------------+
| Chat                   | Visit the channel on `FreeNode <http://webchat.freenode.net/?channels=ansible>`_ |
+------------------------+----------------------------------------------------------------------------------+
| Share & Learn          | Share `playbooks, modules, articles, and scripts <http://bit.ly/NNwUgY>`_        |
+------------------------+----------------------------------------------------------------------------------+

+-----------------------------------------------------------------------------------------------------------+
| What (Real) People Are Saying                                                                             |
+===========================================================================================================+
| "I've been trying to grok Chef these last weeks, and really, I don't get it. I discovered ansible         |
| yesterday at noon, successfully ran it at 1pm, made my first playbook by 2pm, and pushed two small        |
| [contributions to the project] before the office closed... Do that with any other config management       |
| software!"                                                                                                |
+-----------------------------------------------------------------------------------------------------------+
| "Ansible is much more firewall-friendly.  I have a number of hosts that are only accessible via reverse   |
| SSH tunnels, and let me tell you getting puppet or chef to play nice with that is a nightmare."           |
+-----------------------------------------------------------------------------------------------------------+
| "This software has really changed my life as an network admin, the simplicity ansible comes with is       |
| really childs-play and I really adore its design. No more hassle with SSL keys, DNS based 'server         |
| entries' (e.g. puppet and what not). Just plain (secure!) SSH keys and one is good to go."                |
+-----------------------------------------------------------------------------------------------------------+
| "You may get a kick out of the fact that I'm using ansible to install puppetmaster(s).  I'm starting to   |
| migrate all my stuff to the much more sensical ansible. Nice work."                                       |
+-----------------------------------------------------------------------------------------------------------+
| "Simple as hell"                                                                                          |
+-----------------------------------------------------------------------------------------------------------+
| "I swear, I have gotten more done with Ansible in three days than I did in not getting chef installed     |
| in three weeks."                                                                                          |
+-----------------------------------------------------------------------------------------------------------+
| "Puppet was hell... gave up on Chef... found ansible and couldn't be happier."                            |
+-----------------------------------------------------------------------------------------------------------+
| "Really impressed with Ansible. Up and running in ¼ of the time it took to get going with Puppet."        |
+-----------------------------------------------------------------------------------------------------------+

+--------------------------------------------------------------------------------------------------+
| Presented By...                                                                                  |
+==================================================================================================+
| Ansible was created and is run by `Michael DeHaan <http://michaeldehaan.net>`_                   |
| (`@laserllama <http://twitter.com/#!/laserllama>`_), a Raleigh, NC                               |
| based software developer and architect, who also created the popular open-source                 |
| DevOps install server `Cobbler <http://cobbler.github.com/>`_.                                   |
| Cobbler is used to deploy mission critical systems all over the                                  |
| planet, in industries ranging from massively multiplayer gaming, core                            |
| internet infrastructure, finance, chip design, and more.  Michael also                           |
| helped co-author `Func <http://fedorahosted.org/func/>`_, a precursor to Ansible, which is used  |
| to orchestrate systems in lots of diverse places.  He's worked on systems                        |
| software for IBM, Motorola, Red Hat's Emerging Technologies Group,                               |
| Puppet Labs, and is now with `rPath <http://rpath.com>`_.  Reach Michael by email                |
| `here <mailto:michael.dehaan@gmail.com>`_.                                                       |
+--------------------------------------------------------------------------------------------------+

Documentation
`````````````

.. toctree::
   :maxdepth: 1

   gettingstarted
   patterns
   examples
   modules
   YAMLSyntax
   playbooks
   playbooks2
   bestpractices
   api
   moduledev
   faq
   who_uses_ansible



