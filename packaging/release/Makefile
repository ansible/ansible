version ?= $(shell python versionhelper/version_helper.py --raw)

.PHONY: all
all:
	@echo "USAGE:"
	@echo
	@echo "make release version={version} # current version is '${version}'"
	@echo "make publish"
	@echo
	@echo "NOTE: Make sure to source hacking/env-setup before running these targets."

.PHONY: release
release: version summary changelog commit-release
	git show -p
	git status
	@echo
	@echo 'Run `git push` if you are satisfied with the changes.'

.PHONY: version
version:
	sed -i.bak "s/^__version__ = .*$$/__version__ = '${version}'/" ../../lib/ansible/release.py
	rm ../../lib/ansible/release.py.bak

.PHONY: summary
summary:
	@printf '%s\n%s\n%s\n' \
	'release_summary: |' \
	'   | Release Date: $(shell date '+%Y-%m-%d')' \
	'   | `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__' > \
	../../changelogs/fragments/v${version}_summary.yaml

.PHONY: changelog
changelog:
	changelogs/changelog.py release -vv && changelogs/changelog.py generate -vv
	ansible-test sanity changelogs/

.PHONY: commit-release
commit-release:
	git add ../../changelogs/ ../../lib/ansible/release.py
	git commit -m "New release v${version}"

.PHONY: publish
publish: tag postversion commit-postversion
	git show -p
	git status
	@echo
	@echo 'Run `git push --follow-tags` if you are satisfied with the changes.'

.PHONY: tag
tag:
	git tag -a v${version} -m "New release v${version}"

.PHONY: postversion
postversion:
	sed -i.bak "s/^__version__ = .*$$/__version__ = '${version}.post0'/" ../../lib/ansible/release.py
	rm ../../lib/ansible/release.py.bak

.PHONY: commit-postversion
commit-postversion:
	git add ../../lib/ansible/release.py
	git commit -m "Update Ansible release version to v${version}."
