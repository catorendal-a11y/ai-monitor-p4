// Display settings: direct dim choices, brightness presets and touch feedback.
#include "ui_settings.h"
#include <Arduino.h>
#include <lvgl.h>
#include <cstdio>
#include <cstring>
#include "app_settings.h"
#include "config.h"
#include "ui/backlight.h"
#include "ui/idle_dim.h"
#include "ui/theme.h"
#include "ai_monitor/ai_monitor.h"
#include "ui/nova_assets.h"

static lv_obj_t* settingsScreen = nullptr;
static lv_obj_t* dashScreen = nullptr;
static lv_obj_t* settingsReturnScreen = nullptr;
static lv_obj_t* brightnessValue = nullptr;
static lv_obj_t* brightnessSlider = nullptr;
static lv_obj_t *actualBrightnessLabel = nullptr, *saveFeedback = nullptr, *warningTargetLabel = nullptr;
struct AlertTarget { char provider[16] = {}, title[36] = {}; uint32_t window = 0; };
static AlertTarget alertTargets[25];
static uint8_t alertTargetCount = 1, alertTargetIndex = 0;
static uint32_t shownSaveRevision = 0, savedAtMs = 0;
static lv_obj_t* dimButtons[4] = {};
static lv_obj_t* dimLabels[4] = {};
static lv_obj_t* presetButtons[4] = {};
static lv_obj_t* presetLabels[4] = {};
static lv_obj_t* previewButton = nullptr;
static lv_obj_t *alertsButton = nullptr, *alertsOverlay = nullptr, *warningSlider = nullptr, *warningValue = nullptr;
static lv_obj_t *nightButton = nullptr, *nightOverlay = nullptr, *nightToggleLabel = nullptr, *nightValue = nullptr;
static lv_obj_t *nightTimeValues[4] = {}, *nightTimeButtons[8] = {}, *nightSlider = nullptr;
static app_settings::NightSettings nightDraft;
static lv_obj_t *appearanceOverlay = nullptr, *companionPreview = nullptr;
static lv_obj_t *companionButtons[2] = {}, *companionCaptions[2] = {}, *themeButtons[4] = {}, *themeCaptions[4] = {};
static const uint8_t kDimChoices[] = {0, 1, 5, 10};
static const char* kDimNames[] = {"OFF", "1 MIN", "5 MIN", "10 MIN"};
static const uint8_t kBrightnessPresets[] = {25, 50, 75, 100};
static uint8_t lastDimChoice = 255, lastPresetValue = 255;

static void style_button(lv_obj_t* button, bool selected) {
  lv_obj_set_style_bg_color(button, lv_color_hex(selected ? ui_theme::accent : ui_theme::button), 0);
  lv_obj_set_style_bg_opa(button, LV_OPA_COVER, 0);
  lv_obj_set_style_border_color(button, lv_color_hex(selected ? ui_theme::accent : ui_theme::border), 0);
  lv_obj_set_style_border_width(button, selected ? 2 : 1, 0);
  lv_obj_set_style_radius(button, 12, 0);
  lv_obj_set_style_shadow_width(button, 0, 0);
  lv_obj_set_style_pad_all(button, 0, 0);
  lv_obj_set_style_bg_color(button, lv_color_hex(ui_theme::pressed), LV_STATE_PRESSED);
  lv_obj_set_style_border_color(button, lv_color_hex(ui_theme::accent), LV_STATE_PRESSED);
}

static lv_obj_t* make_label(lv_obj_t* parent, lv_coord_t x, lv_coord_t y, lv_coord_t width,
                            const char* text, const lv_font_t* font, uint32_t color, lv_text_align_t align) {
  auto* label = lv_label_create(parent);
  lv_label_set_text(label, text);
  lv_obj_set_pos(label, x, y);
  lv_obj_set_width(label, width);
  lv_label_set_long_mode(label, LV_LABEL_LONG_MODE_CLIP);
  lv_obj_set_style_text_font(label, font, 0);
  lv_obj_set_style_text_color(label, lv_color_hex(color), 0);
  lv_obj_set_style_text_align(label, align, 0);
  return label;
}

static void refresh_brightness();

static void refresh_choices() {
  const uint8_t minutes = app_settings::dim_minutes();
  if (minutes != lastDimChoice) {
    lastDimChoice = minutes;
    for (size_t i = 0; i < 4; ++i) {
      const bool selected = minutes == kDimChoices[i];
      style_button(dimButtons[i], selected);
      lv_obj_set_style_text_color(dimLabels[i], lv_color_hex(selected ? ui_theme::background : ui_theme::text), 0);
    }
  }
  const uint8_t percent = brightness_percent(display_get_brightness());
  if (percent != lastPresetValue) {
    lastPresetValue = percent;
    for (size_t i = 0; i < 4; ++i) {
      const bool selected = percent == kBrightnessPresets[i];
      style_button(presetButtons[i], selected);
      lv_obj_set_style_text_color(presetLabels[i], lv_color_hex(selected ? ui_theme::background : ui_theme::text), 0);
    }
  }
}

static void brightness_slider_cb(lv_event_t* event) {
  const uint8_t percent = static_cast<uint8_t>(lv_slider_get_value(brightnessSlider));
  display_apply_brightness(brightness_raw(percent), lv_event_get_code(event) == LV_EVENT_RELEASED);
  refresh_brightness();
}

static void brightness_preset_cb(lv_event_t* event) {
  const auto index = reinterpret_cast<uintptr_t>(lv_event_get_user_data(event));
  if (index >= 4) return;
  display_apply_brightness(brightness_raw(kBrightnessPresets[index]), true);
  refresh_brightness();
}

static void dim_select_cb(lv_event_t* event) {
  const auto index = reinterpret_cast<uintptr_t>(lv_event_get_user_data(event));
  if (index >= 4) return;
  app_settings::set_dim_minutes(kDimChoices[index]);
  refresh_choices();
}

static void back_cb(lv_event_t*) { ui_settings_hide(); }
static void dim_preview_cb(lv_event_t*) { idle_dim_preview(); }

static lv_obj_t* make_button(lv_obj_t* parent, int x, int y, int width, const char* text,
                            lv_event_cb_t callback, void* data, lv_obj_t** labelOut = nullptr) {
  auto* button = lv_btn_create(parent);
  lv_obj_set_pos(button, x, y);
  lv_obj_set_size(button, width, 48);
  style_button(button, false);
  lv_obj_add_event_cb(button, callback, LV_EVENT_CLICKED, data);
  auto* label = make_label(button, 0, 0, width - 8, text, &lv_font_montserrat_16, ui_theme::text, LV_TEXT_ALIGN_CENTER);
  lv_obj_center(label);
  if (labelOut) *labelOut = label;
  return button;
}

static void refresh_appearance() {
  const auto look = app_settings::appearance();
  for (size_t i = 0; i < 2; ++i) {
    const bool selected = static_cast<uint8_t>(look.companion) == i;
    style_button(companionButtons[i], selected);
    lv_obj_set_style_text_color(companionCaptions[i], lv_color_hex(selected ? ui_theme::background : ui_theme::text), 0);
  }
  for (size_t i = 0; i < 4; ++i) {
    style_button(themeButtons[i], static_cast<uint8_t>(look.theme) == i);
    lv_obj_set_style_bg_color(themeButtons[i], lv_color_hex(ui_theme::palettes[i].button), 0);
    lv_obj_set_style_border_color(themeButtons[i], lv_color_hex(ui_theme::palettes[i].accent), 0);
    lv_obj_set_style_text_color(themeCaptions[i], lv_color_hex(ui_theme::palettes[i].text), 0);
  }
  lv_image_set_src(companionPreview, look.companion == app_settings::Companion::orbit ? &nova_assets::orbit_thumb : &nova_assets::nova_thumb);
}
static void companion_select(lv_event_t* event) {
  auto look = app_settings::appearance();
  look.companion = static_cast<app_settings::Companion>(reinterpret_cast<uintptr_t>(lv_event_get_user_data(event)));
  app_settings::set_appearance(look); refresh_appearance();
}
static void theme_select(lv_event_t* event) {
  auto look = app_settings::appearance();
  look.theme = static_cast<app_settings::Theme>(reinterpret_cast<uintptr_t>(lv_event_get_user_data(event)));
  app_settings::set_appearance(look); ui_theme::apply(look.theme); refresh_appearance();
  lastDimChoice = lastPresetValue = 255; refresh_choices();
}
static void open_appearance(lv_event_t*) { refresh_appearance(); lv_obj_move_foreground(appearanceOverlay); lv_obj_set_hidden(appearanceOverlay, false); }
static void close_appearance(lv_event_t*) { lv_obj_set_hidden(appearanceOverlay, true); }

static void refresh_warning_target();
static void warning_slider_cb(lv_event_t* event) {
  const uint8_t value = static_cast<uint8_t>(lv_slider_get_value(warningSlider));
  char text[96];
  snprintf(text, sizeof(text), "Low quota <= %u %% remaining / Critical <= %u %%", value, value < 10 ? value : 10);
  lv_label_set_text(warningValue, text);
  if (lv_event_get_code(event) == LV_EVENT_RELEASED) {
    const auto& target = alertTargets[alertTargetIndex];
    if (alertTargetIndex == 0) app_settings::set_warning_percent(value);
    else app_settings::set_warning_for(target.provider, target.title, target.window, value);
    refresh_warning_target();
  }
}
static void close_alerts(lv_event_t*) { lv_obj_set_hidden(alertsOverlay, true); }
static void refresh_warning_target() {
  const auto& target = alertTargets[alertTargetIndex];
  const uint8_t percent = alertTargetIndex ? app_settings::warning_for(target.provider, target.title, target.window) : app_settings::warning_percent();
  lv_slider_set_value(warningSlider, percent, LV_ANIM_OFF);
  lv_obj_send_event(warningSlider, LV_EVENT_VALUE_CHANGED, nullptr);
  char text[128];
  if (!alertTargetIndex) snprintf(text, sizeof(text), "GLOBAL DEFAULT");
  else snprintf(text, sizeof(text), "%s / %s / %s", aim::provider_style(target.provider)->label, target.title,
                app_settings::warning_override_for(target.provider, target.title, target.window) ? "CUSTOM" : "INHERITED");
  lv_label_set_text(warningTargetLabel, text);
}
static void change_warning_target(lv_event_t* event) {
  const int direction = reinterpret_cast<intptr_t>(lv_event_get_user_data(event));
  alertTargetIndex = (alertTargetIndex + alertTargetCount + direction) % alertTargetCount;
  refresh_warning_target();
}
static void inherit_warning(lv_event_t*) {
  if (alertTargetIndex) {
    const auto& target = alertTargets[alertTargetIndex];
    app_settings::set_warning_for(target.provider, target.title, target.window, 0);
    refresh_warning_target();
  }
}
static void open_alerts(lv_event_t*) {
  alertTargetCount = 1; alertTargetIndex = 0;
  const auto snapshot = aim::read();
  for (size_t v = 0; v < aim::kMaxViews; ++v) {
    const auto& view = snapshot.views[v];
    if (snapshot.viewsConfigured && v >= snapshot.viewCount) continue;
    if (!view.hasUsage || !aim::provider_style(view.providerKey)) continue;
    for (size_t r = 0; r < view.rowCount && alertTargetCount < 25; ++r) {
      const auto& row = view.rows[r];
      if (!row.valid) continue;
      bool duplicate = false;
      for (size_t i = 1; i < alertTargetCount; ++i)
        duplicate |= alertTargets[i].window == row.windowMinutes && strcmp(alertTargets[i].provider, view.providerKey) == 0 && strcmp(alertTargets[i].title, row.title) == 0;
      if (duplicate) continue;
      auto& target = alertTargets[alertTargetCount++];
      snprintf(target.provider, sizeof(target.provider), "%s", view.providerKey);
      snprintf(target.title, sizeof(target.title), "%s", row.title); target.window = row.windowMinutes;
    }
  }
  refresh_warning_target();
  lv_obj_set_hidden(alertsOverlay, false);
}

static void refresh_night_controls() {
  const auto value = nightDraft;
  lv_label_set_text(nightToggleLabel, value.enabled ? "ON" : "OFF");
  char text[100];
  const uint16_t components[] = {static_cast<uint16_t>(value.start / 60), static_cast<uint16_t>(value.start % 60),
                                 static_cast<uint16_t>(value.end / 60), static_cast<uint16_t>(value.end % 60)};
  for (size_t i = 0; i < 4; ++i) {
    snprintf(text, sizeof(text), "%02u", components[i]);
    if (strcmp(lv_label_get_text(nightTimeValues[i]), text) != 0) lv_label_set_text(nightTimeValues[i], text);
  }
  snprintf(text, sizeof(text), "Night brightness: %u %% / Equal start and end = all day", value.percent);
  lv_label_set_text(nightValue, text);
}
static void night_toggle_cb(lv_event_t*) {
  nightDraft.enabled = !nightDraft.enabled;
  app_settings::set_night(nightDraft); refresh_night_controls();
}
static void night_time_cb(lv_event_t* event) {
  if (lv_event_get_code(event) == LV_EVENT_RELEASED) {
    app_settings::set_night(nightDraft); return;
  }
  const auto choice = reinterpret_cast<uintptr_t>(lv_event_get_user_data(event));
  if (choice >= 8) return;
  const size_t group = choice / 2;
  const int direction = choice % 2 ? 1 : -1;
  auto& value = group < 2 ? nightDraft.start : nightDraft.end;
  value = app_settings::adjust_night_time(value, group % 2 == 0, direction);
  if (lv_event_get_code(event) == LV_EVENT_SHORT_CLICKED) app_settings::set_night(nightDraft);
  refresh_night_controls();
}
static void night_slider_cb(lv_event_t* event) {
  char text[96];
  const uint8_t percent = lv_slider_get_value(nightSlider);
  snprintf(text, sizeof(text), "Night brightness: %u %% / Saved on release", percent);
  lv_label_set_text(nightValue, text);
  if (lv_event_get_code(event) == LV_EVENT_RELEASED) {
    nightDraft.percent = percent;
    app_settings::set_night(nightDraft);
  }
}
static void close_night(lv_event_t*) { lv_obj_set_hidden(nightOverlay, true); }
static void open_night(lv_event_t*) {
  nightDraft = app_settings::night();
  refresh_night_controls();
  lv_slider_set_value(nightSlider, app_settings::night().percent, LV_ANIM_OFF);
  lv_obj_set_hidden(nightOverlay, false);
}

void ui_settings_init() {
  dashScreen = lv_screen_active();
  settingsScreen = lv_obj_create(nullptr);
  lv_obj_set_style_bg_color(settingsScreen, lv_color_hex(ui_theme::background), 0);
  lv_obj_set_style_bg_opa(settingsScreen, LV_OPA_COVER, 0);
  lv_obj_set_style_border_width(settingsScreen, 0, 0);
  lv_obj_set_style_pad_all(settingsScreen, 0, 0);
  lv_obj_set_scrollable(settingsScreen, false);

  auto* header = lv_obj_create(settingsScreen);
  lv_obj_set_size(header, 800, 78);
  lv_obj_set_pos(header, 0, 0);
  lv_obj_set_style_bg_color(header, lv_color_hex(ui_theme::header), 0);
  lv_obj_set_style_border_width(header, 0, 0);
  lv_obj_set_style_radius(header, 0, 0);
  lv_obj_set_style_pad_all(header, 0, 0);
  lv_obj_set_scrollable(header, false);
  make_label(header, 24, 12, 420, "AI MONITOR / DISPLAY", &lv_font_montserrat_14, ui_theme::muted, LV_TEXT_ALIGN_LEFT);
  make_label(header, 24, 34, 500, "Display settings", &lv_font_montserrat_26, ui_theme::text, LV_TEXT_ALIGN_LEFT);
  alertsButton = make_button(header, 608, 16, 168, "ALERTS", open_alerts, nullptr);

  auto* card = lv_obj_create(settingsScreen);
  lv_obj_set_pos(card, 24, 94);
  lv_obj_set_size(card, 752, 314);
  lv_obj_set_style_bg_color(card, lv_color_hex(ui_theme::surface), 0);
  lv_obj_set_style_bg_opa(card, LV_OPA_COVER, 0);
  lv_obj_set_style_border_color(card, lv_color_hex(ui_theme::border), 0);
  lv_obj_set_style_border_width(card, 1, 0);
  lv_obj_set_style_radius(card, 16, 0);
  lv_obj_set_style_pad_all(card, 0, 0);
  lv_obj_set_scrollable(card, false);
  lv_obj_set_clickable(card, false);

  make_label(card, 24, 20, 420, "DAY BRIGHTNESS", &lv_font_montserrat_16, ui_theme::accent, LV_TEXT_ALIGN_LEFT);
  brightnessValue = make_label(card, 600, 12, 128, "", &lv_font_montserrat_30, ui_theme::text, LV_TEXT_ALIGN_RIGHT);
  brightnessSlider = lv_slider_create(card);
  lv_obj_set_pos(brightnessSlider, 24, 64);
  lv_obj_set_size(brightnessSlider, 700, 20);
  lv_slider_set_range(brightnessSlider, 5, 100);
  lv_obj_set_ext_click_area(brightnessSlider, 16);
  lv_obj_set_style_bg_color(brightnessSlider, lv_color_hex(ui_theme::border), LV_PART_MAIN);
  lv_obj_set_style_bg_opa(brightnessSlider, LV_OPA_COVER, LV_PART_MAIN);
  lv_obj_set_style_radius(brightnessSlider, 5, LV_PART_MAIN);
  lv_obj_set_style_bg_color(brightnessSlider, lv_color_hex(ui_theme::accent), LV_PART_INDICATOR);
  lv_obj_set_style_bg_color(brightnessSlider, lv_color_hex(ui_theme::accent), LV_PART_KNOB);
  lv_obj_set_style_radius(brightnessSlider, 12, LV_PART_KNOB);
  lv_obj_add_event_cb(brightnessSlider, brightness_slider_cb, LV_EVENT_VALUE_CHANGED, nullptr);
  lv_obj_add_event_cb(brightnessSlider, brightness_slider_cb, LV_EVENT_RELEASED, nullptr);

  for (size_t i = 0; i < 4; ++i) {
    char text[12];
    snprintf(text, sizeof(text), "%u %%", kBrightnessPresets[i]);
    presetButtons[i] = make_button(card, 24 + i * 130, 104, 118, text, brightness_preset_cb,
                                   reinterpret_cast<void*>(i), &presetLabels[i]);
  }
  actualBrightnessLabel = make_label(card, 552, 112, 176, "", &lv_font_montserrat_14, ui_theme::muted, LV_TEXT_ALIGN_CENTER);
  make_label(card, 24, 174, 400, "DIM AFTER", &lv_font_montserrat_16, ui_theme::accent, LV_TEXT_ALIGN_LEFT);
  for (size_t i = 0; i < 4; ++i) {
    dimButtons[i] = make_button(card, 24 + i * 130, 204, 118, kDimNames[i], dim_select_cb,
                               reinterpret_cast<void*>(i), &dimLabels[i]);
  }
  previewButton = make_button(card, 560, 204, 168, "TEST DIM", dim_preview_cb, nullptr);
  make_label(card, 24, 278, 704, "First touch wakes only. Release before the next tap.",
             &lv_font_montserrat_14, ui_theme::muted, LV_TEXT_ALIGN_LEFT);
  make_button(settingsScreen, 24, 424, 152, "<  BACK", back_cb, nullptr);
  nightButton = make_button(settingsScreen, 200, 424, 176, "NIGHT MODE", open_night, nullptr);
  make_button(settingsScreen, 392, 424, 176, "APPEARANCE", open_appearance, nullptr);
  make_label(settingsScreen, 592, 440, 184, "AI Monitor P4 " FW_VERSION, &lv_font_montserrat_14,
             ui_theme::muted, LV_TEXT_ALIGN_RIGHT);
  lastDimChoice = lastPresetValue = 255;
  refresh_brightness();
  alertsOverlay = lv_obj_create(lv_layer_top());
  lv_obj_set_size(alertsOverlay, 800, 480); lv_obj_set_pos(alertsOverlay, 0, 0);
  lv_obj_set_style_bg_color(alertsOverlay, lv_color_hex(ui_theme::background), 0);
  lv_obj_set_style_bg_opa(alertsOverlay, LV_OPA_80, 0);
  lv_obj_set_style_pad_all(alertsOverlay, 0, 0); lv_obj_set_style_border_width(alertsOverlay, 0, 0);
  lv_obj_set_scrollable(alertsOverlay, false);
  auto* alertCard = lv_obj_create(alertsOverlay);
  lv_obj_set_pos(alertCard, 24, 64); lv_obj_set_size(alertCard, 752, 354);
  lv_obj_set_style_bg_color(alertCard, lv_color_hex(ui_theme::surface), 0);
  lv_obj_set_style_border_color(alertCard, lv_color_hex(ui_theme::border), 0);
  lv_obj_set_style_pad_all(alertCard, 0, 0); lv_obj_set_scrollable(alertCard, false);
  make_label(alertCard, 24, 20, 700, "Quota warning threshold", &lv_font_montserrat_26, ui_theme::text, LV_TEXT_ALIGN_LEFT);
  make_button(alertCard, 24, 72, 96, "< PREV", change_warning_target, reinterpret_cast<void*>(-1));
  make_button(alertCard, 632, 72, 96, "NEXT >", change_warning_target, reinterpret_cast<void*>(1));
  warningTargetLabel = make_label(alertCard, 132, 84, 484, "", &lv_font_montserrat_14, ui_theme::text, LV_TEXT_ALIGN_CENTER);
  warningValue = make_label(alertCard, 24, 142, 700, "", &lv_font_montserrat_16, ui_theme::muted, LV_TEXT_ALIGN_LEFT);
  warningSlider = lv_slider_create(alertCard);
  lv_obj_set_pos(warningSlider, 36, 196); lv_obj_set_size(warningSlider, 680, 20);
  lv_slider_set_range(warningSlider, 5, 50); lv_obj_set_ext_click_area(warningSlider, 16);
  lv_obj_set_style_bg_color(warningSlider, lv_color_hex(ui_theme::accent), LV_PART_INDICATOR);
  lv_obj_set_style_bg_color(warningSlider, lv_color_hex(ui_theme::accent), LV_PART_KNOB);
  lv_obj_add_event_cb(warningSlider, warning_slider_cb, LV_EVENT_VALUE_CHANGED, nullptr);
  lv_obj_add_event_cb(warningSlider, warning_slider_cb, LV_EVENT_RELEASED, nullptr);
  make_label(alertCard, 24, 244, 700, "5-50 %. Release to save. INHERIT restores the global default.", &lv_font_montserrat_14, ui_theme::muted, LV_TEXT_ALIGN_LEFT);
  make_button(alertCard, 24, 278, 176, "INHERIT", inherit_warning, nullptr);
  make_button(alertCard, 552, 278, 176, "DONE", close_alerts, nullptr);
  lv_obj_set_hidden(alertsOverlay, true);
  nightOverlay = lv_obj_create(lv_layer_top());
  lv_obj_set_pos(nightOverlay, 0, 0); lv_obj_set_size(nightOverlay, 800, 480);
  lv_obj_set_style_bg_color(nightOverlay, lv_color_hex(ui_theme::background), 0);
  lv_obj_set_style_bg_opa(nightOverlay, LV_OPA_80, 0);
  lv_obj_set_style_pad_all(nightOverlay, 0, 0); lv_obj_set_style_border_width(nightOverlay, 0, 0);
  lv_obj_set_scrollable(nightOverlay, false);
  auto* nightCard = lv_obj_create(nightOverlay);
  lv_obj_set_pos(nightCard, 24, 64); lv_obj_set_size(nightCard, 752, 354);
  lv_obj_set_style_bg_color(nightCard, lv_color_hex(ui_theme::surface), 0);
  lv_obj_set_style_border_color(nightCard, lv_color_hex(ui_theme::border), 0);
  lv_obj_set_style_pad_all(nightCard, 0, 0); lv_obj_set_scrollable(nightCard, false);
  make_label(nightCard, 24, 20, 520, "Scheduled night brightness", &lv_font_montserrat_26, ui_theme::text, LV_TEXT_ALIGN_LEFT);
  make_button(nightCard, 600, 16, 128, "OFF", night_toggle_cb, nullptr, &nightToggleLabel);
  const char* timeNames[] = {"START / HH", "START / MM", "END / HH", "END / MM"};
  for (size_t i = 0; i < 4; ++i) {
    const int x = 24 + i * 182;
    make_label(nightCard, x, 74, 158, timeNames[i], &lv_font_montserrat_14, ui_theme::muted, LV_TEXT_ALIGN_CENTER);
    nightTimeValues[i] = make_label(nightCard, x, 96, 158, "", &lv_font_montserrat_26, ui_theme::text, LV_TEXT_ALIGN_CENTER);
    for (size_t control = 0; control < 2; ++control) {
      const size_t index = i * 2 + control;
      auto* timeButton = make_button(nightCard, x + control * 86, 134, 72, control ? "+" : "-", night_time_cb, reinterpret_cast<void*>(index));
      nightTimeButtons[index] = timeButton;
      lv_obj_set_height(timeButton, 44);
      lv_obj_remove_event_cb(timeButton, night_time_cb);
      for (auto code : {LV_EVENT_SHORT_CLICKED, LV_EVENT_LONG_PRESSED, LV_EVENT_LONG_PRESSED_REPEAT, LV_EVENT_RELEASED})
        lv_obj_add_event_cb(timeButton, night_time_cb, code, reinterpret_cast<void*>(index));
    }
  }
  nightValue = make_label(nightCard, 24, 202, 700, "", &lv_font_montserrat_16, ui_theme::muted, LV_TEXT_ALIGN_LEFT);
  nightSlider = lv_slider_create(nightCard);
  lv_obj_set_pos(nightSlider, 36, 244); lv_obj_set_size(nightSlider, 680, 20);
  lv_slider_set_range(nightSlider, 5, 50); lv_obj_set_ext_click_area(nightSlider, 16);
  lv_obj_set_style_bg_color(nightSlider, lv_color_hex(ui_theme::accent), LV_PART_INDICATOR);
  lv_obj_set_style_bg_color(nightSlider, lv_color_hex(ui_theme::accent), LV_PART_KNOB);
  lv_obj_add_event_cb(nightSlider, night_slider_cb, LV_EVENT_VALUE_CHANGED, nullptr);
  lv_obj_add_event_cb(nightSlider, night_slider_cb, LV_EVENT_RELEASED, nullptr);
  make_label(nightCard, 24, 286, 480, "HH / MM: tap or hold +/- to adjust.\nTouch restores daytime level for 60 seconds.", &lv_font_montserrat_14, ui_theme::muted, LV_TEXT_ALIGN_LEFT);
  make_button(nightCard, 552, 284, 176, "DONE", close_night, nullptr);
  lv_obj_set_hidden(nightOverlay, true);
  appearanceOverlay = lv_obj_create(lv_layer_top());
  lv_obj_set_size(appearanceOverlay, 800, 480); lv_obj_set_pos(appearanceOverlay, 0, 0);
  lv_obj_set_style_bg_color(appearanceOverlay, lv_color_hex(ui_theme::background), 0);
  lv_obj_set_style_bg_opa(appearanceOverlay, LV_OPA_80, 0); lv_obj_set_style_pad_all(appearanceOverlay, 0, 0);
  lv_obj_set_style_border_width(appearanceOverlay, 0, 0); lv_obj_set_scrollable(appearanceOverlay, false);
  auto* appearanceCard = lv_obj_create(appearanceOverlay); lv_obj_set_pos(appearanceCard, 24, 54); lv_obj_set_size(appearanceCard, 752, 374);
  lv_obj_set_style_bg_color(appearanceCard, lv_color_hex(ui_theme::surface), 0);
  lv_obj_set_style_border_color(appearanceCard, lv_color_hex(ui_theme::border), 0); lv_obj_set_style_pad_all(appearanceCard, 0, 0);
  lv_obj_set_scrollable(appearanceCard, false);
  make_label(appearanceCard, 24, 18, 700, "Make it yours", &lv_font_montserrat_26, ui_theme::text, LV_TEXT_ALIGN_LEFT);
  make_label(appearanceCard, 24, 58, 400, "COMPANION", &lv_font_montserrat_14, ui_theme::muted, LV_TEXT_ALIGN_LEFT);
  for (size_t i = 0; i < 2; ++i) companionButtons[i] = make_button(appearanceCard, 24 + i * 180, 86, 166,
      app_settings::companion_name(static_cast<app_settings::Companion>(i)), companion_select, reinterpret_cast<void*>(i), &companionCaptions[i]);
  companionPreview = lv_image_create(appearanceCard); lv_obj_set_pos(companionPreview, 546, 54); lv_obj_set_clickable(companionPreview, false);
  make_label(appearanceCard, 24, 160, 700, "UI COLOR THEME", &lv_font_montserrat_14, ui_theme::muted, LV_TEXT_ALIGN_LEFT);
  for (size_t i = 0; i < 4; ++i) themeButtons[i] = make_button(appearanceCard, 24 + i * 178, 192, 166,
      app_settings::theme_name(static_cast<app_settings::Theme>(i)), theme_select, reinterpret_cast<void*>(i), &themeCaptions[i]);
  make_label(appearanceCard, 24, 260, 700, "Changes apply now and are saved on this display.", &lv_font_montserrat_14, ui_theme::muted, LV_TEXT_ALIGN_LEFT);
  make_label(appearanceCard, 24, 286, 500, "Provider logos and warning colors stay consistent.", &lv_font_montserrat_12, ui_theme::muted, LV_TEXT_ALIGN_LEFT);
  make_button(appearanceCard, 552, 312, 176, "DONE", close_appearance, nullptr);
  lv_obj_set_hidden(appearanceOverlay, true);
  ui_theme::watch(settingsScreen); refresh_appearance();
  saveFeedback = make_label(lv_layer_top(), 590, 406, 186, "", &lv_font_montserrat_12, ui_theme::accent, LV_TEXT_ALIGN_LEFT);
  lv_obj_set_hidden(saveFeedback, true);
}

static void refresh_brightness() {
  const uint8_t percent = brightness_percent(display_get_brightness());
  const int32_t sliderValue = percent < 5 ? 5 : percent;
  if (!lv_obj_has_state(brightnessSlider, LV_STATE_PRESSED) && lv_slider_get_value(brightnessSlider) != sliderValue)
    lv_slider_set_value(brightnessSlider, sliderValue, LV_ANIM_OFF);
  char text[12];
  snprintf(text, sizeof(text), "%u %%", percent);
  if (strcmp(lv_label_get_text(brightnessValue), text) != 0) lv_label_set_text(brightnessValue, text);
  char actual[48];
  snprintf(actual, sizeof(actual), "Actual %u %%\n%s", brightness_percent(display_get_applied_brightness()), idle_dim_mode());
  if (strcmp(lv_label_get_text(actualBrightnessLabel), actual) != 0) lv_label_set_text(actualBrightnessLabel, actual);
  refresh_choices();
}

void ui_settings_update() {
  const bool choosing = !lv_obj_is_hidden(appearanceOverlay);
  if (choosing && lv_obj_get_index(saveFeedback) != static_cast<int32_t>(lv_obj_get_child_count(lv_layer_top())) - 1) lv_obj_move_foreground(saveFeedback);
  const int x = choosing ? 48 : 590, y = choosing ? 446 : 406;
  if (lv_obj_get_x(saveFeedback) != x || lv_obj_get_y(saveFeedback) != y) lv_obj_set_pos(saveFeedback, x, y);
  if (lv_screen_active() == settingsScreen && !lv_obj_has_state(brightnessSlider, LV_STATE_PRESSED)) refresh_brightness();
  if (shownSaveRevision != app_settings::save_revision()) {
    shownSaveRevision = app_settings::save_revision(); savedAtMs = millis();
    const bool success = app_settings::save_status() == app_settings::SaveStatus::saved;
    lv_label_set_text(saveFeedback, success ? "SAVED" : "SAVE FAILED");
    lv_obj_set_style_text_color(saveFeedback, lv_color_hex(success ? ui_theme::accent : 0xFF5252), 0);
  }
  lv_obj_set_hidden(saveFeedback, lv_screen_active() != settingsScreen || !shownSaveRevision || millis() - savedAtMs >= 5000u);
}
void ui_settings_show() {
  if (lv_screen_active() != settingsScreen) settingsReturnScreen = lv_screen_active();
  refresh_brightness();
  display_set_brightness(display_get_brightness());
  lv_screen_load(settingsScreen);
}
void ui_settings_hide() {
  lv_obj_set_hidden(saveFeedback, true);
  lv_obj_set_hidden(alertsOverlay, true); lv_obj_set_hidden(nightOverlay, true);
  lv_obj_set_hidden(appearanceOverlay, true);
  lv_screen_load(settingsReturnScreen ? settingsReturnScreen : dashScreen);
}
bool ui_settings_is_active() { return lv_screen_active() == settingsScreen; }
