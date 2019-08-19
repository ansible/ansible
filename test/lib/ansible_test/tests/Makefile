all: sanity unit validate-modules-unit

.PHONY: sanity
sanity:
	ansible-test sanity test/lib/ ${FLAGS}

.PHONY: unit
unit:
	PYTHONPATH=$(abspath ${CURDIR}/../..) pytest unit ${FLAGS}

.PHONY: validate-modules-unit
validate-modules-unit:
	PYTHONPATH=$(abspath ${CURDIR}/../_data/sanity/validate-modules):$(abspath ${CURDIR}/../../../../lib) pytest validate-modules-unit ${FLAGS}
