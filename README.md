# viewer
Viewers based on  Slicer 4 enviornment

run ./sviewer <TYPE> <options>
 
Installation of sviewer with full functionality 

Step 0) define slicer in sviewer.sh   

Step1) install bz2 in Slicer's Python Installation -script below works in python
a) Look up location of bz2 file on local python
  python -c "import bz2; print bz2.__file__"

b) Look up dir in Slicer python
  Slicer-build/Slicer --xterm
  DIR=`dirname $(${PYTHONHOME}/bin/python -c "import  array; print array.__file__")` 

c) cp <FILE of Step a)> ${DIR}/bz2.so 
   e.g. cp /usr/lib/python2.7/lib-dynload/bz2.x86_64-linux-gnu.so ${DIR}/bz2.so 
d) Test that it works 
   ${PYTHONHOME}/bin/python -c "import bz2; print bz2.__doc__"

Step 2: install nibabel in python
a) download nibabel 1.3 
https://github.com/nipy/nibabel/archive/1.3.0.tar.gz
and untar 
b) go to nibabel directory and execute 
  cd /data/software/nibabel-1.3.0/
  ${PYTHONHOME}/bin/python setup.py install
c) ${PYTHONHOME}/bin/python -c "import nibabel; print nibabel.__doc__"
 
Step 3: change slicer path in sviewer.sh 

 