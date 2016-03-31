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
from cache    import Cache

class Builder(object):
    
    config = None
    cache = None
    
    def __init__(self, args):
        self.config = Configuration(args)
        self.cache = Cache(self.config.cacheDir)
        if (args.clear_cache):
            self.cache.clear(ignore_errors = True)
            self.cache.ensureCacheDir()
    
    def build(self):
        '''>>> build() -> success
        Build all python libraries and modules for Android.
        '''
        success = False
        versionList = self.config.versionList
        versions = {}
        tempdir = mkdtemp('PythonLibBuild')
        sourceDir = os.path.join(tempdir, 'extractedSources')
        try:
            startTime = time()
            if not self.config.check():
                return
            self.config.parseLibrariesData()
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
                if downloadFile == None:
                    return
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
            self.updateReadMe()
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
            if success:
                self.cache.clear(ignore_errors = True)
            self.config.log.log('Build', 'SUCCESS' if success else 'FAILED')
            self.config.closeLog()
            return success
    
    def setupOptionalLibs(self, tempDir, sourceDir):
        '''>>> setupOptionalLibs(tempDir, sourceDir) -> success
        Download and compile all additional libraries.
        When finished, all libraries and their data are stored in the
        output directory and 'sourceDir' is set up to compile the
        python binaries in it.
        '''
        self.config.log.info('Setting up optional libraries...')
        if not os.path.isdir(sourceDir):
            os.mkdir(sourceDir)
        self.config.log.info('Copying Python patch...')
        shutil.copytree(self.config.pythonPatchDir, os.path.join(sourceDir, 'PythonPatch'))
        libs = {'pythonPatch': os.path.join(sourceDir, 'PythonPatch')}
        minSdkListItems = self.config.computeLibMinAndroidSdkList().items()
        minSdkListItems = sorted(minSdkListItems, reverse = True) # Beginn with the latest sdk version
        for sdkVersion, libraryList in minSdkListItems:
            for libraryName in libraryList:
                libraryData = self.config.additionalLibs[libraryName]
                makefilePath = os.path.join(self.config.filesDir, libraryName, 'Android.mk')
                if not os.path.exists(makefilePath):
                    makefilePath = None
                    self.config.log.info('No local Android.mk file was found for library ' + libraryName + '.')
                extractDir = None
                maxRetries = 5
                for retry in range(maxRetries):
                    self.config.log.info('Downloading library ' + libraryName + ' from ' + libraryData['url'] + '...')
                    downloadFile = self.cache.download(libraryData['url'], tempDir, self.config.log)
                    if downloadFile == None:
                        self.config.log.warn('Download from ' + libraryData['url'] + ' failed, retrying ('
                                             + str(retry + 1) + '/' + str(maxRetries) + ')')
                        continue
                    self.config.log.info('Extracting ' + os.path.basename(downloadFile) + '...')
                    extractDir = buildutils.extract(downloadFile, sourceDir, libraryData.get('extractionFilter', None))
                    if extractDir == False:
                        self.config.log.error('Could not extract archive from ' + libraryData['url'] + ': Unsupported archive format!')
                        return False
                    if type(extractDir) != str:
                        self.config.log.warn('Extraction of archive from ' + libraryData['url'] + ' failed, retrying ('
                                             + str(retry + 1) + '/' + str(maxRetries) + ')')
                        continue
                    break
                else:
                    self.config.log.error('Download from ' + libraryData['url'] + ' failed!')
                    return False
                self.config.log.info('Extracting done.')
                if makefilePath:
                    shutil.copy(makefilePath, os.path.join(extractDir, 'Android.mk'))
                if not os.path.exists(os.path.join(extractDir, 'Android.mk')):
                    self.config.log.warn('No Android.mk file was found for library ' + libraryName + ', ignoring it.')
                    shutil.rmtree(extractDir, ignore_errors = True)
                    continue
                diffPath = os.path.join(self.config.filesDir, libraryName, 'patch.diff')
                if os.path.exists(diffPath):
                    self.config.log.info('Patching ' + libraryName + '...')
                    if not buildutils.applyPatch(self.config.gitPath, extractDir, diffPath, self.config.log):
                        self.config.log.error('Applying patch (' + diffPath + ') failed for library ' + libraryName + ', aborting!')
                        return False
                if 'data' in libraryData.keys():
                    for dataEntry in libraryData['data']:
                        dataSource  = dataEntry[0]
                        dataName    = dataEntry[1]
                        dataSrcPath = os.path.join(extractDir, dataSource)
                        if not os.path.exists(dataSrcPath):
                            self.config.log.warn('Data source defined for library ' + libraryName + ' does not exist: ' +
                                                 dataSource + '. Skipping it.')
                            continue
                        if os.path.isdir(dataSrcPath):
                            shutil.make_archive(os.path.join(self.config.outputDir, 'data', dataName), 'zip', root_dir = extractDir, base_dir = dataSource)
                        else:
                            shutil.copy(dataSrcPath, os.path.join(self.config.outputDir, 'data', dataName + os.path.splitext(dataSrcPath)[1]))
                libs[libraryName] = extractDir
            applicationMKPath = os.path.join(sourceDir, 'Application.mk')
            buildutils.fillTemplate(
                os.path.join(self.config.filesDir, 'Application.mk'),
                applicationMKPath,
                pyShortVersion = '',
                androidSdkVersion = sdkVersion
            )
            androidMKPath = os.path.join(sourceDir, 'Android.mk')
            outputDir = os.path.join(self.config.outputDir, 'libraries')
            with open(androidMKPath, 'w') as androidMK:
                androidMK.write('include $(call all-subdir-makefiles)')
            self.config.log.info('Compiling ' + str(len(libraryList)) + ' additional libraries for Android Sdk version ' + str(sdkVersion) + '...')
            success = False
            if self.config.useMultiThreading:
                subprocessArgs = [buildutils.createCompileSubprocessArgs(
                        self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'), sourceDir, outputDir, abi, self.config.log
                    ) for abi in self.config.cpuAbis]
                success = buildutils.callSubprocessesMultiThreaded(subprocessArgs, self.config.log)
            else:
                success = buildutils.compile(self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'),
                                             sourceDir, outputDir, self.config.cpuAbis, self.config.log)
            if not success:
                self.config.log.error('Compiling the additional libraries failed.')
                return False
            self.config.log.info('Compiling of ' + str(len(libraryList)) + ' additional libraries succeeded.')
            os.remove(applicationMKPath)
            os.remove(androidMKPath)
            if sdkVersion != minSdkListItems[-1][0]:
                for libraryName in libraryList:
                    os.rename(os.path.join(libs[libraryName], 'Android.mk'), os.path.join(libs[libraryName], 'Android.mk.d'))
        self.config.log.info('Compiling of all (' + str(len(libs)) + ') additional libraries succeeded.')
        for libPath in libs.itervalues():
            if os.path.exists(os.path.join(libPath, 'Android.mk.d')):
                os.rename(os.path.join(libPath, 'Android.mk.d'), os.path.join(libPath, 'Android.mk'))
        self.config.log.info('Patching Android.mk files...')
        for module, modulePath in libs.iteritems():
            androidMKPath = os.path.join(modulePath, 'Android.mk')
            if os.path.exists(androidMKPath):
                data = ''
                with open(androidMKPath) as source:
                    for line in source:
                        if 'LOCAL_SRC_FILES :=' in line:
                            data += line.replace('LOCAL_SRC_FILES', 'LOCAL_SRC_FILES := ' + buildutils.escapeNDKParameter(self.config.outputDir)
                                                 + '/libraries/$(TARGET_ARCH_ABI)/lib' + module + '.so\nOLD_LOCAL_SRC_FILES')
                        elif 'LOCAL_SRC_FILES +=' in line:
                            data += line.replace('LOCAL_SRC_FILES', 'OLD_LOCAL_SRC_FILES')
                        elif 'include $(BUILD_SHARED_LIBRARY)' in line:
                            data += 'include $(PREBUILT_SHARED_LIBRARY)\n'
                        else:
                            data += line
                with open(androidMKPath, 'w') as dest:
                    dest.write(data)
        self.config.log.info('Successfully generated additional libraries.')
        return True
    
    def getPatchFile(self, version):
        '''>>> getPatchFile(version) -> path
        Return the path to the patch file for the specified Python version.
        '''
        patchFile = os.path.join(self.config.patchesDir, 'python' + version + '.patch')
        if not os.path.exists(patchFile):
            patchFile = None
        return patchFile
    
    def getAllAviablePythonVersions(self):
        '''>>> getAllAviablePythonVersions() -> version to url dict
        Query all available Python versions from the source server
        and returns a dict with a version to download url mapping.
        Versions are also filtered by the availability of a patch file
        for that version.
        '''
        startTime = time()
        connection = buildutils.Connection(self.config.pythonServer)
        self.config.log.info('Gathering Python versions at "' + connection.host + self.config.pythonServerPath + '"...')
        connection.request('GET', self.config.pythonServerPath, headers={"Connection":" keep-alive"})
        response = connection.getresponse()
        if response.status != 200:
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
        '''>>> versionToUrl(connection, version) -> url
        Takes an existing connection to the Python source server and
        and queries it for the downloadable of the requested Python
        version. If the version exists, the url to its source is
        returned, otherwise the network response is returned.
        '''
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
        '''>>> downloadPythonSource(versionPath, downloadDir) -> path / None
        Download a Python source archive from the Python source server
        at the sub-path 'versionPath' and stores it in 'downloadDir'.
        Returns the path to the downloaded archive on sucess or None
        on failure.
        '''
        self.config.log.info('Downloading Python source from "' + self.config.pythonServer + versionPath + '"...')
        return self.cache.download('https://' + self.config.pythonServer + versionPath, downloadDir, self.config.log)
    
    def extractPythonArchive(self, sourceArchive, extractedDir):
        '''>>> extractPythonArchive(sourceArchive, extractedDir) -> path or None
        Extract the Python archive at 'sourceArchive' to 'extractedDir'.
        Returns the path to the first directory of the extracted archive
        on success or None on error.
        '''
        self.config.log.info('Extracting ' + sourceArchive + '...')
        res = buildutils.extract(sourceArchive, extractedDir, ['Include', 'Lib', 'Modules', 'Objects', 'Parser', 'Python', 'LICENSE', 'README'],
                                 ['.c', '.h', '.py', '.pyc', '.inc', '.txt', '', '.gif', '.png', '.def'])
        if res == False:
            self.config.log.error('Failed to extract ' + sourceArchive + ': Archive is compressed with an unsupported compression.')
            return None
        elif res == None:
            self.config.log.error('Failed to extract ' + sourceArchive + '!')
        return res
    
    def patchPythonSource(self, sourcePath, patchFilePath):
        '''>>> patchPythonSource(sourcePath, patchFilePath) -> success
        Apply the patch at 'patchFilePath' to the Python source at 'sourcePath'.
        '''
        return buildutils.applyPatch(self.config.gitPath, sourcePath, patchFilePath, self.config.log)
    
    def generateModulesZip(self, sourcePath, outputDir):
        '''>>> generateModulesZip(sourcePath, outputDir) -> success
        Generate the Python modules zip from the source at 'sourcePath'
        and store it into 'outputDir'.
        '''
        outputPath = os.path.join(outputDir, 'lib')
        if os.path.exists(outputPath):
            os.remove(outputPath)
        shutil.copy(os.path.join(sourcePath, 'LICENSE'), os.path.join(sourcePath, 'Lib', 'LICENSE.txt'))
        shutil.rmtree(os.path.join(sourcePath, 'Lib', 'test')) # TODO: Make this remove all test and test directories to save storage space
        return shutil.make_archive(outputPath, 'zip', os.path.join(sourcePath, 'Lib')).endswith('lib.zip')
    
    def compilePythonSource(self, sourcePath, pythonVersion, tempDir):
        '''>>> compilePythonSource(sourcePath, pythonVersion, tempDir) -> success
        Compile the source of the given Python version located at 'sourcePath'
        and stores the compiled binaries into the output directory.
        '''
        parentDir = os.path.dirname(sourcePath)
        # Setup the Application.mk.
        buildutils.fillTemplate(
            os.path.join(self.config.filesDir, 'Application.mk'),
            os.path.join(parentDir, 'Application.mk'),
            pyShortVersion = buildutils.getShortVersion(pythonVersion),
            androidSdkVersion = self.config.DEFAULT_MIN_SKD_VERSION
        )
        with open(os.path.join(parentDir, 'Android.mk'), 'w') as androidMK:
            androidMK.write('include $(call all-subdir-makefiles)')
        # Copy the Android.mk and configuration files
        shutil.copy(os.path.join(self.config.filesDir, 'Android.mk'), sourcePath)
        shutil.copy(os.path.join(self.config.filesDir, 'config3.c' if int(pythonVersion[0]) >= 3 else 'config.c'),
                    os.path.join(sourcePath, 'Modules', 'config.c'))
        shutil.copy(os.path.join(self.config.filesDir, 'pyconfig.h'), os.path.join(sourcePath, 'Include'))
        # Setup module libraries
        moduleDeps = {}
        for lib, libData in self.config.additionalLibs.items():
            moduleNames = []
            if 'pyModuleReq' in libData.keys():
                moduleNames = libData['pyModuleReq']
            if int(pythonVersion[0]) >= 3 and 'py3ModuleReq' in libData.keys():
                moduleNames = libData['py3ModuleReq']
            if len(moduleNames) < 1:
                continue
            for moduleName in moduleNames:
                if moduleName in moduleDeps:
                    moduleDeps[moduleName].append(lib)
                else:
                    moduleDeps[moduleName] = [lib]
        for moduleName, moduleDependencies in moduleDeps.iteritems():
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
                libDependencies = ' '.join(moduleDependencies)
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
        '''>>> cleanup(sourcePath, outputDir)
        Remove unnecessary build artefacts in the 'outputDir'
        and cleans the build directory located at 'sourcePath'
        from the last build, so another Python version can be
        compiled there.
        '''
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
            additionalPythonModules += moduleData.get('pyModuleReq', [])
            additionalPythonModules += moduleData.get('py3ModuleReq', [])
        for subdir in os.listdir(sourceParentPath):
            if os.path.isdir(os.path.join(sourceParentPath, subdir)):
                if subdir in additionalPythonModules:
                    shutil.rmtree(os.path.join(sourceParentPath, subdir))
    
    def generateJSON(self):
        '''>>> generateJSON() -> success
        Generate the JSON file with all information needed
        by a connecting client to download the created data.
        '''
        self.config.log.info('Generating JSON file...')
        requirementData = '"requirements": {\n'
        for libName, libData in self.config.additionalLibs.iteritems():
            deps = ['libraries/' + dep for dep in libData.get('dependencies', [])]
            deps += ['data/' + dep[1] for dep in libData.get('data', [])]
            if 'minAndroidSdk' in libData:
                deps += ['androidSdk/' + str(libData['minAndroidSdk'])]
            if len(deps) > 0:
                requirementData += '"libraries/' + libName + '" : ["' + '", "'.join(deps) + '"],\n'
        moduleDeps = {}
        for lib, libData in self.config.additionalLibs.items():
            moduleNames = []
            if 'pyModuleReq' in libData.keys():
                moduleNames = libData['pyModuleReq']
            if 'py3ModuleReq' in libData.keys():
                moduleNames = libData['py3ModuleReq']
            if len(moduleNames) < 1:
                continue
            for moduleName in moduleNames:
                if moduleName in moduleDeps:
                    moduleDeps[moduleName].append(lib)
                else:
                    moduleDeps[moduleName] = [lib]
        for moduleName, moduleDependencies in moduleDeps.iteritems():
            requirementData += '"pyModule/' + moduleName + '" : ["' + '", "'.join(moduleDependencies) + '"],\n'
        requirementData = requirementData[:-2] + '\n},\n'
        
        datafilesData = '"data": {\n'
        for libData in self.config.additionalLibs.itervalues():
            if 'data' in libData.keys():
                for data in libData['data']:
                    datafilesData += '"' + data[1] + '" : {\n'
                    dataPath = os.path.join(self.config.outputDir, 'data', data[1])
                    if not os.path.exists(dataPath):
                        dataPath += '.zip'
                    dataFile = os.path.basename(dataPath)
                    datafilesData += '"path": ["output/data/' + dataFile + '", "' + buildutils.createMd5Hash(dataPath) + '"],\n'
                    if data[2] != 'files/data':
                        datafilesData += '"dest": "' + data[2] + '",\n'
                    datafilesData = datafilesData[:-2] + '\n},\n'
        datafilesData = datafilesData[:-2] + '\n},\n'
        
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
            additionalLibsData = additionalLibsData[:-2] + '\n},\n'
        additionalLibsData = additionalLibsData[:-2] + '\n},\n'
        
        pythonData = ''
        for versionDir in os.listdir(self.config.outputDir):
            if versionDir == 'libraries' or versionDir == 'data':
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
        pythonData += '"__version__": 1\n'
        with open(os.path.join(os.path.dirname(self.config.outputDir), 'index.json'), 'w') as jsonFile:
            jsonFile.write('{\n' + requirementData + datafilesData + additionalLibsData + pythonData + '}\n')
        self.config.log.info('Successfully generated JSON file.')
        return True
    
    def updateReadMe(self):
        '''>>> updateReadMe()
        Update the ReadMe file to display all currently
        available libraries.
        '''
        self.config.log.info('Updating README.md...')
        readmeTemplatePath = os.path.join(self.config.currDir, 'README.md.template')
        readmePath = os.path.join(self.config.currDir, 'README.md')
        # itemTemplate = '* {libName} (from {url}) for {modules}\n'
        libList = ''
        for libraryName, libraryData in self.config.additionalLibs.iteritems():
            libList += '* ' + libraryName + ' (from ' + libraryData['url'] + ')'
            depList = [lib for lib, libData in self.config.additionalLibs.items() if libraryName in libData.get('dependencies', [])]
            if 'pyModuleReq' in libraryData.keys() or 'py3ModuleReq' in libraryData.keys():
                moduleList = libraryData.get('pyModuleReq', []) + libraryData.get('py3ModuleReq', [])
                libList += ' for the Python module' + ('s' if len(moduleList) > 1 else '') + ' ' + ', '.join(moduleList)
                if len(depList) > 0:
                    libList += ' and'
            if len(depList) > 0:
                libList += ' for the librar' + ('ies' if len(depList) > 1 else 'y') + ' ' + ', '.join(depList)
            libList += '\n'
        with open(readmeTemplatePath, 'r') as template:
            with open(readmePath, 'w') as output:
                output.write(template.read().format(libList = libList))

if __name__ == '__main__':
    parser = ArgumentParser(description = DESCRIPTION)
    parser.add_argument('-clear-cache', action = 'store_true', help = 'Clear the download cache, before executing the build.')
    parser.add_argument('--logFile', help = 'The path to a log file. If not specified, all output goes to the console.')
    parser.add_argument('--librariesDataFile', help = 'The path to the file where all information about the libraries can be read from.')
    parser.add_argument('--configFile', default = 'config.cfg', help = 'The path to the config file.')
    parser.add_argument('--patchesDir', default = 'patches', help = 'The path to the directory containing the patch files. Defaults to the directory "patches" in the current directory.')
    parser.add_argument('--outputDir', default = 'output', help = 'The path to the output directory. Defaults to the directory "output" in the current directory.')
    parser.add_argument('--filesDir', default = 'files', help = 'The path to the files directory. Defaults to the directory "files" in the current directory.')
    parser.add_argument('--cacheDir', help = 'The path to the cache directory. Downloaded files will be stored there during compilation. They will get deleted, when the build process succeeds.')
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
