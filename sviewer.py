import argparse
import slite
import readFile

#
# Functions
#
def CreateVolumeScalarNode(referenceNode, nodeName):
  clonedVolumeNode=slicer.vtkMRMLScalarVolumeNode()
  clonedVolumeNode.CopyWithScene(referenceNode)
  clonedVolumeNode.SetAndObserveStorageNodeID("")
  clonedVolumeNode.SetName(nodeName);

  clonedDisplayNode=slicer.vtkMRMLScalarVolumeDisplayNode()
  clonedDisplayNode.CopyWithScene(referenceNode.GetDisplayNode())
  slicer.mrmlScene.AddNode(clonedDisplayNode)
  clonedVolumeNode.SetAndObserveDisplayNodeID(clonedDisplayNode.GetID())

  #VTK_CREATE(vtkImageData, volumeData);
  #clonedVolumeNode->SetAndObserveImageData(volumeData);

  slicer.mrmlScene.AddNode(clonedVolumeNode)

  volID = clonedVolumeNode.GetID()
  return slicer.mrmlScene.GetNodeByID(volID)

def createRowVolumes(fileList,rowName,labelFlag,fourDFlag):

  if not fileList: 
    return ("","")

  if not fourDFlag:
    fileList=[item for sublist in fileList for item in sublist]

  rowScalarType=-1
  volNode=[]
  imgList=[] 
  volScalarType=[]
  numVolumes=len(fileList)

  for index in xrange(numVolumes):
    firstFileName=fileList[index]
    if not isinstance(firstFileName, basestring) :
        firstFileName=firstFileName[0]
    
    volNode.append(slite.loadVolume(firstFileName,labelFlag))

    if fourDFlag :
       iList=[]
       for FILE in fileList[index]: 
         iList.append(readFile.ReadImageSlicer(FILE))

       imgList.append(iList)
    else:
       imgList.append([volNode[index].GetImageData()])

    volScalarType.append(volNode[index].GetImageData().GetScalarType())
    if volScalarType[index] > rowScalarType :
      rowScalarType=volScalarType[index]


  if numVolumes == 1: 
    return (volNode[0],imgList)

  #
  # Set them all to the same scalar type and attach to row
  #
  rowView=vtk.vtkImageAppend()
  rowView.SetAppendAxis(2)

  for index in xrange(numVolumes) :
    if volScalarType[index] != rowScalarType :
      volCorrected = vtk.vtkImageCast()
      volCorrected.SetInputConnection(volNode[index].GetImageDataConnection()) 
      volCorrected.SetOutputScalarType(rowScalarType)
      volCorrected.Update()
      volNode[index].SetImageDataConnection(volCorrected.GetOutputPort())

  for index in reversed(xrange(numVolumes)) :
    rowView.AddInputData(volNode[index].GetImageData())

  rowView.Update()
  # create a volume node 

  rowNode=CreateVolumeScalarNode(volNode[0],rowName) 
  rowNode.SetImageDataConnection(rowView.GetOutputPort())
  
  rowOrigin=rowNode.GetOrigin()

  rowNode.SetOrigin(numVolumes*rowOrigin[0],rowOrigin[1],rowOrigin[2])

  return (rowNode,imgList) 


def getViewerVolumeNode(win,vType):
  sComp=win.sliceLogic().GetSliceCompositeNode() 
  nID=""
  if vType == "fg": 
     nID=sComp.GetForegroundVolumeID()
  elif vType == "bg": 
     nID=sComp.GetBackgroundVolumeID()
  elif vType == "lm":
     nID=sComp.GetLabelVolumeID()

  if nID:  
    return slicer.mrmlScene.GetNodeByID(nID)
  
  return "" 

def getActiveVolumeNode(win):
  sNode=getViewerVolumeNode(win,"fg")
  if not sNode: 
    sNode=getViewerVolumeNode(win,"bg")
  elif not sNode: 
    sNode=getViewerVolumeNode(win,"lm")
  elif not sNode: 
    slite.errorPrint(0,"Viewer has no volume assigned to it")

  return sNode


def customizeViewer(sWidget,wName):
  sWidget.setWindowTitle(wName)
  winHeight=sWidget.height
  winWidth=sWidget.width
  sNode=getActiveVolumeNode(sWidget)
  nSpacing=sNode.GetSpacing()
  nExtent=sNode.GetImageData().GetExtent()
  nHeight=nExtent[3] - nExtent[2] + 1
  nWidth=nExtent[5] - nExtent[4] + 1

  sWidget.resize(winWidth*nWidth*nSpacing[2]/(nHeight*nSpacing[1]),winHeight)
  sWidget.sliceController().setSliceLink(0)

def ChangeFrame(index,vType):
  vNode=getViewerVolumeNode(ctrlWin,vType)
  if vNode:
     if vType == "fg":
        imgList=foregroundImage[0]
     elif vType == "bg":
        imgList=backgroundImage[0]
     elif vType == "lm": 
        imgList=labelmapImage[0]
     else : 
        slite.errorPrint(0,"ChangeFrame: Wrong Type")

     if index < len(imgList):
       vNode.SetAndObserveImageData(imgList[index])

def onSliderFrameChanged(newValue):
  index=int(newValue)

  ChangeFrame(index,"fg")
  ChangeFrame(index,"bg")
  ChangeFrame(index,"lm")
  
def onSliderLevelChanged(newValue):
  vNode=getActiveVolumeNode(ctrlWin) 
  if vNode:
    dNode=vNode.GetVolumeDisplayNode() 
    dNode.AutoWindowLevelOff()
    dNode.SetLevel(newValue)


def onSliderWindowChanged(newValue):
  vNode=getActiveVolumeNode(ctrlWin) 
  if vNode:
    dNode=vNode.GetVolumeDisplayNode() 
    dNode.AutoWindowLevelOff()
    dNode.SetWindow(newValue)

def CreateCtrlPanel(masterWin,collapseFlag):
  if masterWin:
    ctrlWin=masterWin
  else :  
    ctrlWin=slicer.qMRMLWidget()
    ctrlWin.setLayout(qt.QGridLayout())
    ctrlWin.setWindowTitle("4D Control Pannel") 
    ctrlWin.setMRMLScene(slicer.mrmlScene)

  ctrlWinLayout = ctrlWin.layout()

  ctrlFrameLabel = qt.QLabel('Frame')
  ctrlFrameSlider = ctk.ctkSliderWidget()
  ctrlFrameSlider.minimum=0 
  ctrlFrameSlider.maximum=len(foregroundImage[0])
 
  ctrlLevelLabel = qt.QLabel('Level')
  ctrlLevelSlider = ctk.ctkSliderWidget()

  ctrlWindowLabel = qt.QLabel('Window')
  ctrlWindowSlider = ctk.ctkSliderWidget()


  vNode=getActiveVolumeNode(ctrlWin)
  if vNode: 
    vImageRange=vNode.GetImageData().GetScalarRange()
    ctrlLevelSlider.minimum = vImageRange[0]
    ctrlWindowSlider.minimum = vImageRange[0]
    ctrlLevelSlider.maximum = vImageRange[1]
    ctrlWindowSlider.maximum = vImageRange[1]*2

    ctrlLevelSlider.value=vNode.GetVolumeDisplayNode().GetLevel()
    ctrlWindowSlider.value=vNode.GetVolumeDisplayNode().GetWindow()

  ctrlFrameSlider.connect('valueChanged(double)', onSliderFrameChanged)
  ctrlLevelSlider.connect('valueChanged(double)', onSliderLevelChanged)
  ctrlWindowSlider.connect('valueChanged(double)', onSliderWindowChanged)

  if collapseFlag:
    ctrlFrame = ctk.ctkCollapsibleButton()
    ctrlFrame.text = "Viewer Control"
    ctrlFrame.collapsed = 0
    ctrlFrameLayout = qt.QGridLayout(ctrlFrame)
    ctrlWinLayout.addWidget(ctrlFrame)
    ctrlLayout=ctrlFrameLayout
  else: 
    ctrlLayout=ctrlWinLayout
  
  if fourDFlag:  
    ctrlLayout.addWidget(ctrlFrameLabel, 0, 0)
    ctrlLayout.addWidget(ctrlFrameSlider, 0, 1)

  ctrlLayout.addWidget(ctrlLevelLabel, 1, 0)
  ctrlLayout.addWidget(ctrlLevelSlider, 1, 1)
  ctrlLayout.addWidget(ctrlWindowLabel, 2, 0)
  ctrlLayout.addWidget(ctrlWindowSlider, 2, 1)

  # do not do ctrlWin.show() here - for some reason window does not pop up then 
  return ctrlWin

# =======================
#  Main 
# =======================

# first entry is slite.py

parser = argparse.ArgumentParser( description="A 3D viewer of a single or multiple MRs" )
parser.add_argument( "-f", "--foreground",  nargs='+', required=True, help="Images shown in foreground.", action="append")
parser.add_argument( "-b", "--background",  nargs='*', required=False, help="Images shown in background.", action="append")
parser.add_argument( "-l", "--labelmap",  nargs='*', required=False, help="File name of Label maps", action="append")
parser.add_argument( "-4", "--fourD", required=False, help="Load in 4D image sequence.", action="store_true", default = False )
parser.add_argument( "-n", "--window_name", required=False, help="Window name", action="store", default = "Viewer")

args = parser.parse_args()
fourDFlag=args.fourD

#
# Load Volume 
#

(foregroundNode,foregroundImage)=createRowVolumes(args.foreground,"FG",0,fourDFlag) 
(backgroundNode,backgroundImage)=createRowVolumes(args.background,"BG",0,fourDFlag) 
(labelmapNode,labelmapImage)=createRowVolumes(args.labelmap,"LM",1,fourDFlag) 

sliceWidget = []
sliceWidget.append(slite.createViewer("TEST",foregroundNode, backgroundNode, labelmapNode))

customizeViewer(sliceWidget[0],args.window_name)

# window does not come up for some reason 
ctrlWin = CreateCtrlPanel(sliceWidget[0],1)
ctrlWin.show()

 
# Debug stuff 
# slicer.util.saveScene('/tmp/scene.mrml')
# dir(foregroundNode) returns all functions 
# [s for s in dir(blub) if "Get" in s]

# class MarkupsInViewsSelfTestWidget:
