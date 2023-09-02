#!/bin/sh

dir="$(CDPATH="" cd -- "$(dirname -- "$0")" && pwd)"
temp="$(mktemp -d)"

build="$dir/build"
mkdir -p "$build"

name="$(perl -ne 'if (/^.*name="([^"]*)"/) { print $1; exit }' "$dir/fom_mark_as_seen.rpy")"
version="$(perl -ne 'if (/^.*version="([^"]*)"/) { print $1; exit }' "$dir/fom_mark_as_seen.rpy")"
package="$(echo "$name" | tr "[:upper:]" "[:lower:]" | tr "[:blank:]" "-")"

mod="$temp/game/Submods/"
mkdir -p "$mod"

cp -r "$dir/fom_mark_as_seen.rpy" "$mod"

(cd "$temp" || exit 1; find game | zip -9@q "$build/$package-$version.zip" && rm -rf "$temp")