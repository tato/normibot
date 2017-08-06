# Normibot: A Telegram Bot that fetches info about music albums and artists
#
# Copyright (C) 2017 Pablo Tato Ramos. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import logging
from pathlib import Path
import requests
from config import *

# TODO: check for errors in every html request sent (raise_for_status()?)

artist_format = '<b>{}</b>\nCountry:{}\nID:{}\nScore:{}\n'
def artist_to_string(artist):
	return artist_format.format(a['name'], a['country'], a['id'], a['score'])

album_format = '<b>{}</b> ({})\nby {}\n...ID {}'
def album_to_string(album):
	return album_format.format(album['title'], 'TBD', 'Unknown', album['id'])

track_format = '<b>{}</b> ({})\nby {}\nfrom {} ({})\n...'
def track_to_string(track):
	return track_format.format('Not Yet Titled', '00:00', 'Unknown', 'Nowhere', 'TBD')

# TODO: Use inc= arguments to obtain additional info (e.g. &inc=aliases+tags+ratings)
# TODO: I know for sure I can get ratings with that, very likely a list of albums too
def get_artist(artist):
	logging.info('Requesting {} from musicbrainz'.format(artist))
	req = requests.get(
		'http://musicbrainz.org/ws/2/artist/?query=artist:{}&limit=1&fmt=json'.format(artist),
		headers = { 'User-Agent': get_user_agent_string() }
	)
	response = req.json()
	return response['artists'][0] if response['count'] > 0 else None

def get_album(album):
	logging.info('Requesting {} from musicbrainz'.format(album))
	req = requests.get(
		'http://musicbrainz.org/ws/2/release/?query=release:{}&limit=1&fmt=json'.format(album),
		headers = { 'User-Agent': get_user_agent_string() }
	)
	response = req.json()
	return response['releases'][0] if response['count'] > 0 else None

def get_track(song):
	pass

telegram_url = 'https://api.telegram.org/bot{}/'.format(get_telegram_token())
def call_telegram_method(method, args=None):
	r = requests.post(telegram_url + method, data=args)
	return r.json()

def handle_artist(artist, user):
	response = get_artist(artist)
	text = artist_to_string(response) if response else 'Not found'

	user_info = '@' + user['username'] if 'username' in user else user['id']
	logging.info('Sending artist {} to user {}'.format(artist, user_info))
	logging.debug('Response: "{}"'.format(text))

	args = {
		'chat_id': user['id'],
		'text': text,
		'parse_mode': 'HTML'
	}

	call_telegram_method('sendMessage', args)

def handle_album(album, user):
	response = get_album(album)
	text = album_to_string(album) if album else 'Not found'

	user_info = '@' + user['username'] if 'username' in user else user['id']
	logging.info('Sending album {} to user {}'.format(album, user_info))
	logging.debug('Response: "{}"'.format(text))

	args = {
		'chat_id': user['id'],
		'text': text,
		'parse_mode': 'HTML'
	}

	call_telegram_method('sendMessage', args)

def handle_track(song, user):
	pass

def handle_update(update):
	logging.info('Handling update with ID {}'.format(update['update_id']))
	if 'message' in update:
		msg = update['message']
		if 'text' in msg and 'from' in msg:
			t = msg['text']
			if t.startswith('/artist'):
				handle_artist(t[8:], msg['from'])
			elif t.startswith('/album'):
				handle_album(t[7:], msg['from'])
			elif t.startswith('/song'):
				handle_song(t[6:], msg['from'])

def main():
	logging.basicConfig(filename='normibot.log', level=logging.DEBUG, format='(%(asctime)s) %(levelname)s: %(funcName)s() says "%(message)s"')
	logging.debug('Telegram Token: "{}"'.format(get_telegram_token()))
	logging.debug('musicbrainz User-Agent: "{}"'.format(get_user_agent_string()))
	logging.info('Not currently receiving updates. Shutting down.')

	offset = 0
	offsetfile = Path('./OFFSET')
	if offsetfile.exists():
		with offsetfile.open('r') as f:
			offset = int(f.readline())
	while True:
		args = {
			'offset': offset,
			'timeout': 60,
			'allowed_updates': ['message'] # TODO: include inline queries when necessary
		}
		updates = call_telegram_method('getUpdates', args)
		# TODO: this might be too much checking, make some assumptions
		if updates and 'ok' in updates and updates['ok']:
			for update in updates['result']:
				offset = max(offset, update['update_id'])
				handle_update(update)
		offset += 1
		with offsetfile.open('OFFSET', 'w') as f:
			f.write(str(offset))

if __name__ == '__main__':
	main()
