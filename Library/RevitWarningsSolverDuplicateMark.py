'''
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Duplicate mark warnings solver class.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

'''
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

import RevitCommonAPI as com
import Result as res


# import Autodesk
import Autodesk.Revit.DB as rdb

class RevitWarningsSolverDuplicateMark:

    def __init__(self, filterFunc, filterValues = []):
        '''
        Constructor: this solver takes two arguments: a filter function and a list of values to filter by

        :param filterFunc: A function to filter elements in warnings by
        :type filterFunc: func(document, elementId, list of filter values)
        :param filterValues: A list of filter values, defaults to []
        :type filterValues: list, optional
        '''

        self.filter = filterFunc
        self.filterValues = filterValues
        self.filterName = 'Duplicate mark value.'

    # --------------------------- duplicate mark guid ---------------------------
    #: guid identifying this specific warning
    GUID = '6e1efefe-c8e0-483d-8482-150b9f1da21a'
    
    def SolveWarnings(self, doc, warnings):
        '''
        Solver setting element mark to nothing, provided it passes the filter.

        :param doc: Current Revit model document.
        :type doc: Autodesk.Revit.DB.Document
        :param warnings: List of warnings to be solved.
        :type warnings: Autodesk.Revit.DB.FailureMessage

        :return: 
            Result class instance.
            
            - .result = True if all duplicate mark warnings could be solved. Otherwise False.
            - .message will contain stats in format parameter value set to ''
        
        :rtype: :class:`.Result`
        '''

        returnvalue = res.Result()
        if(len(warnings) > 0):
            for warning in warnings:
                elementIds = warning.GetFailingElements()
                for elid in elementIds:
                    element = doc.GetElement(elid)
                    # check whether element passes filter
                    if(self.filter(doc, elid, self.filterValues)):
                        try:
                            pValue = com.GetBuiltInParameterValue(element, rdb.BuiltInParameter.ALL_MODEL_MARK)
                            if (pValue != None):
                                result = com.SetBuiltInParameterValue(doc, element, rdb.BuiltInParameter.ALL_MODEL_MARK, '')
                                returnvalue.Update(result)
                        except Exception as e:
                            returnvalue.UpdateSep(False, 'Failed to solve warning duplicate mark with exception: ' + str(e))
                    else:
                        returnvalue.UpdateSep(True,'Element removed by filter:' + self.filterName + ' : ' + rdb.Element.Name.GetValue(element))
        else:
            returnvalue.UpdateSep(True,'No warnings of type: duplicate mark in model.')
        return returnvalue