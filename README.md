# APython-Libs
This repository hosts all the library files and their generating code for the [APython Project](https://github.com/Abestanis/APython).

The hosted libraries can be accessed with the information provided by the generated index.json which is available at http://abestanis.github.io/APython-Libs/index.json.

## Usage

The build.py script takes care of downloading and patching the source code, calling the [ndk](https://developer.android.com/tools/sdk/ndk/index.html) and generating the index.json file.
For a list of all available options type ```build.py -h``` or ```build.py --help```.

The script will also download and compile the source code from some additional libraries to allow the generation of some python modules which depend on these libraries (e.g. the _ssl module depends on openSSL).

Currently these additional libraries are downloaded:
* openSSL (from https://www.openssl.org/source/openssl-1.1.0f.tar.gz) for the Python modules _ssl, _hashlib, crypt, _crypt
* bzip (from http://www.bzip.org/1.0.6/bzip2-1.0.6.tar.gz) for the Python modules bz2, _bz2
* SDL2_gpu (from https://github.com/grimfang4/sdl-gpu) for the library sdl2X11Emulation
* sdl2X11Emulation (from https://github.com/Abestanis/SDL2X11Emulation) for the library tk
* ffi (from ftp://sourceware.org/pub/libffi/libffi-3.2.1.tar.gz) for the Python module _ctypes
* tcl (from http://netix.dl.sourceforge.net/project/tcl/Tcl/8.6.4/tcl8.6.4-src.tar.gz) for the Python module _tkinter and for the library tk
* SDL2 (from https://www.libsdl.org/release/SDL2-2.0.5.tar.gz) for the libraries SDL2_gpu, sdl2X11Emulation, SDL2_ttf
* pixman (from https://www.cairographics.org/releases/pixman-0.34.0.tar.gz) for the library sdl2X11Emulation
* tk (from http://freefr.dl.sourceforge.net/project/tcl/Tcl/8.6.4/tk8.6.4-src.tar.gz) for the Python module _tkinter
* SDL2_ttf (from https://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-2.0.14.tar.gz) for the library sdl2X11Emulation


The generated lib-files and the json file will be used by the [Python Host App](https://github.com/Abestanis/APython) to download Python versions and the additional modules.
