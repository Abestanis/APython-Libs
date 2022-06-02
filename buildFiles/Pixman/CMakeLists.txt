cmake_minimum_required(VERSION 3.4.1)
project(Pixman C ASM)

if (NOT DEFINED CMAKE_ANDROID_ARCH_ABI)
    message(FATAL_ERROR "Build must be a crosscompile for Android!")
endif()

set(archSpecificSources)
if (${CMAKE_ANDROID_ARCH_ABI} STREQUAL "arm64-v8a" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi-v7a" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi-v6" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi")
    add_definitions(-DTARGET_ARCH=__ARM__)
    if (${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi-v7a")
        add_definitions(-DUSE_ARM_NEON=1 -DUSE_ARM_SIMD=1)
        set(archSpecificSources
                source/pixman/pixman-arm-neon-asm-bilinear.S source/pixman/pixman-arm-neon-asm.S
                source/pixman/pixman-arm-neon.c
                source/pixman/pixman-arm-simd-asm-scaled.S source/pixman/pixman-arm-simd-asm.S
                source/pixman/pixman-arm-simd.c)
        foreach(SOURCE ${archSpecificSources})
            set_source_files_properties("${SOURCE}" PROPERTIES COMPILE_FLAGS "-mfpu=neon -fno-integrated-as")
        endforeach()
    endif()
elseif (${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86_64")
    add_definitions(-DTARGET_ARCH=__X86__)
else()
    message(FATAL_ERROR "Unsupportet architecture ${CMAKE_ANDROID_ARCH_ABI}")
endif()
add_definitions(-DHAVE_CONFIG_H -D__ARM__=2 -D__X86__=3)
configure_file(source/config.h ${PROJECT_BINARY_DIR}/include/config.h COPYONLY) # TODO

add_library(pixman SHARED
        source/pixman/pixman-arm-simd-asm.h source/pixman/pixman-matrix.c
        source/pixman/pixman-general.c source/pixman/pixman-timer.c
        source/pixman/pixman-arm-asm.h source/pixman/pixman-private.h
        source/pixman/pixman-mmx.c source/pixman/pixman-arm-common.h
        source/pixman/pixman-region16.c source/pixman/loongson-mmintrin.h
        source/pixman/pixman-radial-gradient.c source/pixman/pixman-combine32.h
        source/pixman/pixman-compiler.h source/pixman/pixman-utils.c
        source/pixman/pixman-combine32.c source/pixman/pixman-edge.c
        source/pixman/pixman-accessor.h source/pixman/pixman.c source/pixman/pixman-glyph.c
        source/pixman/pixman-ppc.c source/pixman/pixman-gradient-walker.c
        source/pixman/pixman-combine-float.c source/pixman/pixman-edge-accessors.c
        source/pixman/pixman-implementation.c source/pixman/pixman-arm.c
        source/pixman/pixman-image.c source/pixman/pixman-access-accessors.c
        source/pixman/pixman-bits-image.c source/pixman/pixman-x86.c
        source/pixman/pixman-solid-fill.c source/pixman/pixman-trap.c
        source/pixman/pixman-fast-path.c source/pixman/pixman-conical-gradient.c
        source/pixman/pixman-version.h source/pixman/pixman-noop.c
        source/pixman/pixman-inlines.h source/pixman/pixman-region32.c
        source/pixman/pixman-mips.c source/pixman/pixman-filter.c
        source/pixman/pixman-arm-neon-asm.h source/pixman/pixman-edge-imp.h
        source/pixman/pixman-access.c source/pixman/pixman.h
        source/pixman/pixman-linear-gradient.c ${archSpecificSources})
target_include_directories(pixman PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/pixman>
        $<BUILD_INTERFACE:${PROJECT_BINARY_DIR}/include>)

if(NOT TARGET cpufeatures)
    include(AndroidNdkModules)
    android_ndk_import_module_cpufeatures()
endif()
target_link_libraries(pixman PUBLIC cpufeatures)
