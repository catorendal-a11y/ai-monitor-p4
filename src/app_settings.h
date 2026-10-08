#pragma once
// AI Monitor P4 - device settings (NVS-backed, owned by the UI task).
// Brightness persistence lives in display.cpp (same NVS namespace); this
// module holds the remaining on-device settings.

#include <cstdint>

namespace app_settings {

constexpr uint8_t normalize_dim_minutes(uint8_t minutes) {
  return minutes == 0 || minutes == 1 || minutes == 5 || minutes == 10 ? minutes : 5;
}

// Idle dim timeout in minutes (0 = never dim). Persisted.
uint8_t dim_minutes();
void set_dim_minutes(uint8_t minutes);

constexpr uint8_t normalize_warning_percent(uint8_t value) {
  return value >= 5 && value <= 50 ? value : 25;
}
uint8_t warning_percent();
void set_warning_percent(uint8_t value);
enum class SaveStatus : uint8_t { idle, saved, failed };
void report_save(bool success);
SaveStatus save_status();
uint32_t save_revision();
uint8_t warning_override_for(const char* provider, const char* title, uint32_t windowMinutes);
uint8_t warning_for(const char* provider, const char* title, uint32_t windowMinutes);
// Zero removes the override and restores the global default.
void set_warning_for(const char* provider, const char* title, uint32_t windowMinutes, uint8_t percent);

struct NightSettings {
  bool enabled = false;
  uint16_t start = 22 * 60, end = 7 * 60;
  uint8_t percent = 20;
};
inline NightSettings normalize_night(NightSettings value) {
  if (value.start >= 1440) value.start = 22 * 60;
  if (value.end >= 1440) value.end = 7 * 60;
  if (value.percent < 5 || value.percent > 50) value.percent = 20;
  return value;
}
NightSettings night();
void set_night(NightSettings value);
constexpr uint16_t adjust_night_time(uint16_t value, bool hours, int direction) {
  return static_cast<uint16_t>((static_cast<int>(value) + 1440 + direction * (hours ? 60 : 1)) % 1440);
}

}  // namespace app_settings
