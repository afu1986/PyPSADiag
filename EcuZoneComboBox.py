"""
   EcuZoneComboBox.py

   Copyright (C) 2024 - 2025 Marc Postema (mpostema09 -at- gmail.com)

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License
   as published by the Free Software Foundation; either version 2
   of the License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
   Or, point your browser to http://www.gnu.org/copyleft/gpl.html
"""

from PySide6.QtWidgets import QComboBox


class EcuZoneComboBox(QComboBox):
    """
    """
    value = 0
    zoneObject = dict
    def __init__(self, parent, zoneObject: dict):
        super(EcuZoneComboBox, self).__init__(parent)
        self.setStyleSheet("combobox-popup: 3;")
        self.zoneObject = zoneObject
        # Fill Combo Box
        for paramObject in self.zoneObject["params"]:
            if "mask" in paramObject:
                self.addItem(paramObject["name"], int(paramObject["mask"], 2))
            else:
                self.addItem(paramObject["name"], int(paramObject["value"], 16))
        self.setCurrentIndex(0)

    def getCorrespondingByte(self):
        return self.zoneObject["byte"]

    def setCurrentIndex(self, val):
        self.value = val;
        super().setCurrentIndex(val)

    def isComboBoxChanged(self):
        return self.isEnabled() and self.value != self.currentIndex()

    def getZoneAndHex(self):
        value = "None"
        if self.isComboBoxChanged():
            index = self.currentIndex()
            value = "%0.2X" % self.itemData(index)
        return value

    def update(self, byte: str):
        index = self.currentIndex()
        mask = int(self.zoneObject["mask"], 2)
        value = (int(byte, 16) & ~mask) | self.itemData(index)
        byte = "%0.2X" % value
        return byte

    def changeZoneOption(self, data: str, valueType: str):
        byte = int(data, 16)
        if "mask" in self.zoneObject:
            byteData = []
            for i in range(0, len(data), 2):
                byteData.append(data[i:i + 2])

            byteNr = self.zoneObject["byte"]
            mask = int(self.zoneObject["mask"], 2)
            byte = int(byteData[byteNr], 16) & mask

        for i in range(self.count()):
            if self.itemData(i) == byte:
                self.setCurrentIndex(i)
                break
