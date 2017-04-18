# coding=utf8

# Script to download/generate all the checklists based on magiccards.info


import codecs
import os
import re
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



def normalizeName(name):
  match = re.match("^.* \((.*/.*)\)$", name)
  if match:
    # Split card: use what's in the parentheses
    name = match.group(1)
  name = name.replace(u"\xc6", "Ae")
  name = name.replace(u"\u201c", '"')
  name = name.replace(u"\u201d", '"')
  try:
    name.encode("ascii")
  except UnicodeEncodeError, e:
    #print "Failed to encode %s:" % name, e
    pass

  return name

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
  #print "Fetching %s from %s" % (code, url)
  try:
    response = urllib2.urlopen(url)
  except urllib2.URLError:
    return None
  return response.read().decode("utf8")


def parseMagicCardsInfoPage(html, cardCategorizer):

  # Find the appropriate table
  row = etree.HTML(html).find(".//tr[@class='even']")

  if row is None:
    return None

  table = row.getparent()

  #print "table len", len(table)
  rows = iter(table)
  next(rows)  # Skip header row
  cards = {}
  for row in rows:
    cols = list(row)
    raw_name = cols[1][0].text
    cardType = cols[2].text
    manaCost = cols[3].text
    rarity = cols[4].text[0]

    name = normalizeName(raw_name)
    if not name:
      continue

    # Always add card to cardCategorizer
    cardCategorizer.addCard(name, cardType, manaCost)

    # Don't append split card twice?  Or just make this a map
    cards[name] = Card(name, rarity)

  return sorted(cards.values())


class Category:

  CAT_MAP = {
    0: "Unknown",
    1: "Colorless",
    2: "White",
    3: "Blue",
    4: "Black",
    5: "Red",
    6: "Green",
    7: "Gold",
    8: "Hybrid",
    9: "Split",
    10: "Artifact",
    11: "Land",
  }
  def __init__(self, num):
    self.num = num

  def __str__(self):
    return self.CAT_MAP[self.num]


class CardCategorizer(object):
  UNKNOWN = Category(0)
  COLORLESS = Category(1)
  WHITE = Category(2)
  BLUE = Category(3)
  BLACK = Category(4)
  RED = Category(5)
  GREEN = Category(6)
  GOLD = Category(7)
  HYBRID = Category(8)
  SPLIT = Category(9)
  ARTIFACT = Category(10)  # colorless-costing artifacts
  LAND = Category(11)

  MANA_CAT_MAP = {
    "W": WHITE,
    "U": BLUE,
    "B": BLACK,
    "R": RED,
    "G": GREEN,
  }

  COSTLESS_CARD_MAP = {
      "Ancestral Vision": BLUE,
      "Evermind": BLUE,
      "Hypergenesis": GREEN,
      "Living End": BLACK,
      "Restore Balance": WHITE,
      "Wheel of Fate": RED,
  }

  def __init__(self):
    self.cardCatMap = {}
    self.splitCardCosts = {}  # Map from combined name to [cost]

  def _determineColors(self, manaCost):
    """Returns set with each unique color in mana cost; empty for colorless"""
    return set(re.findall("[WUBRG]", manaCost))
    
  def _determineCategory(self, cardType, manaCost):
    if "Land" in cardType:
      return self.LAND

    if not manaCost:
      return self.UNKNOWN

    if "/" in manaCost:
      if re.match("^\d*\{.*\}$", manaCost):
        # All symbols are hybrid, so this is a hybrid card
        return self.HYBRID
      return self.GOLD  # Only some symbols are hybrid, so this is gold
  
    colors = self._determineColors(manaCost)
    if not colors:
      if "Artifact" in cardType:
        return self.ARTIFACT
      return self.COLORLESS

    if len(colors) > 1:
      return self.GOLD

    return self.MANA_CAT_MAP[colors.pop()]

  def addCard(self, name, cardType, manaCost):
    if name in self.cardCatMap:
      return

    if "/" in name:
      # Split card, write down the cost and move on
      if name not in self.splitCardCosts:
        self.splitCardCosts[name] = []
      self.splitCardCosts[name].append(manaCost)
      return

    try:
      cat = self._determineCategory(cardType, manaCost)
      if cat == self.UNKNOWN and name in self.COSTLESS_CARD_MAP:
        cat = self.COSTLESS_CARD_MAP[name]
      self.cardCatMap[name] = cat
    except:
      print "Failure for ", name, cardType, manaCost
      sys.exit(-1)

  def writeToFile(self, filename):

    # Write out split cards
    for name, costs in self.splitCardCosts.iteritems():
      cat = self._determineCategory("", "".join(costs))
      if cat == self.GOLD:
        self.cardCatMap[name] = self.SPLIT
      else:
        self.cardCatMap[name] = cat
    
    print "Categorized %d cards" % len(self.cardCatMap)

    with codecs.open(filename, "w", encoding='utf8') as f:
      f.write("# Cards categorized by how they are sorted (COLORLESS, color, HYBRID, SPLIT, etc)\r\n")
      f.writelines("%s|%s\r\n" % (name, cat) for (name, cat) in sorted(self.cardCatMap.iteritems()))
  


printing_warnings = False

def maybePrintLine(is_warning):
  global printing_warnings
  if is_warning != printing_warnings:
    print ""
    printing_warnings = is_warning


if __name__ == "__main__":
  SKIP_EXISTING = False

  # Parse sets.txt to get set names
  setMap = parseSets("sets.txt")
  if not setMap:
    print >>sys.stderr, "Failed to parse sets.txt"
    sys.exit(-1)

  print "Read %d sets" % len(setMap)

  cardCategorizer = CardCategorizer()

  for (date_str, code), s in sorted(setMap.iteritems()):
    #if s.code not in ["APC"]:
      #continue

    folder = s.set_type.lower()
    if not folder:
      maybePrintLine(True)
      print "WARNING: Unsure where to put set:", s
      continue

    if not os.path.exists(folder):
      os.mkdir(folder)

    if not os.path.exists("fetched"):
      os.mkdir("fetched")
    htmlname = "fetched/%s-mci.html" % s.code.lower()
    html = None
    if os.path.exists(htmlname):
      with codecs.open(htmlname, "r", encoding='utf8') as f:
        html = f.read()

    if not html:
      html = fetchMagicCardsInfoPage(s.code)
      if html:
        with codecs.open(htmlname, "w", encoding='utf8') as f:
          f.write(html)

    if not html:
      maybePrintLine(True)
      print "ERROR: Unable to read/fetch set:", s
      continue

    cards = parseMagicCardsInfoPage(html, cardCategorizer)
    if not cards:
      maybePrintLine(True)
      print "ERROR: Unable to parse html for set:", s
      continue

    textname = "%s/%s-%s.txt" % (folder, s.date_str, s.code.lower())
    with codecs.open(textname, "w", encoding='utf8') as f:
      f.writelines("%s\r\n" % card for card in cards)  # \r\n for windows

    maybePrintLine(False)
    print "%s (%d cards, %s) to %s" % (s.name, len(cards), s.date_str, textname)


  cardCategorizer.writeToFile("categories.txt")

