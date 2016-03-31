import os
import re
import tarfile
import subprocess
try:
    from httplib import HTTPSConnection as Connection
except ImportError:
    print('[Warn ] No HTTPS connection provider found, using HTTP instead.')
    from httplib import HTTPConnection as Connection
from httplib         import HTTPResponse, BadStatusLine, HTTPConnection
from urlparse        import urlparse
from urllib2         import urlopen, HTTPError
from contextlib      import closing
from hashlib         import md5
from multiprocessing import Pool
from time            import time
from zipfile         import ZipFile, BadZipfile

def _callSubprocess(args):
    '''>>>_callSubprocess(args) -> True or (exitcode, stdout, stderr)
    Helper Function to call a subprocess in a different process.
    Calls the subprocess given via 'args'. Returns True, if
    the subprocess succeeded and returns the exitcode and the
    contents of the stdout and stderr of the subprocess on failure.
    '''
    subProcess = subprocess.Popen(args, bufsize = -1, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = subProcess.communicate()
    subProcess.terminate()
    if subProcess.returncode != 0:
        return subProcess.returncode, stdout, stderr
    else:
        return True

def download(url, destFile, logger):
    '''>>> download(url, destFile, logger) -> None or path
    Downloads a file from 'url'. The retrieved file will be saved
    in 'destFile'. If 'destFile' is a directory, the file is saved
    in this directory with the same name it had on the server.
    Progress information is written to the logs via 'logger'.
    On success, the path to the downloaded file is returned.
    In case of an error, None is returned.
    '''
    destFile = destFile if not os.path.isdir(destFile) else os.path.join(destFile, os.path.basename(url))
    if (('//github.com' in url) or ('www.github.com' in url)) and os.path.splitext(url)[1] == '':
        url = getGitRepositoryDownloadUrl(url)
        if os.path.splitext(destFile)[-1] == '':
            destFile += os.path.splitext(u)[-1]
    startTime = time()
    try:
        with closing(urlopen(url)) as download:
            if download.code != 200 or not 'Content-Length' in download.headers:
                if download.code == None:
                    logger.warn('Failed to receive response code from ' + url + ' (status: '
                                 + str(download.info().status) + '), download may fail!')
                else:
                    raise HTTPError(url, download.code, download.info().status, download.headers, None)
            totalLength = int(download.headers['Content-Length'])
            fifth = totalLength / 20
            with open(destFile, 'wb') as downloadFile:
                for i in range(20):
                    downloadFile.write(download.read(size = fifth))
                    logger.console('[Info ] ' + str(int(round(((i + 1) / 20.0) * 100))) + '%', end = '\r')
                downloadFile.write(download.read())
    except HTTPError as e:
        logger.error('Download from ' + url + ' failed (Response code ' + str(e.code)
             + '): ' + str(e.reason))
        return None
    except IOError as ioError:
        logger.error('Download from ' + url + ' failed: ' + ioError.message)
        return None
    logger.info('Download finished in ' + str(round(time() - startTime, 2)) + ' seconds.')
    return destFile

def extract(sourceArchive, extractionDir, extractionFilter = None, allowedFileTypes = None):
    '''>>> extract(sourceArchive, extractionDir, extractionFilter, allowedFileTypes) -> path
    Extracts the archive located under 'sourceArchive'
    and puts its content under 'extractionDir'. If
    'extractionFilter' is specified as a list of filters
    All files and direcories matching a filter won't
    get extracted. If 'allowedFileTypes' is specified, only
    files with the given file ending are extracted. Returns
    the path to the first directory of the extracted content.
    Returns False, if the archive format is not supported and
    None, if an exception occurred during extraction.
    '''
    matcher = None
    if extractionFilter:
        for i in range(len(extractionFilter)):
            filterItem = extractionFilter[i]
            if os.path.splitext(filterItem)[1] == '':
                extractionFilter.append('^' + filterItem.replace('.', '\\.').replace('*', '.*') + '/.*')
            extractionFilter[i] = '^' + filterItem.replace('.', '\\.').replace('*', '.*')
        matcher = re.compile('|'.join(extractionFilter))
    archiveFile = None
    archiveMembers = []
    extension = os.path.splitext(sourceArchive)[-1]
    getMemberName = None
    try:
        if extension == '.zip':
            archiveFile = ZipFile(sourceArchive)
            archiveMembers = archiveFile.namelist()
            getMemberName = lambda member: member
        else:
            archiveFile = tarfile.open(sourceArchive)
            archiveMembers = archiveFile.getmembers()
            getMemberName = lambda member: member.name
        if len(archiveMembers) == 0:
            return extractionDir
        baseDir = getMemberName(archiveMembers[0]).split('/')[0]
        def check_members(members):
            for member in members:
                if getMemberName(member) == baseDir:
                    yield member
                    continue
                if allowedFileTypes != None and os.path.splitext(getMemberName(member))[-1] not in allowedFileTypes:
                    continue
                if matcher != None and matcher.match(getMemberName(member).split('/', 1)[-1]) == None:
                    continue
                yield member
        archiveFile.extractall(path = extractionDir, members = check_members(archiveMembers))
    except tarfile.CompressionError:
        return False
    except (tarfile.TarError, BadZipfile, IOError):
        return None
    return os.path.join(extractionDir, baseDir)

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
    args = createCompileSubprocessArgs(ndkPath, tempDir, sourcePath, outputPath, cpuAbis, logger)
    return subprocess.call(args, cwd = sourcePath, stdout = logger.getOutput(), stderr = logger.getOutput()) == 0

def createMd5Hash(filePath):
    '''>>> createHash(filePath) -> str
    Creates the md5 hash of the file at 'filePath'.
    '''
    md5Hash = md5()
    with open(filePath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), ''):
            md5Hash.update(chunk)
    return md5Hash.hexdigest()

def getGitRepositoryDownloadUrl(url):
    '''>>> getGitRepositoryDownloadUrl(url) -> url
    Takes a git repository url 'url' and returns
    the url to the master zip.
    '''
    return url + ('/' if url[-1] != '/' else '') + 'archive/master.zip'

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
    if response.status != 200:
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
        download(downloadFile[1], os.path.join(destDir, downloadFile[0]), logger)
    return destDir

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

def getShortVersion(version):
    '''>>> getShortVersion(version) -> shortVersion
    Returns the major and minor part of 'version'.
    '''
    return '.'.join(version.split('.')[:2])

def escapeNDKParameter(parameter):
    '''escapeNDKParameter(parameter) -> escapedParameter
    Modifies a parameter so that it can be used by the ndk.
    '''
    if os.name == 'nt':
        return parameter.replace('\\', '/')
    else:
        return parameter

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
        'NDK_OUT=' + escapeNDKParameter(tempDir),
        'NDK_APPLICATION_MK=' + escapeNDKParameter(sourcePath) + '/Application.mk',
        'NDK_PROJECT_PATH=' + escapeNDKParameter(sourcePath),
        'NDK_APP_DST_DIR=' + escapeNDKParameter(outputPath) + '/$(TARGET_ARCH_ABI)',
        'APP_ABI=' + ' '.join(abis if type(abis) in [list, tuple] else [abis])
    ]
    logger.debug(subprocess.list2cmdline(args))
    return args

def applyPatch(gitPath, sourcePath, patchFilePath, logger):
    '''>>> applyPatch(gitPath, sourcePath, patchFilePath, logger) -> success
    Apply the patch in the patchfile 'patchFilePath' to 'sourcePath'.
    '''
    args = [gitPath, '-t', '-p1', '-d', sourcePath, '-i', patchFilePath]
    logger.info('Patching the source code with ' + patchFilePath + '...')
    logger.debug(subprocess.list2cmdline(args))
    return subprocess.call(args, stdout = logger.getOutput(), stderr = logger.getOutput()) == 0
