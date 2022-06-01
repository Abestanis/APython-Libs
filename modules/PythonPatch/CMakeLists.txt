cmake_minimum_required(VERSION 3.4.1)
project(PythonPatch C)

add_library(pythonPatch STATIC redirects.c redirects.h)
set(linkerOptions
        -Wl,--wrap,exit
        -Wl,--wrap,setlocale
        -Wl,--wrap,mbstowcs
        -Wl,--wrap,ttyname
        -Wl,--wrap,fgets)
if(${CMAKE_VERSION} VERSION_LESS 3.13.0)
    set_target_properties(pythonPatch PROPERTIES INTERFACE_LINK_LIBRARIES "${linkerOptions}")
else()
    target_link_options(pythonPatch INTERFACE ${linkerOptions})
endif()
target_include_directories(pythonPatch INTERFACE $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>)
