
import wx

import ParseOracle
#import ParseFMC
import os
import sys
import thread



ID_NEW          = 107
ID_SAVE         = 108
ID_SAVEAS       = 109
ID_LOAD         = 110

ID_UPDATEPRICES = 115
ID_GETVALUE     = 116

ID_EXIT         = 120

#ID_INV_EDITOR = 103

arrExpansionList = ["AN", "AQ", "LG", "DK", "FE", "IA", "HL", "AL",
                    "MI", "VI", "WL", "TE", "SH", "EX", "US", "UL", "UD",
                    "MM", "NE", "PY", "IN", "PS", "AP", "OD", "TO", "JU",
                    "ON", "LE", "SC", "MD", "DS", "FD"]

arrBaseList = [ "A", "B", "U", "RV", "4th", "5th", "6th", "7th", "8th" ]

arrSpecialList = [ "CH", "PR", "Pre", "PO", "P2", "P3", "UG", "St" ]

fmc_setconv = {
    'UN':'U', 
    '4E':'4th',
    '5E':'5th',
    '6E':'6th',
    '7E':'7th',
    '8E':'8th', 
    'MI':'MD', 
    'TR':'TO', 
    'PR':'PY', 
    'TP':'TE', 
    'MR':'MI', 
    'P':'PR', 
    'P3K':'P3', 
    'PO2':'P2', 
}

fileOracleText = "oracle_allcards.txt"
fileCardSetList = "cardlist.txt"
fileFormats = "formats.txt"
filePrices = "fmc_prices.txt"

CUSTOM_STR = "Custom..."
FRAME_TITLE_STR = "Inventory Editor"
UNTITLED_FILE_NAME_STR = "Untitled Inventory"

cardTypes = ['Artifact','Creature','Enchant','Instant','Land','Sorcery','Planeswalker']



class InventoryEditorFrame(wx.Frame):
    
    
    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self, parent, ID, title, wx.DefaultPosition, (545, 625))

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
        
        #self.settings = {}
        #self.settings['ShowAllVersions'] = 1

        self.UpdateTitle()

        f = open("one_each.inv",'w')
        for (n,s,r) in self.CardList:
            if n != "Forest" and n != "Plains" and n != "Swamp" and n!="Mountain" and n!="Island":
                f.write(self.FormKey(n,s)+"|"+'1\n')
        f.close()
        
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
        
        menu_values = wx.Menu()
        menu_values.Append(ID_UPDATEPRICES, "&Update Price List\tCtrl-U")
        menu_values.Append(ID_GETVALUE, "Show &Value of Visible Cards\tCtrl-V")
        menubar.Append(menu_values, "&Values")
        
        self.SetMenuBar(menubar)

        # Events

        self.Bind(wx.EVT_MENU, self.NewInventory, id=ID_NEW)
        self.Bind(wx.EVT_MENU, self.LoadInventory, id=ID_LOAD)
        self.Bind(wx.EVT_MENU, self.SaveInventory, id=ID_SAVE)
        self.Bind(wx.EVT_MENU, self.SaveInventoryAs, id=ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.Exit, id=ID_EXIT)
        
        #self.Bind(EVT_MENU, self.UpdatePrices, id=ID_UPDATEPRICES)
        self.Bind(wx.EVT_MENU, self.GetValue, id=ID_GETVALUE)
        

    def InitCheckBoxes(self, p):
        
        self.colorBox = wx.StaticBox(p, -1, "Colors", (16, 16), (160, 120))

        self.cbColor = {}
        self.cbColor["W"] = wx.CheckBox(p, -1, "White", (32, 40))
        self.cbColor["U"] = wx.CheckBox(p, -1, "Blue", (32, 64))
        self.cbColor["B"] = wx.CheckBox(p, -1, "Black", (32, 88))
        self.cbColor["R"] = wx.CheckBox(p, -1, "Red", (32, 112))
        self.cbColor["G"] = wx.CheckBox(p, -1, "Green", (96, 40))
        self.cbColor["Multi"] = wx.CheckBox(p, -1, "Gold/Multi", (96, 64))
        self.cbColor["Colorless"] = wx.CheckBox(p, -1, "Colorless", (96, 88))
        for v in self.cbColor.values():
            v.SetValue(1)
        
        self.typeBox = wx.StaticBox(p, -1, "Types", (200, 16), (192, 120))

        self.cbType = {}
        self.cbType["Artifact"] = wx.CheckBox(p, -1, "Artifact", (216, 40))
        self.cbType["Creature"] = wx.CheckBox(p, -1, "Creature", (216, 72))
        self.cbType["Enchant"] = wx.CheckBox(p, -1, "Enchantment", (216, 104))
        self.cbType["Instant"] = wx.CheckBox(p, -1, "Instant", (312, 40))
        self.cbType["Land"] = wx.CheckBox(p, -1, "Land", (312, 72))
        self.cbType["Sorcery"] = wx.CheckBox(p, -1, "Sorcery", (312, 104))
        for v in self.cbType.values():
            v.SetValue(1)
        
        self.rarityBox = wx.StaticBox(p, -1, "Rarity", (416, 16), (104, 120))

        self.cbRarity = {}
        self.cbRarity["C"] = wx.CheckBox(p, -1, "Common", (432, 40))
        self.cbRarity["U"] = wx.CheckBox(p, -1, "Uncommon", (432, 64))
        self.cbRarity["R"] = wx.CheckBox(p, -1, "Rare", (432, 88))
        self.cbRarity["X"] = wx.CheckBox(p, -1, "Other", (432, 112))
        self.cbRarity["S"] = self.cbRarity["X"]
        self.cbRarity["L"] = self.cbRarity["X"]
        for v in self.cbRarity.values():
            v.SetValue(1)
        
        for cb in self.cbColor.values() + self.cbType.values() + self.cbRarity.values():
            self.Bind(wx.EVT_CHECKBOX, self.OnVisTainted, cb)


    def InitSetFilterArea(self,  p):

        self.formatBox = wx.StaticBox(p, -1, "Sets", (16, 160), (504, 144))

        self.txtFormatLabel = wx.StaticText(p, -1, "Format:", (32, 188), (64, 24))
        SetFontBold(self.txtFormatLabel)
        
        self.chFormatChoice = wx.Choice(p, 107, (96, 184), (144, 24),  self.FormatList)
        self.Bind(wx.EVT_CHOICE, self.OnSelectFormat, self.chFormatChoice)
        self.chFormatChoice.SetSelection(0)

        #self.btnSelectSets = wx.Button(p, -1, "Select Sets...", (340, 184), (144, 22))
        #self.Bind(wx.EVT_CHOICE, self.OnSelectSets, self.btnSelectSets)
        #self.btnSelectSets.Enable(0)
        
        self.sets = {}
        self.setcovers = {}
        l = 32
        t = 224
        for set in arrExpansionList:
            txt = wx.StaticText(p, -1, set, (l,t), (16,16), wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE )
            txt.Bind(wx.EVT_LEFT_DCLICK, self.OnSetDClick)
            self.setcovers[set] = txt
            self.sets[set] = wx.StaticText(p, -1, set, (l,t), (16,16), wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE )
            l = l + 24
            if l > 492:
                l = 32
                t = t + 24
        l = 32
        t = t + 24
        for set in arrBaseList:
            txt = wx.StaticText(p, -1, set, (l,t), (16,16), wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE )
            txt.Bind(wx.EVT_LEFT_DCLICK, self.OnSetDClick)
            self.setcovers[set] = txt
            self.sets[set] = wx.StaticText(p, -1, set, (l,t), (16,16), wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE )
            l = l + 24
        
        l = l + 18
        for set in arrSpecialList:
            txt = wx.StaticText(p, -1, set, (l,t), (16,16), wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE )
            txt.Bind(wx.EVT_LEFT_DCLICK, self.OnSetDClick)
            self.setcovers[set] = txt
            self.sets[set] = wx.StaticText(p, -1, set, (l,t), (20,16), wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE )
            l = l + 28

        self.cbShowAll = wx.CheckBox(p, -1, "Show All Versions", (360, 184))
        #self.cbShowAll = wx.CheckBox(p, -1, "Show All Versions", (360, 272))
        self.Bind(wx.EVT_CHECKBOX, self.OnVisTainted, self.cbShowAll)


    def InitCardLists(self, p):
        
        #self.txtCardSearch = wx.TextCtrl(p, -1, "", (16, 328), (208, 21))
         
        #self.Bind(wx.EVT_TEXT, self.OnTextEntry, self.txtCardSearch)
        
        self.lvCardList = wx.ListView(p, -1, (16, 324), (208, 220), 
            wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.VSCROLL | wx.LC_NO_HEADER )
        self.lvCardList.InsertColumn(0, "Name:", width=152)
        self.lvCardList.InsertColumn(1, "Set:", width=32)
        
        #self.lvCardList.Bind(wx.EVT_SET_FOCUS, self.OnCardListFocus)
        #self.lvCardList.Bind(wx.EVT_CHAR, self.OnCardListChar)
        #self.lvCardList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelCardList)
        
        self.btnAddCard = wx.Button(p, -1, "Add Card", (230, 380))
        self.btnAddCard.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.OnAddCard, self.btnAddCard)
        
        self.btnDelCard = wx.Button(p, -1, "Delete Card", (230, 420))
        self.Bind(wx.EVT_BUTTON, self.OnDelCard, self.btnDelCard)
        
        #self.lbInvList = wx.ListBox(p, -1, (312, 356), (208, 180))
        self.lvInvList = wx.ListView(p, -1, (312, 324), (208, 220), wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.VSCROLL | wx.LC_NO_HEADER)
        self.lvInvList.InsertColumn(0, "Name:", width=130)
        self.lvInvList.InsertColumn(1, "Set:", width=32)
        self.lvInvList.InsertColumn(2, "#:", width=24)
        
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelInvList, self.lvInvList)
        
        self.OnVisTainted(None)

        
    def InitFileData(self):
        # Map from card name to oracle parts [8 of them] and then sets.
        self.CardDict = ParseOracle.parse(fileOracleText)

        # Array of cards' (name, set, rarity)
        self.CardList = []

        cardfile = open(fileCardSetList)
        for line in cardfile.readlines():
            line = line.strip()
            parts = line.split('|')

            sets = []
            for set in parts[1:]:
                s,r = set.split('-')
                sets.append(s)
                self.CardList.append((parts[0], s, r))
            
            name = CanonizeName(parts[0])
            if len(self.CardDict[name]) < 9:
                self.CardDict[name].append(sets)


        # List of format strings
        self.FormatList = []

        # Map from format strings to list of sets
        self.Formats = {}

        formatfile = open(fileFormats)
        for line in formatfile.readlines():
            line = line.strip()
            parts = line.split('|')
            self.FormatList.append(parts[0])    #keep in-order name list
            self.Formats[parts[0]] = parts[1:]
        self.FormatList.append(CUSTOM_STR)
        self.Formats[CUSTOM_STR] = []

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
        #self.sb.SetStatusText("Left!", 1)
        #self.sb.SetStatusText("Right!", 3)
        self.UpdateNumShown()
        self.SetStatusBar(self.sb)
        
    #Event handlers

    def OnSetDClick(self, event):
        
        #print "Double click!"
        #self.visibilitytainted = 1

        #change set indicator
        set = event.GetEventObject().GetLabel()
        self.sets[set].Enable(not self.sets[set].IsEnabled())
        
        custom = [k for k in self.sets.keys() if self.sets[k].IsEnabled()]
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
        set = self.lvInvList.GetItem(invindex,1).GetText()
        
        for i in range(self.lvCardList.GetItemCount()):
            i_name = self.lvCardList.GetItemText(i)
            i_set = self.lvCardList.GetItem(i,1).GetText()
            
            if i_name == cardname and i_set == set:    
                self.lvCardList.Select(i)
                return
        else:
            sys.stderr.write("ERR: Failed to find matching card in card list\n")
        #i = self.lvInvList.GetNextItem(i, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
        
        
    def OnSelectFormat(self, event):
        
        format = event.GetString()

        for set in self.sets.keys():
            self.sets[set].Enable(0)
            
        for set in self.Formats[format]:
            if self.sets.has_key(set):
                self.sets[set].Enable(1)
            else:
                #print "Couldn't find set:", set
                pass
        self.OnVisTainted(None)

    def OnTestMatch(self, event):
        cardname, set = self.GetSelectedCard()
        
        print "Testing criteria match for:", cardname, "["+set+"]"

        self.RefreshMatchCriteria()
        print self.MatchSearchCriteria(cardname)
        return
        
    def OnAddCard(self, event):

        cardname, set = self.GetSelectedCard()

        key = self.FormKey(cardname,set)

        if self.inventory.has_key(key):
            self.inventory[key] += 1
        else:
            self.inventory[key] = 1
        
        count = self.lvInvList.GetItemCount()
        
        i = 0
        while i < count:
            i_name = self.lvInvList.GetItemText(i)
            i_set = self.lvInvList.GetItem(i,1).GetText()
            
            if i_name == cardname and i_set == set:    
                self.lvInvList.SetStringItem(i, 2, `self.inventory[key]`)
                break
            if (i_name > cardname):
                self.lvInvList.InsertStringItem(i, cardname)
                self.lvInvList.SetStringItem(i, 1, set)
                self.lvInvList.SetStringItem(i, 2, `self.inventory[key]`)
                break
            i += 1
        else:
            self.lvInvList.InsertStringItem(i, cardname)
            self.lvInvList.SetStringItem(i, 1, set)
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
        set = self.lvInvList.GetItem(i, 1).GetText()
        
        key = self.FormKey(cardname,set)

        if not self.inventory.has_key(key):
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
        self.current_file_path, self.current_file_name = os.path.split(path)
        
        #print "Loading from:", path
        file = open(path, 'r')
        line = ""
        try:
            for line in file.readlines():
                key, quantity = line.strip().split('|')
                quantity = int(quantity)
                if quantity <= 0:
                    sys.stderr.write("Invalid quantity for",key)
                    continue

                cut1 = key.find(' [')
                cut2 = key.find(']')
                if cut1 >= 0: 
                    key = key[:cut1] + key[cut2+1:]
                
                if not inven.has_key(key):
                    inven[key] = 0
                inven[key] += quantity
        
        except TypeError:
            dlg = wx.MessageDialog(self, "There was a problem reading the "
                                        "inventory file.  See line:\n"+line,
                                        "Error Reading File",
                                        wx.OK)
            dlg.ShowModal()
            return
        #print "Successfully loaded."
        self.inventory = inven
        self.dirtyinventory = 0
        self.UpdateTitle()
        self.RefreshInvList()

    def CheckSaveChanges(self):
        if not self.dirtyinventory:
            return 0
        
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
            return 0
        elif result == wx.ID_NO:
            return 0
        elif result == wx.ID_CANCEL:
            return 1

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
        #print "Saving to:", path
        file = open(fname, 'w')
        keys = self.inventory.keys()
        keys.sort()
        for k in keys:
            file.write(k+"|"+`self.inventory[k]`+"\n")
        file.close()
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


#    def UpdatePrices(self, evt):
#        if self.isGettingPrices:
#            dlg = wx.MessageDialog(self, "The program is already working on"
#                                        " getting prices."
#                                        "Already Started",
#                                        wx.OK)
#            dlg.ShowModal()
#            return
#        
#        thread.start_new(self.ThGetPrices, ())
#        

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

#    def ThGetPrices(self):
#        self.isGettingPrices = 1
#        info_array = ParseFMC.ParseFMC() #TODO uncomment this
#        #info_array = self.tmp_parse_fmc_from_file()
#        sys.stderr.write("DONE\n")
#        newprices = {}
#        for [name, set, rarity, price] in info_array:
#
#
#            #fix name
#            name = name.replace("Aether", "AEther")
#            name = name.replace("Aerathi", "AErathi")
#            parts = name.split("/")
#            if len(parts) > 1:
#                #split card
#                i = parts[1].find(" (")
#                name = parts[0] + " // " + parts[1][:i]
#             
#            i = name.find(" (")
#            if i >= 0:
#                for j in ['1','2','3','4','a','b']:
#                    i = name.find(" ("+j+")")
#                    if i >= 0:
#                        #version j
#                        name = name[:i]
#                else:
#                    i = name.find(" (Prerelease")
#                    if i >= 0:
#                        name = name[:i]
#                        set = "Pre"
#                    else:
#                        i = name.find(" (DCI")
#                        if i >= 0:
#                            name = name[:i]
#                    
#
#            name = name[:40]
#                
#            #fix set
#            if fmc_setconv.has_key(set): set = fmc_setconv[set]
#
#            key = self.FormKey(name, set).lower()
#            if len(price):
#                newprices[key] = price
#            
#        self.prices = newprices
#
#        pricefile = open(filePrices, 'w')
#        keys = self.prices.keys()
#        keys.sort()
#        for k in keys:
#            #p = round(self.prices[k], 2)
#            pricefile.write(k + "|" + self.prices[k] + "\n")
#        #write out prices to file
#        self.isGettingPrices = 0
#        
    def GetValue(self, evt):

        if self.isUpdatingLists:
            print "Can't get value when visibility lists are being updated."
            return
        if self.isGettingPrices:
            print "Can't get value when prices are being downloaded."
            return

        class NoPriceError(Exception):
            pass
        
        total = 0
        num_err = 0
        for k in self.inventory.keys():
            if self.visiblecards[k]:
                q = self.inventory[k]
                try:
                #if not self.prices.has_key(k):
                    #sys.stderr.write("ERR: no price for card '"+k+"'\n")
                    #num_err += 1
                    #continue
                #p = self.prices[k]
                    p = float(self.GetCardValue(k))
                except:
                    #sys.stderr.write("ERR: no price for card '"+k+"'\n")
                    num_err += 1
                    continue
                total += q * p

        print "Total price: $%2.2d" % round(total, 5)
        print num_err, "cards unaccounted for."
        
        #loop through inventory, and add to total if in visiblecards
        pass
    
    def GetCardValue(self, k):
        n,s = self.SepKey(k)
        k = self.FormKey(n[:40],s).lower()
        if not self.prices.has_key(k):
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
                n,s = self.SepKey(k)
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

        self.isUpdatingLists = 1
        self.SetLeftStatus("Updating card list...")
        self.SetRightStatus("Updating...")
    
        self.visibilitytainted = 0

        #print "Thr. Refreshing visibility list!"
        setdict = self.GetAllowedSets()

        cards = {}
        self.visiblecards = {}

        i = 0
        j = 0
        k = 0
        self.current_card = 0
        self.num_cards_shown = 0
        self.num_cards_total = 0
        self.lvCardList.DeleteAllItems()
        self.lvInvList.DeleteAllItems()
        count = len(self.CardList)

        #print "Beginning refresh loop"
        while i < count:
            try:
                if self.visibilitytainted: 
                    #print "Throwing exception"
                    raise ResetError
                
                (n,s,r) = self.CardList[i]
                
                key = self.FormKey(n,s)
                
                if self.inventory.has_key(key):
                    self.num_cards_total += self.inventory[key]
                
                if not cards.has_key(n):
                    cards[n] = self.MatchSearchCriteria(n)
                if (cards[n] and self.rarities[r] and (self.showAllVersions 
                        or (setdict.has_key(s) and setdict[s]))):
                    self.visiblecards[key] = 1
                    self.lvCardList.InsertStringItem(j, n)
                    self.lvCardList.SetStringItem(j, 1, s)
                    j += 1
                    if self.inventory.has_key(key) and self.inventory[key]:
                        self.lvInvList.InsertStringItem(k, n)
                        self.lvInvList.SetStringItem(k, 1, s)
                        self.lvInvList.SetStringItem(k,2, `self.inventory[key]`)
                        k += 1
                        self.num_cards_shown += self.inventory[key]
                else:
                    self.visiblecards[self.FormKey(n,s)] = 0
                    pass
                i += 1
            except ResetError:
                #print "Exception caught: resetting loop"
                setdict = self.GetAllowedSets()
                self.visibilitytainted = 0
                cards = {}
                self.visiblecards = {}
                i = 0
                j = 0
                k = 0
                self.current_card = 0
                self.num_cards_shown = 0
                self.num_cards_total = 0
                self.lvCardList.DeleteAllItems()
                self.lvInvList.DeleteAllItems()
            except IndexError:
                print "Index error, i =", i, "; count =", count
                raise
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


    def FormKey(self, name, set):
        return name+'-'+set

    def SepKey(self, key):
        i = key.rfind('-')
        return key[:i], key[i+1:]

    def GetAllowedSets(self):
        return dict([(k,self.sets[k].IsEnabled()) for k in self.sets.keys()])
        #return dict([(k,1) for k in self.sets.keys() if self.sets[k].IsEnabled()])
    def MatchSearchCriteria(self, name):

        #fix names for [Version 2], etc
        cut = name.find(' [')
        if cut >= 0: name = name[:cut]
        
        _, cc, super, type, sub, p, t, text, sets = self.CardDict[name]

        #color
        c = ""
        for color in ['W','U','B','R','G']:
            if cc.find(color) >= 0:
                c += color
        
        if len(c) == 0 and not self.colors['Colorless']: return 0
        if len(c) > 1 and not self.colors['Multi']: return 0
        if len(c) == 1 and not self.colors[c]: return 0

        #type

        c = 0
        for t in cardTypes:
            if t == "Enchant" and self.types[t] and type.find("Enchant ") >= 0:
                c += 1
            elif (type.find(t) >= 0 and self.types[t] 
                and type.find("Enchant "+t) < 0):
                c += 1
        if c == 0: return 0

        #check list of card's sets, see if this card matches any of them
        for s in sets:
            if self.allowedsets[s]:
                return 1
        
        return 0

    def RefreshMatchCriteria(self):
        self.colors = dict(
            [(k,self.cbColor[k].GetValue()) for k in self.cbColor.keys()])
        self.types = dict( 
            [(k,self.cbType[k].GetValue()) for k in self.cbType.keys()])
        self.rarities = dict( 
            [(k,self.cbRarity[k].GetValue()) for k in self.cbRarity.keys()])
        self.allowedsets = dict(
            [(k,self.sets[k].IsEnabled()) for k in self.sets.keys()])
        self.showAllVersions = self.cbShowAll.GetValue()

    def GetSelectedCard(self):
        i = self.lvCardList.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
        if i == -1: 
            sys.stderr.write("ERR: No item in card list selected\n")
            raise Exception
        
        #cardname = self.lvCardList.GetItemText(self.current_card)
        cardname = self.lvCardList.GetItemText(i)
        set = self.lvCardList.GetItem(i, 1).GetText()
        
        #print "Card found:", cardname, '['+set+']'
        
        return (cardname, set)


def SetFontBold(control):
    font = control.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    control.SetFont(font)
        
def CanonizeName(name):
    cut = name.find(' [')
    if cut >= 0: name = name[:cut]
    return name
            
