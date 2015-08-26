# APython-Libs
This repository hosts all the library files and their generating code for the [APython Project](https://github.com/Abestanis/APython).

##Usage

The build.py script takes care of downloading and patching the source code, calling the [ndk](https://developer.android.com/tools/sdk/ndk/index.html) and generating the index.json file.
For a list of all avaliable options type ```build.py -h``` or ```build.py --help```.

The skript will also download and compile the source code from some additional libraries to allow the generation of some python modules which depend on these libraries (e.g. the _ssl module depends on openSSL).

Currently these additional libraries are downloaded:
* [openSSL](https://www.openssl.org/) for the _ssl module
* [ffi](https://sourceware.org/libffi/) for the ctypes module
* [bzip](http://www.bzip.org/) for the zlib module

The generated lib-files and the json file will be used by the [Python Host App](https://github.com/Abestanis/APython) to download Python versions and the aditional modules.
