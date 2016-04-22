import urllib, urllib2, cookielib
import json, random

class ustvnow:
	def __init__(self, user, password):
		self.user = user
		self.password = password
		self.mBASE_URL = 'http://m-api.ustvnow.com'
		self.uBASE_URL = 'http://lv2.ustvnow.com'

	def build_query(self, queries):
		return '&'.join([k+'='+urllib.quote(str(v)) for (k,v) in queries.items()])

	def get_channels(self, quality, only_free=True):
		print "[USTVnow] Logging in"
		token = self._login()
		passkey = self._get_json('gtv/1/live/viewdvrlist', {'token': token})['globalparams']['passkey']
		print "[USTVnow] Found key", passkey
		print "[USTVnow] Logging in alternative"
		token = self._login_alt()
		content = self._get_json('gtv/1/live/channelguide', {'token': token})
		channels = []
		print "[USTVnow] Parsing channels"
		for i in content['results']:
			try:
				if i['order'] == 1:
					name = i['stream_code']
					if not only_free or name in ("ABC", "CBS", "CW", "FOX", "NBC", "PBS", "My9"): 
						stream = self._get_json('stream/1/live/view', {'token': token, 'key': passkey, 'scode': i['scode']})['stream']
						url = stream.replace('smil:', 'mp4:').replace('USTVNOW1', 'USTVNOW').replace('USTVNOW', 'USTVNOW' + str(quality))
						print "[USTVnow] found", name,  url
						channels.append({
							'name': name,
							'url': url
							})
			except:
				print "[USTVnow] Something went wrong"
		return channels 
		   
	def _build_url_alt(self, path, queries):
		query = self.build_query(queries)
		return '%s/%s?%s' % (self.uBASE_URL, path, query)

	def _build_json(self, path, queries):
		query = urllib.urlencode(queries)
		return '%s/%s?%s' % (self.mBASE_URL, path, query)

	def _fetch(self, url):
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		return opener.open(url) 

	def _get_json(self, path, queries={}):
		return json.loads(self._fetch(self._build_json(path, queries)).read())

	def _login(self):
		self.cj = cookielib.CookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj)) 
		urllib2.install_opener(opener)
		url = self._build_json('gtv/1/live/login', {'username': self.user, 'password': self.password, 'device':'gtv', 'redir':'0'})
		response = opener.open(url)
		for cookie in self.cj:
			if cookie.name == 'token':
				return cookie.value

	def _login_alt(self):
		self.cj = cookielib.CookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		urllib2.install_opener(opener)
		url = self._build_url_alt('iphone_login', {'username': self.user, 'password': self.password})
		response = opener.open(url)
		for cookie in self.cj:
			if cookie.name == 'token':
				self.cookie = cookie.value
				return cookie.value

