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
  
  def setup(self,orientation,allOrientationFlag):
    if self.ctrlWin:
       return 

    self.cpWidget=viewerUtilities.CtrlPanelWidget(None,None,None,None,None,None,None,None,orientation,allOrientationFlag,args.fg_color_table, args.fg_lower_threshold)
    self.loadNextCase()
    if not self.activeCase :
      liteViewer.errorPrint(0,"Nothing to do!")
      exit()
      return       

    numCols=len(self.cpWidget.nodeList[0])
    if args.all_3_orientations : 
       outline=[3,numCols]
    else : 
       outline=[1,numCols]

    self.cvLogic=CompareVolumes.CompareVolumesLogic()
    sliceNodeList = self.cvLogic.viewerPerVolume(volumeNodes=self.cpWidget.nodeList[0],background=None,label=None,layout=outline,orientation=orientation)
    self.cpWidget.sliceNodeList = sliceNodeList

    self.ctrlWin = self.cpWidget.setup(self.activeCase,True,"")

    # Add Next button to CTRL Panel  
    self.nextButton = qt.QPushButton("Next")
    self.nextButton.toolTip = "Next Case"
    self.nextButton.name = "next case" 
    self.cpWidget.buttonPanel.layout().addWidget(self.nextButton,0,1)
    self.nextButton.connect('clicked()', self.showNext)
    if len(self.caseList) == 0:
      self.nextButton.enabled = False

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
          for BASE,FILE in zip(preList[vType],postList[vType]) :
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

    if len(self.caseList) == 0:
      self.nextButton.enabled = False

# =======================
#  Main 
# =======================

# if call for help 
if len(sys.argv) > 1 and sys.argv[1] == "--help_all" : 
   sys.argv[1] = "-h"

parser = argparse.ArgumentParser( description="A 3D viewer of a single or multiple MRs as defined by <base><case><fg/bg/lm file>" )
parser.add_argument( "--help_all", required=False, help="More in-depth help", action="store_true")
parser.add_argument( "-d", "--basePrefix", nargs='+',required=True, help="Base of file name.", action="append")
parser.add_argument( "-s", "--cases", nargs='+', required=True, help="List of cases to view sequentially.", action="append" )
parser.add_argument( "-f", "--fgPostfix",  nargs='+', required=True, help="File names of images shown in foreground .", action="append")
parser.add_argument( "-b", "--bgPostfix",  nargs='*', required=False, help="File names of images shown in background.", action="append")
parser.add_argument( "-l", "--lmPostfix",  nargs='*', required=False, help="File name of Label maps", action="append")
parser.add_argument( "-4", "--fourD", required=False, help="Load in 4D image sequence.", action="store_true", default = False )
parser.add_argument( "-o", "--orientation", required=False, help="View orientation (Axial, Sagittal, Coronal)", action="store", default = "Axial")
parser.add_argument( "-a", "--all_3_orientations", required=False, help="All three view orientations", action="store_true", default = False)
parser.add_argument( "--fg_color_table", required=False, help="Color table for foreground (e.g. vtkMRMLColorTableNodeFileColdToHotRainbow.txt)", action="store")
parser.add_argument( "--fg_lower_threshold", required=False, help="values below will not be shown in viewer", type=float, default=float('nan'))
parser.add_argument( "--lmBasePrefix", nargs='+',required=False, help="Base of file name for label map (only define if different from -d).", action="append")

args = parser.parse_args()
fourDFlag=args.fourD

viewerUtilities.InitialSlicerSetup()

#
# Load Volume 
#

postList= []
postList.append([item for sublist in args.fgPostfix for item in sublist])

preList=[] 
fgPreList=[] 
# Make same length as fgList 
if len(args.basePrefix) == 1 : 
  base = args.basePrefix[0]
  for index in xrange(len(postList[0])) : 
     fgPreList.extend(base)
else:
  fgPreList=[item for sublist in args.basePrefix for item in sublist]

preList.append(fgPreList) 

# Create Lists
tmpCaseList=[item for sublist in args.cases for item in sublist]
caseList=[]
for CASE in tmpCaseList :
   if '*' in CASE or '?' in CASE :  
     fullCaseList = glob.glob(fgPreList[0] + CASE)
     if fullCaseList :
       for dirCase in sorted(fullCaseList):
         caseList.append(dirCase.replace(fgPreList[0],""))
   else :
       caseList.append(CASE)

if not len(caseList):
   liteViewer.errorPrint(0,"Base path seems to be incorrect - none of the cases %s exists in %s !" % (tmpCaseList,preList[0]))
   sys.exit(1) 

bgList=[] 
if args.bgPostfix:
  if len(args.bgPostfix) == 1 : 
    bg = args.bgPostfix[0]
    for index in xrange(len(postList[0])) : 
      bgList.extend(bg)

  else:
    bgList = [item for sublist in args.bgPostfix for item in sublist]

postList.append(bgList)

# currently not explicitly defined 
preList.append(fgPreList) 

lmList=[] 
if args.lmPostfix:
  if len(args.lmPostfix) == 1 : 
    lm= args.lmPostfix[0]
    for index in xrange(len(postList[0])) : 
      lmList.extend(lm)

  else:
    lmList = [item for sublist in args.lmPostfix for item in sublist]

postList.append(lmList)

if not args.lmBasePrefix or len(args.lmBasePrefix) == 0 :
  lmPreList = preList
else : 
  lmPreList=[] 
  if len(args.lmBasePrefix) == 1 : 
    base = args.lmBasePrefix[0]
    for index in xrange(len(postList[2])) : 
      lmPreList.extend(base)
  else:
    lmPreList=[item for sublist in args.lmBasePrefix for item in sublist]

preList.append(lmPreList) 


# Setup everything 
mCaseW = MultiCaseWidget(preList,caseList,postList)
mCaseW.setup(args.orientation,args.all_3_orientations) 

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
