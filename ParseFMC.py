

#	This script outputs a list of lines of the form 'cardname|price'

import pullparser
import sys
import os.path
import string
import exceptions

import socket
import urllib


ret_type_default	= 0
ret_color_default	= 0
ret_cost_default	= 0
ret_pt_default		= 0

url_fmc_byname_ = "http://www.findmagiccards.com/Find/ByName/A.html"
url_fmc_byname = "http://www.findmagiccards.com/Find/ByName.html"


known_fmc_bugs = {
"Abunas' Chant":"Abuna's Chant", 
"Radiant's Judgement":"Radiant's Judgment", 
"Crovax, The Cursed":"Crovax the Cursed",
"Day/Night (Day)":"Night/Day (Day)",
"Day/Night (Night)":"Night/Day (Night)",
"Skyshroud Poachers":"Skyshroud Poacher",
"Seafarers' Quay":"Seafarer's Quay"
}


def fix_path(url):
	return os.path.normpath(url).replace("\\","/").replace("http:/w","http://w")
	
def parse_list_page(url_to_open, ret_type, ret_color, ret_cost, ret_pt):

	#print "\nPARSING:", url_to_open
	#print '.',

	while 1:
		try:
			f = urllib.urlopen(url_to_open)
			break
		except exceptions.IOError:
			pass

	p = pullparser.PullParser(f)

	ret_list = []

	#proceed until just after title row
	for token in p.tokens():
		if token.type == 'endtag' and token.data == 'tr': break

	#traverse rows of card table
	for token in p.tags('tr'):
		if token.type == 'endtag': continue

		data = ["" for i in range(8)]

		index = 0
		for t in p.tokens():
			if index > 7: break
			if t.type == 'endtag' and t.data == 'td': 
				index = index + 1
			if t.type == 'data':
				data[index] += t.data
		
		#print string.join([CARDNAME, SET, COLOR, TYPE, COST, PT, RARITY, PRICE], "|")
		
		
		#fix known bugs
		if known_fmc_bugs.has_key(data[0]):
			data[0] = known_fmc_bugs[data[0]]
		
		#item = [CARDNAME, SET, RARITY, PRICE]
		item = [data[0], data[1], data[6], data[7]]
		
		if(ret_type):
			item.append(data[3])
		if(ret_color):
			item.append(data[2])
		if(ret_cost):
			item.append(data[2])
		if(ret_pt):
			item.append(data[5])
		
		ret_list.append(item)

	return ret_list

#depth-first-search the website by using successive links; return dictionary
def parse_link_page(url_to_open, 
					ret_type,
					ret_color,
					ret_cost,
					ret_pt):

	ret_list = []
	
	#print "Parsing:", url_to_open
	sys.stderr.write('.')
	
	while 1:
		try:
			f = urllib.urlopen(url_to_open)
			break
		except exceptions.IOError:
			pass
	
	p = pullparser.PullParser(f)

	url_base = os.path.split(url_to_open)[0]


	#find beginning of sub-links
	tokens = p.tokens()
	for token in tokens:
		if token.data == "Cards that start with ?":
			break

	try:
		tokens.next()
	except StopIteration:	#we used up tokens - must be a leaf page
		y = parse_list_page(url_to_open, ret_type, ret_color, ret_cost, ret_pt)
		ret_list.extend( y)
		return ret_list
	
	for token in p.tags('a'):
		if token.type == "endtag": continue
		
		url = dict(token.attrs).get("href", "-")
		#text = p.get_compressed_text(endat=("endtag", "a"))
		
		if url[:4] == "http": continue
		
		z = parse_link_page(fix_path(url_base+"/"+url), 
									ret_type, ret_color, ret_cost, ret_pt)
		ret_list.extend(z)

		

	return ret_list


def ParseFMC( ret_type = ret_type_default, 
				ret_color = ret_color_default, 
				ret_cost = ret_cost_default, 
				ret_pt = ret_pt_default):
	
	x = parse_link_page(url_fmc_byname, ret_type, ret_color, ret_cost, ret_pt)
	return x

if __name__ == "__main__":
	r = ParseFMC()

	for i in r:
		print i
		pass




