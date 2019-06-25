import json
import os
import shutil
from configparser import ConfigParser
from typing import Dict, List, Optional, Tuple

from logger import Logger


class Configuration:
    minSdkVersion = 9
    logFilePath = None
    log = None
    warnOnOutputOverwrite = False
    ndkPath = None
    gitPath = 'git'
    cmakePath = 'cmake'
    makePath = 'ninja'
    currDir = None
    outputDir = None
    patchesDir = None
    buildFilesDir = None
    cacheDir = None
    pythonServer = 'www.python.org'
    pythonServerPath = '/ftp/python/'
    pythonPatchDir = None
    ipcDir = None
    versionList = None
    # additionalLibs_template = {
    #     'libName': {
    #         'url': '',
    #         'provides': '',                         # optional
    #         'dependencies': [],                     # optional
    #         'extractionFilter': [],                 # optional
    #         'pyModuleReq': [],                      # optional
    #         'py3ModuleReq': [],                     # optional
    #         'includeDir': '',                       # optional
    #         'includeDirContent': [],                # optional
    #         'minAndroidSdk': 9,                     # optional
    #         'data': [['src', 'output_name', 'dst']] # optional
    #     }
    # }
    additionalLibs = None
    cpuABIs = []
    useMultiprocessing = True
    librariesDataPath = None

    def __init__(self, args):
        super(Configuration, self).__init__()
        self.currDir = os.path.dirname(os.path.realpath(__file__))
        self.versionList = []
        self.additionalLibs = {}
        self.logFilePath = args.logFile
        if args.configFile is not None:
            self.parseConfigFile(args.configFile)
        self.log = Logger(open(self.logFilePath, 'w') if self.logFilePath is not None else None)
        self.patchesDir = self.resolvePath(args.patchesDir) or self.patchesDir
        self.outputDir = self.resolvePath(args.outputDir) or self.outputDir
        self.buildFilesDir = self.resolvePath(args.buildFilesDir) or self.buildFilesDir
        self.cacheDir = self.resolvePath(args.cacheDir) or self.cacheDir
        self.gitPath = self.resolvePath(args.gitPath) or self.gitPath
        self.cmakePath = self.resolvePath(args.cmakePath) or self.cmakePath
        self.makePath = self.resolvePath(args.makePath) or self.makePath
        self.ndkPath = self.resolvePath(args.ndkPath) or self.ndkPath
        self.pythonPatchDir = args.pythonPatchDir or self.pythonPatchDir
        self.ipcDir = args.ipcDir or self.ipcDir
        if args.versions is not None and len(args.versions) != 0:
            self.versionList = args.versions
        self.pythonServer = args.pythonServer or self.pythonServer
        self.pythonServerPath = args.pythonServerPath or self.pythonServerPath
        if args.cpuABIs is not None and len(args.cpuABIs) != 0:
            self.cpuABIs = args.cpuABIs
        if args.disableMultiprocessing is not None:
            self.useMultiprocessing = not args.disableMultiprocessing
        self.librariesDataPath = args.librariesDataFile or self.librariesDataPath

    def check(self) -> bool:
        if not self._isValidExecutable(self.gitPath):
            self.log.error('The path to the git executable is not specified or incorrect.')
            return False
        if not self._isValidExecutable(self.cmakePath):
            self.log.error('The path to the cmake executable is not specified or incorrect.')
            return False
        if not self._isValidExecutable(self.makePath):
            self.log.error('The path to the make executable is not specified or incorrect.')
            return False
        if self.ndkPath is None or not os.path.isdir(self.ndkPath):
            self.log.error('The path to the ndk executable is not specified or incorrect.')
            return False
        try:
            self.minSdkVersion, allCpuABIs = self._readNdkDefaults()
        except (RuntimeError, IOError) as error:
            self.log.error('The given ndk is invalid: {reason}'.format(reason=error))
            return False
        self.log.debug('Auto-detected minimum sdk version {sdkVersion} and supported CPU ABIs: '
                       '{abiList}'.format(sdkVersion=self.minSdkVersion,
                                          abiList=', '.join(allCpuABIs)))
        if self.pythonPatchDir is None:
            self.log.error('The path to the Python Patch source directory is not specified.')
            return False
        if self.ipcDir is None:
            self.log.error('The path to the IPC source directory is not specified.')
            return False
        if self.patchesDir is None or not os.path.isdir(self.patchesDir):
            self.log.error('The path to the patches directory is incorrect.')
            return False
        if self.outputDir is None:
            self.log.error('The path to the output directory is not specified.')
            return False
        if self.buildFilesDir is None or not os.path.isdir(self.buildFilesDir):
            self.log.error('The path to the build files directory is incorrect.')
            return False
        if self.librariesDataPath is None or not os.path.isfile(self.librariesDataPath):
            self.log.error('The path to the libraries data file is incorrect: '
                           + str(self.librariesDataPath))
            return False
        if not all([cpuAbi in allCpuABIs for cpuAbi in self.cpuABIs]):
            for cpuABI in self.cpuABIs:
                if cpuABI not in allCpuABIs:
                    self.log.error('Got invalid CPU ABI: {abi}'.format(abi=cpuABI))
            return False
        if len(self.cpuABIs) == 0:
            self.cpuABIs = allCpuABIs
        return True

    def parseConfigFile(self, path: str):
        parser = ConfigParser(interpolation=None)
        parser.optionxform = str
        path = self.resolvePath(path)
        if len(parser.read(path)) == 0:
            print('Failed to read the config from ' + path)
            return
        if parser.has_option('General', 'warnOnOutputOverwrite'):
            self.warnOnOutputOverwrite = parser.getboolean('General', 'warnOnOutputOverwrite')
        if parser.has_option('General', 'useMultiprocessing'):
            self.useMultiprocessing = parser.getboolean('General', 'useMultiprocessing')
        if parser.has_option('General', 'versions')\
                and parser.get('General', 'versions').strip().lower() not in ['any', 'all']:
            self.versionList = parser.get('General', 'versions').replace(',', ' ').split()
        if parser.has_option('General', 'cpuABIs')\
                and parser.get('General', 'cpuABIs').strip().lower() not in ['any', 'all']:
            self.cpuABIs = parser.get('General', 'cpuABIs').replace(',', ' ').split()
        if parser.has_option('Paths', 'ndk_dir'):
            self.ndkPath = self.resolvePath(parser.get('Paths', 'ndk_dir'))
        if parser.has_option('Paths', 'git_path'):
            self.gitPath = self.resolvePath(parser.get('Paths', 'git_path'))
        if parser.has_option('Paths', 'cmake_path'):
            self.cmakePath = self.resolvePath(parser.get('Paths', 'cmake_path'))
        if parser.has_option('Paths', 'make_path'):
            self.makePath = self.resolvePath(parser.get('Paths', 'make_path'))
        if parser.has_option('Paths', 'files_dir'):
            self.buildFilesDir = self.resolvePath(parser.get('Paths', 'build_files_dir'))
        if parser.has_option('Paths', 'output_dir'):
            self.outputDir = self.resolvePath(parser.get('Paths', 'output_dir'))
        if parser.has_option('Paths', 'patches_dir'):
            self.patchesDir = self.resolvePath(parser.get('Paths', 'patches_dir'))
        if parser.has_option('Paths', 'cache_dir'):
            self.cacheDir = self.resolvePath(parser.get('Paths', 'cache_dir'))
        if parser.has_option('Paths', 'log_file'):
            self.logFilePath = self.resolvePath(parser.get('Paths', 'log_file'))
        if parser.has_option('Paths', 'python_server'):
            self.pythonServer = parser.get('Paths', 'python_server')
        if parser.has_option('Paths', 'python_server_path'):
            self.pythonServerPath = parser.get('Paths', 'python_server_path')
        if parser.has_option('Paths', 'python_patch_dir'):
            self.pythonPatchDir = self.resolvePath(parser.get('Paths', 'python_patch_dir'))
        if parser.has_option('Paths', 'ipc_dir'):
            self.ipcDir = self.resolvePath(parser.get('Paths', 'ipc_dir'))
        if parser.has_option('Paths', 'libraries_data_file'):
            self.librariesDataPath = self.resolvePath(parser.get('Paths', 'libraries_data_file'))

    def parseLibrariesData(self):
        self.parseLibrariesFile(self.librariesDataPath)

    def parseLibrariesFile(self, path: str):
        parser = ConfigParser(interpolation=None)
        parser.optionxform = str
        parser.read(path)
        for sectionName in parser.sections():
            rawData = dict(parser.items(sectionName))
            sectionData = {}
            if 'url' not in rawData:
                self.log.warn('Module {name} read from "{path}" does not have the required '
                              'dataEntry "url", ignoring it.'.format(name=sectionName, path=path))
                continue
            sectionData['url'] = rawData['url']
            if 'extraction_filter' in rawData:
                sectionData['extractionFilter'] = rawData['extraction_filter'].split(', ')
            if 'include_dir' in rawData:
                sectionData['includeDir'] = rawData['include_dir']
            if 'include_dir_content' in rawData:
                sectionData['includeDirContent'] = rawData['include_dir_content'].split()
            libs = [('', sectionName, lambda: sectionData)]
            if 'provides' in rawData:
                libs.extend((name.strip() + '_', name.strip(), lambda: sectionData.copy())
                            for name in rawData['provides'].split(', '))
            for prefix, libraryName, libDataFactory in libs:
                libData = libDataFactory()
                if prefix + 'min_android_sdk' in rawData:
                    try:
                        libData['minAndroidSdk'] = int(rawData[prefix + 'min_android_sdk'])
                    except ValueError as error:
                        self.log.warn(
                            'Module {name} read from "{path}" has a malformed (not numeric) '
                            'dataEntry "{prefix}min_android_sdk", ignoring it: {reason}.'.format(
                                name=libraryName, prefix=prefix, path=path, reason=error))
                        continue
                if prefix + 'data' in rawData:
                    libData['data'] = []
                    for dataEntry in rawData[prefix + 'data'].split(', '):
                        dataStages = dataEntry.split(' -> ')
                        if len(dataStages) != 3:
                            self.log.warn(
                                'Module {name} read from "{path}" has a malformed dataEntry in '
                                '"{prefix}data": "{dataEntry}" (Could not parse 3 stages), '
                                'ignoring dataEntry.'.format(name=libraryName, prefix=prefix,
                                                             path=path, dataEntry=dataEntry))
                            continue
                        libData['data'].append(dataStages)
                if prefix + 'lib_dep' in rawData:
                    libData['dependencies'] = rawData[prefix + 'lib_dep'].split(', ')
                if prefix + 'py_module_dep' in rawData:
                    libData['pyModuleReq'] = rawData[prefix + 'py_module_dep'].split(', ')
                if prefix + 'py3_module_dep' in rawData:
                    libData['py3ModuleReq'] = rawData[prefix + 'py3_module_dep'].split(', ')
                if 'provides' in rawData:
                    libData['parent'] = sectionName
                if prefix != '' or 'provides' not in rawData:
                    self.additionalLibs[libraryName] = libData

    def computeLibMinAndroidSdkList(self) -> Dict[int, List[str]]:
        """
        Calculate the minimum android sdk version possible needed for each library taking into
        account the dependencies of the library.

        :return: A dict with "minSdkVersion -> list of library name" mapping
        """
        # 1. Create a dict with entries in the form of:
        # <libName>: [minSdkVersion, [list of libs that depend on this lib]]
        libDataTable = {}
        for libName, libData in self.additionalLibs.items():
            if libName not in libDataTable:
                libDataTable[libName] = [self.minSdkVersion, []]
            libDataTable[libName][0] = libData.get('minAndroidSdk', self.minSdkVersion)
            libDataTable[libName][0] = max(libDataTable[libName][0], self.minSdkVersion)
            # Add our self to the list of our dependencies
            for dependency in libData.get('dependencies', []):
                if dependency not in libDataTable:
                    libDataTable[dependency] = [self.minSdkVersion, []]
                libDataTable[dependency][1].append(libName)

        # 2. Update the minSdkVersion attribute based on the dependencies
        def updateMinSdk(libraryData):
            for dependentLib in libraryData[1]:
                if libDataTable[dependentLib][0] < libraryData[0]:
                    libDataTable[dependentLib][0] = libraryData[0]
                    updateMinSdk(libDataTable[dependentLib])
        for libData in libDataTable.values():
            updateMinSdk(libData)

        # 3. Collect the libraries into a dict of <sdkVersion>: [list of libs]
        result = {}
        for libName, libData in libDataTable.items():
            sdkVersion = libData[0]
            result.setdefault(sdkVersion, []).append(libName)
        return result

    def resolvePath(self, path: str) -> Optional[str]:
        if path is None:
            return None
        path = os.path.expanduser(os.path.expandvars(path))
        if os.path.isabs(path):
            return path
        absPath = os.path.join(self.currDir, path)
        if os.path.exists(absPath):
            return absPath
        return shutil.which(path)

    def closeLog(self):
        logOutput = self.log.getOutput()
        if logOutput is not None:
            logOutput.flush()
            logOutput.close()

    @staticmethod
    def _isValidExecutable(path: Optional[str]) -> bool:
        return path is not None and os.path.isfile(path) and os.access(path, os.X_OK)

    def _readNdkDefaults(self) -> Tuple[int, List[str]]:
        with open(os.path.join(self.ndkPath, 'meta', 'platforms.json')) as platformFile:
            minVersion = json.load(platformFile).get('min')
            if minVersion is None:
                raise RuntimeError('Ndk does not provide a minimum version level')
        # noinspection SpellCheckingInspection
        with open(os.path.join(self.ndkPath, 'meta', 'abis.json')) as abisFile:
            supportedABIs = list(json.load(abisFile).keys())
            if len(supportedABIs) == 0:
                raise RuntimeError('Ndk does not provide any supported CPU ABIs')
        return minVersion, supportedABIs
