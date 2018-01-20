import os
import re
import tarfile
import subprocess
from typing import Union, Tuple, Optional, List
from urllib.request import urlopen
from urllib.error import URLError
from contextlib import closing
from hashlib import md5
from multiprocessing import Pool
from time import time
from zipfile import ZipFile, BadZipfile

from logger import Logger


def _callSubprocess(args) -> Union[bool, Tuple[int, bytes, bytes]]:
    """>>>_callSubprocess(args) -> True or (exitcode, stdout, stderr)
    Helper Function to call a subprocess in a different process.
    Calls the subprocess given via 'args'. Returns True, if
    the subprocess succeeded and returns the exitcode and the
    contents of the stdout and stderr of the subprocess on failure.
    """
    subProcess = subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = subProcess.communicate()
    subProcess.terminate()
    if subProcess.returncode != 0:
        return subProcess.returncode, stdout, stderr
    else:
        return True


def download(url, destination: str, logger: Logger) -> Optional[str]:
    """>>> download(url, destination, logger) -> None or path
    Downloads a file from 'url'. The retrieved file will be saved
    in 'destination'. If 'destination' is a directory, the file is saved
    in this directory with the same name it had on the server.
    Progress information is written to the logs via 'logger'.
    On success, the path to the downloaded file is returned.
    In case of an error, None is returned.
    """
    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(url))
    if (('//github.com' in url) or ('www.github.com' in url)) and os.path.splitext(url)[1] == '':
        url = getGitRepositoryDownloadUrl(url)
        if os.path.splitext(destination)[-1] == '':
            destination += os.path.splitext(url)[-1]
    startTime = time()
    try:
        with closing(urlopen(url)) as response:
            if response.code != 200 or 'Content-Length' not in response.headers:
                msg = response.reason if hasattr(response, 'reason') else '?'
                if response.code is None:
                    logger.warn('Failed to receive response code from {url} (reason {msg}), '
                                'download may fail!'.format(url=url, msg=msg))
                else:
                    reason = 'Download failed with code {code}: {msg}'\
                        .format(code=response.code, msg=msg)
                    raise URLError(reason)
            totalLength = int(response.headers['Content-Length'])
            writtenBytes = 0
            with open(destination, 'wb') as downloadFile:
                data = response.read(4096)
                while data:
                    writtenBytes += downloadFile.write(data)
                    percentage = int(round((writtenBytes / totalLength) * 100))
                    twentieth = int(round(percentage / 5))
                    logger.console('[Info ] [{progress}] {bytes}/{total} KB, {percentage}%'.format(
                        progress=('\u2588' * twentieth).ljust(20), bytes=round(writtenBytes / 1000),
                        total=round(totalLength / 1000), percentage=percentage), end='\r')
                    data = response.read(4096)
            logger.console(' ' * 60, end='\r')
    except URLError as error:
        logger.error('Download from {url} failed: {msg}'.format(url=url, msg=error.reason))
        return None
    except IOError as ioError:
        logger.error('Download from {url} failed: {msg}'.format(url=url, msg=ioError.strerror))
        return None
    logger.info('Download finished in {seconds} seconds.'
                .format(seconds=round(time() - startTime, 2)))
    return destination


def extract(sourceArchive: str, extractionDir: str, extractionFilter: Optional[List[str]]=None,
            allowedFileTypes: Optional[List[str]]=None) -> Union[str, bool, None]:
    """>>> extract(sourceArchive, extractionDir, extractionFilter, allowedFileTypes) -> path
    Extracts the archive located under 'sourceArchive'
    and puts its content under 'extractionDir'. If
    'extractionFilter' is specified as a list of filters
    All files and directories matching a filter won't
    get extracted. If 'allowedFileTypes' is specified, only
    files with the given file ending are extracted. Returns
    the path to the first directory of the extracted content.
    Returns False, if the archive format is not supported and
    None, if an exception occurred during extraction.
    """
    matcher = None
    if extractionFilter:
        for i in range(len(extractionFilter)):
            extractionFilter[i] = '^' + extractionFilter[i].replace('.', '\\.').replace('*', '.*')
            if os.path.splitext(extractionFilter[i])[1] == '':
                # if the filter seems to be a directory, add its contents to the list
                extractionFilter.append(extractionFilter[i] + '/.*')
        matcher = re.compile('|'.join(extractionFilter))
    extension = os.path.splitext(sourceArchive)[-1]
    try:
        if extension == '.zip':
            archiveFile = ZipFile(sourceArchive)
            archiveMembers = archiveFile.namelist()

            def getMemberName(member): return member
        else:
            archiveFile = tarfile.open(sourceArchive)
            archiveMembers = archiveFile.getmembers()

            def getMemberName(member): return member.name
        if len(archiveMembers) == 0:
            return extractionDir
        baseDir = getMemberName(archiveMembers[0]).split('/')[0]

        def check_members(members):
            for member in members:
                if getMemberName(member) == baseDir:
                    yield member
                    continue
                if allowedFileTypes is not None and\
                   os.path.splitext(getMemberName(member))[-1] not in allowedFileTypes:
                    continue
                if matcher is not None and\
                   matcher.match(getMemberName(member).split('/', 1)[-1]) is None:
                    continue
                yield member
        archiveFile.extractall(path=extractionDir, members=check_members(archiveMembers))
    except tarfile.CompressionError:
        return False
    except (tarfile.TarError, BadZipfile, IOError):
        return None
    return os.path.join(extractionDir, baseDir)


def ndkCompile(ndkPath: str, tempDir: str, sourcePath: str, outputPath: str,
               cpuABIs: List[str], logger: Logger) -> bool:
    """>>> ndkCompile(ndkPath, tempDir, sourcePath, outputPath, cpuABIs, logger) -> success
    Compiles the source in 'sourcePath', using the ndk
    located at 'ndkPath'. An Application.mk file is
    expected under 'sourcePath'. All temporary objects
    will be placed under 'tempDir'. The output is placed
    under 'outputPath'/$(TARGET_ARCH_ABI). The cpu ABIs
    to compile for are given via 'cpuABIs'. Logs the
    executed command via 'logger'. Returns True, if the
    compilation succeeded, False on failure.
    """
    args = createCompileSubprocessArgs(ndkPath, tempDir, sourcePath, outputPath, cpuABIs, logger)
    return subprocess.call(args, cwd=sourcePath, stdout=logger.getOutput(),
                           stderr=logger.getOutput()) == 0


def createMd5Hash(filePath: str) -> str:
    """>>> createHash(filePath) -> str
    Creates the md5 hash of the file at 'filePath'.
    """
    md5Hash = md5()
    with open(filePath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5Hash.update(chunk)
    return md5Hash.hexdigest()


def getGitRepositoryDownloadUrl(url: str) -> str:
    """>>> getGitRepositoryDownloadUrl(url) -> url
    Takes a git repository url 'url' and returns
    the url to the master zip.
    """
    return url + ('/' if url[-1] != '/' else '') + 'archive/master.zip'


def fillTemplate(templatePath: str, destination: str, **formatArguments):
    """>>> fillTemplate(templatePath, destination, **formatArguments)
    Reads a template from 'templatePath', formats it
    using 'formatArguments' and saves the formatted
    template at 'destination'.
    """
    with open(templatePath) as template:
        templateContent = template.read()
    with open(destination, 'w') as output:
        output.write(templateContent.format(**formatArguments))


def getShortVersion(version: str) -> str:
    """>>> getShortVersion(version) -> shortVersion
    Returns the major and minor part of 'version'.
    """
    return '.'.join(version.split('.')[:2])


def escapeNDKParameter(parameter: str) -> str:
    """escapeNDKParameter(parameter) -> escapedParameter
    Modifies a parameter so that it can be used by the ndk.
    """
    if os.name == 'nt':
        return parameter.replace('\\', '/')
    else:
        return parameter


def callSubProcessesMultiThreaded(subProcessArgs, logger: Logger) -> bool:
    """>>>callSubProcessesMultiThreaded(subprocessArgs, logger) -> success
    Executes the sub processes constructed from the given 'subprocessArgs' in
    parallel. If one of them fail, the exitcode, stdout and stderr are written
    to the logs via 'logger' and False is returned.
    """
    pool = Pool(min(10, len(subProcessArgs)))
    logger.debug('Starting {num} sub processes.'.format(num=len(subProcessArgs)))
    handles = [pool.apply_async(_callSubprocess, [args]) for args in subProcessArgs]
    pool.close()
    while len(handles) > 0:
        result = handles.pop(0).get()
        if result is not True:
            logger.error('Subprocess exited with code {code}.'.format(code=result[0]))
            logger.info(result[1].decode('utf-8'))
            logger.error(result[2].decode('utf-8'))
            return False
    return True


def createCompileSubprocessArgs(ndkPath: str, tempDir: str, sourcePath: str, outputPath: str,
                                ABIs: List[str], logger: Logger) -> List[str]:
    """>>> createCompileSubprocessArgs(ndkPath, tempDir, sourcePath, outputPath, ABIs, logger)
    -> arguments
    Create a list of arguments that can be used to create a subprocess to
    compile the source in 'sourcePath' using the ndk located at 'ndkPath'.
    An Application.mk file is expected under 'sourcePath'. All temporary
    objects will be placed under 'tempDir'. The cpu ABIs to compile for are
    given via 'ABIs'. The output is placed at 'outputPath'/$(TARGET_ARCH_ABI).
    Logs the executed command via 'logger'. Returns the list of arguments.
    """
    args = [
        ndkPath,
        'NDK_OUT=' + escapeNDKParameter(tempDir),
        '-C', escapeNDKParameter(sourcePath),
        'NDK_APPLICATION_MK=' + escapeNDKParameter(sourcePath) + '/Application.mk',
        'NDK_PROJECT_PATH=' + escapeNDKParameter(sourcePath),
        'NDK_APP_DST_DIR=' + escapeNDKParameter(outputPath) + '/$(TARGET_ARCH_ABI)',
        'APP_ABI=' + ' '.join(ABIs if type(ABIs) in [list, tuple] else [ABIs])
    ]
    logger.debug(subprocess.list2cmdline(args))
    return args


def applyPatch(gitPath: str, sourcePath: str, patchFilePath: str, logger: Logger) -> bool:
    """>>> applyPatch(gitPath, sourcePath, patchFilePath, logger) -> success
    Apply the patch in the patchFile 'patchFilePath' to 'sourcePath'.
    """
    args = [gitPath, '-C', sourcePath, 'apply', '-p1', patchFilePath]
    logger.info('Patching the source code with {path}...'.format(path=patchFilePath))
    logger.debug(subprocess.list2cmdline(args))
    return subprocess.call(args, stdout=logger.getOutput(), stderr=logger.getOutput()) == 0
