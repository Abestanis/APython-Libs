import os
from configparser import ConfigParser
from typing import Dict, List, Optional

from logger import Logger


class Configuration:
    ALL_CPU_ABIS = ['armeabi', 'armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64', 'mips', 'mips64']
    DEFAULT_MIN_SKD_VERSION = 14

    logFilePath = None
    log = None
    warnOnOutputOverwrite = False
    ndkPath = None
    gitPath = 'git'
    currDir = None
    outputDir = None
    patchesDir = None
    filesDir = None
    cacheDir = None
    pythonServer = 'www.python.org'
    pythonServerPath = '/ftp/python/'
    pythonPatchDir = None
    versionList = None
    # additionalLibs_template = {
    #     'libName': {
    #         'url': '',
    #         'dependencies': [],                      # optional
    #         'extractionFilter': [],                  # optional
    #         'pyModuleReq': [],                       # optional
    #         'py3ModuleReq': [],                      # optional
    #         'minAndroidSdk': 9,                      # optional
    #         'data': [['src', 'output_name', 'dest']] # optional
    #     }
    # }
    additionalLibs = None
    cpuABIs = ALL_CPU_ABIS[:]
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
        self.filesDir = self.resolvePath(args.filesDir) or self.filesDir
        self.cacheDir = self.resolvePath(args.cacheDir) or self.cacheDir
        self.gitPath = self.resolvePath(args.gitPath) or self.gitPath
        self.ndkPath = self.resolvePath(args.ndkPath) or self.ndkPath
        self.pythonPatchDir = args.pythonPatchDir or self.pythonPatchDir
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
        if self.gitPath is None or os.system(self.gitPath + ' --version') != 0:
            self.log.error('The path to the git executable is not specified or incorrect.')
            return False
        if self.ndkPath is None or not os.path.isfile(self.ndkPath):
            self.log.error('The path to the ndk executable is not specified or incorrect.')
            return False
        if self.pythonPatchDir is None:
            self.log.error('The path to the Python Patch source directory is not specified.')
            return False
        if self.patchesDir is None or not os.path.isdir(self.patchesDir):
            self.log.error('The path to the patches directory is incorrect.')
            return False
        if self.outputDir is None:
            self.log.error('The path to the output directory is not specified.')
            return False
        if self.filesDir is None or not os.path.isdir(self.filesDir):
            self.log.error('The path to the files directory is incorrect.')
            return False
        if self.librariesDataPath is None or not os.path.isdir(self.filesDir):
            self.log.error('The path to the libraries data file is incorrect: '
                           + str(self.librariesDataPath))
            return False
        if not all([cpuAbi in self.ALL_CPU_ABIS for cpuAbi in self.cpuABIs]):
            for cpuABI in self.cpuABIs:
                if cpuABI not in self.ALL_CPU_ABIS:
                    self.log.error('Got invalid cpu ABI: {abi}'.format(abi=cpuABI))
            return False
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
        if parser.has_option('Paths', 'patch_path'):
            self.gitPath = self.resolvePath(parser.get('Paths', 'git_path'))
        if parser.has_option('Paths', 'files_dir'):
            self.filesDir = self.resolvePath(parser.get('Paths', 'files_dir'))
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
        if parser.has_option('Paths', 'libraries_data_file'):
            self.librariesDataPath = self.resolvePath(parser.get('Paths', 'libraries_data_file'))

    def parseLibrariesData(self):
        self.parseLibrariesFile(self.librariesDataPath)

    def parseLibrariesFile(self, path: str):
        parser = ConfigParser(interpolation=None)
        parser.optionxform = str
        parser.read(path)
        for libraryName in parser.sections():
            rawData = dict(parser.items(libraryName))
            libData = {}
            if 'url' not in rawData.keys():
                self.log.warn('Module {name} read from "{path}" does not have the required '
                              'dataEntry "url", ignoring it.'.format(name=libraryName, path=path))
                continue
            libData['url'] = rawData['url']
            if 'lib_dep' in rawData.keys():
                libData['dependencies'] = rawData['lib_dep'].split(', ')
            if 'extraction_filter' in rawData.keys():
                libData['extractionFilter'] = rawData['extraction_filter'].split(', ')
            if 'py_module_dep' in rawData.keys():
                libData['pyModuleReq'] = rawData['py_module_dep'].split(', ')
            if 'py3_module_dep' in rawData.keys():
                libData['py3ModuleReq'] = rawData['py3_module_dep'].split(', ')
            if 'min_android_sdk' in rawData.keys():
                if not rawData['min_android_sdk'].isdigit():
                    self.log.warn(
                        'Module {name} read from "{path}" has a malformed (not numeric) dataEntry '
                        '"min_android_sdk": "{dataEntry}", ignoring it.'.format(
                            name=libraryName, path=path, dataEntry=rawData['min_android_sdk']))
                    continue
                libData['minAndroidSdk'] = int(rawData['min_android_sdk'])
            if 'data' in rawData.keys():
                libData['data'] = []
                for dataEntry in rawData['data'].split(', '):
                    dataStages = dataEntry.split(' -> ')
                    if len(dataStages) != 3:
                        self.log.warn(
                            'Module {name} read from "{path}" has a malformed dataEntry in "data": '
                            '"{dataEntry}" (Could not parse 3 stages), ignoring dataEntry.'
                                .format(name=libraryName, path=path, dataEntry=dataEntry))
                        continue
                    libData['data'].append(dataStages)
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
                libDataTable[libName] = [self.DEFAULT_MIN_SKD_VERSION, []]
            libDataTable[libName][0] = libData.get('minAndroidSdk', self.DEFAULT_MIN_SKD_VERSION)
            libDataTable[libName][0] = max(libDataTable[libName][0], self.DEFAULT_MIN_SKD_VERSION)
            # Add our self to the list of our dependencies
            for dependency in libData.get('dependencies', []):
                if dependency not in libDataTable:
                    libDataTable[dependency] = [self.DEFAULT_MIN_SKD_VERSION, []]
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
            if sdkVersion not in result:
                result[sdkVersion] = []
            result[sdkVersion].append(libName)
        return result

    def resolvePath(self, path: str) -> Optional[str]:
        if path is None:
            return None
        path = os.path.expanduser(os.path.expandvars(path))
        if os.path.isabs(path):
            return path
        return os.path.join(self.currDir, path)

    def closeLog(self):
        logOutput = self.log.getOutput()
        if logOutput is not None:
            logOutput.flush()
            logOutput.close()
