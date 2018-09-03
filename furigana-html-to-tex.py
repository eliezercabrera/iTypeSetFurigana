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

		self.streak = ('', 0)
		self.is_processing = defaultdict(lambda: False)
		self.tex = []

	def handle_starttag(self, tag, attrs):
		self.is_processing[tag] = True
		self.handle_streak(tag, self.Stage.START) 

	def handle_endtag(self, tag):
		self.is_processing[tag] = False
		self.handle_streak(tag, self.Stage.END)

	def handle_data(self, data):
		self.handle_streak('handle_data', self.Stage.DATA)
				
		to_append = Template('$data')
		if self.is_processing['rp']:
			to_append = Template('')
		if self.is_processing['rb']:
			if len(data) == 1:
				to_append = Template('{$data}')
			else:
				to_append = Template('[g]{$data}')
		if self.is_processing['rt']:
			to_append = Template('{$data}')
		self.tex.append(to_append.substitute(data=data))
	
	def reset_streak(self):
		tag, _ = self.streak
		self.streak = (tag, 0)
	
	def increase_streak(self):
		tag, count = self.streak
		self.streak = (tag, count + 1)
	
	def new_streak(self, tag):
		self.streak = (tag, 1)
	
	def handle_streak(self, next_tag, stage):
		to_append = ''
		tag, count = self.streak
		if tag == next_tag and stage == self.Stage.START:
			self.increase_streak()
		# TODO: Review if this elif is necessary.
		elif stage == self.Stage.END and tag == 'handle_data':
			self.reset_streak()
		elif stage in [self.Stage.START, self.Stage.DATA]:
			if tag == 'ruby':
				if stage == self.Stage.START:
					to_append = '\\ruby'
			if tag == 'br':
				to_append = self.NEXT_LINE if count <= 2 else self.NEXT_VERSE				
			self.new_streak(next_tag)
		self.tex.append(to_append)

	def get_lyrics(self):
		return ''.join(self.tex)

def extract_song_info(url):
	bs_raw_lyrics = BeautifulSoup(requests.get(url).text, "html5lib")
	
	artist = bs_raw_lyrics.find('div', class_='artistcontainer').get_text()
	title = bs_raw_lyrics.find('div', class_='titlelyricblocknew').find('h1').get_text()
	lyrics, _ = bs_raw_lyrics.find('div', id='Lyrics').get_text().split('eval(')
	return (artist, title, lyrics)	

def prepare_lyrics_for_furiganization(lyrics):
	refined_lyrics = []
	for line in lyrics.splitlines():
		if line == '':
			refined_lyrics.append('\n\n')
		else:
			refined_lyrics.append("%s\n" % line)
	return '\n'.join(refined_lyrics)

def furiganize_lyrics(lyrics):
	url = 'http://furigana.sourceforge.net/cgi-bin/index.cgi'
	data = {'text': (None, lyrics), 'state': (None, 'output')}
	request = BeautifulSoup(requests.post(url, files=data).text, "html5lib")
	body = str(request.find('body'))
	
	body_tag = '<body>'
	start = body.find(body_tag)
	
	form_tag = '<form'
	end = body.find(form_tag)

	processed_lyrics = body[start + len(body_tag) : end]
	return processed_lyrics

def fill_tex_template(artist, title, lyrics):
	template_file = open('tex_template.tex', 'r', encoding='utf-8')
	template = Template(template_file.read())
	return template.substitute(artist=artist, title=title, lyrics=lyrics)

def main():
	debug = False
	url = 'https://www.lyrical-nonsense.com/lyrics/aimer/brave-shine/'
	
	if not debug:
		if not appex.is_running_extension():
			sys.exit('This script must be run from Safari\'s share sheet.')
		url = appex.get_url()

	if 'www.lyrical-nonsense.com' not in url:
		sys.exit('This script must be run on lyrical-nonsense.com')

	artist, title, lyrics = extract_song_info(url)
	preprocessed_lyrics = prepare_lyrics_for_furiganization(lyrics)
	furigana_lyrics_html = furiganize_lyrics(preprocessed_lyrics)

	parser = MyHTMLParser()
	parser.feed(furigana_lyrics_html)
	
	if debug:
		print(furigana_lyrics_html)
		print(parser.get_lyrics())
	
	clipboard.set(fill_tex_template(artist, title, parser.get_lyrics()))

if __name__ == '__main__':
	main()
