import CompareVolumes
import viewerUtilities
import argparse

# if call for help 
if len(sys.argv) > 1 and sys.argv[1] == "--help_all" : 
   sys.argv[1] = "-h"

parser = argparse.ArgumentParser( description="A 3D viewer of a single or multiple MRs" )
parser.add_argument( "--help_all", required=False, help="More in-depth help", action="store_true")
parser.add_argument( "-f", "--foreground",  nargs='+', required=True, help="File names of images shown in the foreground.", action="append")
parser.add_argument( "-b", "--background", required=False, help="File name of image shown in the background.", action="append")
parser.add_argument( "-l", "--labelmap", required=False, help="File name of a single label map")
parser.add_argument( "-4", "--fourD", required=False, help="Load in 4D image sequence.", action="store_true", default = False )
parser.add_argument( "-n", "--window_name", required=False, help="Window name", action="store", default = "Viewer")
parser.add_argument( "-o", "--orientation", required=False, help="View orientation (Axial, Sagittal, Coronal)", action="store", default = "Axial")
parser.add_argument( "-a", "--all_3_orientations", required=False, help="All three view orientations", action="store_true", default = False)


args = parser.parse_args()
fourDFlag=args.fourD
viewerUtilities.InitialSlicerSetup()

#
# Load Volume 
#
(fgNodeList,fgImageList,missingList) = viewerUtilities.loadVolumes(args.foreground,0,fourDFlag)
(bgNodeList,bgImageList,missingList) = viewerUtilities.loadVolumes(args.background,0,fourDFlag)
(lmNodeList,lmImageList,missingList) = viewerUtilities.loadVolumes(args.labelmap,1,fourDFlag)

if len(lmNodeList) : 
  lmNode=lmNodeList[0]
else :
  lmNode=None

numCols=len(fgNodeList)
if args.all_3_orientations : 
  outline=[3,numCols]
else : 
  outline=[1,numCols]


# https://github.com/pieper/CompareVolumes/blob/master/CompareVolumes.py
cvLogic=CompareVolumes.CompareVolumesLogic()
sliceNodeList = cvLogic.viewerPerVolume(volumeNodes=fgNodeList,background=None,label=lmNode,layout=outline,orientation=args.orientation)

cpWidget=viewerUtilities.CtrlPanelWidget(sliceNodeList,None,fgNodeList,fgImageList,bgNodeList,bgImageList,lmNodeList,lmImageList,args.orientation,args.all_3_orientations)
ctrlWin = cpWidget.setup(args.window_name,0,"")

# For yongs MICCAI paper 
# Both have to be 4D volumes to correctly work !
if True:
  for IND in range(len(fgNodeList)):
    dn = fgNodeList[IND].GetDisplayNode()
    dn.SetLowerThreshold(1)
    dn.ApplyThresholdOn()
    dn.SetAndObserveColorNodeID('vtkMRMLColorTableNodeFileColdToHotRainbow.txt')

ctrlWin.show()


#sWidget = slicer.qMRMLSliceWidget()
#sWidget.setMRMLScene(slicer.mrmlScene)

#layoutManager = slicer.app.layoutManager()
#viewName = fgNodeList[0].GetName() + '-Axial'
#sliceWidget = layoutManager.sliceWidget(viewName)
#sliceWidget.sliceController().setSliceLink(1)

#sliceNodes = slicer.util.getNodes('vtkMRMLSliceNode*')
#layoutManager = slicer.app.layoutManager()
#for sliceNode in sliceNodes.values():
#  sliceWidget = layoutManager.sliceWidget(sliceNode.GetLayoutName())
#  if sliceWidget:  
#      print sliceNode.GetName()
#      sliceWidget.sliceController().setSliceLink(1)

#sliceNode = sliceWidget.mrmlSliceNode()
#sliceNode.SetOrientation(orientation)

#orientations = ('Axial', 'Sagittal', 'Coronal')


# window does not come up for some reason if we do not do it that way 

#

 
# Debug stuff 
# slicer.util.saveScene('/tmp/scene.mrml')
# dir(foregroundNode) returns all functions 
# [s for s in dir(blub) if "Get" in s]

# class MarkupsInViewsSelfTestWidget:
