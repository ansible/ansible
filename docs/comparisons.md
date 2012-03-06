Comparisons
===========

Confused about how Ansible fits in?  Here's a comparison with some common tools.
Accuracy is important, so corrections are VERY welcome if we've got something wrong.
For space reasons, we can't list everybody's favorite management tool.

<table>
   <tr>
      <td></td>
      <td><B><U>Ansible</U></B></font></td>
      <td>Puppet</td>
      <td>Chef</td>
      <td>Func</td>
      <td>Capistrano</td>
   </tr>
   <tr>
      <td>Purpose</td>
      <td><B>Config, Deployment, Ad-Hoc</B></td>
      <td>Config, Deployment</td>
      <td>Config, Deployment</td>
      <td>Ad-Hoc</td>
      <td>Deployment</td>
   </tr>
   <tr>
      <td>Config Language</td>
      <td><B>Simple YAML format</B></td>
      <td>Custom DSL</td>
      <td>Ruby code</td>
      <td>None</td>
      <td>None</td>
   </tr>
   <tr>
      <td>Config Language Style</td>
      <td>Very simple, not expressive</td>
      <td>Very rich & expressive</td>
      <td>Very rich & expressive</td>
      <td>None</td>
      <td>None</td>
   </tr>
   <tr>
      <td>Config Ordering</td>
      <td><B>Simply ordered, with notifiers</B></td>
      <td>Strict dependency DAG</td>
      <td>Simply ordered</td>
      <td>None</td>
      <td>Simply ordered</td>
   </tr>
   <tr>
      <td>Communication</td>
      <td>SSH push</td>
      <td>SSL pull or push trigger</td>
      <td>SSL pull or push trigger(?)</td>
      <td>SSL push</td>
      <td>SSH</td>
   </tr>
   <tr>
      <td>Daemons Required?</td>
      <td><B>no</B></td>
      <td>yes</td>
      <td>yes</td>
      <td>yes</td>
      <td><B>no</B></td>
   </tr>
   <tr>
      <td>Database Required</td>
      <td><B>no</B></td>
      <td>yes</td>
      <td>yes</td>
      <td><B>no</B></td>
      <td><B>no</B></td>
   </tr>
   <tr>
      <td>Inventory Features</td>
      <td>planned</td>
      <td><B>yes</B></td>
      <td><B>yes?</B></td>
      <td>some</td>
      <td>no</td>
   </tr>
   <tr>
      <td>Message Bus Required</td>
      <td><B>no</B></td>
      <td>yes</td>
      <td>yes</td>
      <td><B>no</B></td>
      <td><B>no</B></td>
   </tr>
   <tr>
      <td>Implemented In</td>
      <td>Python</td>
      <td>Ruby</td>
      <td>Ruby, Erlang</td>
      <td>Python</td>
      <td>Ruby</td>
   </tr>
   <tr>
      <td>Extensible In</td>
      <td><B>Anything</B></td>
      <td>Ruby</td>
      <td>Ruby</td>
      <td>Python</td>
      <td>Ruby</td>
   </tr>
   <tr>
      <td>Codebase Size</td>
      <td><B>Small</B></td>
      <td>Large</td>
      <td>Large</td>
      <td>Medium</td>
      <td>Medium</td>
   </tr>
   <tr>
      <td>Module Support</td>
      <td>Emerging</td>
      <td><B>Wide/Established</B></td>
      <td><B>Wide/Established</B></td>
      <td>Medium/Established</td>
      <td>Poor</td>
   </tr>
   <tr>
      <td>Users Targeted</td>
      <td><B>Sysadmins, developers, QA, web admins</B></td>
      <td>Sysadmins</td>
      <td>Sysadmins, web admins</td>
      <td>Sysadmins, developers</td>
      <td>Web admins</td>
   </tr>
   <tr>
      <td>Can Easily Build Applications On It</td>
      <td><B>Yes</B></td>
      <td>No</td>
      <td>No</td>
      <td><B>Yes</B></td>
      <td>No</td>
   </tr>
   <tr>
      <td>Parallelism & Scaling Tech</td>
      <td>Fork/Merge</td>
      <td>Add Servers / Staged Commands / No Server</td>
      <td>Adding More Erlang</td>
      <td>Fork/Merge</td>
      <td>No</td>
   </tr>
   <tr>
      <td>Delegated Hierachies</td>
      <td>No</td>
      <td>No</td>
      <td>No</td>
      <td><B>Yes</B></td>
      <td>No</td>
   </tr>
</td>


