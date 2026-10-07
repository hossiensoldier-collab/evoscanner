# Changelog

همه‌ی تغییرات مهم این پروژه اینجا ثبت می‌شن.
فرمت بر اساس [Keep a Changelog](https://keepachangelog.com/).

## [10.0] — 2026-10-07

### ✨ Added
- **CORTEX** — ایجنت خودمختار (PERCEIVE → PLAN → ACT → REFLECT → LEARN → SUGGEST)
- **HEALTH** dashboard — گزینه ۱۹
- **TEST** (سریع) — گزینه ۲۰
- **DEEP-TEST** (کامل) — گزینه ۲۱
- **SELF-CARE** — ترمیم/ارتقا/صافی — گزینه ۱۷
- **AUTO-HEAL** — تشخیص و تعمیر خودکار — گزینه ۱۸
- **ENGINES** menu — due, forge, sacred, qasd — گزینه ۱۵
- **DUE** integration — گزینه ۱۶
- **WebApp v2** — با CORTEX، Graph، Search
- **pre_run.sh** — آزادسازی پورت‌ها

### 🔧 Fixed
- `R is not defined` در `panel_v10.py` (خط ۲۷۹-۲۸۱)
- `engine` undefined در `due.py` (main + print_summary)
- تداخل پورت ۸۰۸۰ (graph_web → ۸۰۸۲)
- نسخه‌های تکراری `menu_item(22)` و `c == "22"`
- پاکسازی فایل‌های حساس از git (`.env`, `ssh_keys/`, ...)

### 🗑️ Removed
- فایل‌های خراب: `smart.py`, `fix_v12.py`
- فایل‌های زائد: `[`, `PYEOF`, `2.0`, `dest`, `esc`
- APK workflow (Buildozer روی GitHub Actions خرابه)

### 📦 Improved
- ۳ فایل گم‌شده از `features/` پیدا و کپی شد
- ساختار BACKUPS با برچسب زمانی
- مستندات کامل در `ECOSYSTEM.md`

## [1.3] — پیش از 2026-10-05
- نسخه‌ی اولیه‌ی EvoScanner self-evolving

