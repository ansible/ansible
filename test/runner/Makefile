.PHONY: all sanity units

all: sanity units

sanity:
	./ansible-test sanity test/runner/ ${TEST_FLAGS}

units:
	PYTHONPATH=. pytest units ${TEST_FLAGS}
