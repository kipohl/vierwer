import argparse
import os 
import vtk.util.numpy_support
import nibabel as nib
import liteViewer
from __main__ import qt, ctk, vtk, slicer

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
      vtkImgArray = vtk.util.numpy_support.vtk_to_numpy(vtkImg.GetPointData().GetScalars()).reshape(shape3D[2],shape3D[1],shape3D[0])
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
    vNode = liteViewer.loadVolume(firstFileName,labelFlag)
    if not vNode: 
      liteViewer.errorPrint(0,"Could not load %s!" %  firstFileName)  
      return (None,None)

    iVtkList=[vNode.GetImageData()]
    #
    # Load Multi File Volume 
    #
    if multiFileFlag:   
       for FILE in listFileNames[1:] :
         img=ReadImageSlicer(FILE)
         if img:
           iVtkList.append(img)
         else :
           return (None,None)

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
   missingList=[]

   if not fileList: 
     return (volNodeList,imgList,missingList)
   
   if isinstance(fileList, basestring) :
     fileList = [ fileList ]
   elif not fourDFlag and (len(fileList) > 1 or not isinstance(fileList[0], basestring)):
     fileList=[item for sublist in fileList for item in sublist]

   numVolumes=len(fileList)
   # For multiple input   
   for index in xrange(numVolumes):
     (volNode,iList) = load4DVolume(fileList[index],labelFlag)
     if volNode: 
       volNodeList.append(volNode)    
       imgList.append(iList)
     else :
       missingList.append(fileList[index])
   
   return (volNodeList,imgList,missingList)

class CtrlPanelWidget:
  def __init__(self,sliceNodes,sliceWidget,fgNodeList,fgNodeImgList,bgNodeList,bgNodeImgList,lmNodeList,lmNodeImgList,orientation):
    self.sliceNodeList = sliceNodes
    self.singleViewerWidget = sliceWidget   
    self.nodeType = ('FG', 'BG', 'LM')
    self.nodeList=[fgNodeList,bgNodeList,lmNodeList]
    self.nodeImgList=[fgNodeImgList,bgNodeImgList,lmNodeImgList]
    self.ctrlWidget = None
    self.selectedOrientation = orientation
    self.layoutManager = slicer.app.layoutManager()
    self.orientations = ('Axial', 'Sagittal', 'Coronal')
    self.ctrlFrameSlider = None
    self.ctrlLevelSlider = None
    self.ctrlWindowSlider = None
    self.styleObserverTags = []

  def setup(self,wName,frameActiveFlag,parent):
    if self.ctrlWidget : 
      return
    
    # Hides the module panel so that viewer is of maximum size 
    # if sliceNodeList is not defined then it is the single viewer which does not have the module panel 
    if self.sliceNodeList: 
      modulePanel = slicer.util.findChildren(name='PanelDockWidget')
      if modulePanel: 
        modulePanel[0].hide()
      else : 
        print "Ignore 'Failed to obtain reference .. '"

    self.LinkViewers()
    self.numFrames = len(self.nodeImgList[0][0])

    if parent:
       self.ctrlWidget = parent
    else : 
       # Create seperate window 
       self.ctrlWidget=slicer.qMRMLWidget()
       self.ctrlWidget.setMRMLScene(slicer.mrmlScene)
       self.ctrlWidget.setLayout(qt.QFormLayout())

    self.ctrlWidget.setWindowTitle(wName) 
    ctrlLayout = self.ctrlWidget.layout()  

    # Create Slider Panel 
    self.sliderPanel=qt.QWidget()
    self.sliderPanel.setLayout(qt.QGridLayout())
    ctrlLayout.addWidget(self.sliderPanel)
    sliderLayout =  self.sliderPanel.layout()

    if self.numFrames > 1 or frameActiveFlag:  
      self.ctrlFrameLabel = qt.QLabel('Frame')
      self.ctrlFrameSlider = ctk.ctkSliderWidget()
      self.ctrlFrameSlider.connect('valueChanged(double)', self.onSliderFrameChanged)
      sliderLayout.addWidget(self.ctrlFrameLabel, 0, 0)
      sliderLayout.addWidget(self.ctrlFrameSlider, 0, 1)


    self.ctrlLevelLabel = qt.QLabel('Level')
    self.ctrlLevelSlider = ctk.ctkSliderWidget()
    self.ctrlLevelSlider.connect('valueChanged(double)', self.onSliderLevelChanged)
    sliderLayout.addWidget(self.ctrlLevelLabel, 1, 0)
    sliderLayout.addWidget(self.ctrlLevelSlider, 1, 1)

    self.ctrlWindowLabel = qt.QLabel('Window')
    self.ctrlWindowSlider = ctk.ctkSliderWidget()
    self.ctrlWindowSlider.connect('valueChanged(double)', self.onSliderWindowChanged)
    sliderLayout.addWidget(self.ctrlWindowLabel, 2, 0)
    sliderLayout.addWidget(self.ctrlWindowSlider, 2, 1)

    self.setSliderRangesAndValues()

    if self.sliceNodeList :
      self.orientPanel=qt.QWidget()
      self.orientPanel.setLayout(qt.QGridLayout())
      ctrlLayout.addWidget(self.orientPanel)

      self.orientationButtons = {}
      index=0
      for orientation in self.orientations:
        self.orientationButtons[orientation] = qt.QRadioButton()
        self.orientationButtons[orientation].text = orientation
        # self.orientationBox.layout().addWidget(self.orientationButtons[orientation])
        self.orientPanel.layout().addWidget(self.orientationButtons[orientation],0,index)
        self.orientationButtons[orientation].connect("clicked()",lambda o=orientation: self.setOrientation(o))
        index+=1

    self.setOrientation(self.selectedOrientation)

    if True:
      #self.plotFrame = ctk.ctkCollapsibleButton()
      #self.plotFrame.text = "Plotting"
      #self.plotFrame.collapsed = 0
      # f=ctk.ctkVTKChartView()
      # f.show()

      self.plotFrame=qt.QWidget()
      plotFrameLayout = qt.QGridLayout(self.plotFrame)
      ctrlLayout.addWidget(self.plotFrame)
     
      self.plotSettingsFrame = ctk.ctkCollapsibleButton()
      self.plotSettingsFrame.text = "Settings"
      self.plotSettingsFrame.collapsed = 1
      plotSettingsFrameLayout = qt.QGridLayout(self.plotSettingsFrame)
      #plotFrameLayout.addWidget(self.plotSettingsFrame,0,1)

      self.xLogScaleCheckBox = qt.QCheckBox()
      self.xLogScaleCheckBox.setChecked(0)

      self.yLogScaleCheckBox = qt.QCheckBox()
      self.yLogScaleCheckBox.setChecked(0)


      # taken from  https://github.com/fedorov/MultiVolumeExplorer
      self.__chartView = ctk.ctkVTKChartView(self.ctrlWidget) 
      # self.plotFrame)
      #  self.ctrlWidget 
      plotFrameLayout.addWidget(self.__chartView,0,0)

      self.__chart = self.__chartView.chart()
      self.__chartTable = vtk.vtkTable()
      self.__xArray = vtk.vtkFloatArray()
      self.__yArray = vtk.vtkFloatArray()
      # will crash if there is no name
      self.__xArray.SetName('')
      self.__yArray.SetName('signal intensity')
      self.__chartTable.AddColumn(self.__xArray)
      self.__chartTable.AddColumn(self.__yArray)

      self.onInputChanged()
      self.refreshObservers()

    self.buttonPanel=qt.QWidget()
    self.buttonPanel.setLayout(qt.QGridLayout())
    ctrlLayout.addWidget(self.buttonPanel)

    self.exitButton = qt.QPushButton("Exit")
    self.exitButton.toolTip = "Close down slicer."
    self.exitButton.name = "sviewer exit" 
    self.buttonPanel.layout().addWidget(self.exitButton,0,0)
    self.exitButton.connect('clicked()', exit)

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
    sWidgetList = [] 
    if self.sliceNodeList : 
      for snode in self.sliceNodeList.values() :
        sliceWidget = self.layoutManager.sliceWidget(snode.GetLayoutName())
        if sliceWidget:
           sWidgetList.append(sliceWidget)
    else:
      sWidgetList.append(self.singleViewerWidget)
   
    for sliceWidget in sWidgetList : 
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
    fgImages = self.nodeImgList[0]
    mvImage = fgImages[0]
    fgNodes = self.nodeList[0]

    nComponents = self.numFrames

    # TODO: use a timer to delay calculation and compress events
    if event == 'LeaveEvent':
      # reset all the readouts
      # TODO: reset the label text
      return

    if not self.sliceWidgetsPerStyle.has_key(observee):
      return

    print "update plot"
    sliceWidget = self.sliceWidgetsPerStyle[observee]
    sliceLogic = sliceWidget.sliceLogic()
    interactor = observee.GetInteractor()
    xy = interactor.GetEventPosition()
    xyz = sliceWidget.sliceView().convertDeviceToXYZ(xy);

    ras = sliceWidget.sliceView().convertXYZToRAS(xyz)
    # still set bgLayer  
    bgLayer = sliceLogic.GetForegroundLayer()
    # GetBackgroundLayer()
    fgLayer = sliceLogic.GetForegroundLayer()

    volumeNode = fgNodes[0]
    fgVolumeNode = fgNodes[0]
    if not volumeNode or volumeNode.GetID() != fgNodes[0].GetID():
      print "Do nothing"
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
      print "pixel outside the valid extent"

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
      # Kilian
      if False and fgijk[0] == ijk[0] and fgijk[1] == ijk[1] and fgijk[2] == ijk[2] and \
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
      val = mvImage[c].GetScalarComponentAsDouble(ijk[0],ijk[1],ijk[2],0)
      self.__chartTable.SetValue(c, 0, self.__mvLabels[c])
      self.__chartTable.SetValue(c, 1, val)
      print (c,val)
      if useFg:
        fgValue = fgImage.GetScalarComponentAsDouble(ijk[0],ijk[1],ijk[2],0)
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
    self.__chart.GetAxis(1).SetTitle("Hello")
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
      # self.plotFrame.collapsed = 0
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
        frame = v
        frameRange = frame.GetScalarRange()
        self.__mvRange[0] = min(self.__mvRange[0], frameRange[0])
        self.__mvRange[1] = max(self.__mvRange[1], frameRange[1])

      # self.__mvLabels = string.split(self.__mvNode.GetAttribute('MultiVolume.FrameLabels'),',')
      #if len(self.__mvLabels) != nFrames:
      #  return
      self.__mvLabels = []
      for l in range(self.numFrames):
        self.__mvLabels.append(float(l))

      # self.baselineFrames.maximum = self.numFrames


  def LinkViewers(self):
    if self.sliceNodeList:
      sliceNode = self.sliceNodeList.values()[0]
      sliceWidget = self.layoutManager.sliceWidget(sliceNode.GetLayoutName())
      sliceWidget.sliceController().setSliceLink(1)

  def onSliderFrameChanged(self,newValue):
    index=int(newValue)
    for vType in xrange(3):
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
    if self.sliceNodeList : 
      if orientation in self.orientations:
         self.selectedOrientation = orientation
         self.orientationButtons[orientation].checked = True
         for sliceNode in self.sliceNodeList.values():
            sliceNode.SetOrientation(orientation) 

  def setSliderRangesAndValues(self):
      if self.ctrlFrameSlider: 
         self.ctrlFrameSlider.minimum=0 
         self.ctrlFrameSlider.maximum=self.numFrames-1
         self.ctrlFrameSlider.value=0

      vImg = self.nodeImgList[0][0][0]
      vNode = self.nodeList[0][0]
      if vImg and vNode: 
        iRange=vImg.GetScalarRange()
        if  self.ctrlLevelSlider : 
          self.ctrlLevelSlider.minimum = iRange[0]
          self.ctrlLevelSlider.maximum = iRange[1] 
          self.ctrlLevelSlider.value=vNode.GetVolumeDisplayNode().GetLevel()

        if  self.ctrlWindowSlider:
          self.ctrlWindowSlider.minimum = iRange[0]
          self.ctrlWindowSlider.maximum = iRange[1]*1.5
          self.ctrlWindowSlider.value=vNode.GetVolumeDisplayNode().GetWindow()
   
  def setNodeListsAndDisplay(self,newNodeList,newNodeImgList,removeFlag):
    if removeFlag:
      for type in xrange(2):
        if self.nodeList[type] : 
          for node in self.nodeList[type] :
            dNode=node.GetVolumeDisplayNode()
            if dNode :
               slicer.mrmlScene.RemoveNode(dNode)

            slicer.mrmlScene.RemoveNode(node)

    self.nodeList = newNodeList 
    self.nodeImgList=newNodeImgList 
    self.numFrames = len(self.nodeImgList[0][0])
   
    # update display 
    if self.sliceNodeList : 
      index = 0 
      for vName in sorted(self.sliceNodeList.keys()):
        sNode = self.sliceNodeList[vName]
        sWidget = self.layoutManager.sliceWidget(sNode.GetLayoutName())
        sComposite=sWidget.sliceLogic().GetSliceCompositeNode()
        if self.nodeList[0] and (len(self.nodeList[0]) > index) and self.nodeList[0][index]: 
          sComposite.SetForegroundVolumeID(self.nodeList[0][index].GetID())
        else :
          sComposite.SetForegroundVolumeID("")

        if self.nodeList[1] and (len(self.nodeList[1]) > index) and self.nodeList[1][index]: 
          sComposite.SetBackgroundVolumeID(self.nodeList[1][index].GetID())
        else :
          sComposite.SetBackgroundVolumeID("")

        if self.nodeList[2] and (len(self.nodeList[2]) > index) and self.nodeList[2][index]: 
          sComposite.SetLabelVolumeID(self.nodeList[2][index].GetID())
        else :
          sComposite.SetLabelVolumeID("")

        sWidget.fitSliceToBackground()
        index += 1


    # update Slider ranges 
    self.setSliderRangesAndValues()


  
# Debug stuff 
# slicer.util.saveScene('/tmp/scene.mrml')
# dir(foregroundNode) returns all functions 
# [s for s in dir(blub) if "Get" in s]

# class MarkupsInViewsSelfTestWidget:
