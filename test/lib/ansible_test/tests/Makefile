all: sanity unit

.PHONY: sanity
sanity:
	ansible-test sanity test/lib/ ${FLAGS}

.PHONY: unit
unit:
	PYTHONPATH=../../lib/ pytest unit ${FLAGS}
