import json
import re
import requests
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup
from pprint import pprint

import math
import time
import random

class Item:
	def __init__(self,itemData,url):
		self.downloadUrl = url
		self.handleData(itemData)
		self.handleDownloads()
	def __str__(self):
		return "%s [%s]" % (self.itemTitle,self.itemType)
	def __repr__(self):
		return "%s [%s]" % (self.itemTitle,self.itemType)

	def handleData(self,itemData):
		self.itemType = itemData["item_type"].capitalize()
		self.bandName = itemData["band_name"]
		self.itemTitle = itemData["item_title"]
		self.saleId = itemData["sale_item_id"]
		self.albumUrl = "https://f4.bcbits.com/img/a%s_9.jpg" % itemData["item_art_id"]
	def handleDownloads(self):
		downloadPage = requests.get(self.downloadUrl)
		self.cookies = downloadPage.cookies
		downloadSoup = BeautifulSoup(downloadPage.text,'html.parser')
		for script in downloadSoup.find_all("script"):
			script = script.text.splitlines()
			if("var DownloadData = {" in script):
				start = script.index("var DownloadData = {")
				end = start+14
				downloadData = "".join(script[start+1])
				downloadData= json.loads(downloadData[12:-2])
				self.downloads = {}
				for itemFormat,data in downloadData["downloads"].items():
					url= data["url"].replace("download","statdownload") + "&.rand=%d&.vrs=1" % ( math.floor( random.random() * time.time() * 1000))
					self.downloads[itemFormat] = url


				break
	def getDownload(self,itemFormat="mp3-320"):
		return self.downloads[itemFormat]

	def fixDownload(self):
		milis = time.time() * 1000
		rand = int(math.floor(random.random() * milis))


class SongCollection:
	def __init__(self,username,password):
		self.collection = {}
		self.username = username
		postData = {
			"user.name":username,
			"login.password": password
		}
		self.tryLogin(postData)

	def __str__(self):
		title = "%s's Collection\n" % self.username
		for artist,songs in sorted(self.collection.items()):
			title += "\t%s: \n" % artist
			for song in songs:
				title+= "\t\t%s\n" % (song)

		return title

	def tryLogin(self,postData):
		try:
			loginUrl = "https://bandcamp.com/login_cb"
			loginResponse = requests.post(loginUrl,postData)
			loginData = loginResponse.json()
			if("errors" in loginData.keys() ):
				if(loginData["errors"][0]["field"] == 'login.password'):
					raise LoginError("Incorrect Password")
				elif(loginData["errors"][0]["field"] == 'user.name'):
					raise LoginError("Incorrect Username")
				else:
					print(loginData["errors"])
					raise Exception("Unhandled Exception")
			elif("ok" in loginData.keys()):
				self.handleCollectionPage(loginResponse)

		except ConnectionError as e:
			print("Connection Failed")
		except LoginError as e:
			print(e)


	def handleCollectionPage(self,loginResponse):
		userUrl = loginResponse.json()["next_url"]
		cookies = loginResponse.cookies
		collectionPage = requests.get(userUrl,cookies=cookies)

		collectionSoup = BeautifulSoup(collectionPage.text,'html.parser')
		for script in collectionSoup.find_all("script"):
			script = script.text.splitlines()
			if("var CollectionData = {" in script):
				start = script.index("var CollectionData = {")
				itemDetails = script[start+1].replace("item_details: ","")
				regex = '"(?P<id>\d*)":(?P<json>{.*?{.*?}.*?})'
				matches = re.findall(regex,itemDetails)
				urls = script[start+2].replace("redownload_urls: ","")
				urls = json.loads(urls)

				for itemId,itemData in matches:
					itemData = json.loads(itemData)
					i = Item(itemData,urls["p%s" % itemData["sale_item_id"]] )
					if( i.bandName in self.collection.keys() ):
						self.collection[i.bandName].append(i)

					else:
						self.collection[i.bandName] = [i]

				break

	def downloadItem(self,item):
		# Prepared
		# response = requests.get(url)
		# if response(parsed)["result"] == "ok"
		# response = requests.get(url)
		# response(parsed) ["download_url"] <---- Download
		# else: errorType: ExpirationError
		response = requests.get(item.getDownload(),allow_redirects=False)













class LoginError(Exception):
	def __init__(self,value):
		self.value = value
	def __str__(self):
		return repr(self.value)

if __name__ == '__main__':
	# u = input("username")
	# p = input("password")
	with open("login.txt",'r') as f:
		username,password = f.readlines()
		username = username.strip()
	SongCollection(username,password)
