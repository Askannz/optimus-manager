#! /bin/bash

if [[ "${XDG_SESSION_TYPE}" == "wayland" ]]; then
	export __GLX_VENDOR_LIBRARY_NAME="nvidia"
fi
