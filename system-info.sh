#! /bin/bash
set -e


mainFunction () {
	inxiInfo
	displayManagerInfo

	lspciInfo
	xrandrInfo

	glxinfoDefaultInfo
	glxinfoOffloadedInfo

	optimusManagerStatusInfo
	nvidiaSmiInfo

	optimusManagerConfInfo
}


checkDepends () {
	local missing
	local missings=()
	local depend

	local depends=(
		glxinfo
		inxi
		lspci
		nvidia-smi
		xrandr
	)

	for depend in "${depends[@]}"; do
		if [[ ! -x "/usr/bin/${depend}" ]]; then
			missings+=("${depend}")
		fi
	done

	if [[ "${#missings}" -ne 0 ]]; then
		echo "Required software not installed:" >&2

		for missing in "${missings[@]}"; do
			echo "- ${missing}" >&2
		done

		exit 1
	fi
}


displayManagerInfo () {
	local service="/etc/systemd/system/display-manager.service"

	if [[ -f "${service}" ]]; then
		echo "=== display manager ==="

		grep "^ExecStart" "${service}" |
		cut --delimiter='=' --fields=2 |
		rev |
		cut --delimiter='/' --fields=1 |
		rev

		echo
	fi
}


glxinfoDefaultInfo () {
	echo "=== glxinfo default ==="
	glxinfo | grep --ignore-case -e vendor -e renderer
	echo
}


glxinfoOffloadedInfo () {
	echo "=== glxinfo offloaded ==="

	__NV_PRIME_RENDER_OFFLOAD=1 \
	__GLX_VENDOR_LIBRARY_NAME="nvidia" \
	__VK_LAYER_NV_optimus="NVIDIA_only" \
	__GL_SHOW_GRAPHICS_OSD=1 \
	glxinfo |
	grep --ignore-case -e vendor -e renderer ||
	true

	echo
}


inxiInfo () {
	echo "=== inxi ==="
	inxi -SMGsr -c0
	echo
}


lspciInfo () {
	echo "=== lspci ==="
	lspci | grep --ignore-case -e "3d" -e "vga"
	echo
}


nvidiaSmiInfo () {
	echo "=== nvidia-smi ==="
	nvidia-smi
	echo
}


optimusManagerConfInfo () {
	if [[ -x "/usr/bin/optimus-manager" ]]; then
		echo "=== optimus-manager.conf ==="
		cat "/etc/optimus-manager/optimus-manager.conf" || true
	fi
}


optimusManagerLog () {
	local dir="/var/log/optimus-manager/switch"

	if [[ -d "${dir}" ]]; then
		find "${dir}" |
		sort |
		tail -n1
	fi
}


optimusManagerServiceStatus () {
	SYSTEMD_COLORS=0 \
	systemctl --full --no-pager status optimus-manager ||
	true
}


optimusManagerStatusInfo () {
	echo "=== optimus-manager status ==="

	if [[ ! -x "/usr/bin/optimus-manager" ]]; then
		echo "not installed" >&2
	elif [[ -x "/usr/bin/systemctl" ]]; then
		optimusManagerServiceStatus
	elif local log && log="$(optimusManagerLog)" && [[ -n "${log}" ]]; then
		cat "${log}"
	else
		optimus-manager --status || true
	fi

	echo
}


xrandrInfo () {
	echo "=== xrandr providers ==="
	xrandr --listproviders || true
	echo
}


checkDepends
mainFunction
