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

import sys, getopt, os
# to get to the root folder of this repo
# sys.path.insert(0,'../..')

# import file item class
import FileItem as fi
# import file list methods
import FileList as fl
# import UI class
import UIFileSelect as UIFs
# import settings class
import FileSelectSettings as set
# import workloader utils
import Workloader as wl
import WorkloadBucket as wlb


# main method
def main(argv):
    # get arguments
    gotArgs, settings = processArgs(argv)
    if(gotArgs):
        revitfiles = []
        # check a to serch for files is to include sub dirs
        if(settings.inclSubDirs):
            # get revit files in input dir and subdirs
            revitfiles = fl.getRevitFilesInclSubDirs(settings.inputDir, settings.revitFileExtension)
        else:
            # get revit files in input dir
            revitfiles = fl.getRevitFiles(settings.inputDir, settings.revitFileExtension)
        if(len(revitfiles) > 0):
            # lets show the window
            ui = UIFs.MyWindow(xamlFullFileName_, revitfiles, settings)
            uiResult = ui.ShowDialog()
            if(uiResult):
                # build bucket list
                buckets = wl.DistributeWorkload(settings.outputFileNum, ui.selectedFiles, fl.getFileSize)
                # write out file lists
                counter = 0
                for bucket in buckets:
                    fileName =  os.path.join(settings.outputDir, 'Tasklist_' + str(counter)+ '.txt')
                    statusWrite = fl.writeRevitTaskFile(fileName, bucket)
                    print (statusWrite.message)
                    counter += 1
                print('Finished writing out task files')
                sys.exit(0)
            else:
                # do nothing...
                print ('No files selected!')
                sys.exit(2)
        else:
            # show messagew box
            print ('No files found!')
            sys.exit(2)
    else:
        # invalid or no args provided... get out
        sys.exit(1)

# argument processor
def processArgs(argv):
    inputDirectory = ''
    outputDirectory = ''
    outputfileNumber = 1
    revitFileExtension = '.rvt'
    includeSubDirsInSearch = False
    gotArgs = False
    try:
        opts, args = getopt.getopt(argv,"hsi:o:n:e:",["subDir","inputDir=","outputDir=",'numberFiles=','filextension='])
    except getopt.GetoptError:
        print ('test.py -s -i <inputDirectory> -o <outputDirectory> -n <numberOfOutputFiles> -e <fileExtension>')
    for opt, arg in opts:
        if opt == '-h':
            print 'test.py -i <inputDirectory> -o <outputDirectory> -n <numberOfOutputFiles> -e <fileExtension>'
        elif opt in ("-s", "--subDir"):
            includeSubDirsInSearch = True
        elif opt in ("-i", "--inputDir"):
            inputDirectory = arg
            gotArgs = True
        elif opt in ("-o", "--outputDir"):
            outputDirectory = arg
            gotArgs = True
        elif opt in ("-n", "--numberFiles"):
            try:
                value = int(arg)
                outputfileNumber = value
                gotArgs = True
            except ValueError:
                print (arg + ' value is not an integer')
                gotArgs = False
        elif opt in ("-e", "--fileExtension"):
            revitFileExtension = arg
            gotArgs = True

    # check if input values are valid
    if (outputfileNumber < 0 or outputfileNumber > 100):
        gotArgs = False
        print ('The number of output files must be bigger then 0 and smaller then 100')
    if(not FileExist(inputDirectory)):
        gotArgs = False
        print ('Invalid input directory: ' + str(inputDirectory))
    if(not FileExist(outputDirectory)):
        gotArgs = False
        print ('Invalid output directory: ' + str(outputDirectory))
    if(revitFileExtension != '.rvt' and revitFileExtension != '.rfa'):
        gotArgs = False
        print ('Invalid file extension: [' + str(revitFileExtension) + '] expecting: .rvt or .rfa')

    return gotArgs, set.FileSelectionSettings(inputDirectory, includeSubDirsInSearch, outputDirectory, outputfileNumber, revitFileExtension)

# method used to determine directory this script is run from
# this is used to load xaml file
def GetFolderPathFromFile(filePath):
    try:
        value = os.path.dirname(filePath)
    except Exception:
        value = ''
    return value

# used to check whether input and output directory supplied in arguments by user do exist
def FileExist(path):
    try:
        value = os.path.exists(path)
    except Exception:
        value = False
    return value

# the directory this script lives in
currentScriptDir_ = GetFolderPathFromFile(sys.path[0])

# xaml file name
xamlfile_ = 'ui.xaml'
# xaml full path
xamlFullFileName_ =  os.path.join(currentScriptDir_, xamlfile_)

# module entry
if __name__ == "__main__":
   main(sys.argv[1:])
