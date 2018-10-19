from bs4 import BeautifulSoup
from collections import defaultdict
from enum import Enum
from html.parser import HTMLParser
from optparse import OptionParser
from string import Template

import appex
import clipboard
import requests
import sys
import webbrowser

class MyHTMLParser(HTMLParser, object):
	class Stage(Enum):
		START = 1
		DATA = 2
		END = 3

	def __init__(self):
		super(MyHTMLParser, self).__init__()
		self.NEXT_LINE = '\n\n'
		self.NEXT_VERSE = '\n\n\\bigskip\n\n'

		self.is_processing = defaultdict(lambda: False)
		self.tex = []

	def handle_starttag(self, tag, attrs):
		self.is_processing[tag] = True
		if tag == 'br':
			self.tex.append(self.NEXT_LINE)

	def handle_endtag(self, tag):
		self.is_processing[tag] = False
		if tag == 'p':
			self.tex.append(self.NEXT_VERSE)

	def handle_data(self, data):				
		to_append = Template('$data')
		if self.is_processing['rp']:
			to_append = Template('')
		if self.is_processing['rb']:
			if len(data) == 1:
				to_append = Template('\\ruby{$data}')
			else:
				to_append = Template('\\ruby[g]{$data}')
		if self.is_processing['rt']:
			to_append = Template('{$data}')
		self.tex.append(to_append.substitute(data=data))

	def get_lyrics(self):
		final_lyrics = []
		previous_line = 'dummy_non_empty'
		for line in ''.join(self.tex).splitlines():
			if not (previous_line == '' and line == ''):
				final_lyrics.append(line)
			previous_line = line
		return '\n'.join(final_lyrics)

def preprocess_lyrics(lyrics):
	preprocessed_lines = []
	for line in lyrics.splitlines():
		preprocessed_lines.append(line)
		preprocessed_lines.append('')
	return '\n'.join(preprocessed_lines)

def furiganize_lyrics(lyrics):
	url = 'http://furigana.sourceforge.net/cgi-bin/index.cgi'
	data = {'text': (None, lyrics), 'state': (None, 'output')}
	request = BeautifulSoup(requests.post(url, files=data).text, "html5lib")
	body = str(request.find('body'))
	
	body_tag = '<body>'
	start = body.find(body_tag)
	
	form_tag = '<form'
	end = body.find(form_tag)

	preprocessed_lyrics = body[start + len(body_tag) : end]
	processed_lyrics = preprocessed_lyrics.replace('&lt;p&gt;', '<p>').replace('&lt;/p&gt;', '</p>')
	return processed_lyrics

def fill_tex_template(artist, title, lyrics):
	template_file = open('tex_template.tex', 'r', encoding='utf-8')
	template = Template(template_file.read())
	return template.substitute(artist=artist, title=title, lyrics=lyrics)

def main():
	parser = OptionParser()
	parser.add_option('-a',
										'--author',
										dest='author',
										help='Sets song performer to AUTHOR',
										metavar='AUTHOR')
	parser.add_option('-t',
										'--title',
										dest='title',
										help='Sets the title of the song to TITLE',
										metavar='TITLE')
	parser.add_option('-l',
										'--lyrics',
										dest='lyrics',
										help='Sets the lyrics of the song to LYRICS',
										metavar='LYRICS')
	parser.add_option('-d',
										'--debug',
										action='store_true',
										dest='debug',
										default=False,
										help='Runs in debug mode')
	(options, args) = parser.parse_args()

	debug = options.debug
	artist = options.author
	title = options.title
	lyrics = options.lyrics
	
	furigana_lyrics_html = furiganize_lyrics(preprocess_lyrics(lyrics))

	parser = MyHTMLParser()
	parser.feed(furigana_lyrics_html)
	
	if debug:
		print(lyrics)
		print(furigana_lyrics_html)
		print(parser.get_lyrics())
	
	clipboard.set(fill_tex_template(artist, title, parser.get_lyrics()))
	webbrowser.open('shortcuts://')

if __name__ == '__main__':
	main()
