#! /bin/bash
set -e

here="$(realpath "$(dirname "${0}")")"
files=("optimus-manager.install" "PKGBUILD")


mainFunction () {
	checkDescription
	cloneAurRepo
	checkFilesHaveBeenChanged
	syncFiles
	updateSrcinfo
	uploadChanges
	removeAurRepoClone
}


checkDescription () {
	if [[ -z "${description}" ]]; then
		echo "No description provided" >&2
		exit 1
	fi
}


checkFilesHaveBeenChanged () {
	local aurSum
	local changed=false
	local file
	local index=0
	local repoSum

	while [[ "${index}" -lt "${#files[@]}" ]] && ! "${changed}"; do
		repoSum="$(fileSum "${here}/${files[$index]}")"
		aurSum="$(fileSum "${here}/optimus-manager-git/${files[$index]}")"

		if [[ "${repoSum}" != "${aurSum}" ]]; then
			changed=true
		else
			index="$((index +1))"
		fi
	done

	if ! "${changed}"; then
		removeAurRepoClone
		exit 0
	fi
}


cloneAurRepo () {
	cd "${here}"

	if [[ ! -d "optimus-manager-git" ]]; then
		so git clone \
			--depth 1 --shallow-submodules \
			"ssh://aur@aur.archlinux.org/optimus-manager-git.git"
	else
		so git fetch
	fi
}


fileModificationEpoch () {
	local file="${1}"
	stat --format=%Y "${file}"
}


fileSum () {
	local file="${1}"

	sha1sum "${file}" |
	cut --delimiter=' ' --fields=1
}


removeAurRepoClone () {
	so rm --recursive --force "${here}/optimus-manager-git"
}


so () {
	local error

	#shellcheck disable=SC2068
	if ! error="$(${@} 2>&1 >"/dev/null")" ; then
		if [[ -z "${error}" ]] ; then
			error="Command failed"
		fi

		echo "${FUNCNAME[1]}: ${*}:" >&2
		echo "${error}" >&2
		exit 1
	fi
}


syncFiles () {
	local file

	for file in "${files[@]}"; do
		so cp --force "${here}/${file}" "${here}/optimus-manager-git/${file}"
	done
}


updateSrcinfo () {
	cd "${here}/optimus-manager-git"
	makepkg --printsrcinfo > .SRCINFO
}


uploadChanges () {
	cd "${here}/optimus-manager-git"

	so git add --all
	#shellcheck disable=SC2016
	git commit --message="${description}" >/dev/null
	so git push
}


description="${*}"
mainFunction
