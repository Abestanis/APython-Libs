set(DYNAMIC_GLES_3 ON CACHE BOOL "Enable run-time linking to GLES 3" FORCE)
add_subdirectory(source)
target_include_directories(SDL_gpu_shared
        INTERFACE $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/include>)
