import os
import re
from ConfigParser import ConfigParser
from logger       import Logger

class Configuration(object):
    
    ALL_CPU_ABIS = ['armeabi', 'armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64', 'mips', 'mips64']
    
    logFile = None
    log = None
    warnOnOutputOverwrite = False
    ndkPath = None
    gitPath = None
    currDir = None
    outputDir = None
    patchesDir = None
    filesDir = None
    pythonServer = 'www.python.org'
    pythonServerPath = '/ftp/python/'
    pythonPatchDir = None
    versionList = None
    additionalLibs = None
    cpuAbis = ALL_CPU_ABIS[:]
    useMultiThreading = True
    
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
        self.patchesDir = self.processPaths(args.patchesDir) or self.patchesDir
        self.outputDir = self.processPaths(args.outputDir) or self.outputDir
        self.filesDir = self.processPaths(args.filesDir) or self.filesDir
        self.gitPath = self.processPaths(args.gitPath) or self.gitPath
        self.ndkPath = self.processPaths(args.ndkPath) or self.ndkPath
        self.pythonPatchDir = args.pythonPatchDir or self.pythonPatchDir
        self.versionList = args.versions if args.versions != None and len(args.versions) != 0 else self.versionList
        self.pythonServer = args.pythonServer or self.pythonServer
        self.pythonServerPath = args.pythonServerPath or self.pythonServerPath
        self.cpuAbis = args.cpuAbis if args.cpuAbis != None and len(args.cpuAbis) != 0 else self.cpuAbis
        self.useMultiThreading = not args.disableMultiThreading if args.disableMultiThreading != None else self.useMultiThreading
    
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
        if not all([cpuAbi in self.ALL_CPU_ABIS for cpuAbi in self.cpuAbis]):
            for cpuAbi in self.cpuAbis:
                if cpuAbi not in self.ALL_CPU_ABIS:
                    self.log.error('Got invalid cpu api: ' + str(cpuAbi))
            return False
        return True
    
    def parseConfigFile(self, path):
        parser = ConfigParser()
        parser.optionxform = str
        parser.read(path)
        if parser.has_option('General', 'warnOnOutputOverwrite'):
            self.warnOnOutputOverwrite = parser.getboolean('General', 'warnOnOutputOverwrite')
        if parser.has_option('General', 'useMultiThreading'):
            self.useMultiThreading = parser.getboolean('General', 'useMultiThreading')
        if parser.has_option('General', 'versions') and parser.get('General', 'versions').strip().lower() not in ['any', 'all']:
            self.versionList = parser.get('General', 'versions').replace(',', ' ').split()
        if parser.has_option('General', 'cpuAbis') and parser.get('General', 'cpuAbis').strip().lower() not in ['any', 'all']:
            self.cpuAbis = parser.get('General', 'cpuAbis').replace(',', ' ').split()
        if parser.has_option('Paths', 'ndk_dir'):
            self.ndkPath = self.processPaths(parser.get('Paths', 'ndk_dir'))
        if parser.has_option('Paths', 'git_dir'):
            self.gitPath = self.processPaths(parser.get('Paths', 'git_dir'))
        if parser.has_option('Paths', 'files_dir'):
            self.filesDir = self.processPaths(parser.get('Paths', 'files_dir'))
        if parser.has_option('Paths', 'output_dir'):
            self.outputDir = self.processPaths(parser.get('Paths', 'output_dir'))
        if parser.has_option('Paths', 'patches_dir'):
            self.patchesDir = self.processPaths(parser.get('Paths', 'patches_dir'))
        if parser.has_option('Paths', 'log_file'):
            self.logFile = self.processPaths(parser.get('Paths', 'log_file'))
        if parser.has_option('Paths', 'python_server'):
            self.pythonServer = parser.get('Paths', 'python_server')
        if parser.has_option('Paths', 'python_server_path'):
            self.pythonServerPath = parser.get('Paths', 'python_server_path')
        if parser.has_option('Paths', 'python_patch_dir'):
            self.pythonPatchDir = self.processPaths(parser.get('Paths', 'python_patch_dir'))
        if parser.has_section('AdditionalLibs'):
            libEntries = parser.options('AdditionalLibs')
            for entry in [entry for entry in libEntries if entry.endswith('_url')]:
                lib = entry[:-4]
                libData = {'url': parser.get('AdditionalLibs', entry)}
                if lib + '_req' in libEntries:
                    requiredFor = [module.split('|') for module in parser.get('AdditionalLibs', lib + '_req').replace(',', ' ').split()]
                    libData['req']  = [module[0] for module in requiredFor]
                    libData['req3'] = [module[1] if len(module) > 1 else module[0] for module in requiredFor]
                if lib + '_extraction_filter' in libEntries:
                    libData['extraction_filter'] = parser.get('AdditionalLibs', lib + '_extraction_filter').replace(',', ' ').split()
                if lib + '_add_file_copy_opr' in libEntries:
                    opr = parser.get('AdditionalLibs', lib + '_add_file_copy_opr')
                    oprList = re.split(r'(?<!->),?\s(?!->)', opr)
                    lst = []
                    for operation in oprList:
                        oprParts = operation.split('->')
                        lst.append((oprParts[0].strip(), oprParts[1].strip()))
                    libData['file_copy_opr'] = lst
                self.additionalLibs[lib] = libData
    
    def processPaths(self, path):
        if path == None: return None
        path = os.path.expanduser(os.path.expandvars(path))
        if os.path.isabs(path):
            return path
        return os.path.join(self.currDir, path)
    
    def closeLog(self):
        if self.logFile != None:
            self.logFile.flush()
            self.logFile.close()