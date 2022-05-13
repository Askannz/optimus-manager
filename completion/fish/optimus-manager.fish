complete -c optimus-manager --no-files

complete -c optimus-manager -l help -s h            -d 'Show help message and exit.'
complete -c optimus-manager -l version -s v         -d 'Print version and exit.'

complete -c optimus-manager -l status               -d 'Print current status of optimus-manager.'
complete -c optimus-manager -l print-mode           -d 'Print the GPU mode that your current desktop session is running on.'
complete -c optimus-manager -l print-next-mode      -d 'Print the GPU mode that will be used the next time you log into your session.'
complete -c optimus-manager -l print-startup        -d 'Print the GPU mode that will be used on startup.'

complete -c optimus-manager -l switch -x -a 'integrated' -d 'switch to the integrated GPU and power the Nvidia GPU off'
complete -c optimus-manager -l switch -x -a 'nvidia' -d 'switch to the Nvidia GPU'
complete -c optimus-manager -l switch -x -a 'hybrid' -d 'switch to the iGPU but leave the Nvidia GPU available for on-demand offloading'
complete -c optimus-manager -l switch -d 'Set the GPU mode to MODE. You need to log out then log in to apply the change.'

complete -c optimus-manager -l temp-config -F -r    -d 'Set a path to a temporary configuration file to use for the next reboot ONLY. Useful for testing power switching configurations without ending up with an unbootable setup.'

complete -c optimus-manager -l unset-temp-config    -d 'Undo --temp-config (unset temp config path)' --condition '! optimus-manager --status | grep -oP "Temporary config path\s?: \Kno"'
complete -c optimus-manager -l no-confirm           -d 'Do not ask for confirmation and skip all warnings when switching GPUs.' --condition '__fish_contains_opt switch'
complete -c optimus-manager -l cleanup              -d 'Remove auto-generated configuration files left over by the daemon.'
