import argparse
import os 
import vtk.util.numpy_support
import numpy
import nibabel as nib

import CompareVolumes
import slite
#
# Functions
#

def ReadImageSlicer(FileName): 
  mrml = slicer.vtkMRMLScene()
  vl = slicer.vtkSlicerVolumesLogic()
  vl.SetAndObserveMRMLScene(mrml)
  n = vl.AddArchetypeVolume(FileName,'CTC')
  i = n.GetImageData()
  return i

# Implementation based on https://github.com/pieper/CaseHub/blob/5aaeb51d4b7281b39f116b180123227331ce791a/BenchtopNeuro/BenchtopNeuro.py#L306-L348
# interesting to look at 
# https://github.com/loli/medpy/blob/master/medpy/io/load.py
# no flipping needed - checked it 
# reads in image data from second frame (as we assume 1st frame is already read)

def nibVtkConversionDirect(loadedFile,scalarType):
    # startT=time.time()
    py4DImg=loadedFile.get_data()

    tDim=py4DImg.shape[3]
    shape3D=py4DImg.shape[0:3]
    # same as dim=vNode.GetImageData().GetDimensions()
    sDim=shape3D[2]
    yDim=shape3D[1]
    xDim=shape3D[0]

    imgList=[]
    for index in  xrange(1,tDim): 
      vtkImg=vtk.vtkImageData()
      vtkImg.SetDimensions(shape3D)
      vtkImg.AllocateScalars(scalarType,1)
      
      # Maybe this is a better way 
      # import SimpleITK as sitk    
      # img=sitk.GetImageFromArray(py4DImg[:,:,:,index])

      # problem with orientation so currently 
      vtkImgArray = vtk.util.numpy_support.vtk_to_numpy(vtkImg.GetPointData().GetScalars()).reshape(shape3D[2],shape3D[0],shape3D[1])
      #http://nipy.org/nibabel/coordinate_systems.html
      # Problem - different coordinate system between nibabel and vkt 
      for slice in xrange(sDim):
         vtkImgArray[slice,:,:] = py4DImg[:,:,slice,index].T
          # py3DImg = numpy.fliplr(py4DImg[:,:,slice,index])

      # This does not work as 
      # Still Slow 
      # http://www.vtk.org/Wiki/VTK/Examples/Cxx/ImageData/IterateImageData                       
      #for slice in xrange(0,sDim):
      #  for y in xrange(0,yDim):
      #    for x in xrange(0,xDim):
      #      ptr= vtk.util.numpy_support.vtk_to_numpy(vtkImg.GetScalarPointer(x,y,slice))
      #      print ptr
      #      ptr[0]=py4DImg[x,y,slice,index]

      imgList.append(vtkImg)
  
    # endT=time.time()
    # print "Took: %f" % (endT - startT) 
    return imgList

def load4DVolume(listFileNames,labelFlag):

    # Needs to be done that way to work for single file name and multi one 
    firstFileName=listFileNames 
    if isinstance(firstFileName, basestring) :
      multiFileFlag=False
    else :
      firstFileName=listFileNames[0]
      if len(listFileNames) > 1:
        multiFileFlag=True
      else: 
        multiFileFlag=False

    # Load first volume
    vNode = slite.loadVolume(firstFileName,labelFlag)
    if not vNode: 
      slite.errorPrint(0,"Could not load %s!", firstFileName)  

    iVtkList=[vNode.GetImageData()]
    #
    # Load Multi File Volume 
    #
    if multiFileFlag:   
       for FILE in listFileNames[1:] :
         img=ReadImageSlicer(FILE)
         if img:
           iVtkList.append(img)

       return (vNode,iVtkList)

    #
    # Load Single File Volume 
    #
    fileExt=os.path.splitext(firstFileName)[1]
    if fileExt == ".gz" :
       fileExt=os.path.splitext(firstFileName)[1]

    # nibabel 1.3 cannot read nrrd file - so assume it is 3D right now 
    if fileExt == ".nrrd": 
        print "Warning: NRRD files are assumed to be 3D"
        return (vNode,iVtkList)
    
    loadedFile=nib.load(firstFileName)
    # Nothing to do as it is a 3D Volume - so already read by slicer function
    if len(loadedFile.shape) == 3 :
        return (vNode,iVtkList)

    # Sadly enough this was the best solution I found so far - write to file and read in again 
    # imgList=nibVtkConversionWrite(loadedFile)
    imgList=nibVtkConversionDirect(loadedFile,vNode.GetImageData().GetScalarType())
    iVtkList.extend(imgList)

    return (vNode,iVtkList)

def loadVolumes(fileList,labelFlag,fourDFlag):

   imgList=[]    
   volNodeList=[]

   if not fileList: 
     return (volNodeList,imgList)
   
   if not fourDFlag:
     fileList=[item for sublist in fileList for item in sublist]

   numVolumes=len(fileList)

   # For multiple input   
   for index in xrange(numVolumes):
     (volNode,iList) = load4DVolume(fileList[index],labelFlag)
   
     volNodeList.append(volNode)    
     imgList.append(iList)
   
   return (volNodeList,imgList)

class CtrlPanelWidget:
  def __init__(self,sliceNodes,fgNodeList,fgNodeImgList,bgNodeList,bgNodeImgList,lmNodeList,lmNodeImgList):
    self.sliceNodeList = sliceNodes   
    self.nodeType = ('FG', 'BG', 'LM')
    self.nodeList=[fgNodeList,bgNodeList,lmNodeList]
    self.nodeImgList=[fgNodeImgList,bgNodeImgList,lmNodeImgList]
    self.ctrlWidget = ""
    self.selectedOrientation = ""
    self.layoutManager = slicer.app.layoutManager()
    self.numFrames = len(fgNodeImgList[0])
    self.orientations = ('Axial', 'Sagittal', 'Coronal')
    self.LinkViewers()

  def CreateCtrlPanel(self,wName,parent):
    if self.ctrlWidget : 
      return

    if parent:
       self.ctrlWidget=parent
    else :  
       self.ctrlWidget=slicer.qMRMLWidget()
       self.ctrlWidget.setMRMLScene(slicer.mrmlScene)
       self.ctrlWidget.setLayout(qt.QGridLayout())
       

    self.ctrlWidget.setWindowTitle(wName) 
    ctrlLayout = self.ctrlWidget.layout()  

    if self.numFrames > 1:  
      ctrlFrameLabel = qt.QLabel('Frame')
      ctrlFrameSlider = ctk.ctkSliderWidget()
      ctrlFrameSlider.minimum=0 
      ctrlFrameSlider.maximum=self.numFrames-1
      ctrlFrameSlider.connect('valueChanged(double)', self.onSliderFrameChanged)
      ctrlLayout.addWidget(ctrlFrameLabel, 0, 0)
      ctrlLayout.addWidget(ctrlFrameSlider, 0, 1)


    ctrlLevelLabel = qt.QLabel('Level')
    ctrlLevelSlider = ctk.ctkSliderWidget()

    ctrlWindowLabel = qt.QLabel('Window')
    ctrlWindowSlider = ctk.ctkSliderWidget()

    vImg = self.nodeImgList[0][0][0]
    vNode = self.nodeList[0][0]
    if vImg and vNode: 
      iRange=vImg.GetScalarRange()
      ctrlLevelSlider.minimum = iRange[0]
      ctrlWindowSlider.minimum = iRange[0]
      ctrlLevelSlider.maximum = iRange[1]
      ctrlWindowSlider.maximum = iRange[1]*1.2
      ctrlLevelSlider.value=vNode.GetVolumeDisplayNode().GetLevel()
      ctrlWindowSlider.value=vNode.GetVolumeDisplayNode().GetWindow()
  
    ctrlLevelSlider.connect('valueChanged(double)', self.onSliderLevelChanged)
    ctrlWindowSlider.connect('valueChanged(double)', self.onSliderWindowChanged)

    ctrlLayout.addWidget(ctrlLevelLabel, 1, 0)
    ctrlLayout.addWidget(ctrlLevelSlider, 1, 1)
    ctrlLayout.addWidget(ctrlWindowLabel, 2, 0)
    ctrlLayout.addWidget(ctrlWindowSlider, 2, 1)

    #self.orientationBox = qt.QGroupBox("Orientation")
    #self.orientationBox.setLayout(qt.QFormLayout())
    self.orientationButtons = {}
    index=0
    for orientation in self.orientations:
      self.orientationButtons[orientation] = qt.QRadioButton()
      self.orientationButtons[orientation].text = orientation
      # self.orientationBox.layout().addWidget(self.orientationButtons[orientation])
      ctrlLayout.addWidget(self.orientationButtons[orientation],3,index)
      self.orientationButtons[orientation].connect("clicked()",lambda o=orientation: self.setOrientation(o))
      index+=1

    # parametersFormLayout.addWidget(self.orientationBox)
    self.setOrientation(self.orientations[0])

    if True:
      # reload button
      # (use this during development, but remove it when delivering
      #  your module to users)
      self.exitButton = qt.QPushButton("Exit")
      self.exitButton.toolTip = "Close down slicer."
      self.exitButton.name = "sviewer exit"
      ctrlLayout.addWidget(self.exitButton,4,0)
      self.exitButton.connect('clicked()', exit)


    if False:
      self.plotFrame = ctk.ctkCollapsibleButton()
      self.plotFrame.text = "Plotting"
      self.plotFrame.collapsed = 0
      plotFrameLayout = qt.QGridLayout(self.plotFrame)
      ctrlLayout.addWidget(self.plotFrame,5,0)

      #self.plotSettingsFrame = ctk.ctkCollapsibleButton()
      #self.plotSettingsFrame.text = "Settings"
      #self.plotSettingsFrame.collapsed = 1
      #plotSettingsFrameLayout = qt.QGridLayout(self.plotSettingsFrame)
      #plotFrameLayout.addWidget(self.plotSettingsFrame,0,1)
     

      # taken from  https://github.com/fedorov/MultiVolumeExplorer

      # add chart container widget
      self.__chartView = ctk.ctkVTKChartView(self.ctrlWidget)
      plotFrameLayout.addWidget(self.__chartView,3,0,1,3)

      self.__chart = self.__chartView.chart()
      self.__chartTable = vtk.vtkTable()
      self.__xArray = vtk.vtkFloatArray()
      self.__yArray = vtk.vtkFloatArray()
      # will crash if there is no name
      self.__xArray.SetName('')
      self.__yArray.SetName('signal intensity')
      self.__chartTable.AddColumn(self.__xArray)
      self.__chartTable.AddColumn(self.__yArray)
      #self.onInputChanged()
      #self.refreshObservers()

    # do not do ctrlWin.show() here - for some reason window does not pop up then 
    return self.ctrlWidget

  def removeObservers(self):
    # remove observers and reset
    for observee,tag in self.styleObserverTags:
      observee.RemoveObserver(tag)
    self.styleObserverTags = []
    self.sliceWidgetsPerStyle = {}


  def refreshObservers(self):
    """ When the layout changes, drop the observers from
    all the old widgets and create new observers for the
    newly created widgets"""
    self.removeObservers()
    # get new slice nodes
    sliceNodeCount = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSliceNode')
    for nodeIndex in xrange(sliceNodeCount):
      # find the widget for each node in scene
      sliceNode = slicer.mrmlScene.GetNthNodeByClass(nodeIndex, 'vtkMRMLSliceNode')
      sliceWidget = self.layoutManager.sliceWidget(sliceNode.GetLayoutName())
      if sliceWidget:
        # add obserservers and keep track of tags
        style = sliceWidget.sliceView().interactorStyle()
        self.sliceWidgetsPerStyle[style] = sliceWidget
        events = ("MouseMoveEvent", "EnterEvent", "LeaveEvent")
        for event in events:
          tag = style.AddObserver(event, self.processEvent)
          self.styleObserverTags.append([style,tag])

  def processEvent(self,observee,event):
    #if not self.iCharting.checked:
    #  return

    mvImage = self.nodeImgList[0]
    mvNodes = self.nodeList[0]

    nComponents = self.numFrames

    # TODO: use a timer to delay calculation and compress events
    if event == 'LeaveEvent':
      # reset all the readouts
      # TODO: reset the label text
      return

    if not self.sliceWidgetsPerStyle.has_key(observee):
      return

    sliceWidget = self.sliceWidgetsPerStyle[observee]
    sliceLogic = sliceWidget.sliceLogic()
    interactor = observee.GetInteractor()
    xy = interactor.GetEventPosition()
    xyz = sliceWidget.sliceView().convertDeviceToXYZ(xy);

    ras = sliceWidget.sliceView().convertXYZToRAS(xyz)
    bgLayer = sliceLogic.GetForegroundLayer()
    # GetBackgroundLayer()
    fgLayer = sliceLogic.GetForegroundLayer()

    volumeNode = mvNodes[0]
    fgVolumeNode = mvNodes[0]
    if not volumeNode or volumeNode.GetID() != mvNodes[0].GetID():
      return
    #if volumeNode != self.__mvNode:
    #  return

    nameLabel = volumeNode.GetName()
    xyToIJK = bgLayer.GetXYToIJKTransform()
    ijkFloat = xyToIJK.TransformDoublePoint(xyz)
    ijk = []
    for element in ijkFloat:
      try:
        index = int(round(element))
      except ValueError:
        index = 0
      ijk.append(index)

    extent = mvImage[0].GetExtent()
    if not (ijk[0]>=extent[0] and ijk[0]<=extent[1] and \
       ijk[1]>=extent[2] and ijk[1]<=extent[3] and \
       ijk[2]>=extent[4] and ijk[2]<=extent[5]):
      # pixel outside the valid extent
      return

    useFg = False
    if fgVolumeNode:
      fgxyToIJK = fgLayer.GetXYToIJKTransform()
      fgijkFloat = xyToIJK.TransformDoublePoint(xyz)
      fgijk = []
      for element in fgijkFloat:
        try:
          index = int(round(element))
        except ValueError:
          index = 0
        fgijk.append(index)
        fgImage = fgVolumeNode.GetImageData()

      fgChartTable = vtk.vtkTable()
      if fgijk[0] == ijk[0] and fgijk[1] == ijk[1] and fgijk[2] == ijk[2] and \
          fgImage.GetNumberOfScalarComponents() == mvImage[0].GetNumberOfScalarComponents():
        useFg = True

        fgxArray = vtk.vtkFloatArray()
        fgxArray.SetNumberOfTuples(nComponents)
        fgxArray.SetNumberOfComponents(1)
        fgxArray.Allocate(nComponents)
        fgxArray.SetName('frame')

        fgyArray = vtk.vtkFloatArray()
        fgyArray.SetNumberOfTuples(nComponents)
        fgyArray.SetNumberOfComponents(1)
        fgyArray.Allocate(nComponents)
        fgyArray.SetName('signal intensity')
 
        # will crash if there is no name
        fgChartTable.AddColumn(fgxArray)
        fgChartTable.AddColumn(fgyArray)
        fgChartTable.SetNumberOfRows(nComponents)

    # get the vector of values at IJK

    for c in range(nComponents):
      val = mvImage[0].GetScalarComponentAsDouble(ijk[0],ijk[1],ijk[2],c)
      self.__chartTable.SetValue(c, 0, self.__mvLabels[c])
      self.__chartTable.SetValue(c, 1, val)
      if useFg:
        fgValue = fgImage.GetScalarComponentAsDouble(ijk[0],ijk[1],ijk[2],c)
        fgChartTable.SetValue(c,0,self.__mvLabels[c])
        fgChartTable.SetValue(c,1,fgValue)

    baselineAverageSignal = 0
    # if self.iChartingPercent.checked:
    #   # check if percent plotting was requested and recalculate
    #   nBaselines = min(self.baselineFrames.value,nComponents)
    #   for c in range(nBaselines):
    #     baselineAverageSignal += mvImage[0].GetScalarComponentAsDouble(ijk[0],ijk[1],ijk[2],c)
    #   baselineAverageSignal /= nBaselines
    #   if baselineAverageSignal != 0:
    #     for c in range(nComponents):
    #       intensity = mvImage[0].GetScalarComponentAsDouble(ijk[0],ijk[1],ijk[2],c)
    #       self.__chartTable.SetValue(c,1,(intensity/baselineAverageSignal-1)*100.)

    self.__chart.RemovePlot(0)
    self.__chart.RemovePlot(0)

    #if self.iChartingPercent.checked and baselineAverageSignal != 0:
    #  self.__chart.GetAxis(0).SetTitle('change relative to baseline, %')
    #else:
    self.__chart.GetAxis(0).SetTitle('signal intensity')

    #tag = str(self.__mvNode.GetAttribute('MultiVolume.FrameIdentifyingDICOMTagName'))
    #units = str(self.__mvNode.GetAttribute('MultiVolume.FrameIdentifyingDICOMTagUnits'))
    #xTitle = tag+', '+units
    #self.__chart.GetAxis(1).SetTitle(xTitle)
    #if self.iChartingIntensityFixedAxes.checked == True:
    self.__chart.GetAxis(0).SetBehavior(vtk.vtkAxis.FIXED)
    self.__chart.GetAxis(0).SetRange(self.__mvRange[0],self.__mvRange[1])
    #else:
    #  self.__chart.GetAxis(0).SetBehavior(vtk.vtkAxis.AUTO)
    # if useFg:
    if useFg:
      plot = self.__chart.AddPlot(vtk.vtkChart.POINTS)
      if vtk.VTK_MAJOR_VERSION <= 5:
        plot.SetInput(self.__chartTable, 0, 1)
      else:
        plot.SetInputData(self.__chartTable, 0, 1)
      fgplot = self.__chart.AddPlot(vtk.vtkChart.LINE)
      if vtk.VTK_MAJOR_VERSION <= 5:
        fgplot.SetInput(fgChartTable, 0, 1)
      else:
        fgplot.SetInputData(fgChartTable, 0, 1)
    else:
      plot = self.__chart.AddPlot(vtk.vtkChart.LINE)
      if vtk.VTK_MAJOR_VERSION <= 5:
        plot.SetInput(self.__chartTable, 0, 1)
      else:
        plot.SetInputData(self.__chartTable, 0, 1)
      
    if self.xLogScaleCheckBox.checkState() == 2:
      title = self.__chart.GetAxis(1).GetTitle()
      self.__chart.GetAxis(1).SetTitle('log of '+title)

    if self.yLogScaleCheckBox.checkState() == 2:
      title = self.__chart.GetAxis(0).GetTitle()
      self.__chart.GetAxis(0).SetTitle('log of '+title)
    # seems to update only after another plot?..


  def onInputChanged(self):
      self.__chartTable.SetNumberOfRows(self.numFrames)

      self.plotFrame.enabled = True
      self.plotFrame.collapsed = 0
      self.__xArray.SetNumberOfTuples(self.numFrames)
      self.__xArray.SetNumberOfComponents(1)
      self.__xArray.Allocate(self.numFrames)
      self.__xArray.SetName('frame')
      self.__yArray.SetNumberOfTuples(self.numFrames)
      self.__yArray.SetNumberOfComponents(1)
      self.__yArray.Allocate(self.numFrames)
      self.__yArray.SetName('signal intensity')

      self.__chartTable = vtk.vtkTable()
      self.__chartTable.AddColumn(self.__xArray)
      self.__chartTable.AddColumn(self.__yArray)
      self.__chartTable.SetNumberOfRows(self.numFrames)

      # get the range of intensities for the
      self.__mvRange = [0,0]
      for v in self.nodeImgList[0][0]: 
        frame = v.GetOutput()
        frameRange = frame.GetScalarRange()
        self.__mvRange[0] = min(self.__mvRange[0], frameRange[0])
        self.__mvRange[1] = max(self.__mvRange[1], frameRange[1])

      #self.__mvLabels = string.split(self.__mvNode.GetAttribute('MultiVolume.FrameLabels'),',')
      #if len(self.__mvLabels) != nFrames:
      #  return
      #for l in range(nFrames):
      #  self.__mvLabels[l] = float(self.__mvLabels[l])

      self.baselineFrames.maximum = self.numFrames


  def LinkViewers(self):
    if self.sliceNodeList:
      sliceNode = self.sliceNodeList.values()[0]
      sliceWidget = self.layoutManager.sliceWidget(sliceNode.GetLayoutName())
      sliceWidget.sliceController().setSliceLink(1)

  def onSliderFrameChanged(self,newValue):
    index=int(newValue)
    for vType in xrange(2):
      for node,imgList in zip(self.nodeList[vType], self.nodeImgList[vType]) :  
        if index < len(imgList):
          node.SetAndObserveImageData(imgList[index])

  def onSliderLevelChanged(self,newValue):
     for node in self.nodeList[0] : 
       dNode=node.GetVolumeDisplayNode() 
       dNode.AutoWindowLevelOff()
       dNode.SetLevel(newValue)


  def onSliderWindowChanged(self,newValue):
     for node in self.nodeList[0] : 
       dNode=node.GetVolumeDisplayNode() 
       dNode.AutoWindowLevelOff()
       dNode.SetWindow(newValue)

  def setOrientation(self,orientation):
    if orientation in self.orientations:
        self.selectedOrientation = orientation
        self.orientationButtons[orientation].checked = True
        for sliceNode in self.sliceNodeList.values():
          sliceNode.SetOrientation(orientation) 

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
parser.add_argument( "-o", "--orientation", required=False, help="View orientation (Axial, Sagittal, Coronal)", action="store", default = "Axial")

args = parser.parse_args()
fourDFlag=args.fourD

# remove viewers in main window
if False: 
  layoutManager = slicer.app.layoutManager()
  for node in slicer.util.getNodes('vtkMRMLSliceNode*').values():
    #sliceWidget = layoutManager.sliceWidget(node.GetLayoutName())
    # sliceWidget.delete()
    slicer.mrmlScene.RemoveNode(node)
#
# Load Volume 
#
(fgNodeList,fgImageList) = loadVolumes(args.foreground,0,fourDFlag)
(bgNodeList,bgImageList) = loadVolumes(args.background,0,fourDFlag)
(lmNodeList,lmImageList) = loadVolumes(args.labelmap,1,fourDFlag)

# https://github.com/pieper/CompareVolumes/blob/master/CompareVolumes.py
cvLogic=CompareVolumes.CompareVolumesLogic()
sliceNodeList = cvLogic.viewerPerVolume(volumeNodes=fgNodeList,background=bgNodeList,label=lmNodeList,orientation=args.orientation)

cpWidget=CtrlPanelWidget(sliceNodeList,fgNodeList,fgImageList,bgNodeList,bgImageList,lmNodeList,lmImageList)
ctrlWin = cpWidget.CreateCtrlPanel(args.window_name,"")
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
