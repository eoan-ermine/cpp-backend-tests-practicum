#include "my_logger.h"

#include <string_view>
#include <thread>
#include <filesystem>
#include <cassert>
#include <sstream>
#include <string>

using namespace std::literals;

std::string TimePointToString(const std::chrono::system_clock::time_point& time_point) const {
    const auto t_c = std::chrono::system_clock::to_time_t(time_point);
    std::ostringstream tmp_str;
    tmp_str << std::put_time(std::localtime(&t_c), "%Y_%m_%d");
    return tmp_str.str();
}

void CompareFiles(const std::filesystem::path& file_path, const std::filesystem::path& ref_file_path) {
    assert(file_path == ref_file_path);
}

int main() {
    const std::filesystem::path logs_path("/var/log");
    const std::filesystem::path reference_path = std::filesystem::current_path / std::filesystem::path("../../../../cpp-backend-tests-practicum/tests/cpp/test_s02_logger/reference");

    std::filesystem::directory_iterator logs_dir(logs_path);
    std::filesystem::directory_iterator reference_dir(reference_path);

    std::chrono::system_clock::time_point time_point{1000000s};
    std::filesystem::path file_path("sample_log_"s + TimePointToString(time_point) +".log"s);

    Logger::GetInstance().SetTimestamp(time_point);
    LOG("Hello "sv, "world "s, 123);
    LOG(1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 
        1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 
        1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0);

    
    
    СompareFiles(logs_path / file_path, reference_path / file_path);
    
    Logger::GetInstance().SetTimestamp(std::chrono::system_clock::time_point{10000000s});
    LOG("Brilliant logger.", " ", "I Love it");

    static const int attempts = 100000;
    for(int i = 0; i < attempts; ++i) {
        std::chrono::system_clock::time_point ts(std::chrono::seconds(10000000 + i * 100));
        Logger::GetInstance().SetTimestamp(ts);

        LOG("Logging attempt ", i, ". ", "I Love it");
    }
}
