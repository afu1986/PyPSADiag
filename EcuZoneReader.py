"""
   EcuZoneReader.py

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

import csv
import time
import queue
from PySide6.QtCore import Qt, QThread, Signal


class EcuZoneReaderThread(QThread):
    receivedPacketSignal = Signal(list, float)
    updateTableSignal = Signal(str, str, str)
    writeQ = queue.Queue()
    ecuReadZone = str()
    zoneName = str()
    formType = str()
    zoneActive = dict()

    def __init__(self, serialPort=None):
        super(EcuZoneReaderThread, self).__init__()
        self.serialPort = serialPort
        self.isRunning = False

    def stop(self):
        self.isRunning = False

    def __readData(self):
        self.msleep(60)
        data = bytearray()
        runLoop = True
        while runLoop:
            dataLen = self.serialPort.in_waiting
            if dataLen > 1:
                subData = self.serialPort.read(dataLen)
                if len(subData):
                    data.extend(subData)
                    self.msleep(200)
            else:
                runLoop = False
        return data

    def setZonesToRead(self, ecuID, zoneList):
        if not self.serialPort.isOpen():
            self.receivedPacketSignal.emit(["Serial Port Not Open", "", "", ""], time.time())
        else:
            if self.isRunning == False:
                self.start();
            self.writeQ.put(ecuID)
            self.writeQ.put(zoneList)

    def sendReceive(self, cmd: str):
        print(cmd)
        self.serialPort.write(cmd.encode("utf-8"))
        data = self.__readData()
        if len(data) == 0:
            return "Timeout"

        i = data.find(b"\r")
        decodedData = data[:i].decode("utf-8");
        return decodedData

    def readResponse(self):
        data = self.__readData()
        if len(data) == 0:
            self.receivedPacketSignal.emit([self.ecuReadZone, "Timeout", "string", "----", self.zoneName], time.time())
            return

        i = data.find(b"\r")
        decodedData = data[:i].decode("utf-8");
        if len(decodedData) > 2:
            if decodedData[0: + 2] == "62" and len(decodedData) > 6:
                # Get only responce data
                answerZone = decodedData[2: + 6]
                if answerZone.upper() != self.ecuReadZone.upper():
                    print(answerZone + " - " + self.ecuReadZone)
                    self.receivedPacketSignal.emit(["Requesed zone different from received zone", "", "", ""], time.time())
                    return
                answer = decodedData[6:]
                answerDecorated = answer
                valType = self.zoneActive["type"]

                # Check if we can find a "Decorated" answer from Combobox
                if self.formType == "combobox":
                    for paramObject in self.zoneActive["params"]:
                        if valType == "hex":
                            if int(paramObject["value"], 16) == int(answer, 16):
                                self.answerDecorated = str(paramObject["name"])

                self.receivedPacketSignal.emit([self.ecuReadZone, answer, valType, answerDecorated, self.zoneName], time.time())
                self.updateTableSignal.emit(self.ecuReadZone, answer, valType)
            elif decodedData[0: + 2] == "7F":
                self.receivedPacketSignal.emit([self.ecuReadZone, "No Response", "string", "---", self.zoneName], time.time())
                self.updateTableSignal.emit(self.ecuReadZone, "No Response", "string")
            elif decodedData[0: + 2] == "OK":
                self.receivedPacketSignal.emit([self.ecuReadZone, "OK", "string", "---", self.zoneName], time.time())
                self.updateTableSignal.emit(self.ecuReadZone, "OK", "string")
            else:
                self.receivedPacketSignal.emit([self.ecuReadZone, "Unkown Error", "string", decodedData, self.zoneName], time.time())
                self.updateTableSignal.emit(self.ecuReadZone, "Unkown Error", "string")


    def run(self):
        self.isRunning = True
        while self.isRunning:
            if not self.writeQ.empty():
                element = self.writeQ.get()
                if isinstance(element, dict):
                    for zoneIDObject in element:
                        self.ecuReadZone = str(zoneIDObject)
                        self.zoneActive = element[str(zoneIDObject)]
                        self.zoneName = str(self.zoneActive["name"])
                        self.formType = str(self.zoneActive["form_type"])
                        # Send and receive data
                        ecuReadZoneSend = "22" + str(zoneIDObject) + "\r"
                        self.serialPort.write(ecuReadZoneSend.encode("utf-8"))
                        self.readResponse();
                else:
                    # Just empty zone names
                    self.zoneName = ""
                    self.ecuReadZone = str(element)

                    # Send and receive data
                    ecuID = str(element) + "\r";
                    self.serialPort.write(str(ecuID).encode("utf-8"))
                    self.readResponse();
            else:
                self.msleep(100)
