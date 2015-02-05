##
##  Copyright 2012-2015 SRI International
##
##  http://nitrc.org/projects/ncanda-datacore/
##
##  This file is part of the N-CANDA Data Component Software Suite, developed
##  and distributed by the Data Integration Component of the National
##  Consortium on Alcohol and NeuroDevelopment in Adolescence, supported by
##  the U.S. National Institute on Alcohol Abuse and Alcoholism (NIAAA) under
##  Grant No. 1U01 AA021697
##
##  The N-CANDA Data Component Software Suite is free software: you can
##  redistribute it and/or modify it under the terms of the GNU General Public
##  License as published by the Free Software Foundation, either version 3 of
##  the License, or (at your option) any later version.
##
##  The N-CANDA Data Component Software Suite is distributed in the hope that it
##  will be useful, but WITHOUT ANY WARRANTY; without even the implied
##  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with the N-CANDA Data Component Software Suite.  If not, see
##  <http://www.gnu.org/licenses/>.
##

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

 