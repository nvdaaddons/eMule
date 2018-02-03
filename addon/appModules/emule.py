# -*- coding: UTF-8 -*-
# eMule app module
#Copyright (C) 2012-2018 Noelia Ruiz Martínez, Alberto Buffolino
# Released under GPL 2

import appModuleHandler
import addonHandler
import eventHandler
import os
import api
import ui
import speech
import oleacc
import winUser
import windowUtils
import wx
import gui
import textInfos
import controlTypes
import NVDAObjects.IAccessible
from NVDAObjects.IAccessible import IAccessible
from NVDAObjects.IAccessible.sysListView32 import List
from ctypes import * # for c_int
from NVDAObjects.behaviors import RowWithFakeNavigation
from cursorManager import CursorManager
from NVDAObjects.window.edit import EditTextInfo

addonHandler.initTranslation()

class EmuleRowWithFakeNavigation(RowWithFakeNavigation):

	scriptCategory = unicode(addonHandler.getCodeAddon().manifest["summary"])

	def initOverlayClass(self):
		modifiers = ("control", "shift")
		for n in xrange(10):
			for modifier in modifiers:
				gesture = "kb:NVDA+{mod}+{num}".format(mod=modifier, num=n)
				self.bindGesture(gesture, "readColumn")
		self.bindGesture("kb:NVDA+shift+c", "copyColumn")

	def script_readColumn(self, gesture):
		try:
			col = int(gesture.keyName[-1])
		except AttributeError:
			col = int(gesture.mainKeyName[-1])
		if col == 0:
			col += 10
		if "shift" in gesture.modifierNames:
			col += 10
		self._moveToColumnNumber(col)
	# Translators: Message presented in input help mode.
	script_readColumn.__doc__ = _("Reads the specified column for the current list item.")

	def script_copyColumn(self, gesture):
		try:
			col = api.getNavigatorObject().columnNumber
		except NotImplementedError:
			pass
		try:
			header = self._getColumnHeader(col)
			subitem = self._getColumnContent(col)
			column = ": ".join([header, subitem])
		except:
			return
		if api.copyToClip(column):
			# Translators: Message presented when the current column of the list item is copied to clipboard.
			ui.message(_("%s copied to clipboard") % column)
	# Translators: Message presented in input help mode.
	script_copyColumn.__doc__ = _("Copies the last read column of the selected list item to clipboard.")

class FixedList(List):

	def _get__columnOrderArray(self):
		limit=super(FixedList, self).columnCount
		myCoa = (c_int *limit)()
		for n in range(0, limit):
			myCoa[n] = n
		return myCoa

class RichEditCursorManager(CursorManager):

	def makeTextInfo(self, position):
	# Fixes regression for issue 4291.
		return EditTextInfo(self,position)

class AppModule(appModuleHandler.AppModule):

	scriptCategory = unicode(addonHandler.getCodeAddon().manifest["summary"])

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if obj.role == controlTypes.ROLE_LISTITEM:
			clsList.insert(0, EmuleRowWithFakeNavigation)
		elif obj.role==controlTypes.ROLE_LIST:
			clsList.insert(0, FixedList)
		elif obj.windowClassName == "RichEdit20W":
			clsList.insert(0, RichEditCursorManager)
	def getToolBar(self):
		try:
			obj = NVDAObjects.IAccessible.getNVDAObjectFromEvent(
			windowUtils.findDescendantWindow(api.getForegroundObject().windowHandle, visible=True, controlID=16127),
			winUser.OBJID_CLIENT, 0)
		except LookupError:
			return None
		return obj

	def getWhere(self):
		toolBar = self.getToolBar()
		if toolBar is None:
			return None
		children=toolBar.children
		for child in children:
			if child.IAccessibleStates==16:
				return child

	def getName(self):
		where = self.getWhere()
		if where:
			return where.name

	def getHeader(self):
		obj=api.getFocusObject()
		if not (obj and obj.windowClassName == 'SysListView32' and obj.IAccessibleRole==oleacc.ROLE_SYSTEM_LISTITEM): return
		obj=obj.parent
		location=obj.location
		if location and (len(location)==4):
			(left,top,width,height)=location
			obj=NVDAObjects.IAccessible.getNVDAObjectFromPoint(left, top)
			return obj
		return None

	def statusBarObj(self, pos):
		statusBar = api.getStatusBar()
		if statusBar:
			return statusBar.getChild(pos).name

	def script_toolBar(self, gesture):
		obj = self.getToolBar()
		if obj is not None:
			if obj != api.getMouseObject():
				api.moveMouseToNVDAObject(obj)
				api.setMouseObject(obj)
			if not controlTypes.STATE_FOCUSED in obj.states:
				obj.setFocus()
			eventHandler.queueEvent("gainFocus", obj)
	# Translators: Message presented in input help mode
	script_toolBar.__doc__=_("Moves the system focus and mouse to the main Tool Bar.")

	def script_where(self, gesture):
		name = self.getName()
		if name is None:
			return
		ui.message("%s" % name)
	# Translators: Message presented in input help mode.
	# For instance: reads the search window, Statistics, IRC, etc.
	script_where.__doc__=_("Reports the current window.")

	def script_name(self, gesture):
		try:
			obj = NVDAObjects.IAccessible.getNVDAObjectFromEvent(
			windowUtils.findDescendantWindow(api.getForegroundObject().windowHandle, visible=True, controlID=2183),
			winUser.OBJID_CLIENT, 0)
		except LookupError:
			return
		if obj != api.getFocusObject():
			api.moveMouseToNVDAObject(obj)
			api.setMouseObject(obj)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
	# Translators: Message presented in input help mode.
	script_name.__doc__=_("Moves the system focus to the Name field of the Search window.")

	def script_searchList(self, gesture):
		where = self.getWhere()
		if not hasattr(where, "IAccessibleChildID") or where.IAccessibleChildID != 6:
			return
		try:
			obj = NVDAObjects.IAccessible.getNVDAObjectFromEvent(
			windowUtils.findDescendantWindow(api.getForegroundObject().windowHandle, controlID=2833),
			winUser.OBJID_CLIENT, 0)
		except LookupError:
			return
		if obj != api.getFocusObject():
			api.moveMouseToNVDAObject(obj)
			api.setMouseObject(obj)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
	# Translators: Message presented in input help mode.
	script_searchList.__doc__=_("Moves the system focus and mouse to the search parameters list or Edit field for each option, in the Search window.")

	def script_list(self, gesture):
		try:
			obj = NVDAObjects.IAccessible.getNVDAObjectFromEvent(
			windowUtils.findDescendantWindow(api.getForegroundObject().windowHandle, visible=True, className="SysListView32"),
			winUser.OBJID_CLIENT, 0)
		except LookupError:
			return
		if obj != api.getFocusObject():
			api.moveMouseToNVDAObject(obj)
			api.setMouseObject(obj)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
	# Translators: Message presented in input help mode.
	script_list.__doc__=_("Moves the system focus to the first list in the current window. For example the results list in the Search window, downloads in Transfer, etc.")

	def script_readOnlyEdit(self, gesture):
		where = self.getWhere()
		if hasattr(where, "IAccessibleChildID") and where.IAccessibleChildID == 9:
			cID = -1
		else:
			cID = None
		try:
			obj = NVDAObjects.IAccessible.getNVDAObjectFromEvent(
			windowUtils.findDescendantWindow(api.getForegroundObject().windowHandle, visible=True, className="RichEdit20W", controlID=cID),
			winUser.OBJID_CLIENT, 0)
		except LookupError:
			return
		if obj != api.getFocusObject():
			api.moveMouseToNVDAObject(obj)
			api.setMouseObject(obj)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
	# Translators: Message presented in input help mode.
	script_readOnlyEdit.__doc__=_("Moves the system focus to read-only edit boxes in the current window. For example the IRC received messages.")

	def script_header(self, gesture):
		obj = self.getHeader()
		if obj is None:
			return
		api.setNavigatorObject(obj)
		api.moveMouseToNVDAObject(obj)
		api.setMouseObject(obj)
		speech.speakObject(obj)
	# Translators: Message presented in input help mode.
	script_header.__doc__=_("Moves the navigator object and mouse to the current list headers.")

	def script_statusBarFirstChild(self, gesture):
		if self.statusBarObj(0) is None:
			return
		ui.message(self.statusBarObj(0))
	# Translators: Message presented in input help mode.
	script_statusBarFirstChild.__doc__=_("Reports first object of the Status Bar.")

	def script_statusBarSecondChild(self, gesture):
		if self.statusBarObj(1) is None:
			return
		ui.message(self.statusBarObj(1))
	# Translators: Message presented in input help mode.
	script_statusBarSecondChild.__doc__=_("Reports second object of the Status Bar.")

	def script_statusBarThirdChild(self, gesture):
		if self.statusBarObj(2) is None:
			return
		ui.message(self.statusBarObj(2))
	# Translators: Message presented in input help mode.
	script_statusBarThirdChild.__doc__=_("Reports third object of the Status Bar.")

	def script_statusBarForthChild(self, gesture):
		if self.statusBarObj(3) is None:
			return
		ui.message(self.statusBarObj(3))
	# Translators: Message presented in input help mode.
	script_statusBarForthChild.__doc__=_("Reports fourth object of the Status Bar.")

	__gestures = {
		"kb:control+shift+h": "toolBar",
		"kb:control+shift+t": "where",
		"kb:control+shift+n": "name",
		"kb:control+shift+p": "searchList",
		"kb:control+shift+b": "list",
		"kb:control+shift+o": "readOnlyEdit",
		"kb:control+shift+l": "header",
		"kb:control+shift+q": "statusBarFirstChild",
		"kb:control+shift+w": "statusBarSecondChild",
		"kb:control+shift+e": "statusBarThirdChild",
		"kb:control+shift+r": "statusBarForthChild",
	}
