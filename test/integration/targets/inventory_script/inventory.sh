#!/bin/sh
# This script mimics the output from what the contrib/inventory/vmware_inventory.py
# dynamic inventory script produced.
# This ensures we are still covering the same code that the original tests gave us
# and subsequently ensures that ansible-inventory produces output consistent with
# that of a dynamic inventory script
cat inventory.json
