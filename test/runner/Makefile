all: sanity units

.PHONY: sanity
sanity:
	ansible-test sanity test/runner/ ${FLAGS}

.PHONY: units
units:
	PYTHONPATH=.:.. pytest units ${FLAGS}
