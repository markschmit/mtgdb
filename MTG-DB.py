

import wx

from InventoryEditorFrame import *


class MyApp(wx.App):
	def OnInit(self):
		frame = InventoryEditorFrame(None, -1, "Inventory Editor")
		frame.Show(True)
		self.SetTopWindow(frame)
		return True

app = MyApp(0)
app.MainLoop()

