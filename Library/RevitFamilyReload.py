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

import clr
import System

clr.AddReference('System.Core')
clr.ImportExtensions(System.Linq)
clr.AddReference('System')
from System.Collections.Generic import List


# import common library
import RevitCommonAPI as com
import Utility as util
import Result as res
import RevitFamilyUtils as rFamUtil
import RevitFamilyLoadOption as famLoadOpt
from RevitFamilyLoadOption import *

from Autodesk.Revit.DB import *

# --------------------------------------------------- Family Loading / inserting -----------------------------------------

def ReloadAllFamilies(doc, output, libraryLocation, includeSubFolders):
    """reloads a number of families with settings:
    - parameter values overwritten: true"""
    result = res.Result()
    # if a family is reloaded it may bring in new typs not present in the model at reload
    # this list contains the ids of those types (symbols)
    # so they can be deleted if so desired
    symbolIdsToBeDeleted = []   
    try:
        # build library
        library = util.FilesAsDictionary(libraryLocation,'','','.rfa',includeSubFolders)
        if(len(library) == 0):
            output('Library is empty!')
            # get out...
            raise UserWarning('Empty Library')
        else:
            output('Found ' + str(len(library)) + ' families in Library!')
        # get all families in file:
        familyIds = getFamilyIdsFromSymbols(doc)
        if(len(familyIds) > 0):
            output('Found ' + str(len(familyIds)) + ' loadable families in file.')
            for famId in familyIds:
                fam = doc.GetElement(famId)
                famName = Element.Name.GetValue(fam)
                if(famName in library):
                    output('Found match for: ' + famName)
                    if(len(library[famName]) == 1 ):
                        # found single match for family by name
                        output('Match: ' + library[famName][0])
                        # get all symbols attached to this family by name
                        priorLoadSymbolIds = fam.GetFamilySymbolIds()
                        # reload family
                        resultLoad = res.Result()
                        resultLoad = rFamUtil.LoadFamily(doc, library[famName][0])
                        # remove symbols (family types) added through reload process
                        afterLoadSymbolIds = fam.GetFamilySymbolIds()
                        newSymbolIds = getNewSymboldIds(priorLoadSymbolIds, afterLoadSymbolIds)
                        if(len(newSymbolIds) > 0):
                            symbolIdsToBeDeleted = symbolIdsToBeDeleted + newSymbolIds
                    else:
                        matchesMessage = ''
                        for path in library[famName]:
                            matchesMessage = matchesMessage + '...' + path + '\n'
                        matchesMessage = 'Found multiple matches for ' + famName + '\n' + matchesMessage
                        matchesMessage = matchesMessage.strip()
                        # found mutliple matches for family by name only...aborting reload
                        output(matchesMessage)
                        result.UpdateSep(False,matchesMessage)
                else:
                    output('Found no match for: ' + famName)
                    result.UpdateSep(False,'Found no match for ' + famName)
            # delete any new symbols introduced during the reload
            if(len(symbolIdsToBeDeleted)>0):
                resultDelete = com.DeleteByElementIds(doc, symbolIdsToBeDeleted, 'Delete new family types', 'Family types')
                result.Update(resultDelete)
            else:
                message = 'No need to delete any new family typese since no new types where created.'
                output(message)
                result.UpdateSep(True, message)
        else:
            message = 'Found no loadable families in file!'
            output(message)
            result.UpdateSep(True, message)
    except Exception as e:
        message = 'Failed to load families with exception: '+ str(e)
        output (message)
        result.UpdateSep(False, message)
    return result

# doc       current document
def getFamilyIdsFromSymbols(doc):
    ''' get all loadable family ids in file'''
    familyIds = []
    # build list of all categories we want families to be reloaded of
    famCats = List[BuiltInCategory] (rFamUtil.catsLoadableTags)
    famCats.AddRange(rFamUtil.catsLoadableTagsOther) 
    famCats.AddRange(rFamUtil.catsLoadableThreeD)
    famCats.AddRange(rFamUtil.catsLoadableThreeDOther)
    # get all symbols in file
    famSymbols = rFamUtil.GetFamilySymbols(doc, famCats)
    # get families from symbols and filter out in place families
    for famSymbol in famSymbols:
        if (famSymbol.Family.Id not in familyIds and famSymbol.Family.IsInPlace == False):
            familyIds.append(famSymbol.Family.Id)
    return familyIds

# preLoadSymbolIdList      list of Ids of symbols prior the reload
# afterLoadSymbolList       list of ids of symbols after the reload
def getNewSymboldIds(preLoadSymbolIdList, afterLoadSymbolList):
    """returns a list of symbol ids not present prior to reload"""
    ids = []
    for id in afterLoadSymbolList:
        if (id not in preLoadSymbolIdList):
            ids.append(id)
    return ids