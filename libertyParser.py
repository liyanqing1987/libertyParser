import os
import re
import sys
import time
import datetime
import collections

os.environ["PYTHONUNBUFFERED"] = "1"


def openWrite(fileName, message):
    with open(fileName, 'a') as FN:
        FN.write(str(message) + '\n')


# Liberty parser (start) #
class libertyParser():
    """
    Parse liberty file and save a special dictionary data structure.
    Get specified data with sub-function "getData".
    """
    def __init__(self, libFile, cellList=[], debug=False):
        self.debug = debug

        self.debugPrint('* Liberty File : ' + str(libFile))

        # Liberty file must exists.
        if not os.path.exists(libFile):
            print('*Error*: liberty file "' + str(libFile) + '": No such file!')
            sys.exit(1)

        # If cellList is specified, regenerate the cell-based liberty file as libFile.
        if len(cellList) > 0:
            self.debugPrint('* Specified Cell List : ' + str(cellList))
            libFile = self.genCellLibFile(libFile, cellList)

        # Parse the liberty file and organize the data structure as a dictionary.
        groupList = self.libertyParser(libFile)
        self.libDic = self.organizeData(groupList)

    def debugPrint(self, message):
        """
        Print debug message.
        """
        if self.debug:
            currentTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print('DEBUG [' + str(currentTime) + ']: ' + str(message))

    def genCellLibFile(self, libFile, cellList):
        """
        For big liberty files with multi-cells, it will cost too much time to parse the liberty file.
        This function is used to generate a new liberty file only contains the specified cells, so it can save a lot of time on liberty file parsering.
        """
        cellNames = '_'.join(cellList)
        cellLibFile = str(libFile) + '.' + str(cellNames)
        self.debugPrint('>>> Generating cell-based liberty file "' + str(cellLibFile) + '" ...')

        libCellDic = collections.OrderedDict()
        libCellList = []

        # Get lineNum-cellName info on libFile.
        self.debugPrint('    Getting cells from liberty file "' + str(libFile) + '" ...')
        cellCompile = re.compile(r'^\s*(\d+):\s*cell\s*\((.*)\)\s*{\s*$')
        lines = os.popen('grep -n "cell (" ' + str(libFile)).readlines()

        for line in lines:
            line = line.strip()

            if cellCompile.match(line):
                myMatch = cellCompile.match(line)
                lineNum = myMatch.group(1)
                cellName = myMatch.group(2)
                libCellDic[cellName] = lineNum
                libCellList.append(cellName)

        # Make sure all the specified cells are on libFile.
        self.debugPrint('    Check specified cells missing or not.')
        cellMissing = False

        for cell in cellList:
            if cell not in libCellList:
                print('*Error*: cell "' + str(cell) + '" is not in liberty file "' + str(libFile) + '".')
                cellMissing = True

        if cellMissing:
            sys.exit(1)

        # Write cellLibFile - head part.
        firstCellLineNum = libCellDic[libCellList[0]]
        self.debugPrint('    Writing cell liberty file head part ...')
        command = "awk 'NR>0 && NR<" + str(firstCellLineNum) + "' " + str(libFile) + " > " + str(cellLibFile)
        os.system(command)

        # Write cellLibFile - cell part.
        for cell in cellList:
            cellFirstLineNum = libCellDic[cell]
            cellLastLineNum = 0
            cellIndex = libCellList.index(cell)

            if cellIndex == len(libCellList) - 1:
                cellLastLineNum = os.popen("wc -l " + str(libFile) + " | awk '{print $1}'").read().strip()
            else:
                nextCellIndex = cellIndex + 1
                nextCell = libCellList[nextCellIndex]
                cellLastLineNum = int(libCellDic[nextCell]) - 1

            self.debugPrint('    Writing cell liberty file cell "' + str(cell) + '" part ...')
            command = "awk 'NR>=" + str(cellFirstLineNum) + " && NR<=" + str(cellLastLineNum) + "' " + str(libFile) + " >> " + str(cellLibFile)
            os.system(command)

        with open(cellLibFile, 'a') as CLF:
            CLF.write('}\n')

        return cellLibFile

    def getLastOpenedGroupNum(self, openedGroupNumList):
        """
        All of the new attribute data are saved on last opened group, so need to get the last opened group num.
        """
        lastOpenedGroupNum = -1

        if len(openedGroupNumList) > 0:
            lastOpenedGroupNum = openedGroupNumList[-1]

        return lastOpenedGroupNum

    def libertyParser(self, libFile):
        """
        Parse liberty file line in line.
        Save data block based on "group".
        Save data blocks into a list.
        """
        # compile #
        # Group compile.
        # type (name) {
        #   ...
        # }
        groupCompile = re.compile(r'^(\s*)(\S+)\s*\((.*?)\)\s*{\s*$')
        groupDoneCompile = re.compile(r'^\s*}\s*$')

        # Simple attribute compile.
        # key : value;
        simpleAttributeCompile = re.compile(r'^(\s*)(\S+)\s*:\s*(.+)\s*;.*$')
        specialSimpleAttributeCompile = re.compile(r'^(\s*)(\S+)\s*:\s*(.+)\s*$')

        # Complex attribute compile.
        # key (valueList);
        complexAttributeCompile = re.compile(r'^(\s*)(\S+)\s*(\(.+\))\s*;.*$')
        specialComplexAttributeCompile = re.compile(r'^(\s*)(\S+)\s*(\(.+\))\s*$')

        # Multi lines compile.
        # *** \
        # *** \
        # ***;
        multiLinesCompile = re.compile(r'^(.*)\\\s*$')
        multiLinesDoneCompile = re.compile(r'^(.*;)\s*$')

        # Comment compile.
        # /* ... */
        commentStartCompile = re.compile(r'^(\s*)/\*.*$')
        commentEndCompile = re.compile(r'^.*\*/\s*$')

        # Empty line compile.
        emptyLineCompile = re.compile(r'^\s*$')

        # For multi lines.
        multiLinesString = ''

        # For comment (multi-lines).
        commentMark = False

        # Save group data structure into groupList.
        groupList = []
        groupListNum = 0

        # Save opened group list.
        openedGroupNumList = []

        # Last opened group num on groupList, point to the latest open group.
        lastOpenedGroupNum = -1

        self.debugPrint('>>> Parsing liberty file "' + str(libFile) + '" ...')
        startSeconds = int(time.time())
        libFileLine = 0

        with open(libFile, 'r') as LF:
            for line in LF.readlines():
                libFileLine += 1

                # Sort by compile hit rate.
                if commentMark:
                    if commentEndCompile.match(line):
                        commentMark = False
                else:
                    if multiLinesCompile.match(line):
                        myMatch = multiLinesCompile.match(line)
                        currentLineContent = myMatch.group(1)
                        multiLinesString = str(multiLinesString) + str(currentLineContent)
                    else:
                        if multiLinesString:
                            if multiLinesDoneCompile.match(line):
                                myMatch = multiLinesDoneCompile.match(line)
                                currentLineContent = myMatch.group(1)
                                line = str(multiLinesString) + str(currentLineContent)
                            else:
                                print('*Error*: Line ' + str(libFileLine) + ': multi-lines is not finished rightly!')
                                print('         ' + str(line))
                                continue

                        if complexAttributeCompile.match(line):
                            myMatch = complexAttributeCompile.match(line)
                            key = myMatch.group(2)
                            valueList = myMatch.group(3)

                            if key in groupList[lastOpenedGroupNum]:
                                # For "voltage_map" or such kind items (there are some "voltage_map" on the same group).
                                if isinstance(groupList[lastOpenedGroupNum][key], list):
                                    groupList[lastOpenedGroupNum][key].append(valueList)
                                else:
                                    groupList[lastOpenedGroupNum][key] = [groupList[lastOpenedGroupNum][key], valueList]
                            else:
                                groupList[lastOpenedGroupNum][key] = valueList
                        elif simpleAttributeCompile.match(line):
                            myMatch = simpleAttributeCompile.match(line)
                            key = myMatch.group(2)
                            value = myMatch.group(3)
                            groupList[lastOpenedGroupNum][key] = value
                        elif groupCompile.match(line):
                            myMatch = groupCompile.match(line)
                            groupDepth = len(myMatch.group(1))
                            groupType = myMatch.group(2)
                            groupName = myMatch.group(3)

                            (lastOpenedGroupNum) = self.getLastOpenedGroupNum(openedGroupNumList)

                            currentGroupDic = {
                                               'fatherGroupNum': lastOpenedGroupNum,
                                               'depth': groupDepth,
                                               'type': groupType,
                                               'name': groupName,
                                              }

                            groupList.append(currentGroupDic)
                            openedGroupNumList.append(groupListNum)
                            groupListNum += 1
                            (lastOpenedGroupNum) = self.getLastOpenedGroupNum(openedGroupNumList)
                        elif groupDoneCompile.match(line):
                            openedGroupNumList.pop()
                            (lastOpenedGroupNum) = self.getLastOpenedGroupNum(openedGroupNumList)
                        elif commentStartCompile.match(line):
                            if not commentEndCompile.match(line):
                                commentMark = True
                        elif emptyLineCompile.match(line):
                            pass
                        elif specialComplexAttributeCompile.match(line):
                            print('*Warning*: Line ' + str(libFileLine) + ': Irregular liberty line!')
                            print('          ' + str(line))
                            myMatch = specialComplexAttributeCompile.match(line)
                            key = myMatch.group(2)
                            valueList = myMatch.group(3)

                            if key in groupList[lastOpenedGroupNum]:
                                # For "voltage_map" or such kind items (there are some "voltage_map" on the same group).
                                if isinstance(groupList[lastOpenedGroupNum][key], list):
                                    groupList[lastOpenedGroupNum][key].append(valueList)
                                else:
                                    groupList[lastOpenedGroupNum][key] = [groupList[lastOpenedGroupNum][key], valueList]
                            else:
                                groupList[lastOpenedGroupNum][key] = valueList
                        elif specialSimpleAttributeCompile.match(line):
                            print('*Warning*: Line ' + str(libFileLine) + ': Irregular line!')
                            print('          ' + str(line))
                            myMatch = specialSimpleAttributeCompile.match(line)
                            key = myMatch.group(2)
                            value = myMatch.group(3)
                            groupList[lastOpenedGroupNum][key] = value
                        else:
                            print('*Error*: Line ' + str(libFileLine) + ': Unrecognizable line!')
                            print('         ' + str(line))

                        if multiLinesString:
                            multiLinesString = ''

        endSeconds = int(time.time())
        parseSeconds = endSeconds - startSeconds
        self.debugPrint('    Done')
        self.debugPrint('    Parse time : ' + str(libFileLine) + ' lines, ' + str(parseSeconds) + ' seconds.')

        return groupList

    def organizeData(self, groupList):
        """
        Re-organize list data structure (groupList) into a dictionary data structure.
        """
        self.debugPrint('>>> Re-organizing data structure ...')

        for i in range(len(groupList)-1, 0, -1):
            groupDic = groupList[i]
            fatherGroupNum = groupDic['fatherGroupNum']
            groupList[fatherGroupNum].setdefault('group', [])
            groupList[fatherGroupNum]['group'].insert(0, groupDic)

        self.debugPrint('    Done')

        return groupList[0]
# Liberty parser (end) #

# Verification functions (start) #
    def restoreLib(self, libFile, groupDic=''):
        """
        This function is used to verify the liberty parser.
        It converts self.libDic into the original liberty file (comment will be ignored).
        Please save the output message into a file, then compare it with the original liberty file.
        """
        if groupDic == '':
            groupDic = self.libDic

        groupDepth = groupDic['depth']
        groupType = groupDic['type']
        groupName = groupDic['name']

        openWrite(libFile, ' '*groupDepth + str(groupType) + ' (' + str(groupName) + ') {')

        for key in groupDic:
            value = groupDic[key]

            if (key == 'fatherGroupNum') or (key == 'depth') or (key == 'type') or (key == 'name'):
                pass
            elif key == 'group':
                subGroupList = groupDic['group']
                for subGroup in subGroupList:
                    self.restoreLib(libFile, subGroup)
            elif key == 'values':
                openWrite(libFile, '  ' + ' '*groupDepth + key + ' ( \\')
                valueString = re.sub(r'\(', '', value)
                valueString = re.sub(r'\)', '', valueString)
                valueString = re.sub(r'"\s*,\s*"', '"#"', valueString)
                valuesList = re.split('#', valueString)

                for i in range(len(valuesList)):
                    item = valuesList[i].strip()

                    if i == len(valuesList)-1:
                        openWrite(libFile, '    ' + ' '*groupDepth + str(item) + ' \\')
                    else:
                        openWrite(libFile, '    ' + ' '*groupDepth + str(item) + ', \\')

                openWrite(libFile, '  ' + ' '*groupDepth + ');')
            elif key == 'table':
                valueString = re.sub(r'"', '', value)
                valueList = re.split(',', valueString)
                openWrite(libFile, '  ' + ' '*groupDepth + key + ' : "' + str(valueList[0]) + ', \\')

                for i in range(1, len(valueList)):
                    item = valueList[i].strip()

                    if i == len(valueList)-1:
                        openWrite(libFile, str(item) + '";')
                    else:
                        openWrite(libFile, str(item) + ', \\')
            elif isinstance(value, list):
                for item in value:
                    if re.match(r'\(.*\)', item):
                        if key == 'define':
                            openWrite(libFile, '  ' + ' '*groupDepth + key + str(item) + ';')
                        else:
                            openWrite(libFile, '  ' + ' '*groupDepth + key + ' ' + str(item) + ';')
                    else:
                        openWrite(libFile, '  ' + ' '*groupDepth + key + ' : ' + str(item) + ';')
            else:
                if re.match(r'\(.*\)', value):
                    openWrite(libFile, '  ' + ' '*groupDepth + key + ' ' + str(value) + ';')
                else:
                    openWrite(libFile, '  ' + ' '*groupDepth + key + ' : ' + str(value) + ';')

        openWrite(libFile, ' '*groupDepth + '}')
# Verification functions (end) #

# Application functions (start) #
    def getUnit(self):
        """
        Get all "unit" setting.
        Return a dict.
        {
         name1 : unit1,
         name2 : unit2,
         ...
        }
        """
        unitDic = collections.OrderedDict()

        for key in self.libDic.keys():
            if re.match(r'.*_unit', key):
                value = self.libDic[key]
                unitDic[key] = value

        return unitDic

    def getCellList(self):
        """
        Get all cells.
        Return a list.
        [cellName1, cellName2, ...]
        """
        cellList = []

        if 'group' in self.libDic:
            for libGroupDic in self.libDic['group']:
                groupType = libGroupDic['type']

                if groupType == 'cell':
                    cellName = libGroupDic['name']
                    cellList.append(cellName)

        return cellList

    def getCellArea(self, cellList=[]):
        """
        Get cell area information for specified cell list.
        Return a dict.
        {
         cellName1 : area1,
         cellName2 : area2,
         ...
        }
        """
        cellAreaDic = collections.OrderedDict()

        if 'group' in self.libDic:
            for groupDic in self.libDic['group']:
                groupType = groupDic['type']

                if groupType == 'cell':
                    cellName = groupDic['name']

                    if (len(cellList) == 0) or (cellName in cellList):
                        if 'area' in groupDic:
                            cellArea = groupDic['area']
                            cellAreaDic[cellName] = cellArea

        for cellName in cellList:
            if cellName not in cellAreaDic:
                cellAreaDic[cellName] = ''

        return cellAreaDic

    def getCellLeakagePower(self, cellList=[]):
        """
        Get cell leakage_power information for specified cell list.
        Return a dict.
        {
         cellName1 : [
                      {
                       'value' : value,
                       'when' : when,
                       'related_pg_pin' : related_pg_pin,
                      }
                      ...
                     ],
         ...
        }
        """
        cellLeakagePowerDic = collections.OrderedDict()

        if 'group' in self.libDic:
            for groupDic in self.libDic['group']:
                groupType = groupDic['type']

                if groupType == 'cell':
                    cellName = groupDic['name']

                    if (len(cellList) == 0) or (cellName in cellList):
                        if 'group' in groupDic:
                            for cellGroupDic in groupDic['group']:
                                cellGroupType = cellGroupDic['type']

                                if cellGroupType == 'leakage_power':
                                    leakagePowerDic = {}

                                    for (key, value) in cellGroupDic.items():
                                        if (key == 'value') or (key == 'when') or (key == 'related_pg_pin'):
                                            leakagePowerDic[key] = value

                                    cellLeakagePowerDic.setdefault(cellName, [])
                                    cellLeakagePowerDic[cellName].append(leakagePowerDic)

        return cellLeakagePowerDic

    def _getTimingGroupInfo(self, groupDic):
        """
        Split pin timing information from the pin timing dict.
        Return a dict.
        {
         'related_pin' : related_pin,
         'related_pg_pin' : related_pg_pin,
         'timing_sense' : timing_sense,
         'timing_type' : timing_type,
         'when' : when,
         'table_type' : {
                         table_type1 : {
                                        'index_1' : [index1],
                                        'index_2' : [index2],
                                        'values' : [[values]],
                                       }
                         ...
                        },
        }
        """
        timingDic = collections.OrderedDict()

        if 'type' in groupDic:
            groupType = groupDic['type']

            if groupType == 'timing':
                if 'related_pin' in groupDic:
                    timingDic['related_pin'] = groupDic['related_pin']

                if 'related_pg_pin' in groupDic:
                    timingDic['related_pg_pin'] = groupDic['related_pg_pin']

                if 'timing_sense' in groupDic:
                    timingDic['timing_sense'] = groupDic['timing_sense']

                if 'timing_type' in groupDic:
                    timingDic['timing_type'] = groupDic['timing_type']

                if 'when' in groupDic:
                    timingDic['when'] = groupDic['when']

                if 'group' in groupDic:
                    timingDic['table_type'] = collections.OrderedDict()

                    for timingLevelGroupDic in groupDic['group']:
                        timingLevelGroupType = timingLevelGroupDic['type']
                        timingLevelGroupName = timingLevelGroupDic['name']
                        timingDic['table_type'][timingLevelGroupType] = collections.OrderedDict()

                        if timingLevelGroupName != '':
                            timingDic['table_type'][timingLevelGroupType]['template_name'] = timingLevelGroupName

                        if 'sigma_type' in timingLevelGroupDic:
                            # 'sigma_type' is only for ocv lib.
                            timingDic['table_type'][timingLevelGroupType]['sigma_type'] = timingLevelGroupDic['sigma_type']

                        if 'index_1' in timingLevelGroupDic:
                            timingDic['table_type'][timingLevelGroupType]['index_1'] = timingLevelGroupDic['index_1']

                        if 'index_2' in timingLevelGroupDic:
                            timingDic['table_type'][timingLevelGroupType]['index_2'] = timingLevelGroupDic['index_2']

                        if 'values' in timingLevelGroupDic:
                            timingDic['table_type'][timingLevelGroupType]['values'] = timingLevelGroupDic['values']

        return timingDic

    def _getInternalPowerGroupInfo(self, groupDic):
        """
        Split pin internal_power information from the pin internal_power dict.
        Return a dict.
        {
         'related_pin' : related_pin,
         'related_pg_pin' : related_pg_pin,
         'when' : when,
         'table_type' : {
                         table_type1 : {
                                        'index_1' : [index1],
                                        'index_2' : [index2],
                                        'values' : [[values]],
                                       }
                         ...
                        },
        }
        """
        internalPowerDic = collections.OrderedDict()

        if 'type' in groupDic:
            groupType = groupDic['type']

            if groupType == 'internal_power':
                if 'related_pin' in groupDic:
                    internalPowerDic['related_pin'] = groupDic['related_pin']

                if 'related_pg_pin' in groupDic:
                    internalPowerDic['related_pg_pin'] = groupDic['related_pg_pin']

                if 'when' in groupDic:
                    internalPowerDic['when'] = groupDic['when']

                if 'group' in groupDic:
                    internalPowerDic['table_type'] = collections.OrderedDict()

                    for internalPowerLevelGroupDic in groupDic['group']:
                        internalPowerLevelGroupType = internalPowerLevelGroupDic['type']
                        internalPowerDic['table_type'][internalPowerLevelGroupType] = collections.OrderedDict()

                        if 'index_1' in internalPowerLevelGroupDic:
                            internalPowerDic['table_type'][internalPowerLevelGroupType]['index_1'] = internalPowerLevelGroupDic['index_1']

                        if 'index_2' in internalPowerLevelGroupDic:
                            internalPowerDic['table_type'][internalPowerLevelGroupType]['index_2'] = internalPowerLevelGroupDic['index_2']

                        if 'values' in internalPowerLevelGroupDic:
                            internalPowerDic['table_type'][internalPowerLevelGroupType]['values'] = internalPowerLevelGroupDic['values']

        return internalPowerDic

    def _getPinInfo(self, groupDic):
        """
        Split cell pin timing/internal_power information from pin dict.
        Return a dict.
        {
         'timing' : [timingDic1, timingDic2, ...],
         'internal_power' : [internalPowerDic1, internalPowerDic2, ...],
        }
        """
        pinDic = collections.OrderedDict()

        if 'type' in groupDic:
            groupType = groupDic['type']

            if groupType == 'pin':
                if 'group' in groupDic:
                    for pinGroupDic in groupDic['group']:
                        pinGroupType = pinGroupDic['type']

                        if pinGroupType == 'timing':
                            timingDic = self._getTimingGroupInfo(pinGroupDic)
                            pinDic.setdefault('timing', [])
                            pinDic['timing'].append(timingDic)
                        elif pinGroupType == 'internal_power':
                            internalPowerDic = self._getInternalPowerGroupInfo(pinGroupDic)
                            pinDic.setdefault('internal_power', [])
                            pinDic['internal_power'].append(internalPowerDic)

        return pinDic

    def _getBundleInfo(self, groupDic, pinList=[]):
        """
        Split bundle pin timing/internal_power information from the bundle dict.
        Return a dict.
        {
         'pin' : {
                  pinName1 : {
                              'timing' : [timingDic1, timingDic2, ...],
                              'internal_power' : [internalPowerDic1, internalPowerDic2, ...],
                             },
                  pinName2 : {
                              'timing' : [timingDic1, timingDic2, ...],
                              'internal_power' : [internalPowerDic1, internalPowerDic2, ...],
                             },
                  ...
                 }
        }
        """
        bundleDic = collections.OrderedDict()

        if 'members' in groupDic:
            pinListString = groupDic['members']
            pinListString = re.sub(r'\(', '', pinListString)
            pinListString = re.sub(r'\)', '', pinListString)
            pinListString = re.sub(r'"', '', pinListString)
            pinList = pinListString.split(',')

            for pinName in pinList:
                pinName = pinName.strip()
                bundleDic.setdefault('pin', collections.OrderedDict())
                bundleDic['pin'].setdefault(pinName, collections.OrderedDict())

        if 'group' in groupDic:
            for groupDic in groupDic['group']:
                groupType = groupDic['type']

                if groupType == 'pin':
                    pinName = groupDic['name']

                    if (len(pinList) > 0) and (pinName not in pinList):
                        continue

                    bundleDic.setdefault('pin', collections.OrderedDict())
                    bundleDic['pin'].setdefault(pinName, collections.OrderedDict())
                    pinDic = self._getPinInfo(groupDic)

                    if pinDic:
                        bundleDic['pin'][pinName] = pinDic
                elif groupType == 'timing':
                    timingDic = self._getTimingGroupInfo(groupDic)
                    bundleDic.setdefault('timing', [])
                    bundleDic['timing'].append(timingDic)
                elif groupType == 'internal_power':
                    internalPowerDic = self._getInternalPowerGroupInfo(groupDic)
                    bundleDic.setdefault('internal_power', [])
                    bundleDic['internal_power'].append(internalPowerDic)

        return bundleDic

    def _getBusInfo(self, groupDic, pinList=[]):
        """
        Split bus pin timing/internal_power information from the bus dict.
        Return a dict.
        {
         'pin' : {
                  pinName1 : {
                              'timing' : [timingDic1, timingDic2, ...],
                              'internal_power' : [internalPowerDic1, internalPowerDic2, ...],
                             },
                  pinName2 : {
                              'timing' : [timingDic1, timingDic2, ...],
                              'internal_power' : [internalPowerDic1, internalPowerDic2, ...],
                             },
                  ...
                 }
        }
        """
        busDic = collections.OrderedDict()

        if 'group' in groupDic:
            for groupDic in groupDic['group']:
                groupType = groupDic['type']

                if groupType == 'pin':
                    pinName = groupDic['name']

                    if (len(pinList) > 0) and (pinName not in pinList):
                        continue

                    busDic.setdefault('pin', collections.OrderedDict())
                    busDic['pin'].setdefault(pinName, collections.OrderedDict())
                    pinDic = self._getPinInfo(groupDic)

                    if pinDic:
                        busDic['pin'][pinName] = pinDic
                elif groupType == 'timing':
                    timingDic = self._getTimingGroupInfo(groupDic)
                    busDic.setdefault('timing', [])
                    busDic['timing'].append(timingDic)
                elif groupType == 'internal_power':
                    internalPowerDic = self._getInternalPowerGroupInfo(groupDic)
                    busDic.setdefault('internal_power', [])
                    busDic['internal_power'].append(internalPowerDic)

        return busDic

    def getLibPinInfo(self, cellList=[], bundleList=[], busList=[], pinList=[]):
        """
        Get all pins (and timing&intern_power info).
        pin strncture is as below:
        cell -- pin
             |
             -- bundle -- pin
             |
             -- bus    -- pin
        Return a dict.
        {
         cellName1 : {
                      'pin' : [pinDic1, pinDic2, ...],
                      'bundle' : {
                                  'pin' : [pinDic1, pinDic2, ...]
                                 }
                      'bus' : {
                               'pin' : [pinDic1, pinDic2, ...]
                              }
                     },
         ...
        }
        """
        libPinDic = collections.OrderedDict()

        if 'group' in self.libDic:
            for libGroupDic in self.libDic['group']:
                groupType = libGroupDic['type']

                if groupType == 'cell':
                    cellName = libGroupDic['name']

                    if (len(cellList) > 0) and (cellName not in cellList):
                        continue

                    if 'group' in libGroupDic:
                        for cellGroupDic in libGroupDic['group']:
                            cellGroupType = cellGroupDic['type']

                            if cellGroupType == 'pin':
                                pinName = cellGroupDic['name']

                                if (len(pinList) > 0) and (pinName not in pinList):
                                    continue

                                libPinDic.setdefault('cell', collections.OrderedDict())
                                libPinDic['cell'].setdefault(cellName, collections.OrderedDict())
                                libPinDic['cell'][cellName].setdefault('pin', collections.OrderedDict())
                                libPinDic['cell'][cellName]['pin'].setdefault(pinName, collections.OrderedDict())
                                pinDic = self._getPinInfo(cellGroupDic)

                                if pinDic:
                                    libPinDic['cell'][cellName]['pin'][pinName] = pinDic
                            elif cellGroupType == 'bundle':
                                bundleName = cellGroupDic['name']

                                if (len(bundleList) > 0) and (bundleName not in bundleList):
                                    continue

                                bundleDic = self._getBundleInfo(cellGroupDic, pinList)

                                if bundleDic:
                                    libPinDic.setdefault('cell', collections.OrderedDict())
                                    libPinDic['cell'].setdefault(cellName, collections.OrderedDict())
                                    libPinDic['cell'][cellName].setdefault('bundle', collections.OrderedDict())
                                    libPinDic['cell'][cellName]['bundle'].setdefault(bundleName, collections.OrderedDict())
                                    libPinDic['cell'][cellName]['bundle'][bundleName] = bundleDic
                            elif cellGroupType == 'bus':
                                busName = cellGroupDic['name']

                                if (len(busList) > 0) and (bundleName not in busList):
                                    continue

                                busDic = self._getBusInfo(cellGroupDic, pinList)

                                if busDic:
                                    libPinDic.setdefault('cell', collections.OrderedDict())
                                    libPinDic['cell'].setdefault(cellName, collections.OrderedDict())
                                    libPinDic['cell'][cellName].setdefault('bus', collections.OrderedDict())
                                    libPinDic['cell'][cellName]['bus'].setdefault(busName, collections.OrderedDict())
                                    libPinDic['cell'][cellName]['bus'][busName] = busDic

        return libPinDic
# Application functions (end) #
