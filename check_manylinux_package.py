#!/usr/bin/python3

# This short script makes sure that any wheel that we produce
# will meet the 'manylinux' requirements of PEP513.
#
# For example, called 'check_manylinux_package show dist/pycifrw-4.2.1-cp35-cp35mu_linux_x86-64.whl'
#
from auditwheel import main
main.main()
