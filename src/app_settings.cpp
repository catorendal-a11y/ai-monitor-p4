// AI Monitor P4 - device settings implementation (NVS, UI-task only).

#include "app_settings.h"

#include <Arduino.h>
#include <Preferences.h>
#include <cstring>
#include <cstdio>
#include "ai_monitor/ai_monitor.h"

namespace app_settings {

static const char* NVS_NAMESPACE = "aimon";
static const char* KEY_DIM_MIN = "dim_min";
static uint8_t s_dimMinutes = 5;  // default: dim after 5 idle minutes
static bool s_loaded = false;
static uint8_t s_warningPercent = 25;
static NightSettings s_night;
static uint8_t s_savedDim = 5, s_savedWarning = 25;
static NightSettings s_savedNight;
static Appearance s_appearance, s_savedAppearance;
struct WarningRule {
  char provider[16] = {}, title[36] = {};
  uint32_t window = 0;
  uint8_t percent = 0;
};
static WarningRule s_rules[24], s_savedRules[24];
static SaveStatus s_saveStatus = SaveStatus::idle;
static uint32_t s_saveRevision = 0;
void report_save(bool success) { s_saveStatus = success ? SaveStatus::saved : SaveStatus::failed; ++s_saveRevision; }
SaveStatus save_status() { return s_saveStatus; }
uint32_t save_revision() { return s_saveRevision; }
static void night_bytes(const NightSettings& value, uint8_t (&bytes)[6]) {
  bytes[0] = value.enabled; bytes[1] = value.start & 255; bytes[2] = value.start >> 8;
  bytes[3] = value.end & 255; bytes[4] = value.end >> 8; bytes[5] = value.percent;
}

static void ensure_loaded() {
  if (s_loaded) return;
  Preferences prefs;
  if (prefs.begin(NVS_NAMESPACE, true)) {
    s_dimMinutes = normalize_dim_minutes(prefs.getUChar(KEY_DIM_MIN, 5));
    s_warningPercent = normalize_warning_percent(prefs.getUChar("warn_pct", 25));
    uint8_t look[2] = {};
    if (prefs.getBytesLength("appear_v1") == sizeof(look) && prefs.getBytes("appear_v1", look, sizeof(look)) == sizeof(look))
      s_appearance = normalize_appearance({static_cast<Companion>(look[0]), static_cast<Theme>(look[1])});
    s_night = normalize_night({prefs.getBool("night_on", false), prefs.getUShort("night_start", 1320),
                              prefs.getUShort("night_end", 420), prefs.getUChar("night_pct", 20)});
    uint8_t bytes[6] = {};
    if (prefs.getBytesLength("night_v2") == sizeof(bytes) && prefs.getBytes("night_v2", bytes, sizeof(bytes)) == sizeof(bytes))
      s_night = normalize_night({bytes[0] != 0, static_cast<uint16_t>(bytes[1] | bytes[2] << 8),
                                static_cast<uint16_t>(bytes[3] | bytes[4] << 8), bytes[5]});
    if (prefs.getBytesLength("warn_rules") == sizeof(s_rules)) {
      prefs.getBytes("warn_rules", s_rules, sizeof(s_rules));
      for (auto& rule : s_rules) {
        rule.provider[15] = rule.title[35] = '\0';
        if (!aim::provider_style(rule.provider) || rule.percent < 5 || rule.percent > 50) rule = WarningRule{};
      }
    }
    prefs.end();
  }
  s_loaded = true;
  s_savedDim = s_dimMinutes; s_savedWarning = s_warningPercent; s_savedNight = s_night;
  s_savedAppearance = s_appearance;
  memcpy(s_savedRules, s_rules, sizeof(s_rules));
}

uint8_t dim_minutes() {
  ensure_loaded();
  return s_dimMinutes;
}

Appearance appearance() { ensure_loaded(); return s_appearance; }
void set_appearance(Appearance value) {
  ensure_loaded(); value = normalize_appearance(value); s_appearance = value;
  if (value.companion == s_savedAppearance.companion && value.theme == s_savedAppearance.theme) { report_save(true); return; }
  const uint8_t bytes[] = {static_cast<uint8_t>(value.companion), static_cast<uint8_t>(value.theme)};
  Preferences prefs; bool saved = false;
  if (prefs.begin(NVS_NAMESPACE, false)) { saved = prefs.putBytes("appear_v1", bytes, sizeof(bytes)) == sizeof(bytes); prefs.end(); }
  if (saved) s_savedAppearance = value;
  report_save(saved);
}

void set_dim_minutes(uint8_t minutes) {
  ensure_loaded();
  minutes = normalize_dim_minutes(minutes);
  s_dimMinutes = minutes;
  if (minutes == s_savedDim) { report_save(true); return; }
  Preferences prefs;
  bool saved = false;
  if (prefs.begin(NVS_NAMESPACE, false)) { saved = prefs.putUChar(KEY_DIM_MIN, minutes) == sizeof(minutes); prefs.end(); }
  if (saved) s_savedDim = minutes;
  report_save(saved);
}

uint8_t warning_percent() {
  ensure_loaded();
  return s_warningPercent;
}

void set_warning_percent(uint8_t value) {
  ensure_loaded();
  value = normalize_warning_percent(value);
  s_warningPercent = value;
  if (value == s_savedWarning) { report_save(true); return; }
  Preferences prefs;
  bool saved = false;
  if (prefs.begin(NVS_NAMESPACE, false)) { saved = prefs.putUChar("warn_pct", value) == sizeof(value); prefs.end(); }
  if (saved) s_savedWarning = value;
  report_save(saved);
}

NightSettings night() { ensure_loaded(); return s_night; }
void set_night(NightSettings value) {
  ensure_loaded(); value = normalize_night(value);
  s_night = value;
  uint8_t bytes[6], previous[6]; night_bytes(value, bytes); night_bytes(s_savedNight, previous);
  if (memcmp(bytes, previous, sizeof(bytes)) == 0) { report_save(true); return; }
  Preferences prefs;
  bool saved = false;
  if (prefs.begin(NVS_NAMESPACE, false)) {
    saved = prefs.putBytes("night_v2", bytes, sizeof(bytes)) == sizeof(bytes); prefs.end();
  }
  if (saved) s_savedNight = value;
  report_save(saved);
}

uint8_t warning_override_for(const char* provider, const char* title, uint32_t windowMinutes) {
  ensure_loaded();
  for (const auto& rule : s_rules)
    if (rule.percent && rule.window == windowMinutes && strcmp(rule.provider, provider) == 0 && strcmp(rule.title, title) == 0) return rule.percent;
  return 0;
}
uint8_t warning_for(const char* provider, const char* title, uint32_t windowMinutes) {
  const uint8_t value = warning_override_for(provider, title, windowMinutes);
  return value ? value : warning_percent();
}
void set_warning_for(const char* provider, const char* title, uint32_t windowMinutes, uint8_t percent) {
  ensure_loaded();
  if (!provider || !title || !aim::provider_style(provider) || strlen(title) >= 36 || (percent && (percent < 5 || percent > 50))) {
    report_save(false); return;
  }
  WarningRule* target = nullptr;
  for (auto& rule : s_rules)
    if (rule.percent && rule.window == windowMinutes && strcmp(rule.provider, provider) == 0 && strcmp(rule.title, title) == 0) { target = &rule; break; }
  if (!target && percent) for (auto& rule : s_rules) if (!rule.percent) { target = &rule; break; }
  if (!target && percent) { report_save(false); return; }
  if (target) {
    *target = WarningRule{};
    if (percent) {
      snprintf(target->provider, sizeof(target->provider), "%s", provider);
      snprintf(target->title, sizeof(target->title), "%s", title);
      target->window = windowMinutes; target->percent = percent;
    }
  }
  if (memcmp(s_rules, s_savedRules, sizeof(s_rules)) == 0) { report_save(true); return; }
  Preferences prefs;
  bool saved = false;
  if (prefs.begin(NVS_NAMESPACE, false)) { saved = prefs.putBytes("warn_rules", s_rules, sizeof(s_rules)) == sizeof(s_rules); prefs.end(); }
  if (saved) memcpy(s_savedRules, s_rules, sizeof(s_rules));
  report_save(saved);
}

}  // namespace app_settings
