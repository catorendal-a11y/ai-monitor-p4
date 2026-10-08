#include "ui_notifications.h"
#include <Arduino.h>
#include <lvgl.h>
#include <cstdio>
#include <cstring>
#include "ui/quota_notifications.h"
#include "ui/usage_format.h"
#include "ui/theme.h"
#include "app_settings.h"
#include "ui_settings.h"

namespace quota_banner {
static QuotaNotifications policy;
static QuotaNotifications::Alert displayed;
static lv_obj_t *banner = nullptr, *heading = nullptr, *body = nullptr, *dismissButton = nullptr;
static void text(lv_obj_t* label, const char* value) {
  if (strcmp(lv_label_get_text(label), value) != 0) lv_label_set_text(label, value);
}
static void dismiss(lv_event_t*) {
  policy.acknowledge(displayed);
  ui_notifications_update();
}
static lv_obj_t* label(lv_obj_t* parent, int x, int y, int width, const lv_font_t* font) {
  auto* object = lv_label_create(parent);
  lv_obj_set_pos(object, x, y); lv_obj_set_width(object, width);
  lv_obj_set_style_text_font(object, font, 0);
  lv_obj_set_style_text_color(object, lv_color_hex(ui_theme::text), 0);
  lv_label_set_long_mode(object, LV_LABEL_LONG_MODE_CLIP);
  return object;
}
}

void ui_notifications_init() {
  using namespace quota_banner;
  banner = lv_obj_create(lv_layer_top());
  lv_obj_set_pos(banner, 24, 82); lv_obj_set_size(banner, 752, 88);
  lv_obj_set_style_bg_color(banner, lv_color_hex(ui_theme::surface), 0);
  lv_obj_set_style_bg_opa(banner, LV_OPA_COVER, 0);
  lv_obj_set_style_border_width(banner, 2, 0); lv_obj_set_style_radius(banner, 14, 0);
  lv_obj_set_style_pad_all(banner, 0, 0); lv_obj_set_scrollable(banner, false);
  heading = label(banner, 20, 12, 530, &lv_font_montserrat_16);
  body = label(banner, 20, 43, 530, &lv_font_montserrat_16);
  dismissButton = lv_btn_create(banner);
  lv_obj_set_pos(dismissButton, 578, 18); lv_obj_set_size(dismissButton, 152, 48);
  lv_obj_set_style_bg_color(dismissButton, lv_color_hex(ui_theme::button), 0);
  lv_obj_set_style_bg_color(dismissButton, lv_color_hex(ui_theme::pressed), LV_STATE_PRESSED);
  lv_obj_set_style_shadow_width(dismissButton, 0, 0);
  auto* caption = label(dismissButton, 0, 0, 132, &lv_font_montserrat_14);
  lv_label_set_text(caption, "DISMISS");
  lv_obj_set_style_text_align(caption, LV_TEXT_ALIGN_CENTER, 0); lv_obj_center(caption);
  lv_obj_add_event_cb(dismissButton, dismiss, LV_EVENT_CLICKED, nullptr);
  lv_obj_set_hidden(banner, true);
}

void ui_notifications_update() {
  using namespace quota_banner;
  const auto snapshot = aim::read();
  policy.update(snapshot, millis(), [](const char* provider, const aim::Row& row) {
    return app_settings::warning_for(provider, row.title, row.windowMinutes);
  });
  if (!banner) return;
  const auto* alert = policy.current();
  if (!alert || ui_settings_is_active()) { lv_obj_set_hidden(banner, true); return; }
  // Dismiss exactly the alert whose text was visible when this tap began.
  if (lv_obj_has_state(dismissButton, LV_STATE_PRESSED)) return;
  const bool critical = alert->severity == 2;
  const uint32_t color = critical ? 0xFF5252 : 0xFFAA00;
  if (displayed.severity != alert->severity) {
    lv_obj_set_style_border_color(banner, lv_color_hex(color), 0);
    lv_obj_set_style_text_color(heading, lv_color_hex(color), 0);
  }
  displayed = *alert;
  const auto* provider = aim::provider_style(alert->provider);
  char value[160], percent[16];
  snprintf(value, sizeof(value), "%s / %s / %u pending", critical ? "CRITICAL QUOTA" : "LOW QUOTA",
           provider ? provider->label : alert->provider, policy.count());
  text(heading, value);
  format_percent(alert->remaining, true, percent, sizeof(percent));
  snprintf(value, sizeof(value), "%s: %s remaining", alert->title[0] ? alert->title : "Quota", percent);
  text(body, value);
  lv_obj_set_hidden(banner, false);
}
