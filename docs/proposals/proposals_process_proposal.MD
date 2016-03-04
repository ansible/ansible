# Proposal: Proposals - have a process and documentation

*Author*: Robyn Bergeron <@robynbergeron>

*Date*: 04/03/2016

- Status: New
- Proposal type: community development process
- Targeted Release: Forever, until we improve it more at a later date.
- PR for Comments: https://github.com/ansible/ansible/pull/14802#
- Estimated time to implement: 2 weeks at most

Comments on this proposal prior to acceptance are accepted in the comments section of the pull request linked above.

## Motivation
Define light process for how proposals are created and accepted, and document the process permanently in community.html somewhere.

The following suggested process was created with the following ideas in mind:
- Transparency: notifications, decisions made in public meetings, etc. helps people to know what is going on.
- Avoid proliferation of multiple comments in multiple places; keep everything in the PR.
- Action is being taken: Knowing when and where decisions are made, and knowing who is the final authority, gives people the sense that things are moving.
- Ensure that new features or enhancements are added to the roadmap and release notes.

### Problems
Proposals are confusing. Should I write one? Where do I put it? Why can’t I find any documentation about this? Who approves things? This is why we should have a light and unbureaucratic process.

## Solution proposal
This proposal has multiple parts:
- Proposed process for submitting / accepting proposals
- Suggested proposal template

Once the process and template are approved, a PR will be submitted for documenting the process permanently in documentation, as well as a PR to ansible/docs/proposals for the proposal template.

### Proposed Process
1: PROPOSAL CREATION
- Person making the proposal creates the proposal document in ansible/docs/proposals via PR, following the proposal template.
- Author of proposal PR updates the proposal with the PR # / link.
- Notify the community that this proposal exists.
- Author notifies ansible-devel mailing list for transparency, providing link to PR.
- Author includes commentary indicating that comments should *not* be in response to this email, but rather, community members should add comments or feedback to the pull request.

2: KEEP THE PROPOSAL MOVING TOWARDS A DECISION.
- Proposals use public meetings as a mechanism to keep them moving.
- All proposals are decided on in a public meeting by a combination of folks with commit access to Ansible and any interested parties / users, as well as the author of the proposal. Time for approvals will be a portion of the overall schedule; proposals will be reviewed in the order received and may occasionally be deferred to the next meeting. If we are overwhelmed, a separate meeting may be scheduled.

(Note: ample feedback in the comments of the proposal PR should allow for folks to come to broad consensus in one way or another in the meeting rather rapidly, generally without an actual counted vote. However, the decision should be made *in the meeting*, so as to avoid any questions around whether or not the approval of one Ansible maintain / committer reflects the opinions or decision of everyone.)

- *New* proposals are explicitly added to the public IRC meeting agenda for each week by the meeting organizer for for acknowledgement of ongoing discussion and existence, and/or easy approval/rejection. (Either via a separate issue somewhere tracking any meeting items, or by adding a “meeting” label to the PR.)
- Existing new, not-yet-approved proposals are reviewed weekly by meeting organizer to check for slow-moving/stalled proposals, or for flags from the proposal owner indicating that they'd like to have it addressed in the weeks meeting

3: PROPOSAL APPROVED
- Amendments needed to the proposal after IRC discussion should be made immediately.
- The proposal status should be changed to Approved / In Progress in the document.
- The proposal should be moved from /docs/proposals to a docs/roadmap folder (or similar).
- The proposal PR comments should be updated with a note by the meeting organizer that the proposal has been accepted, and further commentary should be in the PRs implementing the code itself.
- Proposals can also be PENDING (waiting on something), or DECLINED. 

4: CODE IN PROGRESS
- Approved proposals should be periodically checked for progress, especially if tied to a release and/or is noted as release blocking.
- PRs implementing the proposal are recommended to link to the original proposal PR or document for context.
5: CODE COMPLETE
- Proposal document, which should be in docs/roadmap, should have their status updated to COMPLETE.
- The release notes file for the targeted release should be updated with a small note regarding the feature or enhancement; completed proposals for community processes should have a follow-up mail sent to the mailing list providing information and links to the new process.
- Hooray! Buy your friend a tasty beverage of their choosing.

### Suggested Proposal Template Outline
Following the .md convention, a proposal template should go in the docs/proposals repository. This is a suggested outline; the template will provide more guidance / context and will be submitted as a PR upon approval of this proposal.

Please note that, in line with the above guidance that some processes will require fine-tuning over time, that the suggested template outline below, as well as the final submitted template to the docs/proposals repo has wiggle room in terms of description, and that what makes sense may vary from one proposal to another. The expectation is that people will simply do what seems right, and over time we’ll figure out what works best — but in the meantime, guidance is nice.

#### TEMPLATE OUTLINE
- Proposal Title
- Author (w/github ID linked)
- Date:

- Status: New, Approved, Pending, Complete
- Proposal type: Feature  / enhancement / community development process
- Targeted Release:
- PR for comments:
- Estimated time to implement:

Comments on this proposal prior to acceptance are accepted in the comments of the PR linked above.

- Motivation / Problems solved:
- Proposed Solution: (what you’re doing, and why; keeping this loose for now.)

Other Suggested things to include:
- Dependencies / requirements:
- Testing:
- Documentation:

## Dependencies / requirements

- Approval of this proposed process is needed to create the actual documentation of the process.
- Weekly, public IRC meetings (which should probably be documented Wrt time / day of week / etc. in the contributor documentation) of the Ansible development community.
- Creation of a “meeting” label in GitHub (or defining some other mechanism to gather items for a weekly meeting agenda, such as a separate issue in GitHub that links to the PRs.)
- Coming to an agreement regarding “what qualifies as a feature or enhancement that requires a proposal, vs. just submitting a PR with code.” It could simply be that if the change is large or very complicated, our recommendation is always to file a proposal to ensure (a) transparency (b) that a contributor doesn’t waste their time on something that ultimately can’t be merged at this time.
- Nice to have: Any new proposal PR landing in docs/proposals is automatically merged and an email automatically notifies the mailing list of the existence and location of the PR for comments.

## Testing

Testing of this proposal will literally be via submitting this proposal through the proposed proposal process. If it fails miserably, we’ll know it needs fine-tuning or needs to go in the garbage can.

## Documentation:

- Documentation of the process, including “what is a feature or enhancement vs. just a regular PR,” along with the steps shown above, will be added to the Ansible documentation in .rst format via PR.  The documentation should also provide guidance on the standard wording of the email notifying ansible-devel list that the proposal exists and is ready for review in the PR comments.
- A proposal template should also be created in the docs/proposals repo directory.
