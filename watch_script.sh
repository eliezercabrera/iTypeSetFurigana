#!/usr/bin/env bash

dir=/home/eli/code/cli_utilities/iTypeSetFurigana/tex_files/

inotifywait -q -m -e modify -e moved_to -e create --format '%w%f' "${dir}" |
    while read file; do
    	./watch_script_helper.py ${file}
    done
