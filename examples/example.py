#!/usr/bin/env python3

import os
import re
import sys

os.environ["PYTHONUNBUFFERED"]="1"
cwd = os.getcwd()
upperLevelPath = os.path.dirname(cwd)
sys.path.append(upperLevelPath)
import libertyParser

################
# Main Process #
################
def main():
    libFile = './example.lib'
    print('')
    print('>>> Input file: ' + str(libFile))

    myLibertyParser = libertyParser.libertyParser(libFile)

    unitDic = myLibertyParser.getUnit()
    print('')
    print('>>> Unit:')
    print(unitDic)

    cellList = myLibertyParser.getCellList()
    print('')
    print('>>> Cell list:')
    print(cellList)

    cellAreaDic = myLibertyParser.getCellArea()
    print('')
    print('>>> Cell area:')
    print(cellAreaDic)

    cellLeakagePowerDic = myLibertyParser.getCellLeakagePower()
    print('')
    print('>>> Cell leakage_power')
    print(cellLeakagePowerDic)

    libPinDic = myLibertyParser.getLibPinInfo(cellList=['DFFX1'], pinList=['Q'])
    print('')
    print('>>> Lib pin info (cell="DFFX1", pin="Q"):')
    print(libPinDic)

if __name__ == '__main__':
    main()
