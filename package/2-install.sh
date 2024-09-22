#! /bin/bash

here="$(realpath "$(dirname "${0}")")"
package="$(find "${here}" -name "*.pkg.*" -print0)"

sudo pacman --upgrade "${package}"
