from __main__ import sys, qt, vtk, slicer

#
# Set the path in slite.sh correctly and then simply execute ./slite.sh <file name 1> <file name 2> ....
# then the program creates an extra viewer for each file 
# 

#
# Functions 
#
def errorPrint(guiFlag,txt):
  if guiFlag:
      qt.QMessageBox.warning(None, "slite", txt)   
  else: 
      print " "
      print "Error: %s" % (txt)   
      print " "

  sys.exit(1)

def loadVolume(fileName,labelFlag):
   if labelFlag:
       result = slicer.util.loadLabelVolume(fileName,returnNode=True)[1]
   else:
       result = slicer.util.loadVolume(fileName,returnNode=True)[1]
 
   if not result: 
       errorPrint(0,"Could not load volume " + fileName)

   return result    

def createViewer(sName,fgNode, bgNode, lNode):
  sWidget = slicer.qMRMLSliceWidget()
  sWidget.setMRMLScene(slicer.mrmlScene)

  # for debugging
  blub=slicer.vtkMRMLSliceCompositeNode()
  blub.SetName(sName)
  slicer.mrmlScene.AddNode(blub)
  sWidget.sliceLogic().SetSliceCompositeNode(blub)

  sComposite=sWidget.sliceLogic().GetSliceCompositeNode()
  if fgNode: 
    sComposite.SetForegroundVolumeID(fgNode.GetID())
   
  if bgNode: 
    sComposite.SetBackgroundVolumeID(bgNode.GetID())

  if lNode: 
    sComposite.SetLabelVolumeID(lNode.GetID())

  return sWidget

#
# Main
#
if __name__ == '__main__':
  vViewer=[]
  for index in range(1,len(sys.argv)):
    vNode=loadVolume(sys.argv[index],0)
    if index > 1: 
       print vViewer[0].sliceLogic().GetSliceCompositeNode().GetID()
    vViewer.append(createViewer("Viewer%d"%index,vNode,"",""))
    vViewer[index-1].setWindowTitle(sys.argv[index])
    vViewer[index-1].show()
    print vViewer[0].sliceLogic().GetSliceCompositeNode().GetID()


  #mw=slicer.qMRMLWidget()
  #mw.setLayout(qt.QVBoxLayout())
  #mw.setMRMLScene(slicer.mrmlScene)
  #mw.show()
