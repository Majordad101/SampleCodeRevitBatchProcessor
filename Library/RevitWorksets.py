#
#License:
#
#
# Revit Batch Processor Sample Code
#
# Copyright (c) 2021  Jan Christel
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

import clr
import System

# import common library modules
import RevitCommonAPI as com
import Result as res
import Utility as util

# import Autodesk
from Autodesk.Revit.DB import *

clr.ImportExtensions(System.Linq)

# -------------------------------------------- common variables --------------------
# header used in reports
REPORT_WORKSETS_HEADER = ['HOSTFILE','ID', 'NAME', 'ISVISIBLEBYDEFAULT']

# --------------------------------------------- utility functions ------------------


# returns the element id of a workset identified by its name
# returns invalid Id (-1) if no such workset exists
def GetWorksetIdByName(doc, worksetName):
    id = ElementId.InvalidElementId
    for p in FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset):
        if(p.Name == worksetName):
            id = p.Id
            break
    return id

# returns the name of the workset isnetified by Id
# return 'unknown' if no matching workset was found
def GetWorksetNameById(doc, idInteger):
    name = 'unknown'
    for p in FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset):
        if(p.Id.IntegerValue == idInteger):
            name = p.Name
            break
    return name

# gets all ids of all user defined worksets in a model
# doc:      current model document
def GetWorksetIds(doc):
    id = []
    for p in FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset):
      id.append(p.Id)
    return id

# get user defined worksets
# doc:      current model document
def GetWorksets(doc):
    worksets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToList()
    return worksets

# get user defined worksets as a collector
# doc:      current model document
def GetWorksetsFromCollector(doc):
    collector = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset)
    return collector

# this is based on a hack from the AutoDesk forum:
# https://forums.autodesk.com/t5/revit-api-forum/open-closed-worksets-in-open-document/td-p/6238121
# and an article from the building coder:
# https://thebuildingcoder.typepad.com/blog/2018/03/switch-view-or-document-by-showing-elements.html
# this method will open worksets in a model containing elements only
def OpenWorksetsWithElementsHack(doc):
    # get worksets in model
    worksetIds = GetWorksetIds(doc)
    # loop over workset and open if anythin is on them
    for wId in worksetIds:
        fworkset = ElementWorksetFilter(wId)
        elemIds = FilteredElementCollector(doc).WherePasses(fworkset).ToElementIds()
        if (len(elemIds)>0):
            # this will force Revit to open the workset containing this element
            uidoc.ShowElements(elemIds.First())

# attemps to change the worksets of elements provided through an element collector
def ModifyElementWorkset(doc, defaultWorksetName, collector, elementTypeName):
    returnvalue = res.Result()
    returnvalue.message = 'Changing ' + elementTypeName + ' workset to '+ defaultWorksetName + '\n'
    # get the ID of the default grids workset
    defaultId = GetWorksetIdByName(doc, defaultWorksetName)
    counterSuccess = 0
    counterFailure = 0
    # check if invalid id came back..workset no longer exists..
    if(defaultId != ElementId.InvalidElementId):
        # get all elements in collector and check their workset
        for p in collector:
            if (p.WorksetId != defaultId):
                # move element to new workset
                transaction = Transaction(doc, "Changing workset " + p.Name)
                trannyStatus = com.InTransaction(transaction, GetActionChangeElementWorkset(p, defaultId))
                if (trannyStatus.status == True):
                    counterSuccess += 1
                else:
                    counterFailure += 1
                returnvalue.status = returnvalue.status & trannyStatus.status
            else:
                counterSuccess += 1
                returnvalue.status = returnvalue.status & True 
    else:
        returnvalue.UpdateSep(False, 'Default workset '+ defaultWorksetName + ' does no longer exists in file!')
    returnvalue.AppendMessage('Moved ' + elementTypeName + ' to workset ' + defaultWorksetName + ' [' + str(counterSuccess) + ' :: ' + str(counterFailure) +']')
    return returnvalue

# returns the required action to change a single elements workset
def GetActionChangeElementWorkset(el, defaultId):
    def action():
        actionReturnValue = res.Result()
        try:
            wsparam = el.get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM)
            wsparam.Set(defaultId.IntegerValue)
            actionReturnValue.message = 'Changed element workset.'
        except Exception as e:
            actionReturnValue.UpdateSep(False, 'Failed with exception: ' + str(e))
        return actionReturnValue
    return action

# ------------------------------------------------------- workset reporting --------------------------------------------------------------------

# gets workset data ready for being printed to file
# doc: the current revit document
# revitFilePath: fully qualified file path of Revit file
def GetWorksetReportData(doc, revitFilePath):
    data = []
    worksets = GetWorksetsFromCollector(doc)
    for ws in worksets:
        data.append([
            revitFilePath, 
            str(ws.Id.IntegerValue), 
            util.EncodeAscii(ws.Name), 
            str(ws.IsVisibleByDefault)])
    return data