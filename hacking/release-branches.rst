Mananging Release Branches
==========================


During a release cycle, the release branch name ``stable-[version]`` will be protected to prevent direct pushes from collaborators and members who have commit access to the repository. Only the designated release managed can cherry pick commits from the upstream ``devel`` branch to the stable release branch. This restriction comes and goes during the release cycle, being enforced closer to release time and being removed after a release to allow contributors and members to cherry-pick commits that are appropriate for inclusion in the next dot release.

The procedure for protecting branches on GitHub is as follows:

**Note:** You must be a repository administrator in order to change these settings.

1. Navigate the the main repository page.
2. Click **Settings**
3. In the left menue, click **Branches**.
4. Under Protected Branches, select the branch you want to restrict.
5. Select **Restrict who can push to this branch**.
6. Search for and select the designated release manager.
7. Click **Save changes**.

Once the release has shipped, the restriction can be removed
