#!/usr/bin/env python
from __future__ import unicode_literals
import sys
import glob
import os
import time
import logging
import argparse
import json

from slackclient import SlackClient

sys.dont_write_bytecode = True

this_dir = os.path.dirname(os.path.realpath(__file__))

'''
Documentation for this file will be provided later.
I'm a bit too busy right now, sorry!
I suggest not trying to develop for SuperBot just
yet, until I can explain how.
'''


class SuperBot(object):
	def __init__(self, config_file=None, credentials_file=None):
		# set the config object
		try:
			self.config = json.load(open(config_file or 'config.json'))
		except (IOError, ValueError):
			self.config = {}

		# set slack token
		self.tokens = json.load(open(credentials_file or 'credentials.json'))
		self.token = self.tokens.get('slack')

		# set working directory for loading plugins or other files
		self.directory = self.config.get('base_path', this_dir)
		
		if self.directory.startswith('~'):
			path = os.path.join(os.path.expanduser('~'), self.directory)
			self.directory = os.path.expanduser(path)
		elif not self.directory.startswith('/'):
			path = os.path.join(os.getcwd(), self.directory)
			self.directory = os.path.abspath(path)

		# establish logging
		log_file = config.get('logfile', 'superbot.log')
		logging.basicConfig(filename=log_file,
							level=logging.INFO,
							format='%(asctime)s %(message)s')
		logging.info('Initialized in: {}'.format(self.directory))
		self.debug = self.config.get('debug', True)
		self.verbose = self.config.get('verbose', True)

		self.username = self.config.get('username', 'superbot')
		self.usercode = self.config.get('usercode', '<@U249VP6H2>')

		# initialize stateful fields
		self.last_ping = 0
		self.plugins = []
		self.slack_client = None

	def _dbg(self, debug_string):
		if self.debug:
			logging.info(debug_string)

	def connect(self):
		"""Convenience method that creates Server instance"""
		self.slack_client = SlackClient(self.token)
		self.slack_client.rtm_connect()

	def _start(self):
		self.connect()
		self.loadPlugins()
		while True:
			for reply in self.slack_client.rtm_read():
				self.eventHandlers(reply)
			self.autoping()
			time.sleep(.1)

	def start(self):
		if 'daemon' in self.config and self.config.get('daemon'):
			import daemon
			with daemon.DaemonContext():
				self._start()
		self._start()

	def autoping(self):
		# hardcode the interval to 3 seconds
		now = int(time.time())
		if now > self.last_ping + 3:
			self.slack_client.server.ping()
			self.last_ping = now

	def debug(self, text=None, ansi_code=None, force=False):
		if self.verbose or force:
			if text:
				if ansi_code:
					print '\033['+str(ansi_code)+'m' + text + '\033[0m'
				else:
					print text
			else:
				print

	def eventHandlers(self, data):
		if "type" in data:
			self._dbg("got {}".format(data["type"]))
			self.handleEvent(data)
			for plugin in self.plugin_instances:
				if self.debug:
					plugin.handleEvent(data)
				else:
					try:
						plugin.handleEvent(data)
					except Exception:
						logging.exception("problem in module {} {}".format(plugin, data))

	def handleEvent(self, data):
		if event["type"] == "hello":
			self.debug(type(self).__name__ + " connected to Slack", 42)

	def sendMessage(self, channel, message=None):
		channel = self.slack_client.server.channels.find(channel)
		if channel is not None and message is not None:
			channel.send_message(message)
			return True
		return False

	def apiCall(self, method, kwargs={}):
		if method is not None:
			response = self.slack_client.server.api_call(method, **kwargs)
			return json.loads(response)

	def loadPlugins(self):
		self.plugin_instances = []
		for name in self.plugin_names:
			module = __import__(name)
			instance = module.Plugin(self)
			self.plugin_instances.append(instance)

	def findPlugins(self):
		sys.path.insert(0, self.directory + '/plugins/')
		for plugin in glob.glob(self.directory + '/plugins/*'):
			sys.path.insert(1, plugin)

		for plugin in glob.glob(self.directory + '/plugins/*.py'):
			logging.info(plugin)
			name = plugin.split('/')[-1][:-3]
			self.plugin_names.append(name)


class Plugin(object):
	def __init__(self, superbot):
		self.sb = superbot

	def handleEvent(self, data):
		raise NotImplementedError

def main():
	bot = SuperBot()
	try:
		bot.start()
	except KeyboardInterrupt:
		sys.exit(0)

if __name__ == '__main__':
	main()