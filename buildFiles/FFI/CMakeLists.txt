cmake_minimum_required(VERSION 3.4.1)
project(FFI C ASM)

if (NOT DEFINED CMAKE_ANDROID_ARCH_ABI)
    message(FATAL_ERROR "Build must be a crosscompile for Android!")
endif()

set(archSpecificSources)
if (${CMAKE_ANDROID_ARCH_ABI} STREQUAL "arm64-v8a")
    add_definitions(-DABI_64_BIT)
    set(ffiArchDirectory aarch64)
elseif (${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86")
    set(archSpecificSources source/src/x86/win32.S)
    set(ffiArchDirectory x86)
elseif (${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86_64")
    add_definitions(-D__x86_64__ -DABI_64_BIT)
    set(archSpecificSources source/src/x86/ffi64.c source/src/x86/unix64.S)
    set(ffiArchDirectory x86)
elseif (${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi-v7a" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi-v6" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi")
    set(archSpecificSources source/src/arm/trampoline.S)
    set(ffiArchDirectory arm)
else()
    message(FATAL_ERROR "Unknown ANDROID_ARCH_ABI: ${CMAKE_ANDROID_ARCH_ABI}")
endif()
add_definitions(-DHAVE_LONG_DOUBLE=1)

add_library(ffi SHARED
        source/src/${ffiArchDirectory}/ffi.c source/src/${ffiArchDirectory}/ffitarget.h
        source/src/${ffiArchDirectory}/sysv.S source/src/closures.c source/src/debug.c
        source/src/java_raw_api.c source/src/prep_cif.c source/src/types.c source/include/ffi.h
        source/include/ffi_common.h source/include/fficonfig.h ${archSpecificSources})
target_include_directories(ffi
        PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/include>)
target_include_directories(ffi
        PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/src/${ffiArchDirectory}>)
