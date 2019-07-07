#!/bin/bash

log_file='/var/log/optimus-manager/boot_setup.log'
[[ ! -d $(dirname $log_file) ]] && mkdir -p $(dirname $log_file)

/usr/bin/python3 -u /usr/bin/optimus-manager-setup --setup-boot 2>&1 | tee -a $log_file

 
