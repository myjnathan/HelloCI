cmake_minimum_required(VERSION 3.10)
project(HelloCI VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

add_executable(hello_ci 
    src/main.cpp
    src/calculator.cpp
)

enable_testing()
add_test(NAME basic_test COMMAND ${CMAKE_CURRENT_BINARY_DIR}/hello_ci)