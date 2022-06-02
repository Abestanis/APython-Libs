cmake_minimum_required(VERSION 3.5.0)

# TODO: Recheck excluded files
# TODO: Look at grpmodule.c
# Links for libraries to download:
# - http://www.gnu.org.ua/software/gdbm/
# - https://de.wikipedia.org/wiki/Lempel-Ziv-Markow-Algorithmus
# - https://www.sqlite.org/download.html

set(PYTHON_SHORT_VERSION 2.7)
project(Python${PYTHON_SHORT_VERSION} C)

if (NOT DEFINED CMAKE_ANDROID_ARCH_ABI)
    message(FATAL_ERROR "Build must be a crosscompile for Android!")
endif()

if (${CMAKE_ANDROID_ARCH_ABI} STREQUAL "arm64-v8a" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "mips64" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86_64")
    add_definitions(-DABI_64_BIT -DCONFIG_64)
else()
    add_definitions(-UABI_64_BIT -DCONFIG_32)
endif()
if (${CMAKE_ANDROID_ARCH_ABI} STREQUAL "arm64-v8a" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi-v7a" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi-v6" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "mips" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "mips64")
    add_definitions(-DANSI) # TODO: Check if this is necessary
endif()
if (${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86_64")
    add_definitions(-DASM) # TODO: Check if this is necessary
endif()
if (${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86")
    add_definitions(-UCONFIG_64 -DPPRO)
endif()

add_library(python${PYTHON_SHORT_VERSION} SHARED)
find_library(z-lib z)
set(pythonPatch-lib -Wl,--whole-archive pythonPatch -Wl,--no-whole-archive)

add_definitions(-DPLATFORM="android" -DVERSION="${PYTHON_SHORT_VERSION}" -DHAVE_EXPAT_CONFIG_H
        -DSOABI="apython-${CMAKE_ANDROID_ARCH_ABI}" -DEXTRA_FUNCTIONALITY -DHAVE_UINT128_T -DNDEBUG)

# General source files
file(GLOB SOURCE_FILES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
        source/Include/*.h
        source/Modules/*.[ch]
        source/Modules/_ctypes/*.[ch]
        source/Modules/_decimal/*.[ch]
        source/Modules/_decimal/libmpdec/*.[ch]
        source/Modules/_io/*.[ch]
        source/Modules/_multiprocessing/*.[ch]
        source/Modules/_sqlite/*.[ch]
        source/Modules/cjkcodecs/*.[ch]
        source/Modules/clinic/*.[ch]
        source/Modules/expat/*.[ch]
        source/Modules/zlib/*.[ch]
        source/Objects/*.[ch]
        source/Objects/stringlib/.[ch]
        source/Parser/*.[ch]
        source/Python/*.[ch])

# All modules that are not supported on Android
set(excludedModules
        source/Modules/almodule.c
        source/Modules/bsddbmodule.c
        source/Modules/cdmodule.c
        source/Modules/clmodule.c
        source/Modules/dbmmodule.c
        source/Modules/expat/xmltok_impl.c
        source/Modules/expat/xmltok_ns.c
        source/Modules/flmodule.c
        source/Modules/fmmodule.c
        source/Modules/fpectlmodule.c
        source/Modules/gdbmmodule.c
        source/Modules/getaddrinfo.c
        source/Modules/getnameinfo.c
        source/Modules/glmodule.c
        source/Modules/grpmodule.c
        source/Modules/imgfile.c
        source/Modules/nismodule.c
        source/Modules/overlapped.c
        source/Modules/sgimodule.c
        source/Modules/spwdmodule.c
        source/Modules/sunaudiodev.c
        source/Modules/svmodule.c
        source/Modules/_bsddb.c
        source/Modules/_ctypes/darwin/dlfcn_simple.c
        source/Modules/_dbmmodule.c
        source/Modules/_gdbmmodule.c
        source/Modules/_lzmamodule.c
        source/Modules/_multiprocessing/pipe_connection.c
        source/Modules/_multiprocessing/win32_functions.c
        source/Modules/_scproxy.c
        source/Modules/_sqlite/cache.c
        source/Modules/_sqlite/connection.c
        source/Modules/_sqlite/cursor.c
        source/Modules/_sqlite/microprotocols.c
        source/Modules/_sqlite/module.c
        source/Modules/_sqlite/prepare_protocol.c
        source/Modules/_sqlite/row.c
        source/Modules/_sqlite/statement.c
        source/Modules/_sqlite/util.c
        source/Modules/_winapi.c
        source/Parser/intrcheck.c
        source/Parser/parsetok_pgen.c
        source/Parser/tokenizer_pgen.c
        source/Python/dynload_aix.c
        source/Python/dynload_atheos.c
        source/Python/dynload_beos.c
        source/Python/dynload_dl.c
        source/Python/dynload_hpux.c
        source/Python/dynload_next.c
        source/Python/dynload_os2.c
        source/Python/dynload_stub.c
        source/Python/dynload_win.c
        source/Python/getcwd.c
        source/Python/mactoolboxglue.c
        source/Python/sigcheck.c)

# Test, example or template source files and source files defining main
set(otherExcluded
        source/Modules/_ctypes/_ctypes_test.c
        source/Modules/_freeze_importlib.c
        source/Modules/_testbuffer.c
        source/Modules/_testcapimodule.c
        source/Modules/_testembed.c
        source/Modules/_testimportmultiple.c
        source/Modules/fpetestmodule.c
        source/Modules/xxlimited.c
        source/Modules/xxmodule.c
        source/Modules/xxsubtype.c
        source/Modules/zlib/example.c
        source/Modules/zlib/minigzip.c
        source/Modules/_hashopenssl.c
        source/Modules/tkappinit.c
        source/Parser/pgenmain.c)

list(REMOVE_ITEM SOURCE_FILES ${excludedModules})
list(REMOVE_ITEM SOURCE_FILES ${otherExcluded})

# Separate Modules #
unset(moduleSources)
unset(additionalModules)
unset(additionalModuleDependencies)
function(addModule name)
    cmake_parse_arguments(ARG "" "" "DEPS;SOURCES" ${ARGN})
    add_library(modulePython${PYTHON_SHORT_VERSION}_${name} SHARED ${ARG_SOURCES})
    set_target_properties(modulePython${PYTHON_SHORT_VERSION}_${name} PROPERTIES
            PREFIX "" OUTPUT_NAME ${name}
            LIBRARY_OUTPUT_DIRECTORY
                ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/python${PYTHON_SHORT_VERSION}Modules)
    target_link_libraries(modulePython${PYTHON_SHORT_VERSION}_${name}
            python${PYTHON_SHORT_VERSION} ${pythonPatch-lib} ${ARG_DEPS})
    list(APPEND moduleSources ${ARG_SOURCES})
    set(moduleSources ${moduleSources} PARENT_SCOPE)
    list(APPEND additionalModules modulePython${PYTHON_SHORT_VERSION}_${name})
    set(additionalModules ${additionalModules} PARENT_SCOPE)
    list(APPEND additionalModuleDependencies ${ARG_DEPS})
    set(additionalModuleDependencies ${additionalModuleDependencies} PARENT_SCOPE)
endfunction()

# _ssl
addModule(_ssl DEPS ssl SOURCES source/Modules/_ssl.c)

# _hashlib
addModule(_hashlib DEPS crypto SOURCES source/Modules/_hashlib.c)

# _bz2module or bz2module
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/bz2module.c)
    addModule(bz2module DEPS bzip SOURCES source/Modules/bz2module.c)
else()
    addModule(_bz2module DEPS bzip SOURCES source/Modules/_bz2module.c)
endif()

# _tkinter
addModule(_tkinter DEPS tk tcl SOURCES source/Modules/_tkinter.c)

# crypt or _crypt
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/cryptmodule.c)
    addModule(crypt DEPS crypto SOURCES source/Modules/cryptmodule.c)
    target_compile_definitions(modulePython${PYTHON_SHORT_VERSION}_crypt PRIVATE -Dcrypt=DES_crypt)
else()
    addModule(_crypt DEPS crypto SOURCES source/Modules/_cryptmodule.c)
    target_compile_definitions(modulePython${PYTHON_SHORT_VERSION}__crypt PRIVATE -Dcrypt=DES_crypt)
endif()

# _curses
addModule(_curses DEPS ncurses SOURCES source/Modules/_cursesmodule.c)

# _curses_panel
addModule(_curses_panel DEPS ncurses SOURCES source/Modules/_curses_panel.c)

# readline
addModule(readline DEPS readline SOURCES source/Modules/readline.c)

# _ctypes
addModule(_ctypes DEPS ffi SOURCES
        source/Modules/_ctypes/cfield.c source/Modules/_ctypes/malloc_closure.c
        source/Modules/_ctypes/_ctypes.c source/Modules/_ctypes/stgdict.c
        source/Modules/_ctypes/ctypes_dlfcn.h source/Modules/_ctypes/callbacks.c
        source/Modules/_ctypes/callproc.c source/Modules/_ctypes/ctypes.h)

# Excluded files because they are in their own separate module
if (${COMPILE_WITH_ADDITIONAL_PYTHON_MODULES})
    target_link_libraries(python${PYTHON_SHORT_VERSION} ${additionalModuleDependencies})
    add_definitions(-Dcrypt=DES_crypt -DCOMPILE_WITH_ADDITIONAL_PYTHON_MODULES)
else()
    list(REMOVE_ITEM SOURCE_FILES ${moduleSources})
endif()

target_sources(python${PYTHON_SHORT_VERSION} PRIVATE ${SOURCE_FILES})

target_include_directories(python${PYTHON_SHORT_VERSION}
        PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Include>
        PRIVATE
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/_io>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/expat>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/cjkcodecs>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/_decimal>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/_decimal/libmpdec>)

target_link_libraries(python${PYTHON_SHORT_VERSION} ${pythonPatch-lib} ${z-lib})
