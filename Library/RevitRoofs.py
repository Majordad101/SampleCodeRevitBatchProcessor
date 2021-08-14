﻿#
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

import RevitCommonAPI as com
import Result as res
import RevitFamilyUtils as rFam
import Utility as util

# import Autodesk
from Autodesk.Revit.DB import *

clr.ImportExtensions(System.Linq)

# -------------------------------------------- common variables --------------------
# header used in reports
REPORT_ROOFS_HEADER = ['HOSTFILE', 'ROOFTYPEID', 'ROOFTYPENAME']

BASIC_ROOF_FAMILY_NAME = 'Basic Roof'
SLOPED_GLAZING_FAMILY_NAME = 'Sloped Glazing'

BUILTIN_ROOF_TYPE_FAMILY_NAMES = [
    BASIC_ROOF_FAMILY_NAME,
    SLOPED_GLAZING_FAMILY_NAME
]

# --------------------------------------------- utility functions ------------------

# returns all wall types in a model
# doc:   current model document
def GetAllRoofTypesByCategory(doc):
    """ this will return a filtered element collector of all Roof types in the model:
    - Basic Roof
    - In place families or loaded families
    - sloped glazing
    """
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Roofs).WhereElementIsElementType()
    return collector

# doc   current model document
def GetRoofTypesByClass(doc):
    """ this will return a filtered element collector of all Roof types in the model:
    - Basic Roof
    - sloped glazing
    it will therefore not return any in place family types ..."""
    return  FilteredElementCollector(doc).OfClass(RoofType)

# collector   fltered element collector containing Roof type elments of family symbols representing in place families
# dic         dictionary containing key: wall type family name, value: list of ids
def BuildRoofTypeDictionary(collector, dic):
    """returns the dictioanry passt in with keys and or values added retrieved from collector passt in"""
    for c in collector:
        if(dic.has_key(c.FamilyName)):
            # todo : check WallKind Enum???
            if(c.Id not in dic[c.FamilyName]):
                dic[c.FamilyName].append(c.Id)
        else:
            dic[c.FamilyName] = [c.Id]
    return dic

# doc   current model document
def SortRoofTypesByFamilyName(doc):
    # get all Wall Type Elements
    wts = GetRoofTypesByClass(doc)
    # get all wall types including in place wall families
    wts_two = GetAllRoofTypesByCategory(doc)
    usedWts = {}
    usedWts = BuildRoofTypeDictionary(wts, usedWts)
    usedWts = BuildRoofTypeDictionary(wts_two, usedWts)
    return usedWts

# doc   current model document
# el    the element of which to check for dependent elements
# filter  what type of dependent elements to filter, Default is None whcih will return all dependent elements
# threshold   once there are more elements depending on element passed in then specified in threshold value it is deemed that other elements 
#             are dependent on this element (stacked walls for instance return as a minimum 2 elements: the stacked wall type and the legend component
#             available for this type
def HasDependentElements(doc, el, filter = None, threshold = 2):
    """ returns 0 for no dependent elements, 1, for other elements depned on it, -1 if an exception occured"""
    value = 0 # 0, no dependent Elements, 1, has dependent elements, -1 an exception occured
    try:
        dependentElements = el.GetDependentElements(filter)
        if(len(dependentElements)) > threshold :
            value = 1
    except Exception as e:
        value = -1
    return value

# doc             current document
# useTyep         0, no dependent elements; 1: has dependent elements
# typeIdGetter    list of type ids to be checked for dependent elements
def GetUsedUnusedTypeIds(doc, typeIdGetter, useType = 0):
    # get all types elements available
    allWallTypeIds = typeIdGetter(doc)
    ids = []
    for wallTypeId in allWallTypeIds:
        wallType = doc.GetElement(wallTypeId)
        hasDependents = HasDependentElements(doc, wallType)
        if(hasDependents == useType):
            ids.append(wallTypeId)
    return ids

# -------------------------------- none in place Roof types -------------------------------------------------------

# doc   current model document
def GetAllRoofInstancesInModelByCategory(doc):
    """ returns all Roof elements placed in model...ignores in place families"""
    return FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Roofs).WhereElementIsNotElementType()
    
# doc   current model document
def GetAllRoofInstancesInModelByClass(doc):
    """ returns all Roof elements placed in model...ignores roof soffits(???)"""
    return FilteredElementCollector(doc).OfClass(Roof).WhereElementIsNotElementType()

# doc   current model document
def GetAllRoofTypeIdsInModelByCategory(doc):
    """ returns all Roof element types available placed in model """
    ids = []
    colCat = GetAllRoofTypesByCategory(doc)
    for cCat in colCat:
        ids.append(cCat.Id)
    return ids

# doc   current model document
def GetAllRoofTypeIdsInModelByClass(doc):
    """ returns all Roof element types available placed in model """
    ids = []
    colClass = GetRoofTypesByClass(doc)
    for cClass in colClass:
        ids.append(cClass.Id)
    return ids

# doc   current document
def GetUsedRoofTypeIds(doc):
    """ returns all used in Roof type ids """
    ids = GetUsedUnusedTypeIds(doc, GetAllRoofTypeIdsInModelByCategory, 1)
    return ids

# famTypeIds        symbol(type) ids of a family
# usedTypeIds       symbol(type) ids in use in a project
def FamilyNoTypesInUse(famTypeIds,unUsedTypeIds):
    """ returns false if any symbols (types) of a family are in use in a model"""
    match = True
    for famTypeId in famTypeIds:
        if (famTypeId not in unUsedTypeIds):
            match = False
            break
    return match
 
# doc   current document
def GetUnusedNonInPlaceRoofTypeIdsToPurge(doc):
    """ returns all unused Roof type ids for:
    - Roof Soffit
    - Compound Roof
    - Basic Roof
    it will therefore not return any in place family types ..."""
    # get unused type ids
    ids = GetUsedUnusedTypeIds(doc, GetAllRoofTypeIdsInModelByClass, 0)
    # make sure there is at least on Roof type per system family left in model
    RoofTypes = SortRoofTypesByFamilyName(doc)
    for key, value in RoofTypes.items():
        if(key in BUILTIN_ROOF_TYPE_FAMILY_NAMES):
            if(FamilyNoTypesInUse(value,ids) == True):
                # remove one type of this system family from unused list
                ids.remove(value[0])
    return ids
 
# -------------------------------- In place Roof types -------------------------------------------------------

# doc   current document
def GetInPlaceRoofFamilyInstances(doc):
    """ returns all instances in place families of category wall """
    # built in parameter containing family name when filtering familyInstance elements:
    # BuiltInParameter.ELEM_FAMILY_PARAM
    # this is a faster filter in terms of performance then LINQ query refer to:
    # https://jeremytammik.github.io/tbc/a/1382_filter_shortcuts.html
    filter = ElementCategoryFilter(BuiltInCategory.OST_Roofs)
    return FilteredElementCollector(doc).OfClass(FamilyInstance).WherePasses(filter)

# doc   current document
def GetAllInPlaceRoofTypeIdsInModel(doc):
    """ returns type ids off all available in place families of category wall """
    ids = rFam.GetAllInPlaceTypeIdsInModelOfCategory(doc, BuiltInCategory.OST_Roofs)
    return ids

# doc   current document
def GetUsedInPlaceRoofTypeIds(doc):
    """ returns all used in place type ids """
    ids = GetUsedUnusedTypeIds(doc, GetAllInPlaceRoofTypeIdsInModel, 1)
    return ids

# doc   current document
def GetUnusedInPlaceRoofTypeIds(doc):
    """ returns all unused in place type ids """
    ids = GetUsedUnusedTypeIds(doc, GetAllInPlaceRoofTypeIdsInModel, 0)
    return ids

# doc   current document
def GetUnusedInPlaceRoofIdsForPurge(doc):
    """returns symbol(type) ids and family ids (when no type is in use) of in place Roof familis which can be purged"""
    ids = rFam.GetUnusedInPlaceIdsForPurge(doc, GetUnusedInPlaceRoofTypeIds)
    return ids