#
#License:
#
#
# Revit Batch Processor Sample Code
#
# Copyright (c) 2020  Jan Christel
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

import datetime
import System
import clr
from System.IO import Path
from Autodesk.Revit.DB import *
import os.path as path

clr.ImportExtensions(System.Linq)

#a class used to return the value  if any, a message and the status of a method (true if everything is ok or false if something went wrong)
class Result: 
    def __init__(self): 
        self.message = '-'
        self.status = True
        self.result = None


#----------------------------------------elements-----------------------------------------------

#method deleting elements by list of element id's
# transactionName : name the transaction will be given
# elementName: will appear in description of what got deleted
def DeleteByElementIds(doc, ids, transactionName, elementName):
    returnvalue = Result()
    def action():
        actionReturnValue = Result()
        try:
            doc.Delete(ids.ToList[ElementId]())
            actionReturnValue.message = 'Deleted ' + str(len(ids)) + ' ' + elementName
        except Exception as e:
            actionReturnValue.status = False
            actionReturnValue.message = 'Failed to delete ' + elementName + ' with exception: ' + str(e)
        return actionReturnValue
    transaction = Transaction(doc,transactionName)
    returnvalue = InTransaction(transaction, action)
    return returnvalue

#attemps to change the worksets of elements provided through an element collector
def ModifyElementWorkset(doc, defaultWorksetName, collector):
    returnvalue = Result()
    returnvalue.message = 'Changing elements workset to '+ defaultWorksetName
    #get the ID of the default grids workset
    defaultId = GetWorksetIdByName(doc, defaultWorksetName)
    #check if invalid id came back..workset no longer exists..
    if(defaultId != ElementId.InvalidElementId):
        #get all grids in model and check their workset
        for p in collector:
            if (p.WorksetId != defaultId):
                #move grid to new workset
                transaction = Transaction(doc, "Changing workset " + p.Name) 
                returnvalue.status = returnvalue.status & InTransaction(transaction, GetActionChangeElementWorkset(p, defaultId)).status
                returnvalue.message = returnvalue.message +'\n' + p.Name 
            else:
                returnvalue.message = returnvalue.message = returnvalue.message + '\n' + p.Name + ' is already on default workset ' + defaultWorksetName
                returnvalue.status = returnvalue.status & True 
    else:
        returnvalue.message = 'Default workset '+ defaultWorksetName + ' does no longer exists in file!'
        returnvalue.status = False
    return returnvalue

# returns the required action to change a single elements workset
def GetActionChangeElementWorkset(el, defaultId):
    def action():
        actionReturnValue = Result()
        try:
            wsparam = el.get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM)
            wsparam.Set(defaultId.IntegerValue)
            actionReturnValue.message = 'Changed element workset.'
        except Exception as e:
            actionReturnValue.status = False
            actionReturnValue.message = 'Failed with exception: ' + str(e)
        return actionReturnValue
    return action

#----------------------------------------worksets-----------------------------------------------

#returns the element id of a workset identified by its name
#returns invalid Id (-1) if no such workset exists
def GetWorksetIdByName(doc, worksetName):
    id = ElementId.InvalidElementId
    for p in FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset):
        if(p.Name == worksetName):
            id = p.Id
            break
    return id

#-------------------------------------------LINKS------------------------------------------------

#deletes all revit links in a file
def DeleteRevitLinks(doc):
    ids = []
    returnvalue = Result()
    for p in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RvtLinks):
        ids.append(p.Id)
    #delete all links at once
    returnvalue = DeleteByElementIds(doc, ids, 'Deleting Revit links', 'Revit link(s)')
    return returnvalue

#deletes all CAD links in a file
def DeleteCADLinks(doc):
    ids = []
    returnvalue = Result()
    for p in FilteredElementCollector(doc).OfClass(ImportInstance):
        ids.append(p.Id)
    #delete all links at once
    returnvalue = DeleteByElementIds(doc, ids, 'Deleting CAD links', 'CAD link(s)')
    return returnvalue


#-------------------------------------------------------file IO --------------------------------------

#get a time stamp in format year_month_day
def GetFileDateStamp():
    d = datetime.datetime.now()
    return d.strftime('%y_%m_%d')

#returns an time stamped output file name based on the revit file name
#file extension needs to include '.', default is '.txt'
#file suffix will be appended after the name but before the file extension. Default is blank.
def GetOutPutFileName(revitFilePath, fileExtension = '.txt', fileSuffix = ''):
    #get date prefix for file name
    filePrefix = GetFileDateStamp()
    name = Path.GetFileNameWithoutExtension(revitFilePath)
    return filePrefix + '_' + name + fileSuffix + fileExtension

# returns the revit file name without the file extension
def GetRevitFileName(revitFilePath):
    name = Path.GetFileNameWithoutExtension(revitFilePath)
    return name

#removes '..\..' or '..\' from relative file path supplied by Revit and replaces it with full path derived from Revit document
def ConvertRelativePathToFullPath(relativeFilePath, fullFilePath):
    if( r'..\..' in relativeFilePath):
        two_up = path.abspath(path.join(fullFilePath ,r'..\..'))
        return two_up + relativeFilePath[5:]
    elif('..' in relativeFilePath):
        one_up = path.abspath(path.join(fullFilePath ,'..'))
        return one_up + relativeFilePath[2:]
    else:
        return relativeFilePath


#synchronises a Revit central file
#returns:
#   - true if sync without exception been thrown
#   - false if an exception occured
def SyncFile (doc):
    returnvalue = Result()
    # set up sync settings
    ro = RelinquishOptions(True)
    transActOptions = TransactWithCentralOptions()
    sync = SynchronizeWithCentralOptions()
    sync.Comment = 'Synchronised by Revit Batch Processor'
    sync.SetRelinquishOptions(ro)
    #Synch it
    try:
        #save local first ( this seems to prevent intermittend crash on sync(?))
        doc.Save()
        doc.SynchronizeWithCentral(transActOptions, sync)
        #relinquish all
        WorksharingUtils.RelinquishOwnership(doc, ro, transActOptions)
        returnvalue.message = 'Succesfully synched file.'
    except Exception as e:
        returnvalue.status = False
        returnvalue.message = 'Failed with exception: ' + str(e)
    return returnvalue

#saves a new central file to given location
def SaveAsWorksharedFile(doc, fullFileName):
    returnvalue = Result()
    try:
        workSharingSaveAsOption = WorksharingSaveAsOptions()
        workSharingSaveAsOption.OpenWorksetsDefault = SimpleWorksetConfiguration.AskUserToSpecify
        workSharingSaveAsOption.SaveAsCentral = True
        saveOption = SaveAsOptions()
        saveOption.OverwriteExistingFile = True
        saveOption.SetWorksharingOptions(workSharingSaveAsOption)
        saveOption.MaximumBackups = 5
        saveOption.Compact = True
        doc.SaveAs(fullFileName, saveOption)
        returnvalue.message = 'Succesfully saved file: '+str(fullFileName)
    except Exception as e:
        returnvalue.status = False
        returnvalue.message = 'Failed with exception: ' + str(e)
    return returnvalue

#save file under new name in given location
# targetFolderPath: directory path of where the file is to be saved
# currentFullFileName: fully qualified file name of the current Revit file
# name data: list of arrays in format[[oldname, newName]] where old name and new name are revit file names without file extension
def SaveAs(doc, targetFolderPath, currentFullFileName, nameData):
    returnvalue = Result()
    revitFileName = GetRevitFileName(currentFullFileName)
    newFileName= ''
    match = False
    for oldName, newName in nameData:
        if (revitFileName.startswith(oldName)):
            match = True
            returnvalue.message = ('Found file name match for: ' + revitFileName + ' new name: ' + newName)
            # save file under new name
            newFileName = targetFolderPath + '\\'+ newName +'.rvt'
            break
    if(match == False):
        # save under same file name
        newFileName = targetFolderPath + '\\'+ revitFileName +'.rvt'
        returnvalue.message = 'Found no file name match for: ' + currentFullFileName
    try:
        returnvalue.status = SaveAsWorksharedFile(doc, newFileName)
        returnvalue.message = returnvalue.message + '\n' + 'Saved file: ' + newFileName
    except Exception as e:
        returnvalue.status = False
        returnvalue.message = returnvalue.message + '\n' + 'Failed to save revit file to new location!' + ' exception: ' + str(e)
    return returnvalue

#enables work sharing
def EnableWorksharing(doc, worksetNameGridLevel = 'Shared Levels and Grids', worksetName = 'Workset1'):
    returnvalue = Result()
    try:
        doc.EnableWorksharing('Shared Levels and Grids','Workset1')
        returnvalue.message = 'Succesfully enabled worksharing.'
    except Exception as e:
        returnvalue.status = False
        returnvalue.message = 'Failed with exception: ' + str(e)
    return returnvalue

#--------------------------------------------Transactions-----------------------------------------

#transaction wrapper
#returns:
#   - False if something went wrong
#   - True if the action has no return value specified and no exception occured
# expects the actiooon to return a class object of type Result!!!
def InTransaction(tranny, action):
    returnvalue = Result()
    try:
        tranny.Start()
        try:
            trannyResult = action()
            tranny.Commit()
            #check what came back
            if (trannyResult!= None):
                #store false value 
                returnvalue = trannyResult
        except Exception as e:
            tranny.RollBack()
            returnvalue.status = False
            returnvalue.message = 'Failed with exception: ' + str(e)
    except Exception as e:
        returnvalue.status = False
        returnvalue.message = 'Failed with exception: ' + str(e)
    return returnvalue

#--------------------------------------------string-----------------------------------------

#encode string as ascii and replaces all non ascii characters
def EncodeAscii (string):
    return string.encode('ascii','replace')
