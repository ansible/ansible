---
name: creating-backports
description: Create backports of a GitHub pull request that has merged into the devel branch in the upstream repository
user-invocable: true
---

Creating Backports
==================

Backport creation workflow
---------------------------

```text
Backporting Progress:
- [ ] Step 1: Verify the referenced pull request
- [ ] Step 2: Identify the git remote for the upstream repository
- [ ] Step 3: Determine the stable branches for the backport
- [ ] Step 4: Create the backport branches
- [ ] Step 5: Create pull requests
- [ ] Step 6: Summarize the work
```

Step 1: Verify the referenced pull request
-------------------------------------------

Use `gh pr view <number>` to verify the PR is merged into devel and get the merge commit SHA:
`gh pr view <number> --json mergeCommit -q .mergeCommit.oid`

Abort if the PR is not merged or merged to wrong branch.

Step 2: Identify the git remote for the upstream repository
------------------------------------------------------------

Identify the upstream remote (typically named `upstream`). If it doesn't exist, offer to create it.

Sync the local devel branch with the identified upstream remote:

- `git fetch <upstream_remote>`
- `git checkout devel`
- `git pull --rebase <upstream_remote> devel`

Step 3: Determine the stable branches for the backport
-------------------------------------------------------

Refer to the backport policy in `context/contributing.md`:

- Bug fixes: backported to latest stable only
- Critical bug fixes: backported to latest and previous stable
- Security issues: must be reported to security@ansible.com privately (not via GitHub)

Ask the user what type of fix this is and confirm the target branches before proceeding.

To identify available stable branches, run: `git ls-remote --heads <upstream_remote> 'refs/heads/stable-*'`

Step 4: Create the backport branches
-------------------------------------

Before creating backport branches, verify you're not on a branch you want to keep (the workflow will create and switch between multiple branches).

First, ensure stable branches are up to date:

- Run `git fetch <upstream_remote>` to get latest stable branch refs

The backport process consists of these steps:

1. Create a new branch for each stable branch: `git checkout -b backport/VERSION/PR_NUMBER <upstream_remote>/STABLE_BRANCH`
   Example: `git checkout -b backport/2.20/1234 upstream/stable-2.20` (if upstream remote is named `upstream`)
2. Cherry-pick the MERGE commit from the referenced pull request into each branch using the `-x` option.
   (The merge commit SHA was obtained in Step 1 with `gh pr view`)
   Example: `git cherry-pick -x <merge_commit_sha>`
   If merge conflicts are encountered:
   - Run `git cherry-pick --abort` to abort the cherry-pick
   - Notify the user that manual conflict resolution is required for this stable branch
   - Explain the user can either:
     a) Manually resolve conflicts (you can help guide them)
     b) Skip this stable branch backport
   - Do NOT continue with remaining branches if conflicts occur - wait for user direction
3. Before pushing, identify the user's fork remote:
   - Typically named `origin`
   - Verify with `git remote -v` that it points to the user's fork, not upstream
   - Confirm the remote name before pushing
4. Push each backport branch to the user's fork remote (identified in step 3, typically `origin`):
   `git push <fork_remote> backport/VERSION/PR_NUMBER`
   Example: `git push origin backport/2.20/1234` (if fork remote is named `origin`)
   Never push to the upstream remote - this would push directly to the upstream repository.

Step 5: Create pull requests
-----------------------------

Confirm with the user that they would like to create a pull request for each backport branch.

Use `gh pr create` for each branch:

- `--base STABLE_BRANCH_NAME` (the stable branch being backported to)
- `--title "[STABLE_BRANCH_NAME] ORIGINAL_PR_TITLE"`
- `--body "Backport of PR #XXXX\n\n(cherry picked from commit COMMIT_HASH)"`

Example: `gh pr create --base stable-2.20 --title "[stable-2.20] Fix bug in module" --body "Backport of PR #1234\n\n(cherry picked from commit abc123)"`

Step 6: Summarize the work
---------------------------

Give the user a summary of the backports that were created. The summary must provide a list of the URL links to all
pull requests that were created.

Error Recovery
--------------

If errors occur during the backport process:

- **Cherry-pick conflicts**: List which branches succeeded and which failed due to conflicts
- **PR creation failures**: Clean up any orphaned branches that weren't converted to PRs
- **Partial success**: Summarize what succeeded and offer to retry failed branches individually
