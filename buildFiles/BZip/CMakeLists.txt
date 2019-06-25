cmake_minimum_required(VERSION 3.4.1)
project(BZip C)

add_library(bzip SHARED
        source/blocksort.c source/bzlib.c source/bzlib.h source/bzlib_private.h
        source/compress.c source/crctable.c source/decompress.c
        source/huffman.c source/randtable.c)
target_include_directories(bzip INTERFACE $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source>)
