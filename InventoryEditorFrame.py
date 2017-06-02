
import wx

import os
import sys
import thread



ID_NEW      = 107
ID_SAVE     = 108
ID_SAVEAS     = 109
ID_LOAD     = 110

ID_EXIT     = 120

filePrices = "fmc_prices.txt"

NONE_STR = "None"
CUSTOM_STR = "Custom..."
FRAME_TITLE_STR = "Inventory Editor"
UNTITLED_FILE_NAME_STR = "Untitled Inventory"

RARITIES_MAP = {
  "M": "Mythic",
  "R": "Rare",
  "U": "Uncommon",
  "C": "Common",
  "X": "Other",
}

class InventoryEditorFrame(wx.Frame):
  FRAME_WIDTH = 640
  FRAME_MARGIN = 16
  FRAME_HEIGHT = 780
  BOX_WIDTH = FRAME_WIDTH - 2 * FRAME_MARGIN

  def __init__(self, parent, ID, title):
    wx.Frame.__init__(self, parent, ID, title, wx.DefaultPosition,
        (self.FRAME_WIDTH + self.FRAME_MARGIN, self.FRAME_HEIGHT))

    panel = wx.Panel(self, -1)

    self.inventory = {}
    self.visiblecards = {}
    self.isUpdatingLists = 0
    self.isGettingPrices = 0
    self.visibilitytainted = 1
    self.prices = {}

    self.num_cards_shown = 0
    self.num_cards_total = 0

    self.current_file_name = ""
    self.current_file_path = "."
    self.dirtyinventory = 0


    self.InitFileData()
    self.InitMenu()
    self.InitStatusBar()
    self.InitCheckBoxes(panel)
    self.InitSetFilterArea(panel)
    #self.RefreshMatchCriteria()
    self.InitCardLists(panel)

    self.UpdateTitle()


  def InitMenu(self):
    menubar = wx.MenuBar()

    menu_file = wx.Menu()
    menu_file.Append(ID_NEW, "&New Inventory\tCtrl-N")
    menu_file.Append(ID_LOAD, "&Open Inventory...\tCtrl-O")
    menu_file.Append(ID_SAVE, "&Save Inventory\tCtrl-S")
    menu_file.Append(ID_SAVEAS, "Save Inventory &As...\tCtrl-A")
    menu_file.AppendSeparator()
    menu_file.Append(ID_EXIT, "E&xit")
    menubar.Append(menu_file, "&File")

    self.SetMenuBar(menubar)

    # Events

    self.Bind(wx.EVT_MENU, self.NewInventory, id=ID_NEW)
    self.Bind(wx.EVT_MENU, self.LoadInventory, id=ID_LOAD)
    self.Bind(wx.EVT_MENU, self.SaveInventory, id=ID_SAVE)
    self.Bind(wx.EVT_MENU, self.SaveInventoryAs, id=ID_SAVEAS)
    self.Bind(wx.EVT_MENU, self.Exit, id=ID_EXIT)


  def InitCheckBoxes(self, p):
    # Rarities

    self.cbRarity = {}
    y_init = 40
    y_max = 100
    y = y_init
    x = 32
    dx = 96
    dy = 20
    self.rarityBox = wx.StaticBox(p, -1, "Rarity", (self.FRAME_MARGIN, 16), (196, y_max - dy / 2))

    for letter in ["M", "R", "U", "C", "X"]:
      rarity = RARITIES_MAP[letter]
      self.cbRarity[letter] = wx.CheckBox(p, -1, rarity, (x, y))
      y += dy
      if y >= 100:
        y = y_init
        x += dx

    for cb in self.cbRarity.values():
      cb.SetValue(0)
      self.Bind(wx.EVT_CHECKBOX, self.OnVisTainted, cb)

    x += dx + self.FRAME_MARGIN + 8
    y = y_init
    self.cbCategory = {}
    self.categoryBox = wx.StaticBox(p, -1, "Category", (236, 16), (388, y_max - dy / 2))

    categories = ["Colorless", "White", "Blue", "Black", "Red", "Green", "Gold", "Hybrid", "Split", "Artifact", "Land"]
    for category in categories:
      self.cbCategory[category] = wx.CheckBox(p, -1, category, (x, y))
      y += dy
      if y >= 100:
        y = y_init
        x += dx

    for key, cb in self.cbCategory.iteritems():
      cb.SetValue(0)
      self.Bind(wx.EVT_CHECKBOX, self.OnVisTainted, cb)


  def InitSetFilterArea(self,  p):
    boxY = 124

    self.formatBox = wx.StaticBox(p, -1, "Sets", (self.FRAME_MARGIN, boxY), (self.BOX_WIDTH, 284))

    self.txtFormatLabel = wx.StaticText(p, -1, "Format:", (32, boxY+28), (64, 24))
    SetFontBold(self.txtFormatLabel)

    self.chFormatChoice = wx.Choice(p, 107, (96, boxY+24), (144, 24),  self.FormatList)
    self.Bind(wx.EVT_CHOICE, self.OnSelectFormat, self.chFormatChoice)
    self.chFormatChoice.SetSelection(0)

    self.sets = {}
    self.setcovers = {}
    label_width = 30
    x_init = 32
    y_init = boxY + 64
    dx = 32
    dy = 20
    max_width = self.BOX_WIDTH - dx

    l = x_init
    t = y_init

    for set_code in self.CoreSets:
      txt = wx.StaticText(p, -1, set_code, (l,t), (label_width,16), wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE )
      txt.Bind(wx.EVT_LEFT_DCLICK, self.OnSetDClick)
      self.setcovers[set_code] = txt
      self.sets[set_code] = wx.StaticText(p, -1, set_code, (l,t), (label_width,16), wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE )
      l = l + dx
      if l > max_width:
        l = x_init
        t = t + dy

    if l > x_init:
      l = x_init
      t = t + dy
    t += 8

    for set_code in self.ExpansionSets:
      txt = wx.StaticText(p, -1, set_code, (l,t), (label_width,16), wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE )
      txt.Bind(wx.EVT_LEFT_DCLICK, self.OnSetDClick)
      self.setcovers[set_code] = txt
      self.sets[set_code] = wx.StaticText(p, -1, set_code, (l,t), (label_width,16), wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE )
      l = l + dx
      if l > max_width:
        l = x_init
        t = t + dy

    if l > x_init:
      l = x_init
      t = t + dy
    t += 8

    for set_code in self.SpecialSets:
      txt = wx.StaticText(p, -1, set_code, (l,t), (label_width,16), wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE )
      txt.Bind(wx.EVT_LEFT_DCLICK, self.OnSetDClick)
      self.setcovers[set_code] = txt
      self.sets[set_code] = wx.StaticText(p, -1, set_code, (l,t), (label_width,16), wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE )
      l = l + dx
      if l > max_width:
        l = x_init
        t = t + dy

    self.cbShowAll = wx.CheckBox(p, -1, "Show unselected-but-legal versions", (300, boxY+28))
    self.Bind(wx.EVT_CHECKBOX, self.OnVisTainted, self.cbShowAll)


  def InitCardLists(self, p):

    listY = 424
    BUTTON_WIDTH = 100
    LIST_WIDTH = (self.BOX_WIDTH - BUTTON_WIDTH - 32) / 2

    listX = self.FRAME_MARGIN
    self.lvCardList = wx.ListView(p, -1, (listX, listY), (LIST_WIDTH, 220), 
      wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.VSCROLL | wx.LC_NO_HEADER )
    self.lvCardList.InsertColumn(0, "Name:", width=152)
    self.lvCardList.InsertColumn(1, "Set:", width=48)

    invX = self.FRAME_MARGIN + self.BOX_WIDTH - LIST_WIDTH
    self.lvInvList = wx.ListView(p, -1, (invX, listY), (LIST_WIDTH, 220), wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.VSCROLL | wx.LC_NO_HEADER)
    self.lvInvList.InsertColumn(0, "Name:", width=130)
    self.lvInvList.InsertColumn(1, "Set:", width=48)
    self.lvInvList.InsertColumn(2, "#:", width=24)

    self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelInvList, self.lvInvList)

    listRight = listX + LIST_WIDTH
    buttonMargin = (invX - listRight - wx.Button.GetDefaultSize()[0]) / 2
    buttonX = listRight + buttonMargin
    self.btnAddCard = wx.Button(p, -1, "Add Card", (buttonX, listY + 54))
    self.btnAddCard.SetDefault()
    self.Bind(wx.EVT_BUTTON, self.OnAddCard, self.btnAddCard)

    self.btnDelCard = wx.Button(p, -1, "Delete Card", (buttonX, listY + 96))
    self.Bind(wx.EVT_BUTTON, self.OnDelCard, self.btnDelCard)


    self.OnVisTainted(None)


  def InitFileData(self):
    with open("data/cardlist.txt") as f:
      self.CardList = []  # Array of cards' (name, set_code, rarity)
      self.CardSetsMap = {}  # Map from card name to set(set codes)
      for line in f:
        parts = line.strip().split("|")
        name = CanonizeName(parts[0])
        sets = set()
        for pair in parts[1:]:
          set_code, rarity = pair.split("-")
          if rarity not in RARITIES_MAP.keys():
            rarity = "X"
          self.CardList.append((name, set_code, rarity))
          sets.add(set_code)
        self.CardSetsMap[name] = sets

    with open("data/setlist.txt") as f:
      self.SetMap = {}
      for line in f:
        if line.strip().startswith("#"):
          continue
        parts = line.strip().split("|")

        self.SetMap[parts[0]] = parts[1:]
      self.CoreSets = self.SetMap["core"]
      self.ExpansionSets = self.SetMap["expansion"]
      self.SpecialSets = self.SetMap["special"]

    with open("data/formats.txt") as f:
      # List of format strings
      self.FormatList = []

      # Map from format strings to list of sets
      self.Formats = {}
      for line in f:
        if line.strip().startswith("#"):
          continue
        parts = line.strip().split("|")

        self.FormatList.append(parts[0])
        self.Formats[parts[0]] = parts[1:]

    self.FormatList.append(NONE_STR)
    self.Formats[NONE_STR] = []
    self.FormatList.append(CUSTOM_STR)
    self.Formats[CUSTOM_STR] = []

    with open("data/categories.txt") as f:
      self.CardCategories = {}
      for line in f:
        if line.strip().startswith("#"):
          continue
        parts = line.strip().split("|")
        self.CardCategories[parts[0]] = parts[1]

    if os.path.exists(filePrices):
      pricefile = open(filePrices)
      for line in pricefile.readlines():
        key, price = line.strip().split('|')
        #print "K, P: '"+key+"', '"+price+"'"
        if len(price):
          self.prices[key] = price
    else:
      print "Failed to open price file."


  def InitStatusBar(self):
    self.sb = wx.StatusBar(self, -1)
    self.sb.SetFieldsCount(4)
    self.sb.SetStatusWidths([16, 206, 86, 208])
    self.UpdateNumShown()
    self.SetStatusBar(self.sb)

  #Event handlers

  def OnSetDClick(self, event):

    #change set indicator
    set_code = event.GetEventObject().GetLabel()
    self.sets[set_code].Enable(not self.sets[set_code].IsEnabled())

    custom = [k for (k, v) in self.sets.iteritems() if v.IsEnabled()]
    custom.sort()

    #print "Custom: ", custom

    #change choice
    for i in range(len(self.FormatList)):
      f = self.Formats[self.FormatList[i]]
      f.sort()
      if f == custom:
        self.chFormatChoice.SetSelection(i)
        break
    else:
      self.chFormatChoice.SetSelection(len(self.FormatList)-1)
      self.Formats[CUSTOM_STR] = custom
    self.OnVisTainted(None)

  def OnSelInvList(self, event):
    invindex = event.GetIndex()
    cardname = self.lvInvList.GetItemText(invindex)
    set_code = self.lvInvList.GetItem(invindex,1).GetText()

    for i in range(self.lvCardList.GetItemCount()):
      i_name = self.lvCardList.GetItemText(i)
      i_set = self.lvCardList.GetItem(i,1).GetText()

      if i_name == cardname and i_set == set_code:
        self.lvCardList.Select(i)
        return
    else:
      sys.stderr.write("ERR: Failed to find matching card in card list\n")
    #i = self.lvInvList.GetNextItem(i, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)


  def OnSelectFormat(self, event):
    fmt = event.GetString()

    for s, widget in self.sets.iteritems():
      widget.Enable(s in self.Formats[fmt])

    self.OnVisTainted(None)


  def OnAddCard(self, event):

    cardname, set_code = self.GetSelectedCard()
    print "adding card '%s'" % cardname

    key = self.CardKey(cardname, set_code)

    if key in self.inventory:
      self.inventory[key] += 1
    else:
      self.inventory[key] = 1

    count = self.lvInvList.GetItemCount()

    # Update the UI for inventory update
    i = 0
    while i < count:
      i_name = self.lvInvList.GetItemText(i)
      i_set = self.lvInvList.GetItem(i,1).GetText()

      if i_name == cardname and i_set == set_code:
        self.lvInvList.SetStringItem(i, 2, `self.inventory[key]`)
        break
      if (i_name > cardname):
        self.lvInvList.InsertStringItem(i, cardname)
        self.lvInvList.SetStringItem(i, 1, set_code)
        self.lvInvList.SetStringItem(i, 2, `self.inventory[key]`)
        break
      i += 1
    else:
      self.lvInvList.InsertStringItem(i, cardname)
      self.lvInvList.SetStringItem(i, 1, set_code)
      self.lvInvList.SetStringItem(i, 2, `self.inventory[key]`)
    self.lvInvList.Select(i)
    self.lvInvList.EnsureVisible(i)

    self.num_cards_shown += 1
    self.num_cards_total += 1
    if not self.dirtyinventory:
      self.dirtyinventory = 1
      self.UpdateTitle()
    self.UpdateNumShown()

  def OnDelCard(self, event):
    i = self.lvInvList.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
    if i == -1: 
      sys.stderr.write("ERR: No item in inventory list selected\n")
      raise Exception

    cardname = self.lvInvList.GetItemText(i)
    set_code = self.lvInvList.GetItem(i, 1).GetText()

    key = self.CardKey(cardname, set_code)

    if key not in self.inventory:
      sys.stderr.write("ERR: Inven shows no record of card: '"+key+"'\n")
      raise Exception

    q = self.inventory[key]

    self.num_cards_shown -= 1
    self.num_cards_total -= 1
    self.UpdateNumShown()

    if (q <= 1):
      #delete from list/inventory
      del self.inventory[key]
      self.lvInvList.DeleteItem(i)
      if(i > 0):
        self.lvInvList.Select(i-1)
        self.lvInvList.EnsureVisible(i-1)
      return

    self.inventory[key] = q - 1
    if not self.dirtyinventory:
      self.dirtyinventory = 1
      self.UpdateTitle()
    self.lvInvList.SetStringItem(i, 2, `self.inventory[key]`)
    self.lvInvList.EnsureVisible(i)


  def LoadInventory(self, event):
    inven = {}
    dlg = wx.FileDialog(self, message="Load file...", 
      defaultDir=self.current_file_path,
      defaultFile="", 
      wildcard="*.inv", 
      style = wx.OPEN | wx.CHANGE_DIR)

    if dlg.ShowModal() != wx.ID_OK:
      #print "Canceled"
      return

    path = dlg.GetPath()

    #print "Loading from:", path
    with open(path, 'r') as f:
      i = 0
      line = ""
      try:
        for i, line in enumerate(f):
          name, set_code, quantity = line.strip().split('|')
          if name == "Name":
            continue
          quantity = int(quantity)
          if quantity <= 0:
            sys.stderr.write("Invalid quantity for",key)
            continue

          key = self.CardKey(name, set_code)
          if key not in inven:
            inven[key] = 0
          inven[key] += quantity
      except ValueError:
        dlg = wx.MessageDialog(self, "There was a problem reading the "
                      "inventory file.  See line %d:\n%s" % (i+1, line),
                      "Error Reading File",
                      wx.OK)
        dlg.ShowModal()
        return
    #print "Successfully loaded."
    self.current_file_path, self.current_file_name = os.path.split(path)
    self.inventory = inven
    self.dirtyinventory = 0
    self.UpdateTitle()
    self.RefreshInvList()

  def CheckSaveChanges(self):
    """Returns whether the user wants to save; returns True on cancellation."""
    if not self.dirtyinventory:
      return False

    if len(self.current_file_name):
      str = "The Inventory file "+self.current_file_name+" has"
    else:
      str = "The contents of the Untitled file have"

    dlg = wx.MessageDialog(self, str + " changed.\n"
                "\nDo you want to save the changes?",
                FRAME_TITLE_STR,
                wx.YES_NO | wx.CANCEL | wx.ICON_EXCLAMATION)
    result = dlg.ShowModal()

    if result == wx.ID_YES:
      self.SaveInventory(None)
      return False
    elif result == wx.ID_NO:
      return False
    elif result == wx.ID_CANCEL:
      return True

  def NewInventory(self, event):
    if self.CheckSaveChanges():
      return

    self.inventory = {}

    self.num_cards_shown = 0
    self.num_cards_total = 0

    self.current_file_name = ""
    self.dirtyinventory = 0

    self.RefreshInvList()
    self.UpdateTitle()
    self.UpdateNumShown()

  def SaveInventory(self, event):
    if not len(self.current_file_name):
      self.SaveInventoryAs(None)
      return

    self.WriteFile()


  def SaveInventoryAs(self, event):
    dlg = wx.FileDialog(self, message="Save file as...", 
      defaultDir = self.current_file_path, 
      defaultFile = self.current_file_name,
      wildcard = "*.inv", 
      style = wx.SAVE | wx.OVERWRITE_PROMPT)

    if dlg.ShowModal() == wx.ID_OK:
      b, f = os.path.split(dlg.GetPath())
      print "Saving to:", b, ",", f

      self.current_file_path = b
      self.current_file_name = f

      self.WriteFile()
    else:
      #print "Canceled!"
      pass

  def WriteFile(self):
    fname = os.path.join(self.current_file_path, self.current_file_name)
    keys = self.inventory.keys()
    keys.sort()
    with open(fname, 'w') as f:
      f.write("|".join(["Name", "Set", "Quantity"]) + "\n")
      for k in keys:
        name, set_code = self.DecodeCardKey(k)
        print 'writing name', name
        f.write("|".join([name, set_code, str(self.inventory[k])]) + "\n")
    self.dirtyinventory = 0
    self.UpdateTitle()

  def Exit(self, event):
    if self.CheckSaveChanges():
      return
    self.Close()

  def OnVisTainted(self, evt):
    #print "Refreshing visible cards list"
    self.RefreshMatchCriteria()
    self.visibilitytainted = 1
    if not self.isUpdatingLists:
      thread.start_new(self.ThRefreshCardList, ())


  def tmp_parse_fmc_from_file(self):
    fmc_file = open("data.txt")
    array = []
    for l in fmc_file.readlines():
      try:
        n, s, r, p = l.strip().split('|')
        array.append([n,s,r,p])
      except:
        print l
        raise

    return array

  def GetCardValue(self, k):
    n,s = self.DecodeCardKey(k)
    k = self.CardKey(n[:40],s).lower()
    if key not in self.prices:
      sys.stderr.write("ERR: no price for card '"+k+"'\n")
      #num_err += 1
      #continue
      raise NoPriceError
    return self.prices[k]


  # General Utility functions

  def SetLeftStatus(self, str):
    self.sb.SetStatusText(str, 1)
  def SetRightStatus(self, str):
    self.sb.SetStatusText(str, 3)

  def RefreshInvList(self):

    if self.isUpdatingLists:
      #make program refresh both lists again
      self.visibilitytainted = 1
      return

    self.lvInvList.DeleteAllItems()

    keys = self.inventory.keys()
    keys.sort()
    i = 0
    self.num_cards_shown = 0
    self.num_cards_total = 0
    for k in keys:
      self.num_cards_total += self.inventory[k]
      if self.visiblecards[k]:
        n,s = self.DecodeCardKey(k)
        self.lvInvList.InsertStringItem(i, n)
        self.lvInvList.SetStringItem(i, 1, s)
        self.lvInvList.SetStringItem(i, 2, `self.inventory[k]`)
        self.num_cards_shown += self.inventory[k]
        i += 1
      else:
        print "Not visible: '"+k+"'"
    self.UpdateNumShown()

  def ThRefreshCardList(self):

    if not self.visibilitytainted:
      return

    class ResetError(Exception):
      pass

    while self.visibilitytainted:
      try:
        self.isUpdatingLists = 1
        self.SetLeftStatus("Updating card list...")
        self.SetRightStatus("Updating...")

        self.visibilitytainted = 0

        cardNameMatchMap = {}
        self.visiblecards = {}

        self.num_cards_shown = 0
        self.num_cards_total = 0
        self.lvCardList.DeleteAllItems()
        self.lvInvList.DeleteAllItems()

        #print "Beginning refresh loop"
        for (name, set_code, rarity) in self.CardList:
          if self.visibilitytainted: 
            #print "Throwing exception"
            raise ResetError

          # Construct the card key
          key = self.CardKey(name, set_code)

          # Count the inventory
          try:
            self.num_cards_total += self.inventory[key]
          except KeyError:
            pass

          # See whether card *name* should be shown
          if name not in cardNameMatchMap:
            cardNameMatchMap[name] = self.MatchSearchCriteria(name)

          visible = (
              cardNameMatchMap[name] and
              rarity in self.allowedRarities and
              (set_code in self.allowedSets or self.showAllVersions))

          if rarity not in self.cbRarity.keys():
            print "UNKNOWN Rarity: %s" % rarity

          self.visiblecards[key] = visible
          if visible:
            # Add entry to card list
            row = self.lvCardList.GetItemCount()
            self.lvCardList.InsertStringItem(row, name)
            self.lvCardList.SetStringItem(row, 1, set_code)

            # Add entry to inventory list (if card is in inventory)
            try:
              count = self.inventory[key]
              if count:
                row = self.lvInvList.GetItemCount()
                self.lvInvList.InsertStringItem(row, name)
                self.lvInvList.SetStringItem(row, 1, set_code)
                self.lvInvList.SetStringItem(row, 2, `count`)
                self.num_cards_shown += count
            except KeyError:
              pass
      except ResetError:
        print "Visibility updated while refreshing, restarting..."
        pass

    #print "Finished refresh loop"
    self.isUpdatingLists = 0
    self.SetLeftStatus(""+`self.lvCardList.GetItemCount()`+" cards")
    self.UpdateNumShown()

  def UpdateNumShown(self):
    self.SetRightStatus("Cards Showing: "+`self.num_cards_shown`+
                      " / "+`self.num_cards_total`)
  def UpdateTitle(self):
    str = FRAME_TITLE_STR + " - ["

    if len(self.current_file_name):
      str += self.current_file_name
    else:
      str += UNTITLED_FILE_NAME_STR

    str += "]"

    if self.dirtyinventory:
      str += "*"

    self.SetTitle(str)


  def CardKey(self, name, set_code):
    return "%s-%s" % (name, set_code)

  def DecodeCardKey(self, key):
    i = key.rfind('-')
    return key[:i], key[i+1:]

  def MatchSearchCriteria(self, name):
    try:
      setOK = len(self.CardSetsMap[name].intersection(self.allowedSets)) > 0
      catOK = self.CardCategories[name] in self.allowedCategories
      return setOK and catOK
    except KeyError:
      print "Card %s isn't in CardSetsMap or CardCategories" % name
      pass
    return False

  def RefreshMatchCriteria(self):
    self.allowedRarities = set(
        [k for (k, v) in self.cbRarity.iteritems() if v.GetValue()])
    if not self.allowedRarities:
      self.allowedRarities = self.cbRarity.keys()
    self.allowedCategories = set(
        [k for (k, v) in self.cbCategory.iteritems() if v.GetValue()])
    if not self.allowedCategories:
      self.allowedCategories = self.cbCategory.keys()

    self.allowedSets = set(
        [k for (k, v) in self.sets.iteritems() if v.IsEnabled()])
    self.showAllVersions = self.cbShowAll.GetValue()

  def GetSelectedCard(self):
    i = self.lvCardList.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
    if i == -1: 
      sys.stderr.write("ERR: No item in card list selected\n")
      raise Exception

    cardname = self.lvCardList.GetItemText(i)
    set_code = self.lvCardList.GetItem(i, 1).GetText()

    #print "Card found:", cardname, '['+set_code+']'

    return (cardname, set_code)


def SetFontBold(control):
  font = control.GetFont()
  font.SetWeight(wx.FONTWEIGHT_BOLD)
  control.SetFont(font)

def CanonizeName(name):
  cut = name.find(' [')
  if cut >= 0: name = name[:cut]
  return name

