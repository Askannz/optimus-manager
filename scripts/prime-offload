#!/bin/bash

log_file='/var/log/optimus-manager/prime_setup.log'
[[ ! -d $(dirname $log_file) ]] && mkdir -p $(dirname $log_file)

/usr/bin/python3 -u /usr/bin/optimus-manager-setup --setup-prime 2>&1 | tee -a $log_file

 
