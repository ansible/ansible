Directives Glossary
===================

Here we list the common playbook objects and their directives.
Note that not all directives affect the object itself and might just be there to be inherited by other contained objects.
Aliases for the directives are not reflected here, nor are mutable ones, for example `action` in task can be substituted by the name of any module plugin.

Be aware that this reflects the 'current development branch' and that the keywords do not have 'version_added' information.

.. contents::
   :local:
   :depth: 1


Play
----
  - **accelerate:** DEPRECATED, set to True to use accelerate connection plugin.
  - **accelerate_ipv6:** DEPRECATED, set to True to force accelerate plugin to use ipv6 for it's connection.
  - **accelerate_port:** DEPRECATED, set to override default port use for accelerate connection.
  - **always_run:** DEPRECATED, forces a task to run even in check mode, use check_mode directive instead.
  - **any_errors_fatal:** Force any un-handled task errors on any host to propagate to all hosts and end the play.
  - **become:** Boolean that controls if privilege escalation is used or not on Task execution.
  - **become_flags:** A string of flag(s) to pass to the privilege escalation program when ``become`` is True.
  - **become_method:** Which method of privilege escalation to use. i.e. sudo/su/etc.
  - **become_user:** User that you 'become' after using privilege escalation, the remote/login user must have permissions to become this user.
  - **check_mode:** A boolean that controls if a task is executed in 'check' mode
  - **connection:** Allows you to change the connection plugin used for tasks to execute on the target.
  - **environment:** A dictionary that gets converted into environment vars to be provided for the task upon execution.
  - **fact_path:** Set the fact path option for the fact gathering plugin controlled by ``gather_facts``.
  - **force_handlers:** Will force notified handler execution for hosts even if they failed during the play, it will not trigger if the play itself fails.
  - **gather_facts:** A boolean that controls if the play will automatically run the 'setup' task to gather facts for the hosts.
  - **gather_subset:** Allows you to pass subset options to the  fact gathering plugin controlled by ``gather_facts``.
  - **gather_timeout:** Allows you to set the timeout for the fact gathering plugin controlled by ``gather_facts``.
  - **handlers:** A section with tasks that are treated as handlers, these won't get executed normally, only when notified. After each section of tasks is complete.
  - **hosts:** A list of groups, hosts or host pattern that translates into a list of hosts that are the play's target.
  - **ignore_errors:** Boolean that allows you to ignore task failures and continue with play. It does not affect connection errors.
  - **max_fail_percentage:** can be used to abort the run after a given percentage of hosts in the current batch has failed.
  - **name:** It's a name, works mostly for documentation, in the case of tasks/handlers it can be an identifier.
  - **no_log:** Boolean that controls information disclosure.
  - **order:**  UNDOCUMENTED!! 
  - **port:** Used to override the default port used in a connection.
  - **post_tasks:** A list of tasks to execute after the ``tasks`` section.
  - **pre_tasks:** A list of tasks to execute before ``roles``.
  - **remote_user:** User used to log into the target via the connection plugin. AKA login user.
  - **roles:** List of roles to execute before the ``tasks`` section. Relative to ``roles_path`` defined in ansible config file.``$HOME/.ansible.cfg``
  - **run_once:** Boolean that will bypass the host loop, forcing the task to execute on the first host available and will also apply any facts to all active hosts.
  - **serial:** Defines the 'batch' of hosts to execute the current play until the end.
  - **strategy:** Allows you to choose the connection plugin to use for the play.
  - **tags:** Tags applied to the task or included tasks, this allows selecting subsets of tasks from the command line.
  - **tasks:** Main list of tasks to execute in the play, they run after ``roles`` and before ``post_tasks``.
  - **vars:** Dictionary/map of variables
  - **vars_files:** List of files that contain vars to include in the play.
  - **vars_prompt:** list of variables to prompt for.
  - **vault_password:** Secret used to decrypt vaulted files or variables.


Role
----
  - **always_run:** DEPRECATED, forces a task to run even in check mode, use check_mode directive instead.
  - **any_errors_fatal:** Force any un-handled task errors on any host to propagate to all hosts and end the play.
  - **become:** Boolean that controls if privilege escalation is used or not on Task execution.
  - **become_flags:** A string of flag(s) to pass to the privilege escalation program when ``become`` is True.
  - **become_method:** Which method of privilege escalation to use. i.e. sudo/su/etc.
  - **become_user:** User that you 'become' after using privilege escalation, the remote/login user must have permissions to become this user.
  - **check_mode:** A boolean that controls if a task is executed in 'check' mode
  - **connection:** Allows you to change the connection plugin used for tasks to execute on the target.
  - **delegate_facts:** Boolean that allows you to apply facts to delegated host instead of inventory_hostname.
  - **delegate_to:** Host to execute task instead of the target (inventory_hostname), connection vars from the delegated host will also be used for the task.
  - **environment:** A dictionary that gets converted into environment vars to be provided for the task upon execution.
  - **ignore_errors:** Boolean that allows you to ignore task failures and continue with play. It does not affect connection errors.
  - **no_log:** Boolean that controls information disclosure.
  - **port:** Used to override the default port used in a connection.
  - **remote_user:** User used to log into the target via the connection plugin. AKA login user.
  - **run_once:** Boolean that will bypass the host loop, forcing the task to execute on the first host available and will also apply any facts to all active hosts.
  - **tags:** Tags applied to the task or included tasks, this allows selecting subsets of tasks from the command line.
  - **vars:** Dictionary/map of variables
  - **when:** Conditional expression, determines if an iteration of a task is run or not.


Block
-----
  - **always:** List of tasks, in a block, that execute no matter if there is an error in the block or not.
  - **always_run:** DEPRECATED, forces a task to run even in check mode, use check_mode directive instead.
  - **any_errors_fatal:** Force any un-handled task errors on any host to propagate to all hosts and end the play.
  - **become:** Boolean that controls if privilege escalation is used or not on Task execution.
  - **become_flags:** A string of flag(s) to pass to the privilege escalation program when ``become`` is True.
  - **become_method:** Which method of privilege escalation to use. i.e. sudo/su/etc.
  - **become_user:** User that you 'become' after using privilege escalation, the remote/login user must have permissions to become this user.
  - **block:** List of tasks in a block.
  - **check_mode:** A boolean that controls if a task is executed in 'check' mode
  - **connection:** Allows you to change the connection plugin used for tasks to execute on the target.
  - **delegate_facts:** Boolean that allows you to apply facts to delegated host instead of inventory_hostname.
  - **delegate_to:** Host to execute task instead of the target (inventory_hostname), connection vars from the delegated host will also be used for the task.
  - **environment:** A dictionary that gets converted into environment vars to be provided for the task upon execution.
  - **ignore_errors:** Boolean that allows you to ignore task failures and continue with play. It does not affect connection errors.
  - **name:** It's a name, works mostly for documentation, in the case of tasks/handlers it can be an identifier.
  - **no_log:** Boolean that controls information disclosure.
  - **port:** Used to override the default port used in a connection.
  - **remote_user:** User used to log into the target via the connection plugin. AKA login user.
  - **rescue:** List of tasks in a block that run if there is a task error in the main ``block`` list.
  - **run_once:** Boolean that will bypass the host loop, forcing the task to execute on the first host available and will also apply any facts to all active hosts.
  - **tags:** Tags applied to the task or included tasks, this allows selecting subsets of tasks from the command line.
  - **vars:** Dictionary/map of variables
  - **when:** Conditional expression, determines if an iteration of a task is run or not.


Task
----
  - **action:** The 'action' to execute for a task, it normally translates into a C(module) or action plugin.
  - **always_run:** DEPRECATED, forces a task to run even in check mode, use check_mode directive instead.
  - **any_errors_fatal:** Force any un-handled task errors on any host to propagate to all hosts and end the play.
  - **args:**  UNDOCUMENTED!! 
  - **async:** Run a task asyncronouslly if the C(action) supports this.
  - **become:** Boolean that controls if privilege escalation is used or not on Task execution.
  - **become_flags:** A string of flag(s) to pass to the privilege escalation program when ``become`` is True.
  - **become_method:** Which method of privilege escalation to use. i.e. sudo/su/etc.
  - **become_user:** User that you 'become' after using privilege escalation, the remote/login user must have permissions to become this user.
  - **changed_when:** Conditional expression that overrides the task's normal 'changed' status.
  - **check_mode:** A boolean that controls if a task is executed in 'check' mode
  - **connection:** Allows you to change the connection plugin used for tasks to execute on the target.
  - **delay:**  UNDOCUMENTED!! 
  - **delegate_facts:** Boolean that allows you to apply facts to delegated host instead of inventory_hostname.
  - **delegate_to:** Host to execute task instead of the target (inventory_hostname), connection vars from the delegated host will also be used for the task.
  - **environment:** A dictionary that gets converted into environment vars to be provided for the task upon execution.
  - **failed_when:** Conditional expression that overrides the task's normal 'failed' status.
  - **ignore_errors:** Boolean that allows you to ignore task failures and continue with play. It does not affect connection errors.
  - **local_action:** Same as action but also implies ``delegate_to: localhost``
  - **loop_control:**  UNDOCUMENTED!! 
  - **name:** It's a name, works mostly for documentation, in the case of tasks/handlers it can be an identifier.
  - **no_log:** Boolean that controls information disclosure.
  - **notify:** Calls a handler from ``handlers`` section by name/identifier if task reports ``status: changed``
  - **poll:**  UNDOCUMENTED!! 
  - **port:** Used to override the default port used in a connection.
  - **register:** Registers a variable which can be later be referenced, i.e. in conditional checks with ``when`` 
  - **remote_user:** User used to log into the target via the connection plugin. AKA login user.
  - **retries:**  UNDOCUMENTED!! 
  - **run_once:** Boolean that will bypass the host loop, forcing the task to execute on the first host available and will also apply any facts to all active hosts.
  - **tags:** Tags applied to the task or included tasks, this allows selecting subsets of tasks from the command line.
  - **until:**  UNDOCUMENTED!! 
  - **vars:** Dictionary/map of variables
  - **when:** Conditional expression, determines if an iteration of a task is run or not.
  - **with_<lookup_plugin>:** with\_ is how loops are defined, it can use any available lookup plugin to generate the item list

