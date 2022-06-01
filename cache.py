import os
from typing import Optional
from urllib.parse import urlparse

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
        """ Ensures, that the cache directory exists. """
        if not os.path.exists(self.cachePath):
            os.mkdir(self.cachePath)

    def download(self, url: str, destination: str, logger: Logger) -> Optional[str]:
        """
        Searches for a file in the cache and downloads it from 'url', if it is not found in the
        cache. The retrieved file will be saved in 'destination'. If 'destination' is a directory,
        the file is saved in this directory with the same name it had on the server. Progress
        information is written to the logs via 'logger'. On success, the path to the downloaded
        file is returned. In case of a download error, None is returned.

        :param url: The url of the file to download.
        :param destination: The path to save the file into, or the directory to save the file into.
        :param logger: A logger to report process.
        :return: The path to the downloaded file on success, None on failure.
        """
        fileName = os.path.basename(url)
        parsedUrl = urlparse(url)
        if parsedUrl.netloc in ['github.com', 'www.github.com'] and not url.endswith('.zip'):
            url = buildutils.getGitRepositoryDownloadUrl(parsedUrl)
            fileName += os.path.splitext(url)[-1]
        if os.path.isdir(destination):
            destination = os.path.join(destination, fileName)
        cachePath = os.path.join(self.cachePath, fileName)
        if not os.path.exists(cachePath):
            if buildutils.download(url, cachePath, logger) is None:
                return None
        else:
            logger.info(f'Using cached version from {cachePath}.')
        shutil.copy(cachePath, destination)
        return destination

    def clear(self, ignore_errors: bool = False):
        """
        Clears the cache and deletes the cache directory. This Cache instance should not be used
        afterwards, until a call to ensureCacheDir.

        :param ignore_errors: If True, ignore errors during deletion.
        """
        shutil.rmtree(self.cachePath, ignore_errors=ignore_errors)
