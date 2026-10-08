#pragma once
#include "ai_monitor/ai_monitor.h"
#include "usage_format.h"

enum class NovaMood : uint8_t { ready, working, updated, low, critical, resting, offline, waiting, issue, greeting };
class NovaState {
 public:
  void greet(uint32_t now) { greeted_ = true; greetedMs_ = now; }
  template<typename Warning>
  NovaMood evaluate(const aim::Snapshot& snapshot, uint32_t now, bool resting, Warning warning) const {
    if (greeted_ && now - greetedMs_ < 2200u) return NovaMood::greeting;
    if (!snapshot.hostPresent) return NovaMood::offline;
    const bool tokenSignalFresh = snapshot.tokenUsageKnown && now - snapshot.tokenActivityMs < 15000u;
    bool hasFresh = false, low = false, critical = false, issue = false;
    for (size_t v = 0; v < aim::kMaxViews; ++v) {
      if (snapshot.viewsConfigured && v >= snapshot.viewCount) continue;
      const auto& view = snapshot.views[v];
      issue |= view.notice;
      if (!view.valid || !view.hasUsage || view.notice || view.fetching || now - view.quotaReceivedMs >= 300000u) continue;
      for (size_t r = 0; r < view.rowCount; ++r) {
        const auto& row = view.rows[r]; if (!row.valid) continue;
        hasFresh = true;
        const float remaining = view.showsRemaining ? row.usedPercent : 100.0f - row.usedPercent;
        const uint8_t limit = warning(view.providerKey, row);
        low |= remaining <= limit; critical |= remaining <= (limit < 10 ? limit : 10);
      }
    }
    if (tokenSignalFresh && snapshot.tokenUsageSeen && snapshot.tokenIdleSeconds < 90u) return NovaMood::working;
    if (critical) return NovaMood::critical;
    if (low) return NovaMood::low;
    if (issue || (snapshot.activity == aim::HostActivity::failed && now - snapshot.activityMs < 60000u)) return NovaMood::issue;
    if (!hasFresh) return NovaMood::waiting;
    if (tokenSignalFresh && snapshot.tokenUsageSeen && snapshot.tokenIdleSeconds >= 90u && snapshot.tokenIdleSeconds < 95u) return NovaMood::updated;
    if (tokenSignalFresh && snapshot.tokenIdleSeconds >= 300u && !(greeted_ && now - greetedMs_ < 60000u)) return NovaMood::resting;
    (void)resting;  // backlight dimming never proves token activity has stopped
    return NovaMood::ready;
  }
 private:
  uint32_t greetedMs_ = 0;
  bool greeted_ = false;
};
