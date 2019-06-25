cmake_minimum_required(VERSION 3.4.1)
project(Readline C)

add_definitions(-DRL_LIBRARY_VERSION="7.0" -DHAVE_CONFIG_H)

add_library(readline SHARED
        source/android.c source/android.h source/ansi_stdlib.h source/bind.c
        source/callback.c source/chardefs.h source/colors.c source/colors.h
        source/compat.c source/complete.c source/config.h source/display.c
        source/funmap.c source/histexpand.c source/histfile.c source/histlib.h
        source/history.c source/history.h source/histsearch.c source/input.c
        source/isearch.c source/keymaps.c source/keymaps.h source/kill.c
        source/macro.c source/mbutil.c source/misc.c source/nls.c
        source/parens.c source/parse-colors.c source/parse-colors.h source/posixdir.h
        source/posixjmp.h source/posixselect.h source/posixstat.h source/readline.c
        source/readline.h source/rlconf.h source/rldefs.h source/rlmbutil.h
        source/rlprivate.h source/rlshell.h source/rlstdc.h source/rltty.c
        source/rltty.h source/rltypedefs.h source/rlwinsize.h source/savestring.c
        source/search.c source/shell.c source/signals.c source/tcap.h
        source/terminal.c source/text.c source/tilde.c source/tilde.h
        source/undo.c source/util.c source/vi_mode.c source/xfree.c
        source/xmalloc.c source/xmalloc.h)

file(GLOB INCLUDE_FILES ${CMAKE_CURRENT_SOURCE_DIR}/source/*.h)
foreach(INCLUDE_FILE ${INCLUDE_FILES})
    get_filename_component(FILE_NAME ${INCLUDE_FILE} NAME)
    configure_file(
            ${INCLUDE_FILE} ${CMAKE_CURRENT_BINARY_DIR}/include/readline/${FILE_NAME} COPYONLY)
endforeach()

target_include_directories(readline
        PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}/include>
        PRIVATE
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source>)

target_link_libraries(
        readline
        ncurses IPC)
