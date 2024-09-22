#! /bin/bash
set -e

here="$(realpath "$(dirname "${0}")")"
files=("optimus-manager.install" "PKGBUILD")


mainFunction () {
	checkUncommittedChanges
	cloneAurRepo
	syncFiles
	updateSrcinfo
	uploadChanges
	removeAurRepoClone
}


checkUncommittedChanges () {
	local uncommittedChanges; uncommittedChanges="$(uncommittedChanges)"

	if [[ -n "${uncommittedChanges}" ]]; then
		echo "Cannot publish: Uncommitted changes:" >&2
		echo "${uncommittedChanges}" >&2
		exit 1
	fi
}


cloneAurRepo () {
	cd "${here}"

	if [[ ! -d "optimus-manager-git" ]]; then
		so git clone \
			--depth 1 --shallow-submodules \
			"ssh://aur@aur.archlinux.org/optimus-manager-git.git"
	fi
}


fileLastCommitDescription () {
	local file="${1}"
	git log -1 --pretty=format:%s -- "${file}"
}


fileModificationEpoch () {
	local file="${1}"
	stat --format=%Y "${file}"
}


lastUpdatedFile () {
	local epoch=0
	local file
	local oldEpoch
	local result

	for file in "${files[@]}"; do
		oldEpoch="${epoch}"
		epoch="$(fileModificationEpoch "${here}/${file}")"

		if [[ "${epoch}" -gt "${oldEpoch}" ]]; then
			result="${file}"
		fi
	done

	echo "${result}"
}


removeAurRepoClone () {
	so rm --recursive --force "${here}/optimus-manager-git"
}


so () {
	local commands="${*}"

	if [[ "${verbose}" -eq 1 ]]; then
		if ! ${commands}; then
			exit "${?}"
		fi
	elif ! error="$(eval "${commands}" 2>&1 >"/dev/null")" ; then
		if [ "${error}" == "" ] ; then
			error="Command failed: ${commands}"
		fi

		echo "${FUNCNAME[1]}: ${error}" >&2
		exit 1
	fi
}


syncFiles () {
	local file

	for file in "${files[@]}"; do
		so cp --force "${here}/${file}" "${here}/optimus-manager-git/${file}"
	done
}


uncommittedChanges () {
	cd "${here}"
	git status --porcelain
}


updateSrcinfo () {
	cd "${here}/optimus-manager-git"
	makepkg --printsrcinfo > .SRCINFO
}


uploadChanges () {
	cd "${here}/optimus-manager-git"

	local description; description="$(fileLastCommitDescription "$(lastUpdatedFile)")"
	if [[ -z "${description}" ]]; then
		echo "${FUNCNAME[0]}: Unable to upload: Empty description" >&2
		exit 1
	fi

	so git add --all
	so git commit --message="${description}"
}


mainFunction
