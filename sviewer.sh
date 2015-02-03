#! /bin/bash -f
# Just the viewer of slicer 
# call ./sviewer <TYPE> Options
# TYPE: lite, single, compare, cases 
SLICER="/software/Slicer4/releasebuild/Slicer-build/Slicer"
CMD="$SLICER --no-splash --disable-scripted-loadable-modules  --disable-cli-modules"

if [ "$1" == "-h" -o "$1" == "--help" ]; then 
   echo "Simple viewers based on slicer enviornment. There are 4 different sviewer currently installed :"
   echo "  lite : simplest of the viewer - currently still in development"
   echo "  single : shows foreground, background, labelmap MR in a single view"
   echo "  compare : shows multiple MRs next to each other"
   echo "  cases: creates a comparison view for each case / modality defined in a list" 
   echo "To find out more about the different viewer call "
   echo "  sviewer <Viewer Type> -h  = brief help "
   echo "  sviewer <Viewer Type> --help_all  = more detailed help"
   exit
fi

TYPE=$1
shift 

PYTHON_FILE=`dirname $0`/${TYPE}Viewer.py

if [ ! -e ${PYTHON_FILE} ]; then 
  echo "Error: viewer type '${TYPE}' does not exist! Run `dirname $0`/sviewer.sh -h to get a listing of the viewers."
  exit
fi  
 
if [ "$TYPE" == "lite" -o "$TYPE" == "single" -o "$1" == "--help_all" ]; then 
 CMD="${CMD} --no-main-window"
fi 

if [ "$1" == "-i" ]; then 
  CMD="$CMD --show-python-interactor"
  shift
fi

if [ "$1" == "-h" -o "$1" == "--help" ]; then  
  $CMD --no-main-window --python-script ${PYTHON_FILE}
else 
  $CMD --python-script ${PYTHON_FILE} $*
fi 
