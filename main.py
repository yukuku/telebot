#Please read "usefull links" before going on, they are necessary for better understanding
import StringIO
import json #Imports the json library that decodes json tokens recieved from telegram api
import logging #Imports the library that puts messages in the log info of the google app engine
import random #Library that creates random numbers
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

class EnableStatus(ndb.Model): #NDB entity called EnabledStatus
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False) #Entity has atribute enabled


# ================================

def setEnabled(chat_id, yes):
    es = ndb.Key(EnableStatus, str(chat_id)).get() #Gets the entity
    if es: #If it exists
        es.enabled = yes #Sets its enabled atribute
        es.put()
        return
    es = EnableStatus(id = str(chat_id)) #If not creates a new entity
    es.put()

def getEnabled(chat_id):
    es = ndb.Key(EnableStatus, str(chat_id)).get()
    if es:
        return es.enabled #Return the atual state
    es = EnableStatus(id = str(chat_id))
    es.put()
    return False


# ================================ This part makes the comunication google-telegram

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
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))


class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))
        #From here you can take message information, now it only uses the chat_id and text,
        #you can take more things from it, search how to use json on google
        update_id = body['update_id']
        message = body['message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text') #Takes the 'text' string
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id'] #Chat id string

        if not text:
            logging.info('no text')
            return

        def reply(msg=None, img=None): #Function used to send messages, it recieves a string message or a binary image
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
            else:
                logging.error('no msg or img specified') #If there is no image it puts in the google log the string
                resp = None

            logging.info('send response:')
            logging.info(resp)
        #From here you can make custom commands, just add an 'elif'
        if text.startswith('/'):
            if text == '/start':
                reply('Bot enabled')
                setEnabled(chat_id, True) #Sets the status to True (read above comments)
            elif text == '/stop':
                reply('Bot disabled')
                setEnabled(chat_id, False) #Changes it to false
            elif text == '/image': #Creates an aleatory image
                img = Image.new('RGB', (512, 512)) #Size of the image
                base = random.randint(0, 16777216)
                pixels = [base+i*j for i in range(512) for j in range(512)]  # generate sample image
                img.putdata(pixels)
                output = StringIO.StringIO()
                img.save(output, 'JPEG')
                reply(img=output.getvalue())
                """If you want to send a different image use this piece of code:
                img = Image.open("image.jpg")
                output = StringIO.StringIO()
                img.save(output, 'JPEG')
                reply(img=output.getvalue())"""
            else:
                reply('What command?')

        #If it is not a command (does not start with /)

        elif 'who are you' in text:
            reply('telebot starter kit, created by yukuku: https://github.com/yukuku/telebot')
        elif 'what time' in text:
            reply('look at the top-right corner of your screen!')
        else:
            if getEnabled(chat_id): #If the status of the bot is enabled the bot answers you
                try:
                    resp1 = json.load(urllib2.urlopen('http://www.simsimi.com/requestChat?lc=en&ft=1.0&req=' + urllib.quote_plus(text.encode('utf-8')))) #Sends you mesage to simsimi IA
                    back = resp1.get('res')
                except urllib2.HTTPError, err:
                    logging.error(err)
                    back = str(err)
                if not back:
                    reply('okay...')
                elif 'I HAVE NO RESPONSE' in back:
                    reply('you said something with no meaning')
                else:
                    reply(back)
            else:
                logging.info('not enabled for chat_id {}'.format(chat_id))

#Telegram comunication (dont change)
app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
