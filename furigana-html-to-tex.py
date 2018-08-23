#!/usr/bin/env python2
from bs4 import BeautifulSoup
from string import Template
from collections import defaultdict

import appex
import requests
import clipboard
import mechanize
from HTMLParser import HTMLParser
import sys

class MyHTMLParser(HTMLParser, object):
	def __init__(self):
		super(MyHTMLParser, self).__init__()
		self.NEXT_LINE = '\n\n'
		self.NEXT_VERSE = '\n\n\\bigskip\n\n'
		self.streak = ('', 0)
		self.statuses = {
			'is_active': {
				'status': 'DORMANT',
				'toggles': {
					'body': {
						'stage': 'AT_START',
						'status': 'AWAKE'
					},
					'form': {
						'stage': 'AT_START',
						'status': 'DEAD'
					}
				}
			}
		}
		self.awake_toggling_tags = {'body': True, 'form': False}
		self.is_processing = defaultdict(lambda: False)
		self.tex = []

	def handle_starttag(self, tag, attrs):
		self.refresh_statuses(tag, 'AT_START')

		if self.statuses['is_active']['status'] is 'AWAKE':
			self.is_processing[tag] = True
			self.handle_streak(tag, 'AT_START') 

	def handle_endtag(self, tag):
		self.refresh_statuses(tag, 'AT_END')
		
		if self.statuses['is_active']['status'] == 'AWAKE':
			self.is_processing[tag] = False
			self.handle_streak(tag, 'AT_END')

	def handle_data(self, data):
		if self.statuses['is_active']['status'] == 'AWAKE':
			self.handle_streak('handle_data', 'AT_DATA')
			
			to_append = Template('$data')
			if self.is_processing['rp']:
				to_append = Template('')
			if self.is_processing['rb']:
				to_append = Template('{$data}')
			if self.is_processing['rt']:
				to_append = Template('{|$data}')
			self.tex.append(to_append.substitute(data=data))

	def refresh_statuses(self, tag, stage):
		for key, value in self.statuses.iteritems():
			if tag in value['toggles']:
				if value['toggles'][tag]['stage'] == stage:
					self.statuses[key]['status'] = value['toggles'][tag]['status']
	
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
		if tag == next_tag and stage == 'AT_START':
			self.increase_streak()
		elif stage == 'AT_END' and tag == 'handle_data':
			self.reset_streak()
		elif stage in ['AT_START', 'AT_DATA']:
			if tag == 'ruby':
				if stage == 'AT_START':
					to_append = '\\jruby'
			if tag == 'br':
				to_append = self.NEXT_LINE if count <= 2 else self.NEXT_VERSE				
			self.new_streak(next_tag)
		self.tex.append(to_append)

	def get_lyrics(self):
		return ''.join(self.tex[:-3])

def extract_song_info(url):
	bs_raw_lyrics = BeautifulSoup(requests.get(url).text, "html5lib")
	
	artist = bs_raw_lyrics.find("div", class_="artistcontainer").get_text()
	title = bs_raw_lyrics.find("div", class_="titlelyricblocknew").find("h1").get_text()
	lyrics = bs_raw_lyrics.find("div", id="Lyrics").get_text()
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
		browser = mechanize.Browser()
		browser.open('http://furigana.sourceforge.net/cgi-bin/index.cgi')
		browser.select_form(nr=0)
		browser.form['text'] = lyrics
		furigana_request = browser.submit()
		return furigana_request.read().decode('utf-8')

def fill_tex_template(artist, title, lyrics):
	template_file = open('tex_template.tex', 'r')
	template = Template(template_file.read())
	return template.substitute(artist=artist, title=title, lyrics=lyrics)

def main():
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
	
	clipboard.set(fill_tex_template(artist, title, parser.get_lyrics()))

if __name__ == '__main__':
	main()
