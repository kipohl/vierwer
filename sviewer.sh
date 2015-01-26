#! /bin/bash -f
# A really quick image viewer (Slicer needs to be build in release build otherwise too slow 

SLICERSUPER=/software/Slicer4/releasebuild

CMD="${SLICERSUPER}/Slicer-build/Slicer --disable-scripted-loadable-modules --no-main-window --disable-cli-modules"

if [ "$1" == "-i" ]; then 
  CMD="$CMD --show-python-interactor"
  shift
fi

$CMD --python-script ./sviewer.py $*

# --verbose-module-discovery 
#
