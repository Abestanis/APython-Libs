# APython-Libs
This repository hosts all the library files and their generating code for the [APython Project](https://github.com/Abestanis/APython).

The hosted libraries can be accessed with the information provided by the generated index.json which is available at http://abestanis.github.io/APython-Libs/index.json.

## Usage

The build.py script takes care of downloading and patching the source code, calling the [ndk](https://developer.android.com/tools/sdk/ndk/index.html) and generating the index.json file.
For a list of all available options type ```build.py -h``` or ```build.py --help```.

The script will also download and compile the source code from some additional libraries to allow the generation of some python modules which depend on these libraries (e.g. _ctypes module depends on ffi).

Currently these additional libraries are downloaded:
* SDL2 (from https://www.libsdl.org/release/SDL2-2.0.7.zip) for the libraries SDL2_gpu, SDL2_ttf, sdl2X11Emulation
* SDL2_gpu (from https://github.com/grimfang4/sdl-gpu) for the library sdl2X11Emulation
* SDL2_ttf (from https://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-2.0.15.tar.gz) for the library sdl2X11Emulation
* bzip (from https://downloads.sourceforge.net/project/bzip2/bzip2-1.0.6.tar.gz) for the Python modules bz2, _bz2
* crypto (from https://github.com/janbar/openssl-cmake) for the Python modules _hashlib, crypt, _crypt and for the library ssl
* ffi (from ftp://sourceware.org/pub/libffi/libffi-3.2.1.tar.gz) for the Python module _ctypes
* ncurses (from ftp://ftp.gnu.org/gnu/ncurses/ncurses-6.0.tar.gz) for the Python modules _curses, _curses_panel
* pixman (from https://www.cairographics.org/releases/pixman-0.34.0.tar.gz) for the library sdl2X11Emulation
* readline (from ftp://ftp.cwru.edu/pub/bash/readline-7.0.tar.gz) for the Python module readline
* sdl2X11Emulation (from https://github.com/Abestanis/SDL2X11Emulation) for the library tk
* ssl (from https://github.com/janbar/openssl-cmake) for the Python module _ssl
* tcl (from https://downloads.sourceforge.net/project/tcl/Tcl/8.6.4/tcl8.6.4-src.tar.gz) for the Python module _tkinter and for the library tk
* tk (from https://downloads.sourceforge.net/project/tcl/Tcl/8.6.4/tk8.6.4-src.tar.gz) for the Python module _tkinter


The generated lib-files and the json file will be used by the [Python Host App](https://github.com/Abestanis/APython) to download Python versions and the additional modules.
