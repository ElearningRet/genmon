#!/usr/bin/env python
#-------------------------------------------------------------------------------
#    FILE: mysupport.py
# PURPOSE: support functions in major classes
#
#  AUTHOR: Jason G Yates
#    DATE: 21-Apr-2018
#
# MODIFICATIONS:
#-------------------------------------------------------------------------------

import os, sys, time, collections, threading, socket, json

from genmonlib import mycommon, myplatform, myconfig

#------------ MySupport class --------------------------------------------------
class MySupport(mycommon.MyCommon):
    def __init__(self, simulation = False):
        super(MySupport, self).__init__()
        self.Simulation = simulation
        self.CriticalLock = threading.Lock()        # Critical Lock (writing conf file)

    #------------ MySupport::LogToFile------------------------------------------
    def LogToFile(self, File, TimeDate, Value, Value2 = None):
        if self.Simulation:
            return
        if not len(File):
            return ""

        try:
            with open(File,"a") as LogFile:     #opens file
                if Value2 != None:
                    LogFile.write(TimeDate + "," + Value + "," + Value2 + "\n")
                else:
                    LogFile.write(TimeDate + "," + Value + "\n")
                LogFile.flush()
        except Exception as e1:
            self.LogError("Error in  LogToFile : File: %s: %s " % (File,str(e1)))

    #------------ MySupport::GetSiteName----------------------------------------
    def GetSiteName(self):
        return self.SiteName

    # ------------------------ MySupport::IsLoaded -----------------------------
    # return true if program is already loaded
    def IsLoaded(self):

        Socket = None

        try:
            #create an INET, STREAMing socket
            Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #now connect to the server on our port
            Socket.connect(("127.0.0.1", self.ServerSocketPort))
            Socket.close()
            return True
        except Exception as e1:
            if Socket != None:
                Socket.close()
            return False

    #------------ MySupport::GetPlatformStats ----------------------------------
    def GetPlatformStats(self, usemetric = None):

        PlatformInfo = collections.OrderedDict()

        if not usemetric == None:
            bMetric = usemetric
        else:
            bMetric = self.UseMetric
        Platform = myplatform.MyPlatform(self.log, bMetric)

        return Platform.GetInfo()

    #---------- MySupport::GetDeadThreadName------------------------------------
    def GetDeadThreadName(self):

        RetStr = ""
        ThreadNames = ""
        for Name, MyThreadObj in self.Threads.items():
            ThreadNames += Name + " "
            if not MyThreadObj.IsAlive():
                RetStr += MyThreadObj.Name() + " "

        if RetStr == "":
            RetStr = "All threads alive: " + ThreadNames

        return RetStr

    # ---------- MySupport::KillThread------------------------------------------
    def KillThread(self, Name, CleanupSelf = False):

        try:
            MyThreadObj = self.Threads.get(Name, None)
            if MyThreadObj == None:
                self.LogError("Error getting thread name in KillThread: " + Name)
                return False

            if not CleanupSelf:
                MyThreadObj.Stop()
                MyThreadObj.WaitForThreadToEnd()
        except Exception as e1:
            self.LogError("Error in KillThread ( " + Name  + "): " + str(e1))
            return

    #---------------------MySupport::StartAllThreads----------------------------
    def StartAllThreads(self):

        for key, ThreadInfo in self.Threads.items():
            ThreadInfo.Start()

    #---------- MySupport:: AreThreadsAlive-------------------------------------
    # ret true if all threads are alive
    def AreThreadsAlive(self):

        for Name, MyThreadObj in self.Threads.items():
            if not MyThreadObj.IsAlive():
                return False

        return True

    # ---------- MySupport::IsStopSignaled--------------------------------------
    def IsStopSignaled(self, Name):

        Thread = self.Threads.get(Name, None)
        if Thread == None:
            self.LogError("Error getting thread name in IsStopSignaled: " + Name)
            return False

        return Thread.StopSignaled()

    # ---------- MySupport::WaitForExit-----------------------------------------
    def WaitForExit(self, Name, timeout = None):

        Thread = self.Threads.get(Name, None)
        if Thread == None:
            self.LogError("Error getting thread name in WaitForExit: " + Name)
            return False

        return Thread.Wait(timeout)

    #------------ MySupport::ValueOut ------------------------------------------
    def ValueOut(self, value, unit, NoString = False):
        try:

            if NoString:
                ReturnDict = collections.OrderedDict()
                ReturnDict["unit"] = unit
                DefaultReturn = json.dumps({'value': 0}, sort_keys=False)
            else:
                DefaultReturn = ""
            if isinstance(value, int):
                if not NoString:
                    return "%d %s" % (int(value), str(unit))
                else:
                    ReturnDict["type"] = 'int'
                    ReturnDict["value"] = value
                    return json.dumps(ReturnDict, sort_keys=False)
            if isinstance(value, long):
                if not NoString:
                    return "%d %s" % (int(value), str(unit))
                else:
                    ReturnDict["type"] = 'long'
                    ReturnDict["value"] = value
                    return json.dumps(ReturnDict, sort_keys=False)
            elif isinstance(value, float):
                if not NoString:
                    return "%.2f %s" % (float(value), str(unit))
                else:
                    ReturnDict = collections.OrderedDict()
                    ReturnDict["type"] = 'float'
                    ReturnDict["value"] = round(value, 2)
                    return json.dumps(ReturnDict, sort_keys=False)
            else:
                self.LogError("Unsupported type in ValueOut: " + str(type(value)))
                return DefaultReturn
        except Exception as e1:
            self.LogErrorLine("Error in ValueOut: " + str(e1))
            return DefaultReturn

    #----------  MySupport::HexStringToString  ---------------------------------
    def HexStringToString(self, input):

        try:
            if not len(input):
                return ""
            if not self.StringIsHex(input):
                return ""
            ByteArray = bytearray.fromhex(input)
            if ByteArray[0] == 0:
                return ""
            End = ByteArray.find('\0')
            if End != -1:
                ByteArray = ByteArray[:End]
            return str(ByteArray).encode('ascii')
        except Exception as e1:
            self.LogErrorLine("Error in HexStringToString: " + str(e1))
            return ""

    #----------  MySupport::StringIsHex  ---------------------------------------
    def StringIsHex(self, input):
        try:
            if " " in input:
                return False
            int(input, 16)
            return True
        except:
            return False
    #------------ MySupport::GetDispatchItem -----------------------------------
    def GetDispatchItem(self, item):

        if isinstance(item, str):
            return item
        if isinstance(item, unicode):
            return str(item)
        elif callable(item):
            return item()
        elif isinstance(item, (int, long)):
            return str(item)
        elif isinstance(item, float):
            return str(item)
        else:
            self.LogError("Unable to convert type %s in GetDispatchItem" % str(type(item)))
            self.LogError("Item: " + str(item))
            return ""

    #------------ MySupport::ProcessDispatch -----------------------------------
    # This function is recursive, it will turn a dict with callable functions into
    # all of the callable functions resolved to stings (by calling the functions).
    # If string output is needed instead of a dict output, ProcessDispatchToString
    # is called
    def ProcessDispatch(self, node, InputBuffer, indent=0):

        if isinstance(InputBuffer, str):
            return self.ProcessDispatchToString(node, InputBuffer, indent)

        if isinstance(node, dict):
            for key, item in node.items():
                if isinstance(item, dict):
                    NewDict = collections.OrderedDict()
                    InputBuffer[key] = self.ProcessDispatch(item, NewDict)
                elif isinstance(item, list):
                    InputBuffer[key] = []
                    for listitem in item:
                        if isinstance(listitem, dict):
                            NewDict2 = collections.OrderedDict()
                            InputBuffer[key].append(self.ProcessDispatch(listitem, NewDict2))
                        else:
                            self.LogError("Invalid type in ProcessDispatch %s " % str(type(node)))
                else:
                    InputBuffer[key] = self.GetDispatchItem(item)
        else:
            self.LogError("Invalid type in ProcessDispatch %s " % str(type(node)))

        return InputBuffer

     #------------ MySupport::ProcessDispatchToString --------------------------
     # This function is recursive, it will turn a dict with callable functions into
     # a printable string with indentation and formatting
    def ProcessDispatchToString(self, node, InputBuffer, indent = 0):

        if not isinstance(InputBuffer, str):
            return ""

        if isinstance(node, dict):
            for key, item in node.items():
                if isinstance(item, dict):
                    InputBuffer += "\n" + ("    " * indent) + str(key) + " : \n"
                    InputBuffer = self.ProcessDispatchToString(item, InputBuffer, indent + 1)
                elif isinstance(item, list):
                    InputBuffer += "\n" + ("    " * indent) + str(key) + " : \n"
                    for listitem in item:
                        if isinstance(listitem, dict):
                            InputBuffer = self.ProcessDispatchToString(listitem, InputBuffer, indent + 1)
                        elif isinstance(listitem, str) or isinstance(listitem, unicode):
                            InputBuffer += (("    " * (indent +1)) +  self.GetDispatchItem(listitem) + "\n")
                        else:
                            self.LogError("Invalid type in ProcessDispatchToString %s %s (2)" % (key, str(type(listitem))))
                else:
                    InputBuffer += (("    " * indent) + str(key) + " : " +  self.GetDispatchItem(item) + "\n")
        else:
            self.LogError("Invalid type in ProcessDispatchToString %s " % str(type(node)))
        return InputBuffer

    #----------  Controller::GetNumBitsChanged----------------------------------
    def GetNumBitsChanged(self, FromValue, ToValue):

        if not len(FromValue) or not len(ToValue):
            return 0, 0
        MaskBitsChanged = int(FromValue, 16) ^ int(ToValue, 16)
        NumBitsChanged = MaskBitsChanged
        count = 0
        while (NumBitsChanged):
            count += NumBitsChanged & 1
            NumBitsChanged >>= 1

        return count, MaskBitsChanged

    #----------  MySupport::GetDeltaTimeMinutes-------------------------------
    def GetDeltaTimeMinutes(self, DeltaTime):

        days, seconds = DeltaTime.days, DeltaTime.seconds
        delta_hours = days * 24 + seconds // 3600
        delta_minutes = (seconds % 3600) // 60

        return (delta_hours * 60 + delta_minutes)
