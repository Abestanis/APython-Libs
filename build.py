#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script will download and compile all Python versions to libraries which
can be used by the APython project (see https://github.com/Abestanis/APython).

To compile the C sources, cmake and the Android NDK is used and
to apply some patches to the source code, git is required.
The path to both can be provided via command line options
or via a configuration file (by default, a config.cfg in the
same directory as this script is used).

Created 18.08.2015 by Sebastian Scholz.
"""

import os
import re
import shutil
import sys
import traceback
import json
from argparse import ArgumentParser, Namespace
from collections import OrderedDict
from tempfile import mkdtemp
from time import time, sleep
from glob import glob
from typing import Dict, Optional, List, Union
from difflib import get_close_matches
from http.client import HTTPResponse

try:
    from http.client import HTTPSConnection as Connection
except ImportError:
    from http.client import HTTPConnection as Connection

import buildutils
from cache import Cache
from config import Configuration
from logger import Loggable


class Builder(Loggable):
    config = None
    cache = None

    def __init__(self, args: Namespace) -> None:
        self.config = Configuration(args)
        super(Builder, self).__init__(self.config.log)
        self.cache = Cache(self.config.cacheDir)
        if args.clear_cache:
            self.cache.clear(ignore_errors=True)
            self.cache.ensureCacheDir()

    def build(self) -> bool:
        """
        Build all Python libraries and modules for Android.

        :return: True if the build was successful.
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
            if not self.createOutputDir(self.config.outputDir) or \
                    not self.setupOptionalLibs(tempdir, sourceDir):
                return False
            if len(versionList) == 0:
                versions = self.getAllAvailablePythonVersions()
                if versions is None:
                    return False
            else:
                connection = Connection(self.config.pythonServer)
                for version in versionList:
                    if self.getPatchFile(version) is None:
                        self.warn('No patch-file found for specified version {version}. '
                                  'Ignoring this version.'.format(version=version))
                        continue
                    versions[version] = self.versionToUrl(connection, version)
                connection.close()
            self.debug('Got {num} versions to process...'.format(num=len(versions)))
            for version, versionPath in versions.items():
                self.info('Processing Python version ' + version)
                versionOutputDir = os.path.join(self.config.outputDir, 'Python' + version)
                if not os.path.exists(versionOutputDir):
                    os.makedirs(versionOutputDir)
                downloadFile = self.downloadPythonSource(versionPath, tempdir)
                if downloadFile is None:
                    return False
                extractedDir = self.extractPythonArchive(downloadFile, sourceDir)
                if extractedDir is None:
                    return False
                if not buildutils.applyPatch(self.config.gitPath, extractedDir,
                                             self.getPatchFile(version), self.config.log):
                    self.error('Patching the sources failed for Python version {version}!'
                               .format(version=version))
                    return False
                self.info('Generating modules zip...')
                if not self.generateModulesZip(extractedDir, versionOutputDir):
                    self.error('Failed to create lib zip at {dir}!'.format(dir=versionOutputDir))
                    return False
                if not self.compilePythonSource(extractedDir, version, tempdir):
                    self.error('Compilation failed for Python version {version}!'
                               .format(version=version))
                    return False
                self.cleanup(extractedDir, versionOutputDir)
            self.info('Done generating libraries.')
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
                if delta != 0 and len(timeArray) == 0:
                    timeArray.append('{delta} {name}'.format(delta=int(delta), name=name))
            self.info('Building finished in {timeStr} and {milliseconds} milliseconds.'
                      .format(timeStr=', '.join(timeArray), milliseconds=milliseconds))
            success = True
        except KeyboardInterrupt:
            self.error('Cancelling build due to interrupt.')
        except Exception as error:
            self.error('Caught exception: {error}'.format(error=error))
            exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
            traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback,
                                      None, self.config.log.getOutput())
        finally:
            self.info('Cleaning up...')
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
                    self.warn('The output directory "{dir}" already exists.'.format(dir=path))
                    # We do not want to override something important
                    if self.config.log.getOutput() is not None:
                        return False
                    if input('Press enter to overwrite the directory or c to cancel the build.') \
                            in ['c', 'C']:
                        self.error('Cancelling build.')
                        return False
                if not os.path.isdir(path):
                    os.remove(path)
                else:
                    for _ in range(3):  # Retry a few times in case of an error
                        shutil.rmtree(path, ignore_errors=True)
                        if not os.path.exists(path):
                            break
                    else:
                        try:
                            shutil.rmtree(path, ignore_errors=False)
                        except IOError as error:
                            self.error('Failed to clean the output directory: {reason}'
                                       .format(reason=error))
                            return False
                # Give the file system time to sync, otherwise creating the dir may raise an error
                sleep(0.5)
                os.mkdir(path)
        else:
            os.mkdir(path)
        return True

    def setupOptionalLibs(self, tempDir, sourceDir) -> bool:
        """
        Download and compile all additional libraries.
        When finished, all libraries and their data are stored in the output directory and
        'sourceDir' is set up to compile the Python binaries in it.

        :param tempDir: The temporary directory to use during building.
        :param sourceDir: The directory to extract the library sources to.
        :return: True if setting up the optional libraries was successful.
        """
        self.info('Setting up optional libraries...')
        if not os.path.isdir(sourceDir):
            os.mkdir(sourceDir)
        self.info('Copying Python patch...')
        shutil.copytree(self.config.pythonPatchDir, os.path.join(sourceDir, 'PythonPatch'))
        self.info('Copying IPC...')
        shutil.copytree(self.config.ipcDir, os.path.join(sourceDir, 'IPC'))
        libs = {'pythonPatch': os.path.join(sourceDir, 'PythonPatch'),
                'IPC': os.path.join(sourceDir, 'IPC')}
        outputDir = os.path.join(self.config.outputDir, 'libraries')
        minSdkList = self.config.computeLibMinAndroidSdkList()
        minSdkList.setdefault(self.config.minSdkVersion, []).append('pythonPatch')
        # Begin with the latest sdk version
        for sdkVersion, libraryList in sorted(minSdkList.items(), reverse=True):
            for libraryName in libraryList:
                if libraryName in ['pythonPatch', 'IPC']:
                    continue
                libraryData = self.config.additionalLibs[libraryName]
                name = libraryData.get('parent', libraryName)
                extractDir = libs.get(name)
                if extractDir is None:
                    makefilePath = os.path.join(
                        self.config.buildFilesDir, name, buildutils.MAKE_FILE)
                    if not os.path.exists(makefilePath):
                        makefilePath = None
                        self.info('No local {makeFile} file was found for library {name}.'
                                  .format(makeFile=buildutils.MAKE_FILE, name=name))
                    libUrl = libraryData['url']
                    maxRetries = 5
                    for retry in range(maxRetries):
                        self.info('Downloading library {name} from {url}...'
                                  .format(name=name, url=libUrl))
                        downloadFile = self.cache.download(libUrl, tempDir, self.config.log)
                        if downloadFile is None:
                            self.warn('Download from {url} failed, retrying ({retry}/{max})'
                                      .format(url=libUrl, retry=retry + 1, max=maxRetries))
                            continue
                        self.info('Extracting {file}...'.format(
                            file=os.path.basename(downloadFile)))
                        extractDir = buildutils.extract(downloadFile, sourceDir,
                                                        libraryData.get('extractionFilter', None))
                        if extractDir is False:
                            self.error('Could not extract archive from {url}: Unsupported '
                                       'archive format!'.format(url=libUrl))
                            return False
                        if type(extractDir) != str:
                            self.warn(
                                'Extraction of archive from {url} failed, retrying ({retry}/{max})'
                                .format(url=libUrl, retry=retry + 1, max=maxRetries))
                            continue
                        break
                    else:
                        self.error('Download from {url} failed!'.format(url=libUrl))
                        return False
                    self.info('Extracting done.')
                    diffPath = os.path.join(self.config.patchesDir, name + '.patch')
                    if os.path.exists(diffPath):
                        self.info('Patching {lib}...'.format(lib=name))
                        if not buildutils.applyPatch(self.config.gitPath, extractDir, diffPath,
                                                     self.config.log):
                            self.error('Applying patch ({path}) failed for library {name}, '
                                       'aborting!'.format(path=diffPath, name=name))
                            return False
                    extractDirMakefile = os.path.join(extractDir, buildutils.MAKE_FILE)
                    if makefilePath:
                        if not os.path.exists(extractDirMakefile):
                            self.copyTemplateMakefile(makefilePath, extractDirMakefile)
                        else:
                            self.mergeMakeFiles(makefilePath, extractDirMakefile)
                    elif not os.path.exists(extractDirMakefile):
                        self.warn('No {makeFile} file was found for library {name}, ignoring it.'
                                  .format(makeFile=buildutils.MAKE_FILE, name=name))
                        shutil.rmtree(extractDir, ignore_errors=True)
                        continue
                    if 'includeDir' in libraryData:
                        includeDir = os.path.join(extractDir, 'inc', libraryData['includeDir'])
                        os.makedirs(includeDir)
                        includeFilters = libraryData.get('includeDirContent', ['include/*.h'])
                        filesToCopy = set()
                        for includeFilter in includeFilters:
                            filesToCopy.update(glob(os.path.join(extractDir, includeFilter)))
                        for path in filesToCopy:
                            shutil.copy(path, includeDir)
                    libs[name] = extractDir
                if 'data' in libraryData:
                    for dataEntry in libraryData['data']:
                        dataSource, dataName = dataEntry[0], dataEntry[1]
                        dataSrcPath = os.path.join(extractDir, dataSource)
                        if not os.path.exists(dataSrcPath):
                            dataSrcPath = os.path.join(self.config.buildFilesDir,
                                                       name, dataSource)
                            if not os.path.exists(dataSrcPath):
                                self.warn('Data source defined for library {name} does not exist: '
                                          '{dataSource}. Skipping it.'
                                          .format(name=libraryName, dataSource=dataSource))
                                continue
                        if os.path.isdir(dataSrcPath):
                            shutil.make_archive(
                                os.path.join(self.config.outputDir, 'data', dataName), 'zip',
                                root_dir=dataSrcPath)
                        else:
                            destination = os.path.join(
                                self.config.outputDir, 'data',
                                dataName + '.' + dataSrcPath.split('.', 1)[1])
                            shutil.copy(dataSrcPath, destination)
            self.info('Compiling {num} additional libraries for Android Sdk version {version}...'
                      .format(num=len(libraryList), version=sdkVersion))
            success = buildutils.build(
                self.config.ndkPath, sourceDir, outputDir, os.path.join(tempDir, 'NDK-Temp'),
                cmakePath=self.config.cmakePath, makePath=self.config.makePath,
                androidSdkVersion=sdkVersion, cpuABIs=self.config.cpuABIs, logger=self.config.log)
            if not success:
                self.error('Compiling the additional libraries failed.')
                return False
            self.info('Compiling of {num} additional libraries succeeded.'
                      .format(num=len(libraryList)))
            if sdkVersion != max(minSdkList.keys()):
                for libraryName in libraryList:
                    os.rename(os.path.join(libs[libraryName], buildutils.MAKE_FILE),
                              os.path.join(libs[libraryName], buildutils.MAKE_FILE + '.d'))
        self.info('Compiling of all ({num}) additional libraries succeeded.'.format(num=len(libs)))
        for libPath in libs.values():
            if os.path.exists(os.path.join(libPath, buildutils.MAKE_FILE + '.d')):
                os.rename(os.path.join(libPath, buildutils.MAKE_FILE + '.d'),
                          os.path.join(libPath, buildutils.MAKE_FILE))
        self.info('Patching {makefile} files...'.format(makefile=buildutils.MAKE_FILE))
        libsOutputDir = buildutils.escapeNDKParameter(outputDir)
        for moduleName, modulePath in libs.items():
            self.patchOptionalLibMakefile(
                os.path.join(modulePath, buildutils.MAKE_FILE),
                libsOutputDir, moduleName, self.config.cpuABIs)

        self.info('Successfully generated additional libraries.')
        return True

    @staticmethod
    def copyTemplateMakefile(sourceMakeFile, targetMakeFile):
        with open(sourceMakeFile) as makeFileTemplate:
            with open(targetMakeFile, 'w') as makeFile:
                for line in makeFileTemplate.readlines():
                    makeFile.write(
                        line.replace('source/', '').replace('/source', ''))

    @staticmethod
    def _parseNextCmakeToken(text, lineGenerator=None):
        if lineGenerator is None:
            lineGenerator = [].__iter__()
        text = text.lstrip()
        while text == '\n' or len(text) == 0:
            try:
                text = next(lineGenerator).lstrip()
            except StopIteration:
                return text, ''
        for quote in ('"', "'"):
            if text.startswith(quote):
                token = ''
                text = text[1:]
                index = text.find(quote)
                while index == -1 or (text[index - 1] == '\\' and text[index - 2] != '\\'):
                    if index == -1:
                        token += text
                        try:
                            text = next(lineGenerator).lstrip()
                        except StopIteration:
                            return token + text, ''
                    index = text.find(quote, index + 1)
                return token + text[:index], text[:index]
        else:
            if text.startswith('#'):
                return text, ''
            for character in ('(', ')'):
                if text.startswith(character):
                    return character, text[len(character):]
            minIndex = len(text)
            for character in ('#', ' ', '(', ')', '\n'):
                index = text.find(character)
                if index != -1 and minIndex > index:
                    minIndex = index
            return text[:minIndex], text[minIndex:]

    def _patchLibCommand(self, command, commandTemplate, originalLine, lineGenerator,
                         allowedTargets, beforeCommandTemplate=None):
        def lineGeneratorWrapper():
            nonlocal originalLine
            while True:
                newLine = next(lineGenerator)
                originalLine += newLine
                yield newLine

        wrappedLineGenerator = lineGeneratorWrapper()
        token, line = self._parseNextCmakeToken(originalLine, wrappedLineGenerator)
        if token.lower() != command.lower():
            return '', originalLine
        token, line = self._parseNextCmakeToken(line, wrappedLineGenerator)
        if token != '(':
            return '', originalLine
        target, line = self._parseNextCmakeToken(line, wrappedLineGenerator)
        if target not in allowedTargets:
            return '', originalLine
        args = ''
        isPrivate = False
        before = False
        token, line = self._parseNextCmakeToken(line, lineGenerator)
        while token != ')':
            if token.lower() == 'private':
                isPrivate = True
            elif token.lower() in ['interface', 'public']:
                isPrivate = False
            elif args == '' and token.lower() == 'before':
                before = True
            elif not isPrivate:
                args += ' ' + token
            token, line = self._parseNextCmakeToken(line, lineGenerator)
        template = commandTemplate if not before or beforeCommandTemplate is None else \
            beforeCommandTemplate
        return template.format(target=target, args=args, openBracket='{', closeBracket='}'), line

    def patchOptionalLibMakefile(
            self, path: str, outputDir: str, moduleName: str, cpuABIs: List[str]):
        """
        Patches the makefile file at the given path.
        This will convert all SHARED targets to imported targets.

        :param path: The path to the makefile.
        :param outputDir: The path to the output directories of the libraries.
        :param moduleName: The name of the module of the makefile.
        :param cpuABIs: The list af ABIs the module was compiled for.
        """
        if not os.path.exists(path):
            return
        # noinspection SpellCheckingInspection
        data = 'macro(MACRO_NOOP)\nendmacro(MACRO_NOOP)\n'
        with open(path) as source:
            patchedTargets = []
            lines = (line for line in source)
            for line in lines:
                tokenLine = line
                tokens = []
                while True:
                    token, tokenLine = self._parseNextCmakeToken(tokenLine)
                    if len(token) == 0:
                        break
                    tokens.append(token.lower())
                if 'add_library' in tokens:
                    startPoint = line.find('add_library') + len('add_library')
                    data += line[:startPoint]
                    line = line[startPoint:]
                    token, restLine = self._parseNextCmakeToken(line, lines)
                    if token != '(':
                        data += line
                        continue
                    libName, restLine = self._parseNextCmakeToken(restLine, lines)
                    libType, rest = self._parseNextCmakeToken(restLine, lines)
                    if libType.lower() in ['shared', 'module']:
                        restLine = rest
                    elif libType.lower() == 'static':
                        data += line
                        continue
                    else:
                        libType = 'SHARED'
                    assert libName != ''
                    libDirGenericPath = outputDir + '/${CMAKE_ANDROID_ARCH_ABI}/'
                    libPath = libDirGenericPath + 'lib{name}.so'.format(name=libName)
                    libDirPath = os.path.join(outputDir, cpuABIs[0])
                    if not os.path.isfile(
                            os.path.join(libDirPath, 'lib{name}.so'.format(name=libName))):
                        matches = get_close_matches('lib{name}.so'.format(name=libName),
                                                    os.listdir(libDirPath), n=1, cutoff=0.75)
                        if len(matches) == 0:
                            data += line
                            continue
                        libPath = libDirGenericPath + matches[0]
                        self.info('Choosing shared library file {path} for {name}'
                                  .format(path=libPath, name=libName))
                    patchedTargets.append(libName)
                    data += '({name} {type} IMPORTED GLOBAL)\nset_property(TARGET {name} ' \
                            'PROPERTY IMPORTED_LOCATION "{path}")\nMACRO_NOOP(' \
                            .format(name=libName, type=libType, path=libPath) + restLine
                elif 'target_include_directories' in tokens:
                    startPoint = line.find('target_include_directories')
                    data += line[:startPoint]
                    command, line = self._patchLibCommand(
                        'target_include_directories',
                        'set_property(TARGET {target} APPEND PROPERTY '
                        'INTERFACE_INCLUDE_DIRECTORIES {args})',
                        line[startPoint:], lines, patchedTargets,
                        'get_property({target}_TEMP_INCLUDE_DIRS TARGET {target} PROPERTY '
                        'INTERFACE_INCLUDE_DIRECTORIES)\n'
                        'set_property(TARGET {target} APPEND PROPERTY '
                        'INTERFACE_INCLUDE_DIRECTORIES {args} '
                        '${openBracket}{target}_TEMP_INCLUDE_DIRS{closeBracket})')
                    data += command + line
                elif 'target_link_libraries' in tokens:
                    startPoint = line.find('target_link_libraries')
                    data += line[:startPoint]
                    command, line = self._patchLibCommand(
                        'target_link_libraries',
                        'set_property(TARGET {target} APPEND PROPERTY '
                        'INTERFACE_LINK_LIBRARIES {args})',
                        line[startPoint:], lines, patchedTargets)
                    data += command + line
                elif 'target_compile_definitions' in tokens:
                    startPoint = line.find('target_compile_definitions')
                    data += line[:startPoint]
                    command, line = self._patchLibCommand(
                        'target_compile_definitions',
                        'set_property(TARGET {target} APPEND PROPERTY '
                        'INTERFACE_COMPILE_DEFINITIONS {args})',
                        line[startPoint:], lines, patchedTargets)
                    data += command + line
                elif 'install' in tokens:
                    data += line.replace('install', 'MACRO_NOOP')
                elif 'add_subdirectory' in tokens:
                    data += line
                    line = line[line.find('add_subdirectory') + len('add_subdirectory'):]
                    token, line = self._parseNextCmakeToken(line, lines)
                    if token != '(':
                        data += line
                        continue
                    dirName, _ = self._parseNextCmakeToken(line, lines)
                    subDir = os.path.join(os.path.dirname(path), dirName)
                    subMkPath = os.path.join(subDir, buildutils.MAKE_FILE)
                    if os.path.isdir(subDir) and os.path.isfile(subMkPath):
                        self.patchOptionalLibMakefile(subMkPath, outputDir, moduleName, cpuABIs)
                else:
                    data += line
        with open(path, 'w') as destination:
            destination.write(data)

    @staticmethod
    def mergeMakeFiles(makefilePath1, makefilePath2):
        data = ''
        with open(makefilePath1) as source:
            for line in source:
                if 'add_subdirectory' in line:
                    with open(makefilePath2) as secondMakeFile:
                        data += secondMakeFile.read()
                else:
                    data += line.replace('source/', '').replace('/source', '')
        with open(makefilePath2, 'w') as destination:
            destination.write(data)

    def getPatchFile(self, version: str) -> str:
        """
        Return the path to the patch file for the specified Python version.

        :param version: The Python version.
        :return: The path to the patch file.
        """
        patchFile = os.path.join(self.config.patchesDir, 'Python' + version + '.patch')
        if not os.path.exists(patchFile):
            patchFile = None
        return patchFile

    def getAllAvailablePythonVersions(self) -> Optional[Dict[str, str]]:
        """
        Query all available Python versions from the source server and returns a dict with a
        version to download url mapping. Versions are also filtered by the availability
        of a patch file for that version.

        :return: A mapping of Python version strings to their corresponding download url.
        """
        startTime = time()
        connection = Connection(self.config.pythonServer)
        self.info('Gathering Python versions at "{url}"...'
                  .format(url=connection.host + self.config.pythonServerPath))
        connection.request('GET', self.config.pythonServerPath,
                           headers={"Connection": "keep-alive"})
        response = connection.getresponse()
        if response.status != 200:
            self.error('Failed to connect to "{host}/{path}":'
                       .format(host=connection.host, path=self.config.pythonServerPath))
            self.error('Response {status}:{reason}'.format(
                status=response.status, reason=response.reason))
            return None
        result = response.read().decode('utf-8').split('\n')
        self.info('Got a response in {seconds} seconds.'
                  .format(seconds=round(time() - startTime, 2)))
        versions = {}
        self.info('Checking availability of the sources...')
        for line in result:
            versionMatch = re.search(r'href\s*=\s*"(.*)"', line)
            if versionMatch is None:
                continue
            version = versionMatch.group(1)
            if re.match(r'\A\d+\.\d+(\.\d+)*/\Z', version) is None:
                continue
            version = version[:-1]
            if self.getPatchFile(version) is None:
                self.info('Ignoring version {version} because no patch-file was found.'
                          .format(version=version))
                continue
            url = self.versionToUrl(connection, version)
            if type(url) != str:
                if version != '2.0':
                    self.info('Ignoring version {version} because it has no downloadable'
                              ' source code. Maybe this version is still in development.'
                              .format(version=version))
                continue
            versions[version] = url
        connection.close()
        return versions

    def versionToUrl(self, connection: Connection, version: str) -> Union[str, HTTPResponse]:
        """
        Takes an existing connection to the Python source server and queries it for the download
        file of the requested Python version. If the version exists, the url to its
        source is returned, otherwise the network response is returned.

        :param connection: An existing connection to the Python download server.
        :param version: The Python version.
        :return: The url for the download of the sources of the Python version.
        """
        path = self.config.pythonServerPath + version + '/Python-' + version + '.tgz'
        self.debug('Checking Python version at "{url}"...'.format(url=connection.host + path))
        startTime = time()
        connection.request('HEAD', path, headers={"Connection": "keep-alive"})
        response = connection.getresponse()
        response.read()  # Empty the request
        self.debug('Got a response in {seconds} seconds.'
                   .format(seconds=round(time() - startTime, 2)))
        if response.status != 200:
            return response
        return path

    def downloadPythonSource(self, versionPath: str, downloadDir: str) -> Optional[str]:
        """
        Download a Python source archive from the Python source server at the sub-path
        'versionPath' and stores it in 'downloadDir'.

        :param versionPath: The relative path on the download server to the Python source file.
        :param downloadDir: The path to the directory to store the downloaded sources in.
        :return: The path to the downloaded file on success or None on failure.
        """
        self.info('Downloading Python source from "{url}"...'
                  .format(url=self.config.pythonServer + versionPath))
        return self.cache.download('https://' + self.config.pythonServer + versionPath,
                                   downloadDir, self.config.log)

    def extractPythonArchive(self, sourceArchive: str, extractedDir: str) -> Optional[str]:
        """
        Extract the Python archive at 'sourceArchive' to 'extractedDir'.

        :param sourceArchive: The path to the source archive file.
        :param extractedDir: The path to the directory where to extract the source to.
        :return: The path to the first directory of the extracted archive
                 on success or None on error.
        """
        self.info('Extracting {archive}...'.format(archive=sourceArchive))
        res = buildutils.extract(
            sourceArchive, extractedDir,
            ['Include', 'Lib', 'Modules', 'Objects', 'Parser', 'Python', 'LICENSE', 'README'],
            ['.c', '.h', '.py', '.pyc', '.inc', '.txt', '', '.gif', '.png', '.def']
        )
        if res is None:
            self.error('Failed to extract {archive}!'.format(archive=sourceArchive))
        elif not res:
            self.error('Failed to extract {archive}: Archive is compressed with an '
                       'unsupported compression.'.format(archive=sourceArchive))
            return None
        return res

    @staticmethod
    def generateModulesZip(sourcePath: str, outputDir: str) -> bool:
        """
        Generate the Python modules zip from the source at 'sourcePath'
        and store it into 'outputDir'.

        :param sourcePath: The path to the Python source directory.
        :param outputDir: The path within to store the modules zip.
        :return: True on success, False otherwise.
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
        """
        Compile the source of the given Python version located at 'sourcePath'
        and stores the compiled binaries into the output directory.

        :param sourcePath: The path to the Python source directory.
        :param pythonVersion: The Python version string.
        :param tempDir: The temporary directory to use during compiling.
        :return: True on success, False otherwise.
        """
        parentDir = os.path.dirname(sourcePath)
        # Copy the makefile
        self.copyTemplateMakefile(
            os.path.join(self.config.buildFilesDir, 'Python' + pythonVersion, buildutils.MAKE_FILE),
            os.path.join(sourcePath, buildutils.MAKE_FILE))
        # Compile
        self.info('Compiling Python {version}...'.format(version=pythonVersion))
        outputDir = os.path.join(self.config.outputDir, 'Python' + pythonVersion)
        return buildutils.build(
            self.config.ndkPath, parentDir, outputDir, os.path.join(tempDir, 'NDK-Temp'),
            cmakePath=self.config.cmakePath, makePath=self.config.makePath,
            androidSdkVersion=self.config.minSdkVersion, cpuABIs=self.config.cpuABIs,
            logger=self.config.log)

    def cleanup(self, sourcePath: str, outputDir: str):
        """
        Remove unnecessary build artifacts in the 'outputDir' and cleans the build directory located
        at 'sourcePath' from the last build, so another Python version can be compiled there.

        :param sourcePath: The path to the source directory.
        :param outputDir: The path to the output directory.
        """
        self.info('Removing unnecessary files...')
        shutil.rmtree(sourcePath)
        additionalLibsNames, additionalLibsData = zip(*self.config.additionalLibs.items())
        for subdir in os.listdir(outputDir):
            if os.path.isdir(os.path.join(outputDir, subdir)):
                for libFile in os.listdir(os.path.join(outputDir, subdir)):
                    if libFile[3:-3] in additionalLibsNames:
                        os.remove(os.path.join(outputDir, subdir, libFile))
        sourceParentPath = os.path.dirname(sourcePath)
        additionalPythonModules = []
        for moduleData in additionalLibsData:
            additionalPythonModules += moduleData.get('pyModuleReq', [])
            additionalPythonModules += moduleData.get('py3ModuleReq', [])
        for subdir in os.listdir(sourceParentPath):
            if os.path.isdir(os.path.join(sourceParentPath, subdir)):
                if subdir in additionalPythonModules:
                    shutil.rmtree(os.path.join(sourceParentPath, subdir))

    def generateJSON(self) -> bool:
        """
        Generate the JSON file with all information needed
        by a connecting client to download the created data.

        :return: True on success, False otherwise.
        """
        self.info('Generating JSON file...')
        requirements = OrderedDict()
        for libName, libData in sorted(self.config.additionalLibs.items()):
            dependencies = ['libraries/' + dep for dep in libData.get('dependencies', [])]
            dependencies += ['data/' + dep[1] for dep in libData.get('data', [])]
            if 'minAndroidSdk' in libData and libData['minAndroidSdk'] > self.config.minSdkVersion:
                dependencies += ['androidSdk/' + str(libData['minAndroidSdk'])]
            if len(dependencies) > 0:
                requirements['libraries/{name}'.format(name=libName)] = dependencies
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
        for moduleName, moduleDependencyList in sorted(moduleDependencies.items()):
            requirements['pyModule/{name}'.format(name=moduleName)] = sorted(moduleDependencyList)
        dataItem = OrderedDict()
        for name, libData in sorted(self.config.additionalLibs.items()):
            if 'data' in libData.keys():
                for data in libData['data']:
                    dataPath = os.path.join(self.config.outputDir, 'data', data[1])
                    if not os.path.exists(dataPath):
                        for path in os.listdir(os.path.dirname(dataPath)):
                            if path.startswith(data[1] + '.'):
                                dataPath = os.path.join(os.path.dirname(dataPath), path)
                                break
                        else:
                            dataPath += '.zip'
                    item = OrderedDict(path=[
                        'output/data/{name}'.format(name=os.path.basename(dataPath)),
                        buildutils.createMd5Hash(dataPath)
                    ])
                    if data[2] != 'files/data':
                        item['dst'] = data[2]
                    dataItem[data[1]] = item

        additionalLibs = set()
        libraries = OrderedDict()
        libraryDir = os.path.join(self.config.outputDir, 'libraries')
        if os.path.isdir(libraryDir):
            for subdir in os.listdir(libraryDir):
                for libFile in os.listdir(os.path.join(libraryDir, subdir)):
                    if libFile.startswith('lib') and libFile.endswith('.so'):
                        additionalLibs.add(libFile[3:-3])
            for lib in sorted(additionalLibs):
                libItem = OrderedDict()
                for architecture in os.listdir(libraryDir):
                    if 'lib' + lib + '.so' in os.listdir(os.path.join(libraryDir, architecture)):
                        filePath = os.path.join(libraryDir, architecture, 'lib' + lib + '.so')
                        libItem[architecture] = [
                            'output/libraries/{abi}/lib{name}.so'
                            .format(abi=architecture, name=lib),
                            buildutils.createMd5Hash(filePath)
                        ]
                libraries[lib] = libItem

        jsonData = OrderedDict()
        jsonData['__version__'] = 2
        jsonData['requirements'] = requirements
        jsonData['data'] = dataItem
        jsonData['libraries'] = libraries
        jsonData['minSdk'] = self.config.minSdkVersion
        for versionDir in os.listdir(self.config.outputDir):
            if versionDir == 'libraries' or versionDir == 'data':
                continue
            version = versionDir[6:]
            versionItem = OrderedDict()
            modulesFile = os.path.join(self.config.outputDir, versionDir, 'lib.zip')
            if not os.path.exists(modulesFile):
                self.error('lib.zip not found in {path}.'
                           .format(path=os.path.join(self.config.outputDir, versionDir)))
                return False
            for architecture in os.listdir(os.path.join(self.config.outputDir, versionDir)):
                abiDir = os.path.join(self.config.outputDir, versionDir, architecture)
                if not os.path.isdir(abiDir):
                    continue
                architectureItem = OrderedDict()
                libFiles = os.listdir(abiDir)
                if not 'lib' + 'python{ver}.so'.format(ver=buildutils.getShortVersion(version)) in \
                       libFiles:
                    self.error('The Python library was not found in {path}.'.format(path=abiDir))
                    return False
                for libRelativePath in libFiles:
                    libFile = os.path.basename(libRelativePath)
                    libPath = os.path.join(abiDir, libRelativePath)
                    if os.path.isdir(libPath):
                        libFiles.extend(
                            os.path.join(libRelativePath, file) for file in os.listdir(libPath))
                        continue
                    lib = 'pythonLib' if 'lib' + 'python' in libFile else libFile[:-3]
                    architectureItem[lib] = [
                        'output/{versionDir}/{abi}/{libFile}'
                        .format(versionDir=versionDir, abi=architecture,
                                libFile=libRelativePath.replace(os.path.sep, '/')),
                        buildutils.createMd5Hash(libPath)
                    ]
                versionItem[architecture] = architectureItem
            versionItem['lib'] = [
                'output/{versionDir}/lib.zip'.format(versionDir=versionDir),
                buildutils.createMd5Hash(modulesFile)
            ]
            jsonData[version] = versionItem
        jsonPath = os.path.join(os.path.dirname(self.config.outputDir), 'index.json')
        with open(jsonPath, 'w') as jsonFile:
            json.dump(jsonData, jsonFile, ensure_ascii=False, indent=0)
        self.info('Successfully generated JSON file.')
        return True

    def updateReadMe(self):
        """ Update the README file to display all currently available libraries. """
        self.info('Updating README.md...')
        readmeTemplatePath = os.path.join(self.config.currDir, 'README.md.template')
        readmePath = os.path.join(self.config.currDir, 'README.md')
        # itemTemplate = '* {libName} (from {url}) for {modules}\n'
        libList = ''
        for libraryName, libraryData in sorted(self.config.additionalLibs.items()):
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
                    library='libraries' if len(depList) > 1 else 'library',
                    list=', '.join(sorted(depList)))
            libList += '\n'
        with open(readmeTemplatePath, 'r') as template:
            with open(readmePath, 'w') as output:
                output.write(template.read().format(libList=libList))


def main():
    parser = ArgumentParser(description=__doc__)
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
    parser.add_argument('--buildFilesDir', default='buildFiles',
                        help='The path to the build files directory. Defaults to the directory '
                             '"buildFiles" in the current directory.')
    parser.add_argument('--cacheDir', help='The path to the cache directory. Downloaded files will '
                                           'be stored there during compilation. They will get '
                                           'deleted, when the build process succeeds.')
    parser.add_argument('--gitPath', help='The path to the patch executable in the git directory.')
    parser.add_argument('--cmakePath', help='The path to the cmake executable.')
    parser.add_argument('--makePath',
                        help='The path to the make executable (e.g. ninja.exe on Windows).')
    parser.add_argument('--ndkPath', help='The path to the ndk directory.')
    parser.add_argument('--pythonPatchDir', help='The path to the directory where the pythonPatch '
                                                 'library source code can be found.')
    parser.add_argument('--ipcDir', help='The path to the directory where the IPC '
                                         'library source code can be found.')
    parser.add_argument('--pythonServer', default=Configuration.pythonServer,
                        help='The host address of the Python server. Defaults to {host}".'
                        .format(host=Configuration.pythonServer))
    parser.add_argument('--pythonServerPath', default=Configuration.pythonServerPath,
                        help='The path on the Python server to see all available Python versions. '
                             'Defaults to "{path}".'.format(path=Configuration.pythonServerPath))
    parser.add_argument('--cpuABIs', nargs='*', default=[],
                        help='The cpu ABIs to compile for. Defaults to all supported by the ndk.')
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
