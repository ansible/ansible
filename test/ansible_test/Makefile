all: sanity unit validate-modules-unit

.PHONY: sanity
sanity:
	$(abspath ${CURDIR}/../../bin/ansible-test) sanity test/lib/ ${FLAGS}

.PHONY: unit
unit:
	PYTHONPATH=$(abspath ${CURDIR}/../lib) pytest unit ${FLAGS}

.PHONY: validate-modules-unit
validate-modules-unit:
	PYTHONPATH=$(abspath ${CURDIR}/../lib/ansible_test/_util/controller/sanity/validate-modules):$(abspath ${CURDIR}/../../lib) pytest validate-modules-unit ${FLAGS}
