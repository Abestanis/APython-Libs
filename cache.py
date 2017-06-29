import os
from typing import Optional

import buildutils
import shutil
from tempfile import mkdtemp

from logger import Logger


class Cache:
    cachePath = None

    def __init__(self, cachePath):
        self.cachePath = cachePath or mkdtemp('tmp', 'APythonLibs')
        self.ensureCacheDir()

    def ensureCacheDir(self):
        """>>> ensureCacheDir
        Ensures, that the cache directory exists.
        """
        if not os.path.exists(self.cachePath):
            os.mkdir(self.cachePath)

    def download(self, url: str, destination: str, logger: Logger) -> Optional[str]:
        """>>> download(url, destination, logger) -> path or None
        Searches for a file in the cache and downloads it from 'url',
        if it is not found in the cache. The retrieved file will be
        saved in 'destination'. If 'destination' is a directory, the file
        is saved in this directory with the same name it had on the
        server. Progress information is written to the logs via
        'logger'. On success, the path to the downloaded file is
        returned. In case of an download error, None is returned.
        """
        fileName = os.path.basename(url)
        if (('//github.com' in url) or ('www.github.com' in url))\
                and os.path.splitext(url)[1] == '':
            url = buildutils.getGitRepositoryDownloadUrl(url)
            fileName += os.path.splitext(url)[-1]
        if os.path.isdir(destination):
            destination = os.path.join(destination, fileName)
        cachePath = os.path.join(self.cachePath, fileName)
        if not os.path.exists(cachePath):
            if buildutils.download(url, cachePath, logger) is None:
                return None
        else:
            logger.info('Using cached version from {path}.'.format(path=cachePath))
        shutil.copy(cachePath, destination)
        return destination

    def clear(self, ignore_errors: bool=False):
        """>>> clear(ignore_errors = False)
        Clears the cache and deletes the cache directory.
        This Cache instance should not be used afterwards,
        until a call to ensureCacheDir.
        """
        shutil.rmtree(self.cachePath, ignore_errors=ignore_errors)
