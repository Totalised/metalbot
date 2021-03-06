#!/usr/bin/python3

import requests
import sys
import logging
import re
import random
import youtubegetter
import config

class command(object):
    def __init__(self, regex, action):
        self.r = re.compile(regex)
        self.action = action

    def check(self, text):
        m = re.search(self.r, text)
        if m:
            return m.groups()

class MetalBot(object):
    def __init__(self):
        self.baseurl = "https://api.telegram.org/bot%s/" % config.telegram_token
        self.update_id = 0

        self.commands = [command("/dice ([0-9]*)", self.cmd_dice),
                command("/metal", self.cmd_metal),
                command("/8ball (.*)", self.cmd_8ball),
                command("/insult (.*)", self.cmd_insult),
                command("/randomimage", self.cmd_randomimage)
                ]

        self.youtube = youtubegetter.YoutubeGetter(config.youtube_key)

    def api_request(self, method, data=None):
        """
        Makes a request to the Telegram API using the method 'method' and sending data 'data', which must be a key-value dictionary.
        """

        try:
            response = requests.post(self.baseurl + method, data).json()
            if response['ok'] == True:
                return response['result']
            else:
                logging.error("API request failed, dunno why?")
        except Exception as e:
            logging.exception("API request failed, dunno why?")

    def check_connection(self):
        """
        Checks the connection to the server and the bot token. Retrieves additional bot details.
        """

        me = self.api_request("getMe")
        if me:
            self.username, self.id, self.first_name = me['username'], me['id'], me['first_name']
        else:
            logging.error("something failed, I'm dying\n")
            exit()
        logging.info("connection ok!")
        logging.info("username: %s" % self.username)
        logging.info("id: %s" % self.id)
        logging.info("first name: %s" % self.first_name)

    def get_updates(self):
        """
        Fetches unconfirmed updates from the server. When this method is called, all updates fetched previously (up to self.update_id) will be confirmed.
        """

        self.updates = self.api_request('getUpdates', {'offset' : self.update_id})
        if self.updates:
            self.update_id = self.updates[-1]['update_id'] + 1
            logging.debug("received %i updates" % len(self.updates))
            return self.updates


    def send_text(self, text, chat_id):
        resp = self.api_request("sendMessage", {'chat_id' : chat_id, 'text' : text})
        if resp:
            return True
        else:
            return False

    def respond(self, text):
        if self.message:
            return self.send_text(text, self.message['chat']['id'])

    def handle_message(self, message):
        self.message = message
        if message['chat']['type'] == 'private':
            self.handle_message_private()
        elif message['chat']['type'] == 'group':
            self.handle_message_group()

    def handle_message_private(self):
        self.handle_message_generic()

    def handle_message_group(self):
        self.handle_message_generic()

    def handle_message_generic(self):
        try:
            text = self.message['text']
            self.parse_command(text)
        except:
            pass

    def parse_command(self, text):
        logging.debug("parsing for commands")
        for cmd in self.commands:
            params = cmd.check(text)
            if not params == None:
                try:
                    cmd.action(params)
                except:
                    logging.exception("something went wrong")
                break


    # actual commands

    def cmd_dice(self, params):
        logging.info("dice rolling...")
        try:
            limit = int(params[0])
            rannum = random.randint(1,limit)
            self.respond("%s rolled: %i" % (self.message['from']['first_name'], rannum))
        except Exception as e:
            logging.exception("something failed :(")
            self.respond("Don't screw me over, %s! \U0001f620" % (self.message['from']['first_name']))

    def cmd_metal(self, params):
        logging.info("metal!")
        link = self.youtube.randomVideo()
        self.respond(link)

    def cmd_8ball(self, params):
        logging.info("8ball")
        ballz = ["yes", "no", "reply hazy,try again", "outlook not so good", "as i see it,yes", "repeat the question", "not in a million years", "it is certain", "it is decidedly so", "my sources say no", "better not tell you now", "signs point to yes", "count on it", "meh"]
        if(len(params[0]) < 10):
            self.respond("whaddya say?")
        else:
            self.respond(random.choice(ballz))

    def cmd_insult(self, params):
        logging.info("insult")
        insults = ["%s, you ugly, venomous toad!", "%s, you infectious pestilence!", "%s, you lunatic, lean-witted fool!", "%s, you impudent, tattered prodigal!", "%s, you old, withered crab tree!", "I bet your brain feels as good as new, %s, seeing that you never use it.", "I wasn't born with enough middle fingers to let you know how I feel about %s", "%s must have been born on a highway because that's where most accidents happen", "%s has two brain cells, one is lost and the other is out looking for it.", "%s, you are so fat the only letters of the alphabet you know are KFC", "% is as bright as a black hole, and twice as dense.", "I fart to make %s smell better", "Learn from %s's parent's mistakes - use birth control!", "Some drink from the fountain of knowledge; %s only gargled.", "%s, you are so stupid, you'd trip over a cordless phone.", "Ordinarily people live and learn. %s just lives.", "%s is as useless as ejection seats on a helicopter.", "%s is as useless as a one-legged man at an arse kicking contest"]
        name = params[0]
        a = False
        if name.lower() == self.first_name.lower():
            name = self.message['from']['first_name']
            a = True
        self.respond(random.choice(insults) % name)

    def cmd_randomimage(self, params):
        logging.info("randomimage")
        self.respond("randomimage")

if __name__ == '__main__':
    logging.basicConfig(filename="metalbot.log", format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.ERROR)
    requests_log.propagate = True
    logging.info("----==== \m/ Hello Metalworld! \m/ ====----")
    random.seed()

    m = MetalBot()

    m.check_connection()

    while True:
        m.get_updates()
        for u in m.updates:
            m.handle_message(u['message'])
