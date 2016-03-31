import os
import buildutils
import shutil

class Cache(object):
    
    cachePath = None
    
    def __init__(self, cachePath):
        self.cachePath = cachePath
        self.ensureCacheDir()
    
    def ensureCacheDir(self):
        '''>>> ensureCacheDir
        Enshures, that the cache directory exists.
        '''
        if not os.path.exists(self.cachePath):
            os.mkdir(self.cachePath)
    
    def download(self, url, destFile, logger):
        '''>>> download(url, destFile, logger) -> path or None
        Searches for a file in the cache and downloads it from 'url',
        if it is not found in the chache. The retrieved file will be
        saved in 'destFile'. If 'destFile' is a directory, the file
        is saved in this directory with the same name it had on the
        server. Progress information is written to the logs via
        'logger'. On success, the path to the downloaded file is
        returned. In case of an download error, None is returned.
        '''
        fileName = os.path.basename(url)
        if (('//github.com' in url) or ('www.github.com' in url)) and os.path.splitext(url)[1] == '':
            url = buildutils.getGitRepositoryDownloadUrl(url)
            fileName += os.path.splitext(url)[-1]
        destFile = destFile if not os.path.isdir(destFile) else os.path.join(destFile, fileName)
        cachePath = os.path.join(self.cachePath, fileName)
        if not os.path.exists(cachePath):
            if buildutils.download(url, cachePath, logger) == None:
                return None
        else:
            logger.info('Using cached version from ' + cachePath)
        shutil.copy(cachePath, destFile)
        return destFile
    
    def clear(self, ignore_errors = False):
        '''>>> clear(ignore_errors = False)
        Clears the cache and deletes the cache directory.
        This Cache instance should not be used afterwards,
        untill a call to ensureCacheDir.
        '''
        shutil.rmtree(self.cachePath, ignore_errors = ignore_errors)
