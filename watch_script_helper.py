#!/usr/bin/env python3

import os
import sys

def main():
	if len(sys.argv) != 2:
		sys.exit('This script must be passed exactly one argument: the filepath to the tex file.')
	
	file_path = str(sys.argv[1])
	if not os.path.isfile(file_path):
		sys.exit('File %s doesn\'t exist' % file_path)

	base_path, full_filename = os.path.split(file_path)
	(filename, extension) = full_filename.split('.')

	if extension != 'tex':
		sys.exit() # No exit message because it would be spammed by inotify.
	
	with open(file_path, 'r', encoding='utf-8') as file:
		first_line = file.readline()
		landscape = ''
		if 'landscape' in first_line:
			landscape = '-l'
		uplatex = 'uplatex -interaction=nonstopmode %s' % file_path
		os.system(uplatex)
		
		dvipdfmx = 'dvipdfmx %s %s.dvi' % (landscape, filename)
		os.system(dvipdfmx)
		
		target = '/home/eli/www/documents/'
		cp = 'cp %s.pdf %s' % (filename, target)
		os.system(cp)

if __name__ == '__main__':
	main()