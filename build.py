import os
import re
import shutil
import sys
import traceback
from argparse import ArgumentParser
from tempfile import mkdtemp
from time import time, sleep
from typing import Dict, Optional
try:
    from http.client import HTTPSConnection as Connection
except ImportError:
    from http.client import HTTPConnection as Connection

import buildutils
from cache import Cache
from config import Configuration

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


class Builder:

    config = None
    cache = None

    def __init__(self, args):
        self.config = Configuration(args)
        self.cache = Cache(self.config.cacheDir)
        if args.clear_cache:
            self.cache.clear(ignore_errors=True)
            self.cache.ensureCacheDir()

    def build(self) -> bool:
        """>>> build() -> success
        Build all python libraries and modules for Android.
        """
        success = False
        versionList = self.config.versionList
        versions = {}
        tempdir = mkdtemp('PythonLibBuild')
        sourceDir = os.path.join(tempdir, 'extractedSources')
        try:
            startTime = time()
            if not self.config.check():
                return False
            self.config.parseLibrariesData()
            if not self.createOutputDir(self.config.outputDir):
                return False
            if not self.setupOptionalLibs(tempdir, sourceDir):
                return False
            if len(versionList) == 0:
                versions = self.getAllAvailablePythonVersions()
                if versions is None:
                    return False
            else:
                connection = Connection(self.config.pythonServer)
                for version in versionList:
                    if self.getPatchFile(version) is None:
                        self.config.log.warn('No patch-file found for specified version {version}. '
                                             'Ignoring this version.'.format(version=version))
                        continue
                    versions[version] = self.versionToUrl(connection, version)
                connection.close()
            self.config.log.debug('Got {num} versions to process...'.format(num=len(versions)))
            for version, versionPath in versions.items():
                self.config.log.info('Processing Python version ' + version)
                versionOutputDir = os.path.join(self.config.outputDir, 'Python' + version)
                if not os.path.exists(versionOutputDir):
                    os.makedirs(versionOutputDir)
                downloadFile = self.downloadPythonSource(versionPath, tempdir)
                if downloadFile is None:
                    return False
                extractedDir = self.extractPythonArchive(downloadFile, sourceDir)
                if extractedDir is None:
                    return False
                if not self.patchPythonSource(extractedDir, self.getPatchFile(version)):
                    self.config.log.error('Patching the sources failed for '
                                          'Python version {version}!'.format(version=version))
                    return False
                self.config.log.info('Generating modules zip...')
                if not self.generateModulesZip(extractedDir, versionOutputDir):
                    self.config.log.error('Failed to create lib zip at {dir}!'
                                          .format(dir=versionOutputDir))
                    return False
                if not self.compilePythonSource(extractedDir, version, tempdir):
                    self.config.log.error('Compilation failed for Python version {version}!'
                                          .format(version=version))
                    return False
                self.cleanup(extractedDir, versionOutputDir)
            self.config.log.info('Done generating libraries.')
            if not self.generateJSON():
                return False
            self.updateReadMe()
            delta = time() - startTime
            deltaMinutes, deltaSeconds = divmod(delta, 60)
            deltaHours, deltaMinutes = divmod(deltaMinutes, 60)
            milliseconds = round((delta - int(delta)) * 1000)
            timeArray = []
            for delta, name in [(deltaHours, 'hours'), (deltaMinutes, 'minutes'),
                                (deltaSeconds, 'seconds')]:
                if delta != 0:
                    timeArray.append('{delta} {name}'.format(delta=int(delta), name=name))
            self.config.log.info('Building finished in {timeStr} and {milliseconds} milliseconds.'
                                 .format(timeStr=', '.join(timeArray), milliseconds=milliseconds))
            success = True
        except KeyboardInterrupt:
            self.config.log.error('Cancelling build due to interrupt.')
        except Exception as error:
            self.config.log.error('Caught exception: {error}'.format(error=error))
            traceback.print_exception(*(sys.exc_info() + (None, self.config.log.getOutput())))
        finally:
            self.config.log.info('Cleaning up...')
            shutil.rmtree(tempdir, ignore_errors=True)
            if success:
                self.cache.clear(ignore_errors=True)
            self.config.log.log('Build', 'SUCCESS' if success else 'FAILED')
            self.config.closeLog()
        return success

    def createOutputDir(self, path: str) -> bool:
        if os.path.exists(path):
            if not os.path.isdir(path) or len(os.listdir(path)) != 0:
                if self.config.warnOnOutputOverwrite:
                    self.config.log.warn('The output directory "{dir}" already exists.'
                                         .format(dir=path))
                    # We do not want to override something important
                    if self.config.log.getOutput() is not None:
                        return False
                    if input('Press enter to overwrite the directory or c to cancel the build.')\
                            in ['c', 'C']:
                        self.config.log.error('Cancelling build.')
                        return False
                if not os.path.isdir(path):
                    os.remove(path)
                else:
                    for i in range(3):  # Retry a few times in case of an error
                        shutil.rmtree(path, ignore_errors=True)
                        if not os.path.exists(path):
                            break
                # Give the file system time to sync, otherwise creating the dir may raise an error
                sleep(0.5)
                os.mkdir(path)
        else:
            os.mkdir(path)
        return True

    def setupOptionalLibs(self, tempDir, sourceDir) -> bool:
        """>>> setupOptionalLibs(tempDir, sourceDir) -> success
        Download and compile all additional libraries.
        When finished, all libraries and their data are stored in the
        output directory and 'sourceDir' is set up to compile the
        python binaries in it.
        """
        self.config.log.info('Setting up optional libraries...')
        if not os.path.isdir(sourceDir):
            os.mkdir(sourceDir)
        self.config.log.info('Copying Python patch...')
        shutil.copytree(self.config.pythonPatchDir, os.path.join(sourceDir, 'PythonPatch'))
        libs = {'pythonPatch': os.path.join(sourceDir, 'PythonPatch')}
        outputDir = os.path.join(self.config.outputDir, 'libraries')
        minSdkList = self.config.computeLibMinAndroidSdkList()
        for sdkVersion in sorted(minSdkList, reverse=True):  # Begin with the latest sdk version
            libraryList = minSdkList[sdkVersion]
            for libraryName in libraryList:
                libraryData = self.config.additionalLibs[libraryName]
                makefilePath = os.path.join(self.config.filesDir, libraryName, 'Android.mk')
                if not os.path.exists(makefilePath):
                    makefilePath = None
                    self.config.log.info('No local Android.mk file was found for library {name}.'
                                         .format(name=libraryName))
                maxRetries = 5
                for retry in range(maxRetries):
                    self.config.log.info('Downloading library {name} from {url}...'
                                         .format(name=libraryName, url=libraryData['url']))
                    downloadFile = self.cache.download(libraryData['url'], tempDir, self.config.log)
                    if downloadFile is None:
                        self.config.log.warn(
                            'Download from {url} failed, retrying ({retry}/{max})'
                            .format(url=libraryData['url'], retry=retry + 1, max=maxRetries))
                        continue
                    self.config.log.info('Extracting {file}...'
                                         .format(file=os.path.basename(downloadFile)))
                    extractDir = buildutils.extract(downloadFile, sourceDir,
                                                    libraryData.get('extractionFilter', None))
                    if extractDir is False:
                        self.config.log.error('Could not extract archive from {url}: Unsupported '
                                              'archive format!'.format(url=libraryData['url']))
                        return False
                    if type(extractDir) != str:
                        self.config.log.warn(
                            'Extraction of archive from {url} failed, retrying ({retry}/{max})'
                            .format(url=libraryData['url'], retry=retry + 1, max=maxRetries))
                        continue
                    break
                else:
                    self.config.log.error('Download from {url} failed!'
                                          .format(url=libraryData['url']))
                    return False
                self.config.log.info('Extracting done.')
                if makefilePath:
                    shutil.copy(makefilePath, os.path.join(extractDir, 'Android.mk'))
                if not os.path.exists(os.path.join(extractDir, 'Android.mk')):
                    self.config.log.warn('No Android.mk file was found for library {name}, '
                                         'ignoring it.'.format(name=libraryName))
                    shutil.rmtree(extractDir, ignore_errors=True)
                    continue
                diffPath = os.path.join(self.config.filesDir, libraryName, 'patch.diff')
                if os.path.exists(diffPath):
                    self.config.log.info('Patching {lib}...'.format(lib=libraryName))
                    if not buildutils.applyPatch(self.config.patchPath, extractDir, diffPath,
                                                 self.config.log):
                        self.config.log.error('Applying patch ({path}) failed for library {name}, '
                                              'aborting!'.format(path=diffPath, name=libraryName))
                        return False
                if 'data' in libraryData.keys():
                    for dataEntry in libraryData['data']:
                        dataSource, dataName = dataEntry[0], dataEntry[1]
                        dataSrcPath = os.path.join(extractDir, dataSource)
                        if not os.path.exists(dataSrcPath):
                            self.config.log.warn('Data source defined for library {name} does not '
                                                 'exist: {dataSource}. Skipping it.'
                                                 .format(name=libraryName, dataSource=dataSource))
                            continue
                        if os.path.isdir(dataSrcPath):
                            shutil.make_archive(
                                os.path.join(self.config.outputDir, 'data', dataName), 'zip',
                                root_dir=dataSrcPath)
                        else:
                            destination = os.path.join(self.config.outputDir, 'data',
                                                       dataName + os.path.splitext(dataSrcPath)[1])
                            shutil.copy(dataSrcPath, destination)
                libs[libraryName] = extractDir
            applicationMKPath = os.path.join(sourceDir, 'Application.mk')
            buildutils.fillTemplate(
                os.path.join(self.config.filesDir, 'Application.mk'),
                applicationMKPath,
                pyShortVersion='',
                androidSdkVersion=sdkVersion
            )
            androidMKPath = os.path.join(sourceDir, 'Android.mk')
            with open(androidMKPath, 'w') as androidMK:
                androidMK.write('include $(call all-subdir-makefiles)')
            self.config.log.info('Compiling {num} additional libraries for Android Sdk version '
                                 '{version}...'.format(num=len(libraryList), version=sdkVersion))
            if self.config.useMultiprocessing:
                subprocessArgs = [
                    buildutils.createCompileSubprocessArgs(
                        self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'),
                        sourceDir, outputDir, abi, self.config.log
                    ) for abi in self.config.cpuABIs
                ]
                success = buildutils.callSubProcessesMultiThreaded(subprocessArgs, self.config.log)
            else:
                success = buildutils.ndkCompile(
                    self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'), sourceDir,
                    outputDir, self.config.cpuABIs, self.config.log)
            if not success:
                self.config.log.error('Compiling the additional libraries failed.')
                return False
            self.config.log.info('Compiling of {num} additional libraries succeeded.'
                                 .format(num=len(libraryList)))
            os.remove(applicationMKPath)
            os.remove(androidMKPath)
            if sdkVersion != max(minSdkList.keys()):
                for libraryName in libraryList:
                    os.rename(os.path.join(libs[libraryName], 'Android.mk'),
                              os.path.join(libs[libraryName], 'Android.mk.d'))
        self.config.log.info('Compiling of all ({num}) additional libraries succeeded.'
                             .format(num=len(libs)))
        for libPath in libs.values():
            if os.path.exists(os.path.join(libPath, 'Android.mk.d')):
                os.rename(os.path.join(libPath, 'Android.mk.d'),
                          os.path.join(libPath, 'Android.mk'))
        self.config.log.info('Patching Android.mk files...')
        libsOutputDir = buildutils.escapeNDKParameter(outputDir)
        for moduleName, modulePath in libs.items():
            self.patchOptionalLibAndroidMk(os.path.join(modulePath, 'Android.mk'),
                                           libsOutputDir, moduleName)

        self.config.log.info('Successfully generated additional libraries.')
        return True

    def patchOptionalLibAndroidMk(self, path: str, outputDir: str, moduleName: str):
        """>>> patchOptionalLibAndroidMk(path, outputDir, moduleName):
        Patches the Android.mk file at the given path.
        It will point LOCAL_SRC_FILES to the pre-build library and
        replace include $(BUILD_SHARED_LIBRARY) with include $(PREBUILT_SHARED_LIBRARY).
        """
        if os.path.exists(path):
            data = ''
            with open(path) as source:
                for line in source:
                    if 'LOCAL_SRC_FILES :=' in line:
                        data += line.replace(
                            'LOCAL_SRC_FILES',
                            'LOCAL_SRC_FILES := {outputDir}/$(TARGET_ARCH_ABI)/lib{name}.so\n'
                            'OLD_LOCAL_SRC_FILES'.format(
                                outputDir=outputDir, name=moduleName)
                        )
                    elif 'LOCAL_SRC_FILES +=' in line:
                        data += line.replace('LOCAL_SRC_FILES', 'OLD_LOCAL_SRC_FILES')
                    elif 'include $(BUILD_SHARED_LIBRARY)' in line:
                        data += 'include $(PREBUILT_SHARED_LIBRARY)\n'
                    elif 'include $(call all-subdir-makefiles)' in line:
                        subDirsWithMk = [os.path.join(dirPath, 'Android.mk')
                                         for dirPath in os.listdir(os.path.dirname(path))
                                         if os.path.isdir(dirPath)
                                         and os.path.exists(os.path.join(dirPath, 'Android.mk'))]
                        for subMkPath in subDirsWithMk:
                            self.patchOptionalLibAndroidMk(subMkPath, outputDir, moduleName)
                    else:
                        data += line
            with open(path, 'w') as destination:
                destination.write(data)

    def getPatchFile(self, version: str) -> str:
        """>>> getPatchFile(version) -> path
        Return the path to the patch file for the specified Python version.
        """
        patchFile = os.path.join(self.config.patchesDir, 'python' + version + '.patch')
        if not os.path.exists(patchFile):
            patchFile = None
        return patchFile

    def getAllAvailablePythonVersions(self) -> Optional[Dict[str, str]]:
        """>>> getAllAvailablePythonVersions() -> version to url dict
        Query all available Python versions from the source server
        and returns a dict with a version to download url mapping.
        Versions are also filtered by the availability of a patch file
        for that version.
        """
        startTime = time()
        connection = Connection(self.config.pythonServer)
        self.config.log.info('Gathering Python versions at "{url}"...'
                             .format(url=connection.host + self.config.pythonServerPath))
        connection.request('GET', self.config.pythonServerPath,
                           headers={"Connection": "keep-alive"})
        response = connection.getresponse()
        if response.status != 200:
            self.config.log.error('Failed to connect to "{host}/{path}":'
                                  .format(host=connection.host, path=self.config.pythonServerPath))
            self.config.log.error('Response {status}:{reason}'.format(status=response.status,
                                                                      reason=response.reason))
            return None
        result = response.read().decode('utf-8').split('\n')
        self.config.log.info('Got a response in {seconds} seconds.'
                             .format(seconds=round(time() - startTime, 2)))
        versions = {}
        self.config.log.info('Checking availability of the sources...')
        for line in result:
            versionMatch = re.search(r'href\s*=\s*"(.*)"', line)
            if versionMatch is None:
                continue
            version = versionMatch.group(1)
            if re.match('\A\d+\.\d+(\.\d+)*/\Z', version) is None:
                continue
            version = version[:-1]
            if self.getPatchFile(version) is None:
                self.config.log.info('Ignoring version {version} because no patch-file was found.'
                                     .format(version=version))
                continue
            url = self.versionToUrl(connection, version)
            if type(url) != str:
                if version != '2.0':
                    self.config.log.info('Ignoring version {version} because it has no downloadable'
                                         ' source code. Maybe this version is still in development.'
                                         .format(version=version))
                continue
            versions[version] = url
        connection.close()
        return versions

    def versionToUrl(self, connection: Connection, version: str) -> str:
        """>>> versionToUrl(connection, version) -> url
        Takes an existing connection to the Python source server and
        and queries it for the downloadable of the requested Python
        version. If the version exists, the url to its source is
        returned, otherwise the network response is returned.
        """
        path = self.config.pythonServerPath + version + '/Python-' + version + '.tgz'
        self.config.log.debug('Checking Python version at "{url}"...'
                              .format(url=connection.host + path))
        startTime = time()
        connection.request('HEAD', path, headers={"Connection": "keep-alive"})
        response = connection.getresponse()
        response.read()  # Empty the request
        self.config.log.debug('Got a response in {seconds} seconds.'
                              .format(seconds=round(time() - startTime, 2)))
        if response.status != 200:
            return response
        return path

    def downloadPythonSource(self, versionPath: str, downloadDir: str) -> Optional[str]:
        """>>> downloadPythonSource(versionPath, downloadDir) -> path / None
        Download a Python source archive from the Python source server
        at the sub-path 'versionPath' and stores it in 'downloadDir'.
        Returns the path to the downloaded archive on success or None
        on failure.
        """
        self.config.log.info('Downloading Python source from "{url}"...'
                             .format(url=self.config.pythonServer + versionPath))
        return self.cache.download('https://' + self.config.pythonServer + versionPath,
                                   downloadDir, self.config.log)

    def extractPythonArchive(self, sourceArchive: str, extractedDir: str) -> Optional[str]:
        """>>> extractPythonArchive(sourceArchive, extractedDir) -> path or None
        Extract the Python archive at 'sourceArchive' to 'extractedDir'.
        Returns the path to the first directory of the extracted archive
        on success or None on error.
        """
        self.config.log.info('Extracting {archive}...'.format(archive=sourceArchive))
        res = buildutils.extract(
            sourceArchive, extractedDir,
            ['Include', 'Lib', 'Modules', 'Objects', 'Parser', 'Python', 'LICENSE', 'README'],
            ['.c', '.h', '.py', '.pyc', '.inc', '.txt', '', '.gif', '.png', '.def']
        )
        if res is None:
            self.config.log.error('Failed to extract {archive}!'.format(archive=sourceArchive))
        elif not res:
            self.config.log.error('Failed to extract {archive}: Archive is compressed with an '
                                  'unsupported compression.'.format(archive=sourceArchive))
            return None
        return res

    def patchPythonSource(self, sourcePath: str, patchFilePath: str) -> bool:
        """>>> patchPythonSource(sourcePath, patchFilePath) -> success
        Apply the patch at 'patchFilePath' to the Python source at 'sourcePath'.
        """
        return buildutils.applyPatch(self.config.patchPath, sourcePath,
                                     patchFilePath, self.config.log)

    def generateModulesZip(self, sourcePath: str, outputDir: str) -> bool:
        """>>> generateModulesZip(sourcePath, outputDir) -> success
        Generate the Python modules zip from the source at 'sourcePath'
        and store it into 'outputDir'.
        """
        outputPath = os.path.join(outputDir, 'lib')
        if os.path.exists(outputPath):
            os.remove(outputPath)
        shutil.copy(os.path.join(sourcePath, 'LICENSE'),
                    os.path.join(sourcePath, 'Lib', 'LICENSE.txt'))
        # TODO: Make this remove all test and test directories to save storage space
        shutil.rmtree(os.path.join(sourcePath, 'Lib', 'test'))
        return shutil.make_archive(outputPath, 'zip',
                                   os.path.join(sourcePath, 'Lib')).endswith('lib.zip')

    def compilePythonSource(self, sourcePath: str, pythonVersion: str, tempDir: str) -> bool:
        """>>> compilePythonSource(sourcePath, pythonVersion, tempDir) -> success
        Compile the source of the given Python version located at 'sourcePath'
        and stores the compiled binaries into the output directory.
        """
        parentDir = os.path.dirname(sourcePath)
        # Setup the Application.mk.
        buildutils.fillTemplate(
            os.path.join(self.config.filesDir, 'Application.mk'),
            os.path.join(parentDir, 'Application.mk'),
            pyShortVersion=buildutils.getShortVersion(pythonVersion),
            androidSdkVersion=self.config.DEFAULT_MIN_SKD_VERSION
        )
        with open(os.path.join(parentDir, 'Android.mk'), 'w') as androidMK:
            androidMK.write('include $(call all-subdir-makefiles)')
        # Copy the Android.mk and configuration files
        shutil.copy(os.path.join(self.config.filesDir, 'Android.mk'), sourcePath)
        # Setup module libraries
        moduleDependencies = {}
        for lib, libData in self.config.additionalLibs.items():
            moduleNames = []
            if 'pyModuleReq' in libData.keys():
                moduleNames = libData['pyModuleReq']
            if int(pythonVersion[0]) >= 3 and 'py3ModuleReq' in libData.keys():
                moduleNames = libData['py3ModuleReq']
            if len(moduleNames) < 1:
                continue
            for moduleName in moduleNames:
                if moduleName in moduleDependencies:
                    moduleDependencies[moduleName].append(lib)
                else:
                    moduleDependencies[moduleName] = [lib]
        for moduleName, moduleDependencies in moduleDependencies.items():
            moduleDir = os.path.join(parentDir, moduleName)
            if not os.path.exists(moduleDir):
                os.mkdir(moduleDir)
            pythonDir = os.path.basename(sourcePath)
            moduleWildcards = [moduleName + '.[ch]', moduleName + 'module.c', moduleName + '/*.c']
            moduleWildcards = [
                '$(wildcard $(LOCAL_PATH)/../{pyDir}/Modules/{wildcard})'
                .format(pyDir=pythonDir, wildcard=wildcard) for wildcard in moduleWildcards
            ]
            buildutils.fillTemplate(
                os.path.join(self.config.filesDir, 'module-Android.mk'),
                os.path.join(moduleDir, 'Android.mk'),
                moduleSourceWildcards=' '.join(moduleWildcards),
                libDependencies=' '.join(moduleDependencies),
                pythonDir=pythonDir
            )
        # Compile
        self.config.log.info('Compiling Python {version}...'.format(version=pythonVersion))
        outputDir = os.path.join(self.config.outputDir, 'Python' + pythonVersion)
        if self.config.useMultiprocessing:
            subprocessArgs = [
                buildutils.createCompileSubprocessArgs(
                    self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'),
                    parentDir, outputDir, abi, self.config.log
                ) for abi in self.config.cpuABIs
            ]
            return buildutils.callSubProcessesMultiThreaded(subprocessArgs, self.config.log)
        else:
            return buildutils.ndkCompile(self.config.ndkPath, os.path.join(tempDir, 'NDK-Temp'),
                                         parentDir, outputDir, self.config.cpuABIs, self.config.log)

    def cleanup(self, sourcePath: str, outputDir: str):
        """>>> cleanup(sourcePath, outputDir)
        Remove unnecessary build artifacts in the 'outputDir'
        and cleans the build directory located at 'sourcePath'
        from the last build, so another Python version can be
        compiled there.
        """
        self.config.log.info('Removing unnecessary files...')
        shutil.rmtree(sourcePath)
        for subdir in os.listdir(outputDir):
            if os.path.isdir(os.path.join(outputDir, subdir)):
                for libFile in os.listdir(os.path.join(outputDir, subdir)):
                    if libFile[3:-3] in self.config.additionalLibs.keys()\
                            or libFile == 'libpythonPatch.so':
                        os.remove(os.path.join(outputDir, subdir, libFile))
        sourceParentPath = os.path.dirname(sourcePath)
        additionalPythonModules = []
        for moduleData in self.config.additionalLibs.values():
            additionalPythonModules += moduleData.get('pyModuleReq', [])
            additionalPythonModules += moduleData.get('py3ModuleReq', [])
        for subdir in os.listdir(sourceParentPath):
            if os.path.isdir(os.path.join(sourceParentPath, subdir)):
                if subdir in additionalPythonModules:
                    shutil.rmtree(os.path.join(sourceParentPath, subdir))

    def generateJSON(self) -> bool:
        """>>> generateJSON() -> success
        Generate the JSON file with all information needed
        by a connecting client to download the created data.
        """
        self.config.log.info('Generating JSON file...')
        requirementData = '"requirements": {\n'
        for libName, libData in self.config.additionalLibs.items():
            dependencies = ['libraries/' + dep for dep in libData.get('dependencies', [])]
            dependencies += ['data/' + dep[1] for dep in libData.get('data', [])]
            if 'minAndroidSdk' in libData:
                dependencies += ['androidSdk/' + str(libData['minAndroidSdk'])]
            if len(dependencies) > 0:
                requirementData += '"libraries/{name}" : ["{dependencies}"],\n'.format(
                    name=libName, dependencies='", "'.join(dependencies))
        moduleDependencies = {}
        for lib, libData in self.config.additionalLibs.items():
            moduleNames = []
            if 'pyModuleReq' in libData.keys():
                moduleNames += libData['pyModuleReq']
            if 'py3ModuleReq' in libData.keys():
                moduleNames += [name for name in libData['py3ModuleReq'] if name not in moduleNames]
            if len(moduleNames) < 1:
                continue
            for moduleName in moduleNames:
                if moduleName in moduleDependencies:
                    moduleDependencies[moduleName].append('libraries/' + lib)
                else:
                    moduleDependencies[moduleName] = ['libraries/' + lib]
        for moduleName, moduleDependencies in moduleDependencies.items():
            requirementData += '"pyModule/{name}" : ["{dependencies}"],\n'.format(
                name=moduleName, dependencies='", "'.join(moduleDependencies))
        requirementData = requirementData[:-2] + '\n},\n'

        datafilesData = '"data": {\n'
        for libData in self.config.additionalLibs.values():
            if 'data' in libData.keys():
                for data in libData['data']:
                    datafilesData += '"' + data[1] + '" : {\n'
                    dataPath = os.path.join(self.config.outputDir, 'data', data[1])
                    if not os.path.exists(dataPath):
                        dataPath += '.zip'
                    datafilesData += '"path": ["output/data/{name}", "{hash}"],\n'.format(
                        name=os.path.basename(dataPath), hash=buildutils.createMd5Hash(dataPath))
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
        libraryDir = os.path.join(self.config.outputDir, 'libraries')
        for lib in additionalLibs:
            additionalLibsData += '"' + lib + '": {\n'
            for architecture in os.listdir(libraryDir):
                if 'lib' + lib + '.so' in os.listdir(os.path.join(libraryDir, architecture)):
                    filePath = os.path.join(libraryDir, architecture, 'lib' + lib + '.so')
                    additionalLibsData += \
                        '"{abi}": ["output/libraries/{abi}/lib{name}.so", "{hash}"],\n'.format(
                            abi=architecture, name=lib, hash=buildutils.createMd5Hash(filePath))
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
                self.config.log.error('lib.zip not found in {path}.'
                                      .format(path=os.path.join(self.config.outputDir, versionDir)))
                return False
            for architecture in os.listdir(os.path.join(self.config.outputDir, versionDir)):
                abiDir = os.path.join(self.config.outputDir, versionDir, architecture)
                if not os.path.isdir(abiDir):
                    continue
                pythonData += '"' + architecture + '": {\n'
                if not 'libpython{ver}.so'.format(ver=buildutils.getShortVersion(version)) in \
                        os.listdir(abiDir):
                    self.config.log.error('The python library was not found in {path}.'
                                          .format(path=abiDir))
                    return False
                for libFile in os.listdir(abiDir):
                    if 'libpython' in libFile:
                        lib = 'pythonLib'
                    else:
                        lib = libFile[:-3]
                    libPath = os.path.join(abiDir, libFile)
                    pythonData += '"{name}": ["output/{versionDir}/{abi}/{libFile}", "{hash}"],\n'\
                        .format(name=lib, versionDir=versionDir, abi=architecture,
                                libFile=libFile, hash=buildutils.createMd5Hash(libPath))
                pythonData = pythonData[:-2] + '\n'
                pythonData += '},\n'
            pythonData += '"lib": ["output/{versionDir}/lib.zip", "{hash}"]\n'.format(
                versionDir=versionDir, hash=buildutils.createMd5Hash(modulesFile))
            pythonData += '},\n'
        pythonData += '"__version__": 1\n'
        jsonPath = os.path.join(os.path.dirname(self.config.outputDir), 'index.json')
        with open(jsonPath, 'w') as jsonFile:
            jsonFile.write('{\n' + requirementData + datafilesData
                           + additionalLibsData + pythonData + '}\n')
        self.config.log.info('Successfully generated JSON file.')
        return True

    def updateReadMe(self):
        """>>> updateReadMe()
        Update the ReadMe file to display all currently
        available libraries.
        """
        self.config.log.info('Updating README.md...')
        readmeTemplatePath = os.path.join(self.config.currDir, 'README.md.template')
        readmePath = os.path.join(self.config.currDir, 'README.md')
        # itemTemplate = '* {libName} (from {url}) for {modules}\n'
        libList = ''
        for libraryName, libraryData in self.config.additionalLibs.items():
            libList += '* ' + libraryName + ' (from ' + libraryData['url'] + ')'
            depList = [lib for lib, libData in self.config.additionalLibs.items()
                       if libraryName in libData.get('dependencies', [])]
            if 'pyModuleReq' in libraryData.keys() or 'py3ModuleReq' in libraryData.keys():
                moduleList = libraryData.get('pyModuleReq', [])
                moduleList += [name for name in libraryData.get('py3ModuleReq', [])
                               if name not in moduleList]
                libList += ' for the Python {module} {list}'.format(
                    module='modules' if len(moduleList) > 1 else 'module',
                    list=', '.join(moduleList))
                if len(depList) > 0:
                    libList += ' and'
            if len(depList) > 0:
                libList += ' for the {library} {list}'.format(
                    library='libraries' if len(depList) > 1 else 'library', list=', '.join(depList))
            libList += '\n'
        with open(readmeTemplatePath, 'r') as template:
            with open(readmePath, 'w') as output:
                output.write(template.read().format(libList=libList))


def main():
    parser = ArgumentParser(description=DESCRIPTION)
    parser.add_argument('-clear-cache', action='store_true',
                        help='Clear the download cache, before executing the build.')
    parser.add_argument('--logFile', help='The path to a log file. '
                                          'If not specified, all output goes to the console.')
    parser.add_argument('--librariesDataFile', help='The path to the file where all information '
                                                    'about the libraries can be read from.')
    parser.add_argument('--configFile', default='config.cfg', help='The path to the config file.')
    parser.add_argument('--patchesDir', default='patches',
                        help='The path to the directory containing the patch files. '
                             'Defaults to the directory "patches" in the current directory.')
    parser.add_argument('--outputDir', default='output',
                        help='The path to the output directory. Defaults to the directory '
                             '"output" in the current directory.')
    parser.add_argument('--filesDir', default='files',
                        help='The path to the files directory. Defaults to the directory '
                             '"files" in the current directory.')
    parser.add_argument('--cacheDir', help='The path to the cache directory. Downloaded files will '
                                           'be stored there during compilation. They will get '
                                           'deleted, when the build process succeeds.')
    parser.add_argument('--gitPath', help='The path to the patch executable in the git directory.')
    parser.add_argument('--ndkPath', help='The path to the ndk-build executable.')
    parser.add_argument('--pythonPatchDir', help='The path to the directory where the pythonPatch '
                                                 'library source code can be found.')
    parser.add_argument('--pythonServer', default=Configuration.pythonServer,
                        help='The host address of the Python server. Defaults to {host}".'
                        .format(host=Configuration.pythonServer))
    parser.add_argument('--pythonServerPath', default=Configuration.pythonServerPath,
                        help='The path on the Python server to see all available Python versions. '
                             'Defaults to "{path}".'.format(path=Configuration.pythonServerPath))
    parser.add_argument('--cpuABIs', nargs='*', default=Configuration.ALL_CPU_ABIS,
                        help='The cpu ABIs to compile for. Defaults to all. Possible values are '
                             + ', '.join(Configuration.ALL_CPU_ABIS))
    parser.add_argument('--disableMultiprocessing', default=False, action='store_true',
                        help='If set, turns off the multiprocessing of the compilation. '
                             'By default, multiprocessing is turned on.')
    parser.add_argument('versions', nargs='*', help='The Python versions to download. '
                                                    'Empty means all versions available.')
    args = parser.parse_args()
    builder = Builder(args)
    sys.exit(0 if builder.build() else 1)

if __name__ == '__main__':
    main()
