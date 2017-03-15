.PHONY: all compile sanity units

all: compile sanity units

compile:
	./ansible-test compile test/runner/ ${TEST_FLAGS}

sanity:
	./ansible-test sanity test/runner/ ${TEST_FLAGS}

units:
	PYTHONPATH=. pytest units ${TEST_FLAGS}
