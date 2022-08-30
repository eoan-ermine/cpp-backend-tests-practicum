cd sprint1/problems/restaurant_multi_threaded/solution
mkdir build
cd build
conan install ..
cmake -D CMAKE_CXX_COMPILER=/usr/bin/g++-10 ..
cmake --build .