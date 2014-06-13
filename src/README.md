LogikSim Source
===============

To run LogikSim from source run: ```main.py```

The test suit can be run with:
```
Unix:    python3 -m unittest discover --patten="*_spec.py"
Windows: py -3 -m unittest discover --patten="*_spec.py"
```


Dependencies
============

Under Linux the dependencies can usually be installed via the
package manager. For Ubuntu run:
```
sudo apt-get install python3-pyside
```

On Windows the depencies have to be installed manually.

### Python 3 ###

The main source code interpreter.

http://python.org

*tested with version 3.4.1*

### PySide ###

Python bindings of the cross-platform GUI toolkit Qt.

http://www.pyside.org/

*tested with version 1.2.2*

## cx_Freeze (optional) ##

Python extension to convert Python scripts into executables.
It is only needed to build installers on Windows.

http://cx-freeze.sourceforge.net/

*tested with version 4.3.3 from
http://www.lfd.uci.edu/~gohlke/pythonlibs/#cx_freeze*


Installer
=========

We provide installer for Windows. It can be build by running:
```
py setup.py build
```

To run the executable the Microsoft Visual C++ Redistributable Package
has to be installed:
- 32bit: http://www.microsoft.com/en-us/download/details.aspx?id=5555
- 64bit: http://www.microsoft.com/en-us/download/details.aspx?id=14632

