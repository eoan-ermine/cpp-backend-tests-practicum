cd sprint1/problems/async_server/solution
mkdir build
cd build
conan install ..
cmake -D CMAKE_CXX_COMPILER=/usr/bin/g++-10 ..
cmake --build .