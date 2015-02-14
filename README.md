## viewer - a lightweight medical imaging viewer using 3D Slicer

### Example Usage

```
./sviewer <TYPE> <options>

Simple viewers based on slicer environment. There are 4 different sviewer currently installed :
  lite : simplest of the viewer - currently still in development
  single : shows foreground, background, labelmap MR in a single view
  compare : shows multiple MRs next to each other
  cases: creates a comparison view for each case / modality defined in a list
To find out more about the different viewer call 
  sviewer <Viewer Type> -h  = brief help 
  sviewer <Viewer Type> --help_all  = more detailed help
```
 
### Installation of sviewer with full functionality 

1. Define path to slicer using the SLICER environment variable in sviewer.sh   
2. Install bz2 in Slicer's Python Installation - script below works in python
    
    a. Look up location of bz2 file on local python
      
        ```
        BZFILE=`python -c "import bz2; print bz2.__file__"`
        ```
    
    b. Find where Slicer stores python shared libs
        
        ```
        cd <path_to>/Slicer-build/Slicer --xterm
        LIBDIR=`dirname $(${PYTHONHOME}/bin/python -c "import  array; print array.__file__")`
        
        # on Mac
        LIBDIR=`dirname $(/Applications/Slicer.app/Contents/bin/SlicerPython -c "import  array; print array.__file__")`
        ```
        
    c. Copy bz2 into Slicer 
        
        ```
        cp ${BZFILE} ${LIBDIR}/bz2.so
        # e.g., cp /usr/lib/python2.7/lib-dynload/bz2.x86_64-linux-gnu.so ${DIR}/bz2.so
        ```
        
    d. Test that it works
        
        ```
        ${PYTHONHOME}/bin/python -c "import bz2; print bz2.__doc__"
        ```

3. install nibabel in python

    a. Download nibabel 1.3
        
        ```
        wget https://github.com/nipy/nibabel/archive/1.3.0.tar.gz
        tar -xvzf 1.3.0.tar.gz
        ```
         
    b. Go to nibabel directory and execute 
  
        ```
        cd /data/software/nibabel-1.3.0/
        ${PYTHONHOME}/bin/python setup.py install
        ```
    c. Verify nibabel install
        
        ```
        ${PYTHONHOME}/bin/python -c "import nibabel; print nibabel.__doc__"
        ```
        
4. Change slicer path in sviewer.sh 
 
**Copyright 2012-2015 SRI International**  
<http://nitrc.org/projects/ncanda-datacore/>  
This file is part of the N-CANDA Data Component Software Suite, developed
and distributed by the Data Integration Component of the National
Consortium on Alcohol and NeuroDevelopment in Adolescence, supported by
the U.S. National Institute on Alcohol Abuse and Alcoholism (NIAAA) under
Grant No. 1U01 AA021697  
The N-CANDA Data Component Software Suite is free software: you can
redistribute it and/or modify it under the terms of the GNU General Public
License as published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.  
The N-CANDA Data Component Software Suite is distributed in the hope that it
will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.  
You should have received a copy of the GNU General Public License along
with the N-CANDA Data Component Software Suite. If not, see 
<http://www.gnu.org/licenses/>.

 