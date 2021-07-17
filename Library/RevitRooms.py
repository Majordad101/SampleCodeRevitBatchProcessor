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
REPORT_ROOMS_HEADER = ['HOSTFILE','ID', 'NAME', 'GROUP TYPE', 'NUMBER OF INSTANCES']

# --------------------------------------------- utility functions ------------------

# returns a list of rooms from the model
# doc   current document
def GetAllRooms(doc):
    return FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).ToList()

# returns a list of unplaced rooms from the model
# doc   current document
def GetUnplacedRooms(doc):
    coll = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms)
    unplaced = []
    for r in coll:
        if(r.Location == None):
            unplaced.append(r)
    return unplaced

# returns a list of not enclosed rooms from the model
# doc   current document
def GetNotEnclosedRooms(doc):
    coll = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms)
    unplaced = []
    boundaryOption = SpatialElementBoundaryOptions()
    for r in coll:
        boundarySegments = r.GetBoundarySegments(boundaryOption)
        if(r.Area == 0.0 and r.Location != None and (boundarySegments == None or len(boundarySegments)) == 0):
            unplaced.append(r)
    return unplaced

# returns a list of redundants rooms from the model
# doc   current document
def GetRedundantRooms(doc):
    coll = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms)
    unplaced = []
    boundaryOption = SpatialElementBoundaryOptions()
    for r in coll:
        boundarySegments = r.GetBoundarySegments(boundaryOption)
        if(r.Area == 0.0 and(boundarySegments != None and len(boundarySegments) > 0)):
            unplaced.append(r)
    return unplaced