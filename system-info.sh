#! /bin/bash
set -e


mainFunction () {
	inxiInfo
	displayManagerInfo

	lspciInfo
	xrandrInfo
	glxinfoOffloadedInfo

	kernelErrorsInfo
	displayManagerErrorsInfo
	nvidiaX11LogInfo

	nvidiaSmiInfo

	optimusManagerDaemonInfo
	optimusManagerSwitchingInfo
	optimusManagerConfInfo
	optimusManagerX11ConfInfo
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


displayManagerErrorsInfo () {
	if [[ -f "/usr/lib/systemd/system/${displayManager}.service" ]]; then
		echo "=== display manager errors ==="
		journalctl --boot=1 --priority=3 --unit="${displayManager}.service" --no-pager
		echo
	fi
}


displayManagerInfo () {
	local service="/etc/systemd/system/display-manager.service"

	if [[ -f "${service}" ]]; then
		echo "=== display manager ==="

		displayManager="$(
			grep "^ExecStart" "${service}" |
			cut --delimiter='=' --fields=2 |
			rev |
			cut --delimiter='/' --fields=1 |
			rev
		)"

		echo "${displayManager}"
		echo
	fi
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


kernelErrorsInfo () {
	if [[ -x "/usr/bin/journalctl" ]]; then
		echo "=== kernel errors ==="
		journalctl --boot=1 --priority=3 --dmesg --no-pager
		echo
	fi
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


nvidiaX11LogInfo () {
	local log="/var/log/Xorg.0.log"
	echo "=== nvidia x11 log ==="

	if [[ ! -f "${log}" ]]; then
		echo "no log at: ${log}"
	else
		local messages; messages="$(
			grep -e "nvidia" "${log}"
		)"

		if [[ -z "${messages}" ]]; then
			echo "no nvidia messages at: ${messages}"
		else
			echo "(--) = probed"
			echo "(**) = from config file"
			echo "(==) = default setting"
			echo "(++) = from command line"
			echo "(!!) = notice"
			echo "(II) = informational"
			echo "(WW) = warning"
			echo "(EE) = error"
			echo "(NI) = not implemented"
			echo "(??) = unknown"
			echo "${messages}"
		fi
	fi

	echo
}


optimusManagerConfInfo () {
	if [[ -x "/usr/bin/optimus-manager" ]]; then
		echo "=== optimus-manager conf ==="
		cat "/etc/optimus-manager/optimus-manager.conf" || true
		echo
	fi
}


optimusManagerDaemonInfo () {
	echo "=== optimus-manager daemon ==="

	if [[ ! -x "/usr/bin/optimus-manager" ]]; then
		echo "not installed" >&2
	elif [[ -x "/usr/bin/systemctl" ]]; then
		optimusManagerServiceStatus
	elif local log && log="$(optimusManagerLog "daemon")" && [[ -n "${log}" ]]; then
		cat "${log}"
	else
		optimus-manager --status || true
	fi

	echo
}


optimusManagerLog () {
	local type="${1}"
	local dir="/var/log/optimus-manager/${type}"

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


optimusManagerSwitchingInfo () {
	echo "=== optimus-manager switching log ==="

	if local log && log="$(optimusManagerLog "switch")" && [[ -n "${log}" ]]; then
		cat "${log}"
	else
		echo "absent"
	fi

	echo
}


optimusManagerX11ConfInfo () {
	local conf="/etc/X11/xorg.conf.d/10-optimus-manager.conf"

	echo "=== optimus-manager x11 conf ==="

	if [[ -f "${conf}" ]]; then
		cat "${conf}"
	else
		echo "not generated"
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
