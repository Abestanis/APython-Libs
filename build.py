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

import re
import shutil
import os
import buildutils
from argparse import ArgumentParser
from time     import time, sleep
from tempfile import mkdtemp
from config   import Configuration

#TODO: Update README.md with all modules and dependencies

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
                connection = buildutils.Connection(self.config.pythonServer)
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
            makefilePath = os.path.join(self.config.filesDir, lib, 'Android.mk')
            if not os.path.exists(makefilePath):
                self.config.log.warn('Ignoring library ' + lib + ', because no Android.mk file was found.')
                continue
            self.config.log.info('Downloading library ' + lib + ' from ' + data['url'] + '...')
            downloadFile = buildutils.download(data['url'], tempDir, self.config.log)
            self.config.log.info('Extracting ' + os.path.basename(downloadFile) + '...')
            extractDir = buildutils.extract(downloadFile, sourceDir, data.get('extraction_filter', None), ['.c', '.h', '.S'])
            self.config.log.info('Extracting done.')
            shutil.copy(makefilePath, os.path.join(extractDir, 'Android.mk'))
            for src, dest in data.get('file_copy_opr', []):
                dest = dest.replace('/', os.path.sep)
                shutil.copy(os.path.join(self.config.filesDir, lib, src), os.path.join(extractDir, dest))
            libs[lib] = extractDir
        applicationMKPath = os.path.join(sourceDir, 'Application.mk')
        buildutils.fillTemplate(
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
            subprocessArgs = [buildutils.createCompileSubprocessArgs(self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'),
                                                               sourceDir, outputDir, abi, self.config.log) for abi in self.config.cpuAbis]
            success = buildutils.callSubprocessesMultiThreaded(subprocessArgs, self.config.log)
        else:
            success = buildutils.compile(self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'),
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
                            data += 'LOCAL_SRC_FILES := ' + buildutils.escapeNDKParameter(self.config.outputDir) + '/libraries/$(TARGET_ARCH_ABI)/lib' + module + '.so\n'
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
        connection = buildutils.Connection(self.config.pythonServer)
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
        return buildutils.download('https://' + self.config.pythonServer + versionPath, downloadDir, self.config.log)
    
    def extractPythonArchive(self, sourceArchive, extractedDir):
        self.config.log.info('Extracting ' + sourceArchive + '...')
        try:
            return buildutils.extract(sourceArchive, extractedDir, ['Include', 'Lib', 'Modules', 'Objects', 'Parser', 'Python'],
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
        buildutils.fillTemplate(
            os.path.join(self.config.filesDir, 'Application.mk'),
            os.path.join(parentDir, 'Application.mk'),
            pyShortVersion = buildutils.getShortVersion(pythonVersion)
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
            buildutils.fillTemplate(
                os.path.join(self.config.filesDir, 'module-Android.mk'),
                os.path.join(moduleDir, 'Android.mk'),
                moduleSourceWildcards = ' '.join(moduleWildcards),
                libDependencies = lib
            )
        # Compile
        self.config.log.info('Compiling Python ' + pythonVersion + '...')
        outputDir = os.path.join(self.config.outputDir, 'Python' + pythonVersion)
        if self.config.useMultiThreading:
            subprocessArgs = [buildutils.createCompileSubprocessArgs(self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'),
                                                               parentDir, outputDir, abi, self.config.log) for abi in self.config.cpuAbis]
            return buildutils.callSubprocessesMultiThreaded(subprocessArgs, self.config.log)
        else:
            return buildutils.compile(self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'),
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
                    additionalLibsData += '"' + architecture + '": ["output/libraries/' + architecture + '/lib' + lib + '.so", "' + buildutils.createMd5Hash(filePath) + '"],\n'
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
                if not 'libpython' + buildutils.getShortVersion(version) + '.so' in os.listdir(os.path.join(self.config.outputDir, versionDir, architecture)):
                    self.config.log.error('The python library was not found in ' + os.path.join(self.config.outputDir, versionDir, architecture) + '.')
                    return False
                for libFile in os.listdir(os.path.join(self.config.outputDir, versionDir, architecture)):
                    lib = ''
                    if 'libpython' in libFile:
                        lib = 'pythonLib'
                    else:
                        lib = libFile[:-3]
                    libPath = os.path.join(self.config.outputDir, versionDir, architecture, libFile)
                    pythonData += '"' + lib + '": ["output/' + versionDir + '/' + architecture + '/' + libFile + '", "' + buildutils.createMd5Hash(libPath) + '"],\n'
                pythonData = pythonData[:-2] + '\n'
                pythonData += '},\n'
            pythonData += '"lib": ["output/' + versionDir + '/lib.zip", "' + buildutils.createMd5Hash(modulesFile) + '"]\n'
            pythonData += '},\n'
        pythonData += '"__version__": 2\n'
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
