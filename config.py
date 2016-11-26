import os
import re
from ConfigParser import ConfigParser
from logger       import Logger

class Configuration(object):
    
    ALL_CPU_ABIS = ['armeabi', 'armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64', 'mips', 'mips64']
    DEFAULT_MIN_SKD_VERSION = 8
    
    logFile = None
    log = None
    warnOnOutputOverwrite = False
    ndkPath = None
    gitPath = None
    currDir = None
    outputDir = None
    patchesDir = None
    filesDir = None
    cacheDir = None
    pythonServer = 'www.python.org'
    pythonServerPath = '/ftp/python/'
    pythonPatchDir = None
    versionList = None
    #template = {
    #    'libName': {
    #        'url': '',
    #        'dependencies': [],                      # optional
    #        'extractionFilter': [],                  # optional
    #        'pyModuleReq': [],                       # optional
    #        'py3ModuleReq': [],                      # optional
    #        'minAndroidSdk': 8,                      # optional
    #        'data': [['src', 'output_name', 'dest']] # optional
    #    }
    #}
    additionalLibs = None
    cpuAbis = ALL_CPU_ABIS[:]
    useMultiThreading = True
    librariesDataPath = None
    
    def __init__(self, args):
        super(Configuration, self).__init__()
        self.currDir = os.path.dirname(os.path.realpath(__file__))
        self.versionList = []
        self.additionalLibs = {}
        self.logFile = args.logFile
        if args.configFile != None:
            self.parseConfigFile(args.configFile)
        if self.logFile != None:
            self.logFile = open(self.logFile, 'w')
        self.log = Logger(self.logFile)
        self.patchesDir = self.resolvePath(args.patchesDir) or self.patchesDir
        self.outputDir = self.resolvePath(args.outputDir) or self.outputDir
        self.filesDir = self.resolvePath(args.filesDir) or self.filesDir
        self.cacheDir = self.resolvePath(args.cacheDir) or self.cacheDir
        self.gitPath = self.resolvePath(args.gitPath) or self.gitPath
        self.ndkPath = self.resolvePath(args.ndkPath) or self.ndkPath
        self.pythonPatchDir = args.pythonPatchDir or self.pythonPatchDir
        self.versionList = args.versions if args.versions != None and len(args.versions) != 0 else self.versionList
        self.pythonServer = args.pythonServer or self.pythonServer
        self.pythonServerPath = args.pythonServerPath or self.pythonServerPath
        self.cpuAbis = args.cpuAbis if args.cpuAbis != None and len(args.cpuAbis) != 0 else self.cpuAbis
        self.useMultiThreading = not args.disableMultiThreading if args.disableMultiThreading != None else self.useMultiThreading
        self.librariesDataPath = args.librariesDataFile or self.librariesDataPath
    
    def check(self):
        if self.gitPath == None or not os.path.isfile(self.gitPath):
            self.log.error('The path to the git executable is not specified or incorrect.')
            return False
        if self.ndkPath == None or not os.path.isfile(self.ndkPath):
            self.log.error('The path to the ndk executable is not specified or incorrect.')
            return False
        if self.pythonPatchDir == None:
            self.log.error('The path to the Python Patch source directory is not specified.')
            return False
        if self.patchesDir == None or not os.path.isdir(self.patchesDir):
            self.log.error('The path to the patches directory is incorrect.')
            return False
        if self.outputDir == None:
            self.log.error('The path to the output directory is not specified.')
            return False
        if self.filesDir == None or not os.path.isdir(self.filesDir) :
            self.log.error('The path to the files directory is incorrect.')
            return False
        if self.librariesDataPath == None or not os.path.isdir(self.filesDir) :
            self.log.error('The path to the libraries data file is incorrect: ' + str(self.librariesDataPath))
            return False
        if not all([cpuAbi in self.ALL_CPU_ABIS for cpuAbi in self.cpuAbis]):
            for cpuAbi in self.cpuAbis:
                if cpuAbi not in self.ALL_CPU_ABIS:
                    self.log.error('Got invalid cpu api: ' + str(cpuAbi))
            return False
        return True
    
    def parseConfigFile(self, path):
        parser = ConfigParser()
        parser.optionxform = str
        path = self.resolvePath(path)
        if len(parser.read(path)) == 0:
            self.log.warn('Failed to read the config from ' + path)
            return
        if parser.has_option('General', 'warnOnOutputOverwrite'):
            self.warnOnOutputOverwrite = parser.getboolean('General', 'warnOnOutputOverwrite')
        if parser.has_option('General', 'useMultiThreading'):
            self.useMultiThreading = parser.getboolean('General', 'useMultiThreading')
        if parser.has_option('General', 'versions') and parser.get('General', 'versions').strip().lower() not in ['any', 'all']:
            self.versionList = parser.get('General', 'versions').replace(',', ' ').split()
        if parser.has_option('General', 'cpuAbis') and parser.get('General', 'cpuAbis').strip().lower() not in ['any', 'all']:
            self.cpuAbis = parser.get('General', 'cpuAbis').replace(',', ' ').split()
        if parser.has_option('Paths', 'ndk_dir'):
            self.ndkPath = self.resolvePath(parser.get('Paths', 'ndk_dir'))
        if parser.has_option('Paths', 'git_dir'):
            self.gitPath = self.resolvePath(parser.get('Paths', 'git_dir'))
        if parser.has_option('Paths', 'files_dir'):
            self.filesDir = self.resolvePath(parser.get('Paths', 'files_dir'))
        if parser.has_option('Paths', 'output_dir'):
            self.outputDir = self.resolvePath(parser.get('Paths', 'output_dir'))
        if parser.has_option('Paths', 'patches_dir'):
            self.patchesDir = self.resolvePath(parser.get('Paths', 'patches_dir'))
        if parser.has_option('Paths', 'cache_dir'):
            self.cacheDir = self.resolvePath(parser.get('Paths', 'cache_dir'))
        if parser.has_option('Paths', 'log_file'):
            self.logFile = self.resolvePath(parser.get('Paths', 'log_file'))
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
    
    def parseLibrariesFile(self, path):
        parser = ConfigParser()
        parser.optionxform = str
        parser.read(path)
        for libraryName, rawData in [(libName, dict(parser.items(libName))) for libName in parser.sections()]:
            libData = {}
            if not 'url' in rawData.keys():
                self.log.warn('Module ' + libraryName + ' read from "' + path +
                              '" does not have the required dataEntry "url", ignoring it.')
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
                    self.log.warn('Module ' + libraryName + ' read from "' + path +
                                  '" has a malformed (not numeric) dataEntry "min_android_sdk": "' +
                                  rawData['min_android_sdk'] + '" , ignoring it.')
                    continue
                libData['minAndroidSdk'] = int(rawData['min_android_sdk'])
            if 'data' in rawData.keys():
                libData['data'] = []
                for dataEntriy in rawData['data'].split(', '):
                    dataStages = dataEntriy.split(' -> ')
                    if len(dataStages) != 3:
                        self.log.warn('Module ' + libraryName + ' read from "' + path +
                                  '" has a malformed dataEntry in "data": "' +
                                  dataEntriy + '" (Could not parse 3 stages), ignoring dataEntry.')
                        continue
                    libData['data'].append(dataStages)
            self.additionalLibs[libraryName] = libData
    
    def computeLibMinAndroidSdkList(self):
        res = {}
        libVersionTable = {}
        changed = False
        for libName, libData in self.additionalLibs.iteritems():
            libVersionTable[libName] = libData.get('minAndroidSdk', self.DEFAULT_MIN_SKD_VERSION)
        def getMinSdkVersion(lib, scannedLibs):
            minSdk = libVersionTable[lib]
            if 'dependencies' in self.additionalLibs[lib].keys():
                for dep in self.additionalLibs[lib]['dependencies']:
                    if dep in scannedLibs:
                        raise Exception('Infinite recursive dependency detected for lib "' + dep +
                                        '" (scannedLibs = ' + str(scannedLibs) + ')')
                    minSdk = max(getMinSdkVersion(dep, scannedLibs + [dep]), minSdk)
                    if minSdk > libVersionTable[dep]:
                        libVersionTable[dep] = minSdk
                        changed = True
            return minSdk
        def computeVersionTable(versionTable):
            changed = False
            for libName, sdkVersion in libVersionTable.iteritems():
                sdkVersion = getMinSdkVersion(libName, [])
                if sdkVersion > libVersionTable[libName]:
                    libVersionTable[libName] = sdkVersion
                    changed = True
            return computeVersionTable(versionTable) if changed else versionTable
        libVersionTable = computeVersionTable(libVersionTable)
        for libName, sdkVersion in libVersionTable.iteritems():
            if not sdkVersion in res.keys():
                res[sdkVersion] = []
            res[sdkVersion].append(libName)
        return res
    
    def resolvePath(self, path):
        if path == None: return None
        path = os.path.expanduser(os.path.expandvars(path))
        if os.path.isabs(path):
            return path
        return os.path.join(self.currDir, path)
    
    def closeLog(self):
        if self.logFile != None:
            self.logFile.flush()
            self.logFile.close()
