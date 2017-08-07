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
import requests
from config import *

def artist_to_string(artist):
    if 'name' not in artist:
        return 'Something went wrong, I\'m so very sorry :('

    sb = ['<b>', artist['name'], '</b>']
    if 'disambiguation' in artist:
        sb.extend(['\n', artist['disambiguation']])

    if 'area' in artist:
        area = artist['area']
        if 'name' in area:
            sb.extend(['\nfrom ', area['name']])

    if 'life-span' in artist:
        ls = artist['life-span']
        if 'begin' in ls:
            sb.extend(['\nborn in ', ls['begin']])

    return ''.join(sb)

def album_to_string(album):
	# TODO: figure out which attributes are optional in the API response
    if 'title' not in album:
        return 'Something went wrong, I\'m so very sorry :('

	sb = ['<b>', album['title'], '</b>']
	if 'date' in album:
		sb.extend([' (', str(album['date']), ')')

    ac = album.get('artist-credit', [])
	if ac:
		credit = ac[0]
		if 'artist' in credit:
			artist = credit['artist']
			if 'name' in artist:
                sb.extend(['\nby ', artist['name']])

	return ''.join(sb)

# TODO: Use inc= arguments to obtain additional info (e.g. &inc=aliases+tags+ratings)
# TODO: I know for sure I can get ratings with that, very likely a list of albums too
# TODO UPDATED: I don't know why I was so sure but I think there aren't any inc= in the search page
def search_artist(artist_name, count):
	logging.info('Requesting {} from musicbrainz'.format(artist_name))
    furl = 'http://musicbrainz.org/ws/2/artist/?query=artist:{}&limit={}&fmt=json'
	req = requests.get(
		furl.format(artist_name, count),
		headers = { 'User-Agent': get_user_agent_string() }
	)
    # TODO: What abount HTML Errors
	response = req.json()
    # Assuming response['artists'] is a list here, fuck this defensive coding
	return response.get('artists', [])

def search_release(release_name, count):
	logging.info('Requesting {} from musicbrainz'.format(release_name))
    furl = 'http://musicbrainz.org/ws/2/release/?query=release:{}&limit={}&fmt=json'
	req = requests.get(
		furl.format(release_name, count),
		headers = { 'User-Agent': get_user_agent_string() }
	)
    # TODO: What about HTML Errors?
	response = req.json()
    # Assuming response['releases'] is a list here, fuck this defensive coding
    return response.get('releases', [])

# IDEA: It might be nicer to use **kwargs instead of an explicit dict argument
telegram_url = 'https://api.telegram.org/bot{}/'.format(get_telegram_token())
def call_telegram_method(method, **kwargs):
	r = requests.post(telegram_url + method, data=kwargs)
	return r.json()

def handle_artist(artist_name, chat_id):
	response = search_artist(artist_name, 1)
    if not isinstance(response, list):
        logging.error('search_artist didnt return list with {}'.format(artist_name))
        return

    if len(response) < 1:
        logging.info('Sending not found {} to {}'.format(artist_name, chat_id))
        call_telegram_method('sendMessage', chat_id = chat_id, text = 'Not found')
        return

	text = artist_to_string(response[0])

	logging.info('Sending artist {} to chat {}'.format(artist_name, chat_id))
	logging.debug('Response: "{}"'.format(text))

	call_telegram_method('sendMessage', chat_id = chat_id, text = text, parse_mode = 'HTML')

def handle_release(release_title, chat_id):
	response = search_release(release_title, 1)
    if not isinstance(response, list):
        logging.error('search_release didnt return list with {}'.format(release_title))
        return

    if len(response) < 1:
        logging.info('Sending not found {} to {}'.format(release_title, chat_id))
        return

	text = release_to_string(response[0])

	logging.info('Sending release "{}" to chat id {}'.format(release_title, chat_id))
	logging.debug('Response: "{}"'.format(text))

	call_telegram_method('sendMessage', chat_id = chat_id, text = text, parse_mode = 'HTML')

def handle_track(track_title, chat_id):
	call_telegram_method(
        'sendMessage',
        chat_id = chat_id,
        text = '<b>NO PREGUNTES TODAVÍA XOXO</b>\n',
        parse_mode = 'HTML'
    )

def handle_update(update):
	logging.info('Handling update with ID {}'.format(update['update_id']))
	if 'message' in update:
		msg = update['message']
		if 'text' in msg and 'chat' in msg: # Chat isn't optional, but checking just in case
			t = msg['text']
			if t.startswith('/artist'):
				handle_artist(t[8:], msg['chat'].get('id', 0))
			elif t.startswith('/album'):
				handle_release(t[7:], msg['chat'].get('id', 0))
			elif t.startswith('/song'):
				handle_track(t[6:], msg['chat'].get('id', 0))

def main():
	logging.basicConfig(filename='normibot.log', level=logging.DEBUG, format='(%(asctime)s) %(levelname)s: %(funcName)s() says "%(message)s"')
	logging.debug('Telegram Token: "{}"'.format(get_telegram_token()))
	logging.debug('musicbrainz User-Agent: "{}"'.format(get_user_agent_string()))
	logging.info('Not currently receiving updates. Shutting down.')

	offset = 0
	# HACK: In order to calculate the offset, I getUpdates as a way to get older updates and get the
	# HACK: latest offset that way. This has several problems:
	# HACK:  - If there aren't old messages, I will wait for the first query and ignore it
	# HACK:  - If there are more messages than the default limit telegram sends me, what happens
	# HACK:     depends on the order the updates are sent. If older updates are sent, I will
	# HACK:     possibly answer old queries again. I could make the limit bigger but that's a
	# HACK:     bandaid.
	updates = call_telegram_method('getUpdates', timeout = 60, allowed_updates = ['message'])
	if updates and updates.get('ok', False):
		for update in updates.get('result', []):
			offset = max(offset, update.get('update_id', 0) + 1)

	while True:
		# TODO: allow inline updates when necessary
		updates = call_telegram_method('getUpdates', offset = offset, timeout = 60, allowed_updates = ['message'])
		if updates and updates.get('ok', False):
			for update in updates.get('result', []):
				offset = max(offset, update.get('update_id', 0) + 1)
				handle_update(update)

if __name__ == '__main__':
	main()
