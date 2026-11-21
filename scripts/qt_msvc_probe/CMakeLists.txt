cmake_minimum_required(VERSION 3.21)
project(MEGAQtMSVCPreflight LANGUAGES CXX)

# Isolated real C++ compilation against the SAME Qt and MSVC toolchain
# used by the MEGAsync target; no vcpkg or upstream build required.
if(NOT MSVC)
    message(FATAL_ERROR "MEGA Qt/MSVC preflight requires MSVC")
endif()
if(NOT DEFINED MEGA_COMPAT_MODE OR
   NOT MEGA_COMPAT_MODE MATCHES "^(baseline|stl4043)$")
    message(FATAL_ERROR "MEGA_COMPAT_MODE must be baseline or stl4043")
endif()

find_package(Qt5 5.15 COMPONENTS Core REQUIRED)
add_executable(MEGAQtMSVCPreflight probe.cpp)
target_link_libraries(MEGAQtMSVCPreflight PRIVATE Qt5::Core)
target_compile_features(MEGAQtMSVCPreflight PRIVATE cxx_std_17)
target_compile_options(MEGAQtMSVCPreflight PRIVATE /WX)

if(MEGA_COMPAT_MODE STREQUAL "stl4043")
    # Do not turn off /WX or suppress C4996 as a whole.
    target_compile_definitions(MEGAQtMSVCPreflight PRIVATE
        _SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING)
endif()

# Record the actual identities from CMake, never guessed from folder names.
file(WRITE "${CMAKE_BINARY_DIR}/probe-environment.txt"
    "compiler=${CMAKE_CXX_COMPILER}\n"
    "compiler_version=${CMAKE_CXX_COMPILER_VERSION}\n"
    "qt_version=${Qt5Core_VERSION_STRING}\n"
    "qt_core_dir=${Qt5Core_DIR}\n"
    "generator=${CMAKE_GENERATOR}\n"
    "mode=${MEGA_COMPAT_MODE}\n")
