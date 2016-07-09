AP=ansible-playbook -i inventory

test:
	$(AP) cleanup-and-copy-service-files.yml
	$(AP) enabled-test-service.yml  --check
