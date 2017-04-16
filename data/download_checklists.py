# coding=utf8

# Script to download all the checklists from magiccards.info


import codecs
import os
import sys
import urllib2

from lxml import etree

class Set(object):
  def __init__(self, date_str, name, code, set_type):
    self.date_str = date_str
    self.name = name
    self.code = code
    self.set_type = set_type

  def __str__(self):
    return "%s (%s) - %s" % (self.name, self.code, self.date_str)


class Card(object):
  def __init__(self, name, rarity):
    self.name = name
    self.rarity = rarity

  def __str__(self):
    return "|".join([self.name, self.rarity])


def parseSets(filename):
  f = open(filename)
  setMap = {}
  for i, line in enumerate(f.xreadlines()):
    if line.strip().startswith("#"):
      continue

    parts = line.strip().split("\t")

    if len(parts) < 5:
      #print "Skipping line %d without much data: %s" % (i, str(parts))
      continue

    (date_str, name, code, set_type) = (parts[0], parts[1], parts[3], parts[4])

    # See if this is MTGO-only set
    if len(parts) >= 6 and "Magic Online" in parts[5]:
      #print "Skipping MTGO-only set on line %d: %s" % (i, str(parts))
      continue

    if not code:
      #print "Skipping set without code on line %d: %s" % (i, str(parts))
      continue

    if "(" in code:
      code = code.split("(")[0].strip()

    if set_type.endswith(" set"):
      set_type = set_type[:-4]

    s = Set(date_str, name, code, set_type)
    setMap[(date_str, code)] = s
    
  return setMap


def parseMagicCardsInfoPage(html):

  # Find the appropriate table
  row = etree.HTML(html).find(".//tr[@class='even']")

  if row is None:
    return None

  table = row.getparent()

  #print "table len", len(table)
  rows = iter(table)
  next(rows)  # Skip header row
  ret = []
  for row in rows:
    cols = list(row)
    name = cols[1][0].text
    rarity = cols[4].text[0]
    if not name:
      continue

    name = name.replace(u"\xc6", "Ae")
    ret.append(Card(name, rarity))

  return ret


def fetchMagicCardsInfoPage(code):
  if not code:
    return None

  # Map of codes from mtg.gamepedia to findmagiccards.info
  SET_CODE_REMAP = {
      "NEM": "NE",
      }

  if code.upper() in SET_CODE_REMAP:
    code = SET_CODE_REMAP[code.upper()]

  url = "http://magiccards.info/query?q=e%%3A%s%%2Fen&v=list&s=cname" % code
  response = urllib2.urlopen(url)
  return response.read()


printing_warnings = False

def maybePrintLine(is_warning):
  global printing_warnings
  if is_warning != printing_warnings:
    print ""
    printing_warnings = is_warning


if __name__ == "__main__":
  SKIP_EXISTING = True

  # Parse sets.txt to get set names
  setMap = parseSets("sets.txt")
  if not setMap:
    print >>sys.stderr, "Failed to parse sets.txt"
    sys.exit(-1)

  print "Read %d sets" % len(setMap)

  for (date_str, code), s in sorted(setMap.iteritems()):
    #if s.code not in ["NEM"]:
      #continue

    folder = s.set_type.lower()
    if not folder:
      maybePrintLine(True)
      print "WARNING: Unsure where to put set:", s
      continue

    if not os.path.exists(folder):
      os.mkdir(folder)
    filename = "%s/%s-%s.txt" % (folder, s.date_str, s.code.lower())

    if SKIP_EXISTING and os.path.exists(filename):
      # Skip downloading what we have.  Disable this if fresh fetch desired.
      maybePrintLine(True)
      print "SKIP:", s
      continue

    html = fetchMagicCardsInfoPage(s.code)
    if not html:
      maybePrintLine(True)
      print "ERROR: Unable to fetch set:", s
      continue

    cards = parseMagicCardsInfoPage(html)
    if not cards:
      maybePrintLine(True)
      print "ERROR: Unable to parse html for set:", s
      continue

    with codecs.open(filename, "w", encoding='utf-8') as f:
      f.writelines("%s\r\n" % card for card in cards)  # \r\n for windows

    maybePrintLine(False)
    print "%s (%d cards, %s) to %s" % (s.name, len(cards), s.date_str, filename)
