#!/bin/bash

### Debian/Ubuntu/Mint
sudo apt-get update -qq
sudo apt-get install -y gawk
sudo apt-get install -y gfortran
sudo apt-get install -y libopenblas-dev
sudo apt-get install -y liblapack-dev
sudo apt-get install -y libfftw3-dev libfftw3-doc
sudo apt-get install -y openmpi-bin openmpi-doc libopenmpi-dev
sudo apt-get install -y xterm
sudo apt-get install -y openbabel
sudo apt-get install -y jmol
sudo apt-get install -y python3-dev python3-pip python3-pyqt5 python3-pyqt5.qtsvg

### Python dependencies
# numpy>=2.0 required for np.trapezoid; --break-system-packages needed on Debian 12+
python3 -m pip install --break-system-packages 'numpy>=2.0' matplotlib pandas scipy
