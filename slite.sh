#! /bin/bash -f
# A really quick image viewer (Slicer needs to be build in release build otherwise too slow - just provide file names 
# ./slite.sh <file 1> <file 2> ... 
# and it creates a viewer for each file 

SLICERSUPER=/software/Slicer4/releasebuild
${SLICERSUPER}/Slicer-build/Slicer --disable-scripted-loadable-modules --no-main-window --disable-cli-modules --show-python-interactor --python-script ./slite.py $*
# --verbose-module-discovery 
