from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigText, ConfigNothing, ConfigYesNo, NoSave
from Components.ConfigList import ConfigListScreen
from Components.ServiceList import refreshServiceList
from Components.Sources.StaticText import StaticText
from ustv import ustvnow
from enigma import eDVBDB, eTimer

import cookielib
import os
import re
import urllib, urllib2
import sys

'''
	ustvnow XBMC Plugin
	Copyright (C) 2011 t0mm0

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.

20131227 - Modified by Dean Vaughan - http://deanvaughan.org to work from command line and output stream files to a directory
20140610 - Modified by Dean Vaughan - http://deanvaughan.org to work without XBMC running or installed
20150514 - Modified by Guido Reijntjens as a enigma2 plugin - http://www.openpli.org
20160422 - Modifief by Guido Reijntjens as the older iPad/iPhone related links are obsoleted - http://www.openpli.org
'''

config.USTVNOW = ConfigSubsection()
config.USTVNOW.email = ConfigText(default = "", fixed_size = False)
config.USTVNOW.password = ConfigText(default = "", fixed_size = False)
config.USTVNOW.quality = ConfigSelection(default = "1", choices = [("1", _("Low")), ("2", _("Mid")), ("3", _("High")), ("4", _("HD"))])
config.USTVNOW.onlyFree = ConfigYesNo(default = True)

class Ustvnow(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "Setup"
		self.setup_title = _("USTVNow Plugin - Press OK to read channels")

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))

		self.list = []
		ConfigListScreen.__init__(self, self.list, session = session)
		self.createSetup()

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.green,
			"red": self.cancel,
			"cancel": self.cancel,
			"ok": self.ok,
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def createSetup(self):
		self.list = []
		self.reloadBouquet = None
		self.list.append(getConfigListEntry(_("Email Address"), config.USTVNOW.email))
		self.list.append(getConfigListEntry(_("Password"), config.USTVNOW.password))
		self.list.append(getConfigListEntry(_("Stream quality"), config.USTVNOW.quality))
		self.list.append(getConfigListEntry(_("Only load FREE channels"), config.USTVNOW.onlyFree))
		self["config"].list = self.list

	def ok(self):
		if config.USTVNOW.email.value and config.USTVNOW.password.value:
			self["config"].l.setList([getConfigListEntry(_("Creating USTVNow servicelist"), NoSave(ConfigNothing()))])
			self["config"].selectionEnabled(0)
			self.Timer = eTimer()
			self.Timer.callback.append(self.createUserBouquet)
			self.Timer.start(0, True)

	def green(self, answer=True):
		if answer:
			config.USTVNOW.save()
			config.save()
			self.close()
		else:
			self.createSetup()

	def cancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelCallback, MessageBox, _("Really close without saving settings?"))
		else:
			self.cancelCallback(True)

	def cancelCallback(self, answer):
		if answer:
			for x in self["config"].list:
				x[1].cancel()
			self.close()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

	def createUserBouquet(self):
		f = open('/etc/enigma2/userbouquet.ustvnow.tv', 'w')
		f.write('#NAME USTV-NOW\n')
		channelscounter = 0
		for c in ustvnow(config.USTVNOW.email.value, config.USTVNOW.password.value).get_channels(int(config.USTVNOW.quality.value), config.USTVNOW.onlyFree.value):
			channelscounter += 1
			f.write("#SERVICE 4097:0:1:0:0:0:0:0:0:1:" + c["url"].replace(":","%3a")+":" + c["name"] + "\n")
			f.write("#DESCRIPTION " + c["name"] + "\n")
		f.close()
		eDVBDB.getInstance().reloadBouquets()
		refreshServiceList()
		self.session.openWithCallback(self.green, MessageBox, channelscounter and _("%d Services found") % channelscounter or _("No services found"), MessageBox.TYPE_INFO, timeout=10)

def main(session, **kwargs):
	session.open(Ustvnow)

def Plugins(**kwargs):
	name = _("USTV-Now")
	description = _("Lets configure and reload the USTV-NOW userbouqeut")
	return [PluginDescriptor(name=name, description=description, where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)]