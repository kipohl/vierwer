#! /bin/bash -f
# Just the viewer of slicer 
# call ./sviewer <TYPE> Options
# TYPE: lite, single, compare, cases 
SLICER="/software/Slicer4/releasebuild/Slicer-build/Slicer"
CMD="$SLICER --no-splash --disable-scripted-loadable-modules  --disable-cli-modules"
TYPE=$1
shift 
if [ "$TYPE" == "lite" -o "$TYPE" == "single" ]; then 
 CMD="${CMD} --no-main-window"
fi 

if [ "$1" == "-i" ]; then 
  CMD="$CMD --show-python-interactor"
  shift
fi

$CMD --python-script `dirname $0`/${TYPE}Viewer.py $*
