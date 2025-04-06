#! /bin/bash

here="$(realpath "$(dirname "${0}")")"
package="$(find "${here}" -name "*.pkg.*")"

sudo pacman --upgrade "${package}"
