#! /bin/bash

if [[ "${XDG_SESSION_TYPE}" == "wayland" ]] && [[ -x "/usr/bin/nvidia-persistenced" ]]; then
	export __EGL_VENDOR_LIBRARY_FILENAMES="/usr/share/glvnd/egl_vendor.d/50_mesa.json"
	export __GLX_VENDOR_LIBRARY_NAME="nvidia"
	export __VK_LAYER_NV_optimus="NVIDIA_only"
fi
