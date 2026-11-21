cmake_minimum_required(VERSION 3.21)
project(MEGAWinRTLinkProbe LANGUAGES CXX)
if(NOT WIN32 OR NOT MSVC OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
    message(FATAL_ERROR "This linker probe requires the real Windows x64 MSVC toolchain")
endif()
add_executable(MEGAWinRTLinkProbe probe.cpp)
target_compile_features(MEGAWinRTLinkProbe PRIVATE cxx_std_17)
# Official Windows SDK umbrella import library for C++/WinRT. Do not
# substitute runtime DLLs, ship WindowsApp.lib, or disable real APIs.
target_link_libraries(MEGAWinRTLinkProbe PRIVATE WindowsApp)
