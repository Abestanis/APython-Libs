import os
import re
import tarfile
import subprocess
from typing import Union, Tuple, Optional, List
from urllib.request import urlretrieve
from urllib.error import URLError
from hashlib import md5
from multiprocessing import Pool
from time import time
from zipfile import ZipFile, BadZipfile

from logger import Logger

MAKE_FILE = 'CMakeLists.txt'


def _callSubprocess(args: List[List[str]]) -> Union[bool, Tuple[int, bytes, bytes]]:
    """
    Helper function to call a subprocess in a different process.
    Calls the processes given via 'args'. Returns True, if the subprocess succeeded and
    returns the exitcode and the contents of the stdout and stderr of the subprocess on failure.

    :param args: A list of a list of process arguments.
    :return: True if the commands successfully completed or (exitcode, stdout, stderr).
    """
    allStdout = b''
    allStderr = b''
    for argList in args:
        subProcess = subprocess.Popen(
            argList, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = subProcess.communicate()
        subProcess.terminate()
        allStderr += stderr
        allStdout += stdout
        if subProcess.returncode != 0:
            return subProcess.returncode, allStdout, allStderr
    return True


def _handleDownloadProcess(logger, currentBlock, blockSize, totalSize):
    """
    Handle process updates during the download of a file.

    :param logger: The logger to report the update on.
    :param currentBlock: The number of the current download block.
    :param blockSize: The size of a download block in bytes.
    :param totalSize: The size of all download blocks in bytes or -1 if unknown.
    """
    writtenBytes = currentBlock * blockSize
    if totalSize == -1:
        progress = ''.join('O' if currentBlock % 3 == i else 'o' for i in range(3))
        logger.console(f'[Info ] [{progress}] {round(writtenBytes / 1000)} KB', end='\r')
        return
    percentage = int(round((writtenBytes / totalSize) * 100))
    twentieth = int(round(percentage / 5))
    progress = ('\u2588' * twentieth).ljust(20)
    logger.console(f'[Info ] [{progress}] {round(writtenBytes / 1000)}/{round(totalSize / 1000)} '
                   f'KB, {percentage}%', end='\r')


def download(url, destination: str, logger: Logger) -> Optional[str]:
    """
    Downloads a file from 'url'. The retrieved file will be saved in 'destination'.
    If 'destination' is a directory, the file is saved in this directory with the same name it
    had on the server. Progress information is written to the logs via 'logger'. On success,
    the path to the downloaded file is returned. In case of an error, None is returned.

    :param url: The url of the file to download.
    :param destination: The path to save the file into, or the directory to save the file into.
    :param logger: A logger to report process.
    :return: The path to the downloaded file on success, None on failure.
    """
    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(url))
    if (('//github.com' in url) or ('www.github.com' in url)) and os.path.splitext(url)[1] == '':
        url = getGitRepositoryDownloadUrl(url)
        if os.path.splitext(destination)[-1] == '':
            destination += os.path.splitext(url)[-1]
    startTime = time()
    try:
        urlretrieve(url, destination, lambda *args: _handleDownloadProcess(logger, *args))
        logger.console(' ' * 60, end='\r')
    except URLError as error:
        logger.error(f'Download from {url} failed: {error.reason}')
        return None
    except IOError as ioError:
        logger.error(f'Download from {url} failed: {ioError.strerror}')
        return None
    logger.info(f'Download finished in {round(time() - startTime, 2)} seconds.')
    return destination


def extract(sourceArchive: str, extractionDir: str, extractionFilters: Optional[List[str]] = None,
            allowedFileTypes: Optional[List[str]] = None) -> Union[str, bool, None]:
    """
    Extracts the archive located under 'sourceArchive' and puts its content under 'extractionDir'.
    If 'extractionFilters' is specified as a list of filters all files and directories matching
    any of the filters won't get extracted. If 'allowedFileTypes' is specified, only files with the
    given file ending are extracted. Returns the path to the first directory of the extracted
    content. Returns False, if the archive format is not supported and None, if an exception
    occurred during extraction.

    :param sourceArchive: The archive to extract.
    :param extractionDir: The directory to extract the archive to.
    :param extractionFilters: An optional list of extraction filters.
    :param allowedFileTypes: An optional list of allowed file extensions.
    :return: Path to the first extracted directory, False if the archive
             format is unsupported or None on error.
    """
    matcher = None
    if extractionFilters:
        extractionFilters.append(MAKE_FILE)
        for i in range(len(extractionFilters)):
            extractionFilters[i] = '^' + extractionFilters[i].replace('.', '\\.').replace('*', '.*')
            if os.path.splitext(extractionFilters[i])[1] == '':
                # if the filter seems to be a directory, add its contents to the list
                extractionFilters.append(extractionFilters[i] + '/.*')
        matcher = re.compile('|'.join(extractionFilters))
    extension = os.path.splitext(sourceArchive)[-1]
    try:
        if extension == '.zip':
            archiveFile = ZipFile(sourceArchive)
            archiveMembers = archiveFile.namelist()

            def getMemberName(member):
                return member
        else:
            archiveFile = tarfile.open(sourceArchive)
            archiveMembers = archiveFile.getmembers()

            def getMemberName(member):
                return member.name
        if len(archiveMembers) == 0:
            return extractionDir
        baseDir = getMemberName(archiveMembers[0]).split('/')[0]

        def check_members(members):
            for member in members:
                if getMemberName(member) == baseDir:
                    yield member
                    continue
                if allowedFileTypes is not None and \
                        os.path.splitext(getMemberName(member))[-1] not in allowedFileTypes:
                    continue
                if matcher is not None and \
                        matcher.match(getMemberName(member).split('/', 1)[-1]) is None:
                    continue
                yield member

        archiveFile.extractall(path=extractionDir, members=check_members(archiveMembers))
    except tarfile.CompressionError:
        return False
    except (tarfile.TarError, BadZipfile, IOError):
        return None
    return os.path.join(extractionDir, baseDir)


def createMd5Hash(filePath: str) -> str:
    """
    Creates the md5 hash of the file at 'filePath'.

    :param filePath: The path to the file.
    :return: The md5 hash.
    """
    md5Hash = md5()
    with open(filePath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5Hash.update(chunk)
    return md5Hash.hexdigest()


def getGitRepositoryDownloadUrl(url: str) -> str:
    """
    Takes a git repository url 'url' and returns the url to the master zip.

    :param url: The url to a GitHub repository.
    :return: The url to the master archive of the repository.
    """
    return url + ('/' if url[-1] != '/' else '') + 'archive/master.zip'


def getShortVersion(version: str) -> str:
    """
    :param version: A Python version.
    :return: The major and minor part of 'version'.
    """
    return '.'.join(version.split('.')[:2])


def escapeNDKParameter(parameter: str) -> str:
    """
    Modifies a parameter so that it can be used by the NDK.

    :param parameter: The value to escape.
    :return: The escaped value.
    """
    if os.name == 'nt':
        return parameter.replace('\\', '/')
    else:
        return parameter


def callSubProcessesMultiThreaded(subProcessArgs: List[List[List[str]]], logger: Logger) -> bool:
    """
    Executes the sub processes constructed from the given 'subprocessArgs' in parallel.
    If one of them fail, the exitcode, stdout and stderr are written to the logs via
    'logger' and False is returned.

    :param subProcessArgs: A list of lists containing the process arguments.
    :param logger: The logger to report process.
    :return: True on success, False otherwise.
    """
    pool = Pool(min(10, len(subProcessArgs)))
    logger.debug(f'Starting {len(subProcessArgs)} sub processes.')
    handles = [pool.apply_async(_callSubprocess, [args]) for args in subProcessArgs]
    pool.close()
    while len(handles) > 0:
        result = handles.pop(0).get()
        if result is not True:
            logger.error(f'Subprocess exited with code {result[0]}.')
            logger.info(result[1].decode('utf-8'))
            logger.error(result[2].decode('utf-8'))
            return False
    return True


def createCompileSubprocessArgs(
        cmakePath: str, ndkPath: str, tempDir: str, sourcePath: str, outputPath: str,
        makePath: str, apiLevel: int, cpuAbi: str, logger: Logger, debugBuild: bool = False
) -> List[List[str]]:
    """
    Create a list of arguments that can be used to create a subprocess to compile the source in
    'sourcePath' using the ndk located at 'ndkPath'. A makefile file is expected under
    'sourcePath'. All temporary objects will be placed under 'tempDir'. The cpu ABIs to compile
    for are given via 'cpuAbi'. The output is placed at 'outputPath'/abi.
    Logs the executed command via 'logger'.

    :param cmakePath: The path to the cmake executable.
    :param ndkPath: The path to the ndk directory.
    :param tempDir: A temporary directory to use during building.
    :param sourcePath: The path to the directory with the source files.
    :param outputPath: The path to the directory to store the generated libraries.
    :param makePath: The path tho the make executable.
    :param apiLevel: The Android api level to compile for.
    :param cpuAbi: The CPU ABIs to compile for.
    :param logger: The logger to log the generated commands.
    :param debugBuild: If the build should be a debug build.
    :return: A list of lists containing the process arguments.
    """
    args = [
        [
            cmakePath,
            '-D' + 'ANDROID_ABI=' + cpuAbi,
            '-D' + 'ANDROID_PLATFORM=android-' + str(apiLevel),
            '-D' + 'ANDROID_NDK=' + ndkPath,
            '-D' + 'CMAKE_LIBRARY_OUTPUT_DIRECTORY=' + os.path.join(outputPath, cpuAbi),
            '-D' + 'CMAKE_BUILD_TYPE=' + ('Debug' if debugBuild else 'Release'),
            '-D' + 'CMAKE_TOOLCHAIN_FILE=' + os.path.join(
                ndkPath, 'build', 'cmake', 'android.toolchain.cmake'),
            '-D' + 'ANDROID_NATIVE_API_LEVEL=' + str(apiLevel),
            '-D' + 'ANDROID_TOOLCHAIN=clang',
            '-D' + 'CMAKE_SYSTEM_NAME=Android',
            '-D' + 'CMAKE_ANDROID_ARCH_ABI=' + cpuAbi,
            '-D' + 'CMAKE_SYSTEM_VERSION=' + str(apiLevel),
            '-G' + 'Ninja',
            '-D' + 'CMAKE_MAKE_PROGRAM=' + makePath,
            sourcePath,
            '-B' + os.path.join(tempDir, cpuAbi)
        ], [
            cmakePath,
            '--build',
            os.path.join(tempDir, cpuAbi)
        ]
    ]
    logger.debug(' && '.join(subprocess.list2cmdline(arguments) for arguments in args))
    return args


def applyPatch(gitPath: str, sourcePath: str, patchFilePath: str, logger: Logger) -> bool:
    """
    Apply the patch in the patchFile 'patchFilePath' to 'sourcePath'.

    :param gitPath: The path to the git executable.
    :param sourcePath: The path to the file or directory to patch.
    :param patchFilePath: The path to the patch file.
    :param logger: The logger to report process.
    :return: True on success, False otherwise.
    """
    """>>> applyPatch(gitPath, sourcePath, patchFilePath, logger) -> success
    Apply the patch in the patchFile 'patchFilePath' to 'sourcePath'.
    """
    args = [gitPath, '-C', sourcePath, 'apply', '-p1', patchFilePath]
    logger.info(f'Patching the source code with {patchFilePath}...')
    logger.debug(subprocess.list2cmdline(args))
    return subprocess.call(args, stdout=logger.getOutput(), stderr=logger.getOutput()) == 0


def build(ndkPath, sourceDir, outputDir, tempDir, cmakePath, makePath,
          androidSdkVersion, cpuABIs, logger):
    """
    Compile the sources at the given sourceDir.

    :param ndkPath: The path to the ndk directory
    :param sourceDir: The path to the directory with the source files.
    :param outputDir: The path to the directory to store the generated libraries.
    :param tempDir: A temporary directory to use during building.
    :param cmakePath: The path to the cmake executable.
    :param makePath: The path tho the make executable.
    :param androidSdkVersion: The Android api level to compile for.
    :param cpuABIs: The CPU ABIs to compile for.
    :param logger: The logger to log the generated commands.
    :return: True on success, False otherwise.
    """
    makeFilePath = os.path.join(sourceDir, MAKE_FILE)
    with open(makeFilePath, 'w') as makeFile:
        # noinspection SpellCheckingInspection
        makeFile.write('''cmake_minimum_required(VERSION 3.5)
file(GLOB children RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/*)
foreach(child ${children})
    if(IS_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/${child})
        if(${child} MATCHES "Python-[0-9].*")
            list(APPEND pythonDirs ${child})
        else()
            add_subdirectory(${child})
        endif()
    endif()
endforeach()
foreach(pythonDir ${pythonDirs})
    add_subdirectory(${pythonDir})
endforeach()''')
    subprocessArgs = [
        createCompileSubprocessArgs(cmakePath, ndkPath, tempDir, sourceDir, outputDir, makePath,
                                    androidSdkVersion, abi, logger) for abi in cpuABIs
    ]
    return callSubProcessesMultiThreaded(subprocessArgs, logger)
