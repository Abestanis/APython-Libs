from __future__ import print_function
DESCRIPTION = '''
This script will download and compile all Python versions to libraries which
can be used by the APython project (see https://github.com/Abestanis/APython).

To compile the C sources, the Android NDK is used and
to apply some patches to the source code, git is required.
The path to both can be provided via command line options
or via a configuration file (by default, a config.cfg in the
same directory as this script is used).

Created 18.08.2015 by Sebastian Scholz.
'''

try:
    from httplib import HTTPSConnection as Connection
except ImportError:
    print('[Warn ] No HTTPS connection provider found, using HTTP instead.')
    from httplib import HTTPConnection as Connection
from httplib      import HTTPResponse, BadStatusLine, HTTPConnection
from argparse     import ArgumentParser
from ConfigParser import ConfigParser
from time         import time, sleep
from tempfile     import mkdtemp
from urlparse     import urlparse
from urllib2      import urlopen
from contextlib   import closing
from hashlib      import md5
from subprocess   import Popen, PIPE
from multiprocessing import Pool
import re
import shutil
import os
import tarfile
import subprocess

class Logger(object):
    
    _output = None
    
    def __init__(self, output = None):
        self._output = output
    
    def console(self, message, end = '\n'):
        if self._output == None:
            print(message, end = end)
    
    def log(self, prefix, message):
        if self._output == None:
            print(prefix + ' ' + message)
        else:
            self._output.write(prefix + ' ' + message + '\n')
            self._output.flush()
    
    def debug(self, message):
        self.log('[Debug]', message)
    
    def info(self, message):
        self.log('[Info ]', message)
    
    def warn(self, message):
        self.log('[Warn ]', message)
    
    def error(self, message):
        self.log('[ERROR]', message)
    
    def getOutput(self):
        return self._output

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

def _callSubprocess(args):
    '''>>>_callSubprocess(args) -> True or (exitcode, stdout, stderr)
    Helper Function to call a subprocess in a different process.
    Calls the subprocess given via 'args'. Returns True, if
    the subprocess succeeded and returns the exitcode and the
    contents of the stdout and stderr of the subprocess on failure.
    '''
    subprocess = Popen(args, bufsize = -1, stdout = PIPE, stderr = PIPE)
    stdout, stderr = subprocess.communicate()
    subprocess.terminate()
    if subprocess.returncode != 0:
        return subprocess.returncode, stdout, stderr
    else:
        return True

class Util(object):
    
    @staticmethod
    def download(url, destFile, logger):
        '''>>> download(url, destFile, logger) -> HTTPResponse or path
        Downloads a file from 'url'. The retrieved file will be saved
        in 'destFile'. If 'destFile' is a directory, the file is saved
        in this directory with the same name it had on the server.
        Progress information is written to the logs via 'logger'.
        In the case of a connection failure, the HTTPResponse containing
        the reason is returned. On success, the path to the downloaded
        file is returned.
        '''
        destFile = destFile if not os.path.isdir(destFile) else os.path.join(destFile, os.path.basename(url))
        startTime = time()
        with closing(urlopen(url)) as download:
            totalLength = int(download.headers['Content-Length'])
            fifth = totalLength / 20
            with open(destFile, 'wb') as downloadFile:
                for i in range(20):
                    downloadFile.write(download.read(size = fifth))
                    logger.console('[Info ] ' + str(int(round(((i + 1) / 20.0) * 100))) + '%', end = '\r')
                downloadFile.write(download.read())
        logger.info('Download finished in ' + str(round(time() - startTime, 2)) + ' seconds.')
        return destFile
    
    @staticmethod
    def extract(sourceArchive, extractionDir, subDirFilter = None, allowedFileTypes = None, allowedPaths = None):
        '''>>> extract(sourceArchive, extractionDir, subDirFilter, allowedFileTypes, allowedPaths) -> path
        Extracts the archive located under 'sourceArchive'
        and puts its content under 'extractionDir'. If
        'subDirFilter' is specified as a list of directory
        names, those directories and their contents will not
        get extracted. If 'allowedFileTypes' is specified, only
        files with the given file ending are extracted. When
        'allowedPaths' is present, it overwrites the 'allowedFileTypes'
        for these paths. Returns the path to the first directory
        of the extracted content.
        '''
        subDirFilter = subDirFilter or []
        allowedPaths = allowedPaths if allowedPaths != None else []
        tarFile = tarfile.open(sourceArchive)
        if len(tarFile.getmembers()) == 0:
            return extractionDir
        baseDir = tarFile.getmembers()[0].name.split('/')[0]
        def check_members(members):
            allowedDirs = [baseDir + '/' + path for path in subDirFilter]
            whitelistPaths = [baseDir + '/' + path for path in allowedPaths]
            for member in members:
                if member.name == baseDir:
                    yield member
                    continue
                pathParts = member.name.split('/')
                if len(pathParts) < 2:
                    continue
                pathInWhitelist = member.name in whitelistPaths
                if len(allowedDirs) == 0 or pathParts[0] + '/' + pathParts[1] in allowedDirs or pathInWhitelist:
                    if allowedFileTypes == None or member.isdir() or os.path.splitext(member.name)[1] in allowedFileTypes or pathInWhitelist:
                        yield member
        tarFile.extractall(path = extractionDir, members = check_members(tarFile.getmembers()))
        return os.path.join(extractionDir, baseDir)
    
    @staticmethod
    def compile(ndkPath, tempDir, sourcePath, outputPath, cpuAbis, logger):
        '''>>> compile(ndkPath, tempDir, sourcePath, outputPath, cpuAbis, logger) -> success
        Compiles the source in 'sourcePath', using the ndk
        located at 'ndkPath'. An Application.mk file is
        expected under 'sourcePath'. All temporary objects
        will be placed under 'tempDir'. The output is placed
        under 'outputPath'/$(TARGET_ARCH_ABI). The cpu abis
        to compile for are given via 'cpuAbis'. Logs the
        executed command via 'logger'. Returns True, if the
        compilation succeeded, False on failure.
        '''
        args = Util.createCompileSubprocessArgs(ndkPath, tempDir, sourcePath, outputPath, cpuAbis, logger)
        return subprocess.call(args, cwd = sourcePath, stdout = logger.getOutput(), stderr = logger.getOutput()) == 0
    
    @staticmethod
    def createMd5Hash(filePath):
        '''>>> createHash(filePath) -> str
        Creates the md5 hash of the file at 'filePath'.
        '''
        md5Hash = md5()
        with open(filePath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), ''):
                md5Hash.update(chunk)
        return md5Hash.hexdigest()
    
    @staticmethod
    def downloadGitDir(url, destination, logger):
        '''>>> downloadGitDir(url, destination, logger) -> path
        Downloads all files located under the Github
        directory at 'url' and saves them into a folder
        in 'destination', which is called like the folder
        on GitHub. 'logger' is used to print some
        information. Returns the path to the downloaded
        directory on success and a HTTPResponse on
        failure.
        '''
        startTime = time()
        url = urlparse(url)
        connection = Connection(url.hostname)
        logger.info('Searching in git dir from "' + url.geturl() + '"...')
        connection.request('GET', url.path, headers={"Connection":" keep-alive"})
        response = connection.getresponse()
        if (response.status != 200):
            return response
        result = response.read()
        downloadUrls = []
        for match in re.finditer('href="' + url.path.replace('tree', 'blob', 1) + '/(.*?)"', result):
            fileName = match.group(1)
            if fileName == '':
                continue
            downloadUrls.append((fileName, ('https://raw.githubusercontent.com' + url.path + '/' + fileName).replace('/tree', '')))
        logger.info('Found ' + str(len(downloadUrls)) + ' files in ' + str(round(time() - startTime, 2)) + ' milliseconds.')
        destDir = os.path.join(destination, os.path.basename(url.path))
        if not os.path.isdir(destDir):
            os.mkdir(destDir)
        for downloadFile in downloadUrls:
            logger.info('Downloading ' + os.path.basename(downloadFile[1]) + ' ...')
            Util.download(downloadFile[1], os.path.join(destDir, downloadFile[0]), logger)
        return destDir
    
    @staticmethod
    def fillTemplate(templatePath, destination, **formatArguments):
        '''>>> fillTemplate(templatePath, destination, **formatArguments)
        Reads a template from 'templatePath', formats it
        using 'formatArguments' and saves the formatted
        template at 'destination'.
        '''
        templateContent = ''
        with open(templatePath) as template:
            templateContent = template.read()
        with open(destination, 'w') as output:
            output.write(templateContent.format(**formatArguments))
    
    @staticmethod
    def getShortVersion(version):
        '''>>> getShortVersion(version) -> shortVersion
        Returns the major and minor part of 'version'.
        '''
        return '.'.join(version.split('.')[:2])
    
    @staticmethod
    def escapeNDKParameter(parameter):
        '''escapeNDKParameter(parameter) -> escapedParameter
        Modifies a parameter so that it can be used by the ndk.
        '''
        if os.name == 'nt':
            return parameter.replace('\\', '/')
        else:
            return parameter
    
    @staticmethod
    def callSubprocessesMultiThreaded(subprocessArgs, logger):
        '''>>>callSubprocessesMultiThreaded(subprocessArgs, logger) -> success
        Executes the subprocesses constructed from the given 'subprocessArgs' in
        parrallel. If one of them fail, the exitcode, stdout and stderr are written
        to the logs via 'logger' and False is returned.
        '''
        pool = Pool(min(10, len(subprocessArgs)))
        handles = [pool.apply_async(_callSubprocess, [args]) for args in subprocessArgs]
        logger.debug('Started ' + str(len(handles)) + ' subprocesses.')
        pool.close()
        while len(handles) > 0:
            result = handles.pop(0).get()
            if result != True:
                logger.error('Subprocess exited with code ' + str(result[0]))
                logger.info(result[1])
                logger.error(result[2])
                return False
        return True
    
    @staticmethod
    def createCompileSubprocessArgs(ndkPath, tempDir, sourcePath, outputPath, abis, logger):
        '''>>> createCompileSubprocessArgs(ndkPath, tempDir, sourcePath, outputPath, abis, logger) -> arguments
        Create a list of arguments that can be used to create a subprocess to
        compile the source in 'sourcePath' using the ndk located at 'ndkPath'.
        An Application.mk file is expected under 'sourcePath'. All temporary
        objects will be placed under 'tempDir'. The cpu abis to compile for are
        given via 'abis'. The output is placed at 'outputPath'/$(TARGET_ARCH_ABI).
        Logs the executed command via 'logger'. Returns the list of arguments.
        '''
        args = [
            ndkPath,
            'NDK_OUT=' + Util.escapeNDKParameter(tempDir),
            'NDK_APPLICATION_MK=' + Util.escapeNDKParameter(sourcePath) + '/Application.mk',
            'NDK_PROJECT_PATH=' + Util.escapeNDKParameter(sourcePath),
            'NDK_APP_DST_DIR=' + Util.escapeNDKParameter(outputPath) + '/$(TARGET_ARCH_ABI)',
            'APP_ABI=' + ' '.join(abis if type(abis) in [list, tuple] else [abis])
        ]
        logger.debug(subprocess.list2cmdline(args))
        return args

class Builder(object):
    
    config = None
    
    def __init__(self, args):
        self.config = Configuration(args)
    
    def build(self):
        success = False
        versionList = self.config.versionList
        versions = {}
        tempdir = mkdtemp('PythonLibBuild')
        sourceDir = os.path.join(tempdir, 'extractedSources')
        try:
            startTime = time()
            if not self.config.check():
                return
            if os.path.exists(self.config.outputDir):
                if not os.path.isdir(self.config.outputDir) or len(os.listdir(self.config.outputDir)) != 0:
                    if self.config.warnOnOutputOverwrite:
                        self.config.log.warn('The output directory "' + self.config.outputDir + '" already exists.')
                        if self.config.logFile == None:
                            if raw_input('Press enter to overwrite the directory or c to cancel the build.') in ['c', 'C']:
                                self.config.log.error('Cancelling build.')
                                return
                    if not os.path.isdir(self.config.outputDir):
                        os.remove(self.config.outputDir)
                    else:
                        for i in range(3):
                            shutil.rmtree(self.config.outputDir, ignore_errors = True)
                            if not os.path.exists(self.config.outputDir):
                                break
                    sleep(0.5)
                    os.mkdir(self.config.outputDir)
            else:
                os.mkdir(self.config.outputDir)
            if not self.setupOptionalLibs(tempdir, sourceDir):
                return
            if len(versionList) == 0:
                versions = self.getAllAviablePythonVersions()
                if versions == None:
                    return
            else:
                connection = Connection(self.config.pythonServer)
                for version in versionList:
                    if self.getPatchFile(version) == None:
                        self.config.log.warn('No patch-file found for specified version ' + version + '. Ignoring this version.')
                        continue
                    versions[version] = self.versionToUrl(connection, version)
                connection.close()
            self.config.log.debug('Got ' + str(len(versions)) + ' versions to process...')
            for version, versionPath in versions.items():
                self.config.log.info('Processing Python version ' + version)
                versionOutputDir = os.path.join(self.config.outputDir, 'Python' + version)
                if not os.path.exists(versionOutputDir):
                    os.makedirs(versionOutputDir)
                downloadFile = self.downloadPythonSource(versionPath, tempdir)
                extractedDir = self.extractPythonArchive(downloadFile, sourceDir)
                if extractedDir == None:
                    return
                if not self.patchPythonSource(extractedDir, self.getPatchFile(version)):
                    self.config.log.error('Patching the sources failed for Python version ' + version + '!')
                    return
                self.config.log.info('Generating modules zip...')
                if not self.generateModulesZip(extractedDir, versionOutputDir):
                    self.config.log.error('Failed to create lib zip at ' + versionOutputDir + '!')
                    return
                if not self.compilePythonSource(extractedDir, version, tempdir):
                    self.config.log.error('Compilation failed for Python version ' + version + '!')
                    return
                self.cleanup(extractedDir, versionOutputDir)
            self.config.log.info('Done generating libraries.')
            if not self.generateJSON():
                return
            delta = time() - startTime
            deltaMinutes, deltaSeconds = divmod(delta, 60)
            deltaHours, deltaMinutes = divmod(deltaMinutes, 60)
            self.config.log.info('Building finished in ' + ((str(int(deltaHours)) + ' hours, ') if deltaHours != 0 else '')
                                 + str(int(deltaMinutes)) + ' minutes, ' + str(int(deltaSeconds)) + ' seconds and '
                                 + str(int(round((delta - int(delta)) * 1000))) + ' milliseconds.')
            success = True
        except KeyboardInterrupt:
            self.config.log.error('Cancelling build due to interrupt.')
        except Exception as e:
            import sys, traceback
            self.config.log.error('Caught exception: ' + str(e))
            traceback.print_exception(*(sys.exc_info() + (None, self.config.log.getOutput())))
        finally:
            self.config.log.info('Cleaning up...')
            shutil.rmtree(tempdir, ignore_errors = True)
            self.config.log.log('Build', 'SUCCESS' if success else 'FAILED')
            self.config.closeLog()
            return success
    
    def setupOptionalLibs(self, tempDir, sourceDir):
        self.config.log.info('Setting up optional libraries...')
        if not os.path.isdir(sourceDir):
            os.mkdir(sourceDir)
        self.config.log.info('Copying Python patch...')
        shutil.copytree(self.config.pythonPatchDir, os.path.join(sourceDir, 'PythonPatch'))
        libs = {'pythonPatch': os.path.join(sourceDir, 'PythonPatch')}
        for lib, data in self.config.additionalLibs.iteritems():
            makefilePath = os.path.join(self.config.filesDir, lib, lib + '-Android.mk')
            if not os.path.exists(makefilePath):
                self.config.log.warn('Ignoring library ' + lib + ', because no Android.mk file was found.')
                continue
            self.config.log.info('Downloading library ' + lib + ' from ' + data['url'] + '...')
            downloadFile = Util.download(data['url'], tempDir, self.config.log)
            self.config.log.info('Extracting ' + os.path.basename(downloadFile) + '...')
            extractDir = Util.extract(downloadFile, sourceDir, data.get('extraction_filter', None), ['.c', '.h', '.S'])
            self.config.log.info('Extracting done.')
            shutil.copy(makefilePath, os.path.join(extractDir, 'Android.mk'))
            for src, dest in data.get('file_copy_opr', []):
                dest = dest.replace('/', os.path.sep)
                shutil.copy(os.path.join(self.config.filesDir, lib, src), os.path.join(extractDir, dest))
            libs[lib] = extractDir
        applicationMKPath = os.path.join(sourceDir, 'Application.mk')
        Util.fillTemplate(
            os.path.join(self.config.filesDir, 'Application.mk'),
            applicationMKPath,
            pyShortVersion = ''
        )
        androidMKPath = os.path.join(sourceDir, 'Android.mk')
        outputDir = os.path.join(self.config.outputDir, 'libraries')
        with open(androidMKPath, 'w') as androidMK:
            androidMK.write('include $(call all-subdir-makefiles)')
        self.config.log.info('Compiling ' + str(len(self.config.additionalLibs)) + ' additional libraries...')
        success = False
        if self.config.useMultiThreading:
            subprocessArgs = [Util.createCompileSubprocessArgs(self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'),
                                                               sourceDir, outputDir, abi, self.config.log) for abi in self.config.cpuAbis]
            success = Util.callSubprocessesMultiThreaded(subprocessArgs, self.config.log)
        else:
            success = Util.compile(self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'),
                                   sourceDir, outputDir, self.config.cpuAbis, self.config.log)
        if not success:
            self.config.log.error('Compiling the additional libraries failed.')
            return False
        self.config.log.info('Compiling of the additional libraries succeeded.')
        os.remove(applicationMKPath)
        os.remove(androidMKPath)
        self.config.log.info('Patching Android.mk files...')
        for module, modulePath in libs.iteritems():
            androidMKPath = os.path.join(modulePath, 'Android.mk')
            if os.path.exists(androidMKPath):
                data = ''
                with open(androidMKPath) as source:
                    for line in source:
                        if 'LOCAL_SRC_FILES :=' in line:
                            data += 'LOCAL_SRC_FILES := ' + Util.escapeNDKParameter(self.config.outputDir) + '/libraries/$(TARGET_ARCH_ABI)/lib' + module + '.so\n'
                        elif 'LOCAL_SRC_FILES +=' in line:
                            continue
                        elif 'include $(BUILD_SHARED_LIBRARY)' in line:
                            data += 'include $(PREBUILT_SHARED_LIBRARY)\n'
                        else:
                            data += line
                with open(androidMKPath, 'w') as dest:
                    dest.write(data)
        self.config.log.info('Successfully generated additional libraries.')
        return True
    
    def getPatchFile(self, version):
        patchFile = os.path.join(self.config.patchesDir, 'python' + version + '.patch')
        if not os.path.exists(patchFile):
            patchFile = None
        return patchFile
    
    def getAllAviablePythonVersions(self):
        startTime = time()
        connection = Connection(self.config.pythonServer)
        self.config.log.info('Gathering Python versions at "' + connection.host + self.config.pythonServerPath + '"...')
        connection.request('GET', self.config.pythonServerPath, headers={"Connection":" keep-alive"})
        response = connection.getresponse()
        if (response.status != 200):
            self.config.log.error('Failed to connect to "' + connection.host + '/' + self.config.pythonServerPath + '":')
            self.config.log.error('Response ' + str(response.status) + ': ' + response.reason)
            return None
        result = response.read().split('\n')
        self.config.log.info('Got a response in ' + str(round(time() - startTime, 2)) + ' milliseconds.')
        versions = {}
        self.config.log.info('Checking availability of the sources...')
        for line in result:
            versionMatch = re.search(r'href\s*=\s*"(.*)"', line)
            if versionMatch == None:
                continue
            version = versionMatch.group(1)
            if re.match('\A\d+\.\d+(\.\d+)*/\Z', version) == None:
                continue
            version = version[:-1]
            if self.getPatchFile(version) == None:
                self.config.log.info('Ignoring version ' + version + ' because no patch-file was found.')
                continue
            url = self.versionToUrl(connection, version)
            if type(url) != str:
                if version != '2.0':
                    self.config.log.info('Ignoring version ' + version + ' because it has no downloadable source code. ' +
                                         'Maybe this version is still in development.')
                continue
            versions[version] = url
        connection.close()
        return versions
    
    def versionToUrl(self, connection, version):
        path = self.config.pythonServerPath + version + '/Python-' + version + '.tgz'
        self.config.log.debug('Checking Python version at "' + connection.host + path + '"...')
        startTime = time()
        connection.request('HEAD', path, headers={"Connection":" keep-alive"})
        response = connection.getresponse()
        response.read() # Empty the request
        self.config.log.debug('Got a response in ' + str(round(time() - startTime, 2)) + ' seconds.')
        if response.status != 200:
            return response
        return path
    
    def downloadPythonSource(self, versionPath, downloadDir):
        self.config.log.info('Downloading Python source from "' + self.config.pythonServer + versionPath + '"...')
        return Util.download('https://' + self.config.pythonServer + versionPath, downloadDir, self.config.log)
    
    def extractPythonArchive(self, sourceArchive, extractedDir):
        self.config.log.info('Extracting ' + sourceArchive + '...')
        try:
            return Util.extract(sourceArchive, extractedDir, ['Include', 'Lib', 'Modules', 'Objects', 'Parser', 'Python'],
                                ['.c', '.h', '.py', '.pyc', '.inc'], ['LICENSE'])
        except tarfile.CompressionError as error:
            self.config.log.error('Failed to extract ' + sourceArchive + ': Archive is compressed with an unsupported compression.')
            print(error)
            return None
        self.config.log.info('Extracting done.')
    
    def patchPythonSource(self, sourcePath, patchFilePath):
        args = [self.config.gitPath, '-t', '-p1', '-d', sourcePath, '-i', patchFilePath]
        self.config.log.info('Patching the source code with ' + patchFilePath + '...')
        self.config.log.debug(subprocess.list2cmdline(args))
        return subprocess.call(args, stdout = self.config.log.getOutput(), stderr = self.config.log.getOutput()) == 0
    
    def generateModulesZip(self, sourcePath, outputDir):
        outputPath = os.path.join(outputDir, 'lib')
        if (os.path.exists(outputPath)):
            os.remove(outputPath)
        shutil.copy(os.path.join(sourcePath, 'LICENSE'), os.path.join(sourcePath, 'Lib', 'LICENSE.txt'))
        shutil.rmtree(os.path.join(sourcePath, 'Lib', 'test')) # TODO: Make this remove all test and test directories to save storage space
        return shutil.make_archive(outputPath, 'zip', os.path.join(sourcePath, 'Lib')).endswith('lib.zip')
    
    def compilePythonSource(self, sourcePath, pythonVersion, tempDir):
        parentDir = os.path.dirname(sourcePath)
        # Setup the Application.mk.
        Util.fillTemplate(
            os.path.join(self.config.filesDir, 'Application.mk'),
            os.path.join(parentDir, 'Application.mk'),
            pyShortVersion = Util.getShortVersion(pythonVersion)
        )
        with open(os.path.join(parentDir, 'Android.mk'), 'w') as androidMK:
            androidMK.write('include $(call all-subdir-makefiles)')
        # Copy the Android.mk and configuration files
        shutil.copy(os.path.join(self.config.filesDir, 'Android.mk'), sourcePath)
        shutil.copy(os.path.join(self.config.filesDir, 'config3.c' if int(pythonVersion[0]) >= 3 else 'config.c'),
                    os.path.join(sourcePath, 'Modules', 'config.c'))
        shutil.copy(os.path.join(self.config.filesDir, 'pyconfig.h'), os.path.join(sourcePath, 'Include'))
        # Setup module libraries
        for lib, libData in self.config.additionalLibs.items():
            if (len(libData.get('req', [])) < 1):
                continue
            moduleName = None # TODO: Handle multiple dependencies
            if int(pythonVersion[0]) >= 3:
                moduleName = libData['req3'][0]
            else:
                moduleName = libData['req'][0]
            moduleDir = os.path.join(parentDir, moduleName)
            if not os.path.exists(moduleDir):
                os.mkdir(moduleDir)
            pythonDir = os.path.basename(sourcePath)
            moduleWildcards = [moduleName + '.[ch]', moduleName + 'module.c', moduleName + '/*.c']
            moduleWildcards = ['$(wildcard $(LOCAL_PATH)/../' + pythonDir + '/Modules/' + wildcard + ')' for wildcard in moduleWildcards]
            Util.fillTemplate(
                os.path.join(self.config.filesDir, 'module-Android.mk'),
                os.path.join(moduleDir, 'Android.mk'),
                moduleSourceWildcards = ' '.join(moduleWildcards),
                libDependencies = lib
            )
        # Compile
        self.config.log.info('Compiling Python ' + pythonVersion + '...')
        outputDir = os.path.join(self.config.outputDir, 'Python' + pythonVersion)
        if self.config.useMultiThreading:
            subprocessArgs = [Util.createCompileSubprocessArgs(self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'),
                                                               parentDir, outputDir, abi, self.config.log) for abi in self.config.cpuAbis]
            return Util.callSubprocessesMultiThreaded(subprocessArgs, self.config.log)
        else:
            return Util.compile(self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'),
                                parentDir, outputDir, self.config.cpuAbis, self.config.log)
    
    def cleanup(self, sourcePath, outputDir):
        self.config.log.info('Removing unnecessary files...')
        shutil.rmtree(sourcePath)
        for subdir in os.listdir(outputDir):
            if os.path.isdir(os.path.join(outputDir, subdir)):
                for libfile in os.listdir(os.path.join(outputDir, subdir)):
                    if libfile[3:-3] in self.config.additionalLibs.keys() or libfile == 'libpythonPatch.so':
                        os.remove(os.path.join(outputDir, subdir, libfile))
        sourceParentPath = os.path.dirname(sourcePath)
        additionalPythonModules = []
        for moduleData in self.config.additionalLibs.itervalues():
            additionalPythonModules += moduleData.get('req', [])
            additionalPythonModules += moduleData.get('req3', [])
        for subdir in os.listdir(sourceParentPath):
            if os.path.isdir(os.path.join(sourceParentPath, subdir)):
                if subdir in additionalPythonModules:
                    shutil.rmtree(os.path.join(sourceParentPath, subdir))
    
    def generateJSON(self):
        self.config.log.info('Generating JSON file...')
        additionalLibs = set() 
        additionalLibsData = '"libraries": {\n'
        for subdir in os.listdir(os.path.join(self.config.outputDir, 'libraries')):
            for libFile in os.listdir(os.path.join(self.config.outputDir, 'libraries', subdir)):
                if libFile.startswith('lib') and libFile.endswith('.so'):
                    additionalLibs.add(libFile[3:-3])
        for lib in additionalLibs:
            additionalLibsData += '"' + lib + '": {\n'
            for architecture in os.listdir(os.path.join(self.config.outputDir, 'libraries')):
                if 'lib' + lib + '.so' in os.listdir(os.path.join(self.config.outputDir, 'libraries', architecture)):
                    filePath = os.path.join(self.config.outputDir, 'libraries', architecture, 'lib' + lib + '.so')
                    additionalLibsData += '"' + architecture + '": ["output/libraries/' + architecture + '/lib' + lib + '.so", "' + Util.createMd5Hash(filePath) + '"],\n'
            if self.config.additionalLibs.has_key(lib):
                reqs = self.config.additionalLibs[lib].get('req', [])[:]
                reqs += self.config.additionalLibs[lib].get('req3', [])
                additionalLibsData += '"required_for": [' + ', '.join(['"' + requirement + '"' for requirement in set(reqs)]) + ']\n'
            else:
                additionalLibsData = additionalLibsData[:-2] + '\n'
            additionalLibsData += '},\n'
        additionalLibsData = additionalLibsData[:-2] + '\n'
        additionalLibsData += '},\n'
        pythonData = ''
        for versionDir in os.listdir(self.config.outputDir):
            if versionDir == 'libraries':
                continue
            version = versionDir[6:]
            pythonData += '"' + version + '": {\n'
            modulesFile = os.path.join(self.config.outputDir, versionDir, 'lib.zip')
            if not os.path.exists(modulesFile):
                self.config.log.error('lib.zip not found in ' + os.path.join(self.config.outputDir, versionDir) + '.')
                return False
            for architecture in os.listdir(os.path.join(self.config.outputDir, versionDir)):
                if not os.path.isdir(os.path.join(self.config.outputDir, versionDir, architecture)):
                    continue
                pythonData += '"' + architecture + '": {\n'
                if not 'libpython' + Util.getShortVersion(version) + '.so' in os.listdir(os.path.join(self.config.outputDir, versionDir, architecture)):
                    self.config.log.error('The python library was not found in ' + os.path.join(self.config.outputDir, versionDir, architecture) + '.')
                    return False
                for libFile in os.listdir(os.path.join(self.config.outputDir, versionDir, architecture)):
                    lib = ''
                    if 'libpython' in libFile:
                        lib = 'pythonLib'
                    else:
                        lib = libFile[:-3]
                    libPath = os.path.join(self.config.outputDir, versionDir, architecture, libFile)
                    pythonData += '"' + lib + '": ["output/' + versionDir + '/' + architecture + '/' + libFile + '", "' + Util.createMd5Hash(libPath) + '"],\n'
                pythonData = pythonData[:-2] + '\n'
                pythonData += '},\n'
            pythonData += '"lib": ["output/' + versionDir + '/lib.zip", "' + Util.createMd5Hash(modulesFile) + '"]\n'
            pythonData += '},\n'
        pythonData += '"__version__": 1\n'
        with open(os.path.join(os.path.dirname(self.config.outputDir), 'index.json'), 'w') as jsonFile:
            jsonFile.write('{\n' + additionalLibsData + pythonData + '}\n')
        self.config.log.info('Successfully generated JSON file.')
        return True

if __name__ == '__main__':
    parser = ArgumentParser(description = DESCRIPTION)
    parser.add_argument('--logFile', help = 'The path to a log file. If not specified, all output goes to the console.')
    parser.add_argument('--configFile', default = 'config.cfg', help = 'The path to the config file.')
    parser.add_argument('--patchesDir', default = 'patches', help = 'The path to the directory containing the patch files. Defaults to the directory "patches" in the current directory.')
    parser.add_argument('--outputDir', default = 'output', help = 'The path to the output directory. Defaults to the directory "output" in the current directory.')
    parser.add_argument('--filesDir', default = 'files', help = 'The path to the files directory. Defaults to the directory "files" in the current directory.')
    parser.add_argument('--gitPath', help = 'The path to the patch executable in the git directory.')
    parser.add_argument('--ndkPath', help = 'The path to the ndk-build executable.')
    parser.add_argument('--pythonPatchDir', help = 'The path to the directory where the pythonPatch library source code can be found.')
    parser.add_argument('--pythonServer', default = Configuration.pythonServer, help = 'The host address of the Python server. Defaults to "' + Configuration.pythonServer + '".')
    parser.add_argument('--pythonServerPath', default = Configuration.pythonServerPath, help = 'The path on the Python server to see all available Python versions. Defaults to "' + Configuration.pythonServerPath + '".')
    parser.add_argument('--cpuAbis', nargs = '*', default = Configuration.ALL_CPU_ABIS, help = 'The cpu abis to compile for. Defaults to all. Possible values are ' + ', '.join(Configuration.ALL_CPU_ABIS))
    parser.add_argument('--disableMultiThreading', default = False, action='store_true', help = 'If set, turns off the multithreading of the compilation. By default, multithreading is turned on.')
    parser.add_argument('versions', nargs = '*', help = 'The Python versions to download. Empty means all versions available.')
    args = parser.parse_args()
    builder = Builder(args)
    builder.build()
