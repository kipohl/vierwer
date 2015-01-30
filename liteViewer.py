from __main__ import sys, qt, vtk, slicer

# https://github.com/pieper/CompareVolumes/blob/master/CompareVolumes.py
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
  #blub=slicer.vtkMRMLSliceCompositeNode()
  #blub.SetName(sName)
  #slicer.mrmlScene.AddNode(blub)
  #sWidget.sliceLogic().SetSliceCompositeNode(blub)

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
  
  applicationLogic=slicer.vtkMRMLApplicationLogic()
  applicationLogic.SetMRMLScene(slicer.mrmlScene)

  vNodeList=[]
  vViewer=[]
  for index in range(1,len(sys.argv)):
    vNode=loadVolume(sys.argv[index],0)
    vNodeList.append(vNode)
    vViewer.append(createViewer("Viewer%d"%index,vNode,"",""))
    vViewer[index-1].setWindowTitle(sys.argv[index])
    vViewer[index-1].show()



  # Initialization did not make compare viewer work 
  if False: 
  # initialize enviornment - same copied from trunk/Applications/SlicerApp/qSlicerAppMainWindow.cxx
    mw=qt.QMainWindow()
    layoutFrame=qt.QFrame(mw.centralWidget())
    layoutFrame.setObjectName("CentralWidgetLayoutFrame")
    centralLayout = qt.QHBoxLayout(mw.centralWidget())
    centralLayout.setContentsMargins(0, 0, 0, 0)
    centralLayout.addWidget(layoutFrame)
   
    #QwindowColor = mw.centralWidget().palette().color(QPalette::Window);
    #QPalette centralPalette = this->CentralWidget->palette();
    #centralPalette.setColor(QPalette::Window, QColor(95, 95, 113));
    #this->CentralWidget->setAutoFillBackground(true);
    #this->CentralWidget->setPalette(centralPalette);
    
    #// Restore the palette for the children
    #centralPalette.setColor(QPalette::Window, windowColor);
    #layoutFrame->setPalette(centralPalette);
    #layoutFrame->setAttribute(Qt::WA_NoSystemBackground, true);
    #layoutFrame->setAttribute(Qt::WA_TranslucentBackground, true);
    
    layoutManager=slicer.qSlicerLayoutManager(layoutFrame)
    # layoutManager.setScriptedDisplayableManagerDirectory(slicer.app.slicerHome + "/bin/Python/mrmlDisplayableManager")
    slicer.app.setLayoutManager(layoutManager)

    import CompareVolumes
    cvLogic=CompareVolumes.CompareVolumesLogic()
    cvLogic.viewerPerVolume(volumeNodes=vNodeList)
 
  #mw=slicer.qMRMLWidget()
  #mw.setLayout(qt.QVBoxLayout())
  #mw.setMRMLScene(slicer.mrmlScene)
  #mw.show()
