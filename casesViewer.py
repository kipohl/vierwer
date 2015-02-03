import viewerUtilities
import qt
import argparse
import CompareVolumes
import liteViewer
import glob

liteViewer.Exit_On_Error_Flag=False

class MultiCaseWidget:
  def __init__(self,preFileList,cases,postFileList):
    self.preList=preFileList
    self.caseList=cases 
    self.postList=postFileList
    self.activeCase=""
    self.ctrlWin="" 
  
  def setup(self,orientation):
    if self.ctrlWin:
       return 

    self.cpWidget=viewerUtilities.CtrlPanelWidget(None,None,None,None,None,None,None,None,orientation)
    self.loadNextCase()
    if not self.activeCase :
      liteViewer.errorPrint(0,"Nothing to do!")
      exit()
      return       
 
    self.cvLogic=CompareVolumes.CompareVolumesLogic()
    sliceNodeList = self.cvLogic.viewerPerVolume(volumeNodes=self.cpWidget.nodeList[0],background=self.cpWidget.nodeList[1],label=self.cpWidget.nodeList[2],orientation=orientation)
    self.cpWidget.sliceNodeList = sliceNodeList

    self.ctrlWin = self.cpWidget.setup(self.activeCase,"")

    # Add Next button to CTRL Panel  
    self.nextButton = qt.QPushButton("Next")
    self.nextButton.toolTip = "Next Case"
    self.nextButton.name = "next case" 
    self.cpWidget.buttonPanel.layout().addWidget(self.nextButton,0,1)
    self.nextButton.connect('clicked()', self.showNext)

    self.ctrlWin.show()

  def loadNextCase(self):
    
    while len(self.caseList):
      self.activeCase=self.caseList.pop(0)
      # Load Volumes of first case
      nodeList = [] 
      nodeImgList  = [] 
      missingList = []
      for vType in xrange(3):
        fileList = []
        if len(postList[vType]):  
          for BASE,FILE in zip(preList,postList[vType]) :
            fullFile=BASE + self.activeCase + FILE
            fullFileList = glob.glob(fullFile)
            if fullFileList :
               fileList.append(sorted(fullFileList))
            else: 
               fileList.append(fullFile)

        (nodes,images,missing) = viewerUtilities.loadVolumes(fileList,vType > 1,fourDFlag)

        if len(missing) :
           missingList.extend(missing)
        else :
          nodeList.append(nodes)
          nodeImgList.append(images)
     
      if len(missingList):
         liteViewer.errorPrint(1,"Going to next case as the following files could not be loaded for %s: %s" % (self.activeCase, missingList )) 
         self.activeCase = None

      else:
        self.cpWidget.setNodeListsAndDisplay(nodeList,nodeImgList,1)   
        if self.cpWidget.ctrlWidget:
          self.cpWidget.ctrlWidget.setWindowTitle(self.activeCase) 
        break

  def showNext(self):
    # Load Next 
    self.loadNextCase()

    if len(caseList) == 0:
      self.nextButton.enabled = False

# =======================
#  Main 
# =======================

# first entry is slite.py

parser = argparse.ArgumentParser( description="A 3D viewer of a single or multiple MRs as defined by <base><case><fg/bg/lm file>" )
parser.add_argument( "-d", "--basePrefix", nargs='+',required=True, help="Base of file name.", action="append")
parser.add_argument( "-c", "--cases", nargs='+', required=True, help="List of cases to view sequentially.", action="append" )
parser.add_argument( "-f", "--fgPostfix",  nargs='+', required=True, help="File names of images shown in foreground .", action="append")
parser.add_argument( "-b", "--bgPostfix",  nargs='*', required=False, help="File names of images shown in background.", action="append")
parser.add_argument( "-l", "--lmPostfix",  nargs='*', required=False, help="File name of Label maps", action="append")
parser.add_argument( "-4", "--fourD", required=False, help="Load in 4D image sequence.", action="store_true", default = False )
parser.add_argument( "-o", "--orientation", required=False, help="View orientation (Axial, Sagittal, Coronal)", action="store", default = "Axial")

args = parser.parse_args()
fourDFlag=args.fourD

# remove other viewers
layoutManager = slicer.app.layoutManager()
for node in slicer.util.getNodes('vtkMRMLSliceNode*').values():
     slicer.mrmlScene.RemoveNode(node)

#
# Load Volume 
#

# Create Lists
caseList=[item for sublist in args.cases for item in sublist]
postList= []
postList.append([item for sublist in args.fgPostfix for item in sublist])

preList=[item for sublist in args.basePrefix for item in sublist]
# Make same length as fgList 
if len(preList) == 1 : 
  base = preList[0]
  for index in xrange(1,len(postList[0])) : 
     preList.append(base)

if args.bgPostfix:
  postList.append([item for sublist in args.bgPostfix for item in sublist])
else: 
  postList.append([])

if args.lmPostfix:
  postList.append([item for sublist in args.lmPostfix for item in sublist])
else: 
  postList.append([])


# Setup everything 
mCaseW = MultiCaseWidget(preList,caseList,postList)
mCaseW.setup(args.orientation) 

# remove viewers of main window
#layoutManager = slicer.app.layoutManager()
#print sliceNodeList
#for node in slicer.util.getNodes('vtkMRMLSliceNode*').values():
#  if node not in sliceNodeList.values(): 
#     print node.GetID() 
#     slicer.mrmlScene.RemoveNode(node)


 
# Debug stuff 
# slicer.util.saveScene('/tmp/scene.mrml')
# dir(foregroundNode) returns all functions 
# [s for s in dir(blub) if "Get" in s]

# class MarkupsInViewsSelfTestWidget:
