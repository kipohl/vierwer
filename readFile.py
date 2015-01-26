import sys

# Execute the following to be able to import vtk
# if you use Slicer Reader ./runPyInsideSlimSlicer SLICER /readFile.py <filename> 
# if you use VTK Reader you can also  run ./runPy readFile.py  VTK <filename> 


def main():
  if len(sys.argv) < 3 :
      usage()

  MODE = str(sys.argv[1])
  INPUT = str(sys.argv[2])

  if MODE in ("VTK"):
    print "VTK"
    IMG = ReadImageVTK(INPUT)
  else:
    print "SLICER"
    IMG = ReadImageSlicer(INPUT)

  print (IMG.GetScalarRange())
  # this is the same as 
  # import vtk.util.numpy_support
  # a = vtk.util.numpy_support.vtk_to_numpy(i.GetPointData().GetScalars())
  # print(a.min(),a.max())

  print " " 
  print "===== Done ====" 
  sys.exit(' ') 
  # DONE    
    
def ReadImageSlicer(FileName): 
  import slicer
  mrml = slicer.vtkMRMLScene()
  vl = slicer.vtkSlicerVolumesLogic()
  vl.SetAndObserveMRMLScene(mrml)
  n = vl.AddArchetypeVolume(FileName,'CTC')
  i = n.GetImageData()
  return i


def ReadImageVTK(FileName): 
  # import vtk
  import vtkITK  
  READER = vtkITK.vtkITKArchetypeImageSeriesScalarReader() 
  READER.SetUseOrientationFromFile(True)
  READER.SetUseNativeOriginOn();
  READER.SetOutputScalarTypeToNative()
  READER.SetDesiredCoordinateOrientationToNative()
  READER.SetArchetype(FileName)
  if READER.CanReadFile(FileName) == 0 :
    print "ERROR:ITK_Generic_Reader: Cannot read " + FileName
    sys.exit(' ')    

  READER.Update()

  return READER.GetOutput() 
  
def usage():

    print ' -------------------------------------------------------------------------'
    print ' Reads image file '
    print ' Usage: readFile.py <mode> <filename>  '
    print ' example: ./statistics.py VTK white.nrrd'
    print ' -------------------------------------------------------------------------'
    sys.exit(' ')

#-------------------------------
if __name__ == "__main__":
    main()
