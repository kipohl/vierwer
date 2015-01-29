#! /bin/bash -f
# A really quick image viewer (Slicer needs to be build in release build otherwise too slow 

SLICERSUPER=/software/Slicer4/releasebuild
# --no-main-window
CMD="${SLICERSUPER}/Slicer-build/Slicer --no-splash --disable-scripted-loadable-modules  --disable-cli-modules"
# CMD="$CMD --no-main-window"
if [ "$1" == "-i" ]; then 
  CMD="$CMD --show-python-interactor"
  shift
fi

$CMD --python-script ./sviewer.py $*

# --verbose-module-discovery 
#
