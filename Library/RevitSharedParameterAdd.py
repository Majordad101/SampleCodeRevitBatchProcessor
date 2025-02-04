'''
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This module contains a function to bind a shared parameter to a category.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
based on building coder article:
https://thebuildingcoder.typepad.com/blog/2012/04/adding-a-category-to-a-shared-parameter-binding.html

'''


import Autodesk.Revit.DB as rdb

# custom result class
import Result as res
# import InTransaction from common module
import RevitCommonAPI as com

def LoadSharedParameterFile(doc, path):
    '''
    Loads a shared parameter file.

    :param doc: Current Revit model document.
    :type doc: Autodesk.Revit.DB.Document
    :param path: Fully qualified file path to shared parameter text file.
    :type path: str

    :return: The opened shared parameter file.
    :rtype: Autodesk.Revit.DB.DefinitionFile
    '''

    app = doc.Application
    app.SharedParametersFilename = path
    return app.OpenSharedParameterFile()

def BindSharedParameter(doc, category, parameterName, groupName, parameterType, isVisible, isInstance, parameterGrouping, sharedParameterFilepath):
    '''
    Binds a shared parameter to a revit category.

    Refer building coder articel referenced in header


    :param doc: Current Revit model document.
    :type doc: Autodesk.Revit.DB.Document
    :param category: The built in category, to which the parameter will be bound.
    :type category: Autodesk.Revit.DB.BuiltInCatgeory
    :param parameterName: The parameter name.
    :type parameterName: str
    :param groupName: The group under which the parameter appears in shared parameter text file.
    :type groupName: str
    :param paramType: The parameter type. (Area, vs text vs... (deprecated in Revit 2022!)
    :type paramType: Autodesk.Revit.DB.ParameterType
    :param isVisible: Is parmeter visible in UI to users.
    :type isVisible: bool
    :param isInstance: True parameter is an instance parameter, otherwise type parameter.
    :type isInstance: bool
    :param parameterGrouping: Where parameter appears in properties section in UI.
    :type parameterGrouping: str
    :param sharedParameterFilepath: Fully qualified file path to shared parameter text file.
    :type sharedParameterFilepath: str

    :return: 
        Result class instance.

        - Parameter binding status returned in result.status. False if an exception occured, otherwise True.
        - result.message will contain the name of the shared parameter.
        
        On exception (handled by optimizer itself!):
        
        - result.status (bool) will be False.
        - result.message will contain exception message.
    
    :rtype: :class:`.Result`
    '''

    returnvalue = res.Result()
    try:
    
        app = doc.Application
    
        # This is needed already here to 
        # store old ones for re-inserting
        catSet = app.Create.NewCategorySet()
 
        # Loop all Binding Definitions
        # IMPORTANT NOTE: Categories.Size is ALWAYS 1 !?
        # For multiple categories, there is really one 
        # pair per each category, even though the 
        # Definitions are the same...
 
        iter = doc.ParameterBindings.ForwardIterator()
        iter.Reset()
        while iter.MoveNext():
            if(iter.Key != None):
                definition = iter.Key
                elemBind = iter.Current
                # check parameter name match
                if(parameterName == definition.Name):
                    try: 
                        cat = doc.Settings.Categories.get_Item(category)
                        if(elemBind.Categories.Contains(cat)):
                            # check parameter type
                            if(definition.ParameterType != parameterType):
                                returnvalue.status = False
                                returnvalue.message = parameterName + ': wrong paramter type: '+ str(definition.ParameterType)
                                return returnvalue
                            #check binding type
                            if(isInstance):
                                if(elemBind.GetType() != rdb.InstanceBinding):
                                    returnvalue.status = False
                                    returnvalue.message = parameterName + ': wrong binding type (looking for instance but got type)'
                                    return returnvalue
                            else:
                                if(elemBind.GetType() != rdb.TypeBinding):
                                    returnvalue.status = False
                                    returnvalue.message = parameterName + ': wrong binding type (looking for type but got instance)'
                                    return returnvalue
                    
                            # Check Visibility - cannot (not exposed)
                            # If here, everything is fine, 
                            # ie already defined correctly
                            returnvalue.message = parameterName + ': Parameter already bound to category: ' + str(cat.Name)
                            return returnvalue
                    except Exception as e:
                        print(parameterName + ' : Failed to check parameter binding' + str(e))
                    # If here, no category match, hence must 
                    # store "other" cats for re-inserting
                    else:
                        for catOld in elemBind.Categories:
                            catSet.Insert(catOld)

        # If here, there is no Binding Definition for 
        # it, so make sure Param defined and then bind it!
        defFile = LoadSharedParameterFile(doc,sharedParameterFilepath)
        defGroup = defFile.Groups.get_Item(groupName)
        if defGroup == None:
            defGroup = defFile.Groups.Create(groupName)
        if defGroup.Definitions.Contains(defGroup.Definitions.Item[parameterName]):
            definition = defGroup.Definitions.Item[parameterName]
        else:
            opt = rdb.ExternalDefinitionCreationOptions(parameterName, parameterType)
            opt.Visible = isVisible
            definition = defGroup.Definitions.Create(opt)

        #get category from builtin category
        catSet.Insert(doc.Settings.Categories.get_Item(category))

        bind = None
        if(isInstance):
            bind = app.Create.NewInstanceBinding(catSet)
        else:
            bind = app.Create.NewTypeBinding(catSet)
    
        # There is another strange API "feature". 
        # If param has EVER been bound in a project 
        # (in above iter pairs or even if not there 
        # but once deleted), Insert always fails!? 
        # Must use .ReInsert in that case.
        # See also similar findings on this topic in: 
        # http://thebuildingcoder.typepad.com/blog/2009/09/adding-a-category-to-a-parameter-binding.html 
        # - the code-idiom below may be more generic:

        def action():
            actionReturnValue = res.Result()
            try:
                if(doc.ParameterBindings.Insert(definition, bind, parameterGrouping)):
                    actionReturnValue.message =  parameterName + ' : parameter succesfully bound'
                    return actionReturnValue
                else:
                    if(doc.ParameterBindings.ReInsert(definition, bind, parameterGrouping)):
                        actionReturnValue.message = parameterName + ' : parameter succesfully bound'
                        return actionReturnValue
                    else:
                        actionReturnValue.status = False
                        actionReturnValue.message = parameterName + ' : failed to bind parameter!'
            except Exception as e:
                actionReturnValue.status = False
                actionReturnValue.message = parameterName + ' : Failed to bind parameter with exception: ' + str(e)
            return actionReturnValue
        transaction = rdb.Transaction(doc,'Binding parameter')
        returnvalue = com.InTransaction(transaction, action)    
        return returnvalue

    except Exception as e:
        returnvalue.status = False
        returnvalue.message = parameterName + ' : Failed to bind parameter with exception: ' + str(e)
    return returnvalue
