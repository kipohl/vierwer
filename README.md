# viewer
Viewers based on  Slicer 4 enviornment
 

# Installation of sviewer with full functionality 

Step1) install bz2 in python
a) Look up location on local python
  import bz2
  bz2.__file__
  '/usr/lib/python2.7/lib-dynload/bz2.x86_64-linux-gnu.so

b) Look up dir in  Slicer python
  /software/Slicer4/releasebuild/python-install/bin/python
  import array
  array.__file__
 /software/Slicer4/releasebuild/python-install/lib/python2.7/lib-dynload/array.so

c) cp /usr/lib/python2.7/lib-dynload/bz2.x86_64-linux-gnu.so to /software/Slicer4/releasebuild/python-build/lib/python2.7/lib-dynload/bz2.so 

d) Test that it works 
 /software/Slicer4/releasebuild/python-install/bin/python -c "import bz2; print bz2.__doc__"

Step 2: install nibabel in python
a) download nibabel 1.3 
https://github.com/nipy/nibabel/archive/1.3.0.tar.gz
and untar 
b) go to nibabel directory and execute 
cd /data/software/nibabel-2.0.0/
 /software/Slicer4/releasebuild/python-install/bin/python setup.py install
c) /software/Slicer4/releasebuild/python-install/bin/python -c "import nibabel; print nibabel.__doc__"
 
Step 3: change slicer path in sviewer.sh 

 