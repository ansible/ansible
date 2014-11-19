The Deploy Helper module explained
==================================

.. _deploy_helper_intro:

Introduction
````````````

Deploying software with Ansible can be done in many ways. The Deploy Helper
module is here to remove some of the boilerplate tasks needed to do so.
It does, however, presume a certain method and structure outlined below. Those familiar with
Capistrano will recognize it's folder structure, although you can change any of the used defaults.

An example folder structure looks as follows:

.. _deploy_helper_folder_structure:

.. code-block:: yaml

    releases:
        - 20140415234508
        - 20140415235146
        - 20140416082818

    shared:
        - sessions
        - source
        - uploads

    current: -> releases/20140416082818

.. note:: "Current" is a symlink in the above example

The ``releases`` folder holds all the available releases. A release is a complete build of the application being
deployed. This can be a clone of a repository for example, or a sync of a local folder on your filesystem.
Having timestamped folders is one way of having distinct releases, but you could choose your own strategy like
git tags or commit hashes.

During a deploy, a new folder is added in the releases folder and any build steps required are performed. Once
the new build is ready, the deploy procedure is completed by replacing the ``current`` symlink with a link to
this build.

The ``shared`` folder holds any resource that is shared between different releases. Examples of this are web-server
session files, or files uploaded by users of your application. It's quite common to have symlinks from a release
folder pointing to a shared/subfolder, and creating these links would be automated as of the build steps.

The ``current`` symlink points to one of the releases. Probably the latest one, unless a deploy is in progress.
The web-server's root for the project will go through this symlink, so the 'downtime' when switching to a new release
is reduced to the time it takes to switch the link.

To distinguish between successful builds and unfinished ones, a file can be placed in the folder of the release
that is currently in progress. The existence of this file will mark it as unfinished, and allow an automated
procedure to remove it later. One of the last steps of the build process would be to remove this file.

When you write a deploy procedure like this in Ansible, this is roughly what you need to do:

.. code-block:: yaml

    - create the project root folder
    - create the releases folder
    - create the shared folder
    - generate a timestamp
    ... clone, build and prepare your project...
    - remove build in progress file
    - create the symlink
    - delete the old releases

How to achieve this using Deploy Helper
```````````````````````````````````````

Many of the steps covered in the introduction are embedded in the Deploy Helper module. A typical deploy playbook
would take just 2 tasks (not counting the tasks needed to actually build your project)::

    - tasks:
        - deploy_helper: path=/path/to/project state=present
        ... clone, build and prepare your project...
        - deploy_helper: path=/path/to/project release={{ deploy_helper.new_release }} state=finalize

On ``state=present`` the file structure is set up. This means the root folder, the releases folder and the shared folder.
In addition, a set of facts is gathered, accessible via the 'deploy_helper' name. The most important one is probably
the 'new_release', it contains a generated timestamp that you can use as a new release folder.

On ``state=finalize`` the release is considered finished and ready to go. If a file with the name 'DEPLOY_UNFINISHED'
exists in the new release folder, it will be deleted. The current symlink is then recreated to point to the new_release.
In addition, any releases that still contain the 'DEPLOY_UNFINISHED' file will also be deleted (they are considered
failed builds from previous aborted deploy attempts). Finally, the old releases are cleaned up keeping only the number
of builds set in the ``keep_releases`` parameter.

The complete list of facts returned by this module is::

    project_path:           whatever you set in the path parameter is returned, for convenience
    current_path:           the path to the symlink
    releases_path:          the path to the folder to keep releases in
    shared_path:            the path to the folder to keep shared resources in
    unfinished_filename:    the file to check for to recognize unfinished builds
    previous_release:       the release the current symlink is pointing to
    previous_release_path:  the full path to the current symlink target
    new_release:            either the 'release' parameter or a generated timestamp
    new_release_path:       the path to the new release folder (not created by the module)

If the default folders are not an exact fit, parameters can be used to set different paths. These can be relative
to the ``path`` parameters, or absolute - or, in case of ``shared_path``, an empty string::

    - tasks:
        - deploy_helper: path=/path/to/project
                         current_path=active
                         releases_path=versions
                         shared_path=''

        - deploy_helper: path=/path/to/project
                         current_path=/var/www/project/active
                         releases_path=/path/to/versions
                         shared_path=''

Also, the name used for the release does not have to be a generated timestamp. If you have your own naming
strategy, you can just pass the release name into the module as a parameter::

    - tasks:
        - deploy_helper: path=/path/to/root release=v1.1.1 state=present
        - deploy_helper: path=/path/to/root release={{ deploy_helper.new_release }} state=finalize

If there is a need to break up the process a bit more, the deploy_module can be used to gather the facts before
anything is actually done::

    - tasks:
        - deploy_helper: path=/path/to/project state=query

        # facts are now available
        - debug: var=deploy_helper

.. note:: Remember that it is necessary to set the 'release' parameter on the next run, otherwise a new timestamp will be generated.

The ``state=finalize`` step automatically cleans by default, but it does not have to. Cleaning can be done at any
time::

    - tasks:
        - deploy_helper: path=/path/to/project release={{ deploy_helper.new_release }} state=finalize clean=False
        ...black magic voodoo after finalize and before cleanup...
        - deploy_helper: path=/path/to/project state=clean

That should cover most situations regarding the deployment of a web application. Happy deploying!

.. seealso::

    :doc:`deploy_helper_module`
        The module documentation for the Deploy Helper Module.
    `Ansible-project group <https://groups.google.com/d/msg/ansible-project/R3Kr2uMYUt4/b-WLJ3m6L1AJ>`_
        The thread where this module was discussed
    `Deploying with Ansible <http://future500.nl/articles/2014/07/thoughts-on-deploying-with-ansible/>`_
        An article describing the methods, ideas and problems that went into this module
    `Capistrano <http://capistranorb.com/>`_
        The project that served as inspiration.
