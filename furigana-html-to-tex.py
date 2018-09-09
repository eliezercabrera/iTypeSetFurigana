from bs4 import BeautifulSoup
from collections import defaultdict
from enum import Enum
from html.parser import HTMLParser
from string import Template

import appex
import clipboard
import requests
import sys

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

def extract_song_info(url):
	bs_raw_lyrics = BeautifulSoup(requests.get(url).text, "html5lib")
	
	artist = bs_raw_lyrics.find('div', class_='artistcontainer').get_text()
	title = bs_raw_lyrics.find('div', class_='titlelyricblocknew').find('h1').get_text()
	raw_lyrics = str(bs_raw_lyrics.find('div', class_='olyrictext'))
	preprocessed_lyrics = raw_lyrics.replace('<div class="olyrictext">', '').replace('</div>', '')
	lyrics = '\n\n'.join(preprocessed_lyrics.splitlines())
	return (artist, title, lyrics)

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
	debug = False
	get_lyrics_from_clipboard = False
	url = 'https://www.lyrical-nonsense.com/lyrics/aimer/brave-shine/'
	
	if not debug and not get_lyrics_from_clipboard:
		if not appex.is_running_extension():
			sys.exit('This script must be run from Safari\'s share sheet.')
		url = appex.get_url()

	if 'www.lyrical-nonsense.com' not in url:
		sys.exit('This script must be run on lyrical-nonsense.com')

	artist = 'blank'
	title = 'blank'
	lyrics= ''
	if get_lyrics_from_clipboard:
		lyrics = clipboard.get()
	else:
		artist, title, lyrics = extract_song_info(url)

	furigana_lyrics_html = furiganize_lyrics(lyrics)

	parser = MyHTMLParser()
	parser.feed(furigana_lyrics_html)
	
	if debug:
		print(lyrics)
		print(furigana_lyrics_html)
		print(parser.get_lyrics())
	
	clipboard.set(fill_tex_template(artist, title, parser.get_lyrics()))

if __name__ == '__main__':
	main()
