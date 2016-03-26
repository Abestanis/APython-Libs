import sys

class Logger(object):    
    _output = None
    
    def __init__(self, output = None):
        self._output = output
    
    def console(self, message, end = '\n'):
        if self._output == None:
            sys.stdout.write(message + end)
    
    def log(self, prefix, message):
        if self._output == None:
            print(prefix + ' ' + message)
        else:
            self._output.write(prefix + ' ' + message + '\n')
            self._output.flush()
    
    def debug(self, message):
        self.log('[Debug]', message)
    
    def info(self, message):
        self.log('[Info ]', message)
    
    def warn(self, message):
        self.log('[Warn ]', message)
    
    def error(self, message):
        self.log('[ERROR]', message)
    
    def getOutput(self):
        return self._output
