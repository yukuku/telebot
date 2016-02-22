import StringIO
import json
import logging
import random
import urllib
import urllib2

# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

TOKEN = 'YOUR_BOT_TOKEN_HERE'

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'


# ================================

class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)


# ================================

def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False


# ================================

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook',
                                                                     urllib.urlencode({'url': url})))))


class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        update_id = body['update_id']
        message = body['message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']
        who = ['who are you', 'Who are you']
        if not text:
            logging.info('no text')
            return

        def reply(msg=None, img=None, audio=None, document=None, location=None):
            if msg:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    'reply_to_message_id': str(message_id),
                })).read()

            elif img:
                resp = multipart.post_multipart(BASE_URL + 'sendPhoto', [
                    ('chat_id', str(chat_id)),
                    ('reply_to_message_id', str(message_id)),
                ], [
                    ('photo', 'image.jpg', img),
                ])

            elif audio:
                resp = multipart.post_multipart(BASE_URL + 'sendAudio', [
                    ('chat_id', str(chat_id)),
                    ('reply_to_message_id', str(message_id)),
                ], [
                    ('audio', 'audio.mp3', audio),
                ])

            elif document:
                resp = multipart.post_multipart(BASE_URL + 'sendDocument', [
                    ('chat_id', str(chat_id)),
                    ('reply_to_message_id', str(message_id)),
                ], [
                    ('document', 'document.pdf', document),
                ])

            elif location:
                resp = urllib2.urlopen(BASE_URL + 'sendLocation', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'latitude': location[0],
                    'longitude': location[1],
                    'reply_to_message_id': str(message_id),
                })).read()

            else:
                logging.error('no msg or action specified')
                resp = None

            logging.info('send response:')
            logging.info(resp)

        if text.startswith('/'):
            if text == '/start':
                reply('Bot enabled ' + u'\U0001F60E' + ', digit /help to list all available commands')
                setEnabled(chat_id, True)

            elif text == '/stop':
                reply('Bot disabled')
                setEnabled(chat_id, False)

            elif text == '/image':
                img = Image.new('RGB', (512, 512))
                base = random.randint(0, 16777216)
                pixels = [base+i*j for i in range(512) for j in range(512)]  # generate sample image
                img.putdata(pixels)
                output = StringIO.StringIO()
                img.save(output, 'JPEG')
                reply(img=output.getvalue())

            elif text == '/my_image':
                img = Image.open('image.jpg')
                output = StringIO.StringIO()
                img.save(output, 'JPEG')
                reply(img=output.getvalue())

            elif text == '/audio':
                audio_file = open('audio.mp3')
                audio = audio_file.read()
                reply(audio=audio)

            elif text == '/pdf':
                document_file = open('document.pdf')
                document = document_file.read()
                reply(document=document)

            elif text == '/location':
                location = [40.748817, -73.985428]
                reply(location=location)

            elif text == '/help':
                reply('Hello '+fr['first_name']+' here you can control me by sending these commands:\n\n'
                      '/image: generate sample image\n/my_image: get custom image\n'
                      '/audio: get house sample\n/pdf: get sample document\n/location: get default location\n')
            else:
                reply('What command? Try /help')

        elif any(s in text for s in who):
            reply('My name is telegram_engine bot! nice to meet you '+fr['first_name']+'!')
        elif 'what time' in text:
            reply('look at the top of your screen! ' + u'\U0001F51D')
        else:
            # coding: utf-8
            from lib.simsimi import SimSimi
            from lib.language_codes import LC_ENGLISH
            from lib.simsimi import SimSimiException

            back = ""
            simSimi = SimSimi(conversation_language=LC_ENGLISH,
                              conversation_key='YOUR_SIMSIMI_TOKEN')

            try:
                from unicodedata import normalize
                text = normalize('NFKD', text).encode('ASCII', 'ignore')
                response = simSimi.getConversation(text)
                if not response['response']:
                    reply('You exceeded simsimi api daily limit!')
                back = response['response']
            except SimSimiException as e:
                    print e
            if not back:
                reply('Something went wrong..')
            elif 'I HAVE NO RESPONSE' in back:
                reply('you said something with no meaning')
            else:
                reply(back)


app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
