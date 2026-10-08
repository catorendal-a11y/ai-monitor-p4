#include "../src/app_settings.cpp"
#include <cstdlib>
#include <iostream>

static unsigned failures = 0;
#define CHECK(value) do { if (!(value)) { ++failures; std::cerr << __LINE__ << ": " #value "\n"; } } while (false)

int main() {
  using namespace app_settings;
  Preferences legacy;
  legacy.putBool("night_on", true); legacy.putUShort("night_start", 1200);
  legacy.putUShort("night_end", 360); legacy.putUChar("night_pct", 15);
  CHECK(dim_minutes() == 5 && warning_percent() == 25);
  CHECK(night().enabled && night().start == 1200 && night().end == 360 && night().percent == 15);
  fake_nvs::fail_open = true;
  set_dim_minutes(1); CHECK(save_status() == SaveStatus::failed);
  CHECK(dim_minutes() == 1);  // temporary setting remains usable
  fake_nvs::fail_open = false;
  set_dim_minutes(1); CHECK(save_status() == SaveStatus::saved);
  CHECK(fake_nvs::values["dim_min"][0] == 1);
  const auto writes = fake_nvs::writes;
  set_dim_minutes(1); CHECK(fake_nvs::writes == writes);
  fake_nvs::fail_write = true;
  set_warning_percent(30); CHECK(save_status() == SaveStatus::failed);
  fake_nvs::fail_write = false;
  set_warning_percent(30); CHECK(save_status() == SaveStatus::saved);
  set_warning_for("codex", "Session", 300, 10);
  CHECK(warning_for("codex", "Session", 300) == 10);
  CHECK(warning_for("zcode", "Session", 300) == 30);
  CHECK(warning_for("codex", "Session", 10080) == 30);
  CHECK(warning_for("codex", "Week", 10080) == 30);
  const auto ruleWrites = fake_nvs::writes;
  set_warning_for("codex", "Session", 300, 10);
  CHECK(fake_nvs::writes == ruleWrites);
  fake_nvs::fail_write = true;
  set_warning_for("codex", "Week", 10080, 40); CHECK(save_status() == SaveStatus::failed);
  fake_nvs::fail_write = false;
  set_warning_for("codex", "Week", 10080, 40); CHECK(save_status() == SaveStatus::saved);
  fake_nvs::fail_write = true;
  set_night({true, 1260, 390, 10}); CHECK(save_status() == SaveStatus::failed);
  CHECK(fake_nvs::values["night_v2"].empty());
  fake_nvs::fail_write = false;
  set_night({true, 1260, 390, 10}); CHECK(save_status() == SaveStatus::saved);
  CHECK(fake_nvs::values["night_v2"].size() == 6);
  // Reload persisted bytes as a reboot would, independently of the active values.
  s_loaded = false; s_rules[0] = WarningRule{}; s_dimMinutes = 5; s_warningPercent = 25; s_night = NightSettings{};
  CHECK(dim_minutes() == 1 && warning_percent() == 30);
  CHECK(warning_for("codex", "Session", 300) == 10);
  CHECK(warning_for("codex", "Week", 10080) == 40);
  CHECK(night().enabled && night().start == 1260 && night().end == 390 && night().percent == 10);
  set_warning_for("codex", "Session", 300, 0);
  CHECK(warning_for("codex", "Session", 300) == 30);
  set_warning_for("unknown", "Session", 300, 10); CHECK(save_status() == SaveStatus::failed);
  set_warning_for("codex", "Session", 300, 51); CHECK(save_status() == SaveStatus::failed);
  if (failures) return EXIT_FAILURE;
  std::cout << "NVS persistence, failure/retry, window identity and migration checks passed\n";
}
