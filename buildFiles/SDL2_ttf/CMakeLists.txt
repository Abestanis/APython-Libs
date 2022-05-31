add_subdirectory(source/external/freetype-2.9.1)
target_include_directories(freetype INTERFACE
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/external/freetype-2.9.1/include>)
file(WRITE ${CMAKE_BINARY_DIR}/cmake/FindFreetype.cmake "
if(NOT DEFINED freetype_FOUND)
    set(freetype_FOUND True)
    set(freetype_LIBRARY freetype)
    set(freetype_INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/source/external/freetype-2.9.1/include)
endif()
")
add_subdirectory(source)
target_include_directories(SDL2_ttf INTERFACE $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source>)
add_library(Freetype::Freetype ALIAS freetype)
