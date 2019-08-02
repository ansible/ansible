all: sanity unit

.PHONY: sanity
sanity:
	ansible-test sanity test/runner/ ${FLAGS}

.PHONY: unit
unit:
	PYTHONPATH=.:.. pytest unit ${FLAGS}
