"""Menu Map — دیاگرام ASCII کامل پنل"""
import os
import sys
import time

C = {
    "R": "\033[0;31m", "G": "\033[0;32m", "Y": "\033[1;33m",
    "B": "\033[0;34m", "M": "\033[0;35m", "Cy": "\033[0;36m",
    "W": "\033[1;37m", "D": "\033[0m",
    "Bold": "\033[1m", "Dim": "\033[2m",
}


def clear():
    os.system("clear")


def pause():
    try:
        input(f"\n{C['Dim']}Enter...{C['D']}")
    except (EOFError, KeyboardInterrupt):
        pass


def show_overview():
    clear()
    print(C["Cy"] + r"""
  ╔══════════════════════════════════════════════════════════════════╗
  ║                                                                  ║
  ║           E V O S C A N N E R     v 3 . 0 . 0                    ║
  ║                                                                  ║
  ║                    Complete Menu Map                             ║
  ║                                                                  ║
  ╚══════════════════════════════════════════════════════════════════╝
""" + C["D"])

    print(f"""
{C['Bold']}{C['W']}┌─── KAR / WORK ──────────────────────────────────────────────┐{C['D']}
{C['Y']}│{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[1]{C['D']}  {C['Bold']}Explore & Search{C['D']}     {C['Dim']}search, ask, related, path{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[2]{C['D']}  {C['Bold']}Collect & Scan{C['D']}         {C['Dim']}run, enrich, hunter{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[7]{C['D']}  {C['Bold']}Graph Explorer{C['D']}         {C['Dim']}entities, peers, paths{C['D']}
{C['Y']}│{C['D']}
{C['Bold']}{C['W']}├─── DANESH / KNOWLEDGE ──────────────────────────────────────┤{C['D']}
{C['Y']}│{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[3]{C['D']}  {C['Bold']}Learning & Goals{C['D']}       {C['Dim']}paths for 5 goals{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[11]{C['D']} {C['Bold']}Learn & Knowledge{C['D']}      {C['Dim']}extract, techniques, snippets{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[12]{C['D']} {C['Bold']}Extended Sources{C['D']}       {C['Dim']}papers, awesome, PyPI, RSS{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[17]{C['D']} {C['Bold']}Ideas & Advisor{C['D']}        {C['Dim']}project, package, need{C['D']}
{C['Y']}│{C['D']}
{C['Bold']}{C['W']}├─── SYSTEM ───────────────────────────────────────────────────┤{C['D']}
{C['Y']}│{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[4]{C['D']}  {C['Bold']}Agents & Self-Evolve{C['D']}   {C['Dim']}hunter, judge, archivist, critic{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[5]{C['D']}  {C['Bold']}Data & Export{C['D']}          {C['Dim']}JSON, CSV, MD, snapshots{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[6]{C['D']}  {C['Bold']}Servers{C['D']}                {C['Dim']}API, web UI, watch, IDE{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[8]{C['D']}  {C['Bold']}Bookmarks & History{C['D']}    {C['Dim']}saved items{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[9]{C['D']}  {C['Bold']}Settings{C['D']}               {C['Dim']}theme, config{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[10]{C['D']} {C['Bold']}Self-Upgrade{C['D']}           {C['Dim']}patch, rollback{C['D']}
{C['Y']}│{C['D']}
{C['Bold']}{C['W']}├─── INTEGRATION ──────────────────────────────────────────────┤{C['D']}
{C['Y']}│{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[13]{C['D']} {C['Bold']}GitHub Token{C['D']}           {C['Dim']}set, test, delete{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[14]{C['D']} {C['Bold']}AI Agent{C['D']}               {C['Dim']}auto-patch via LLM{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[15]{C['D']} {C['Bold']}AI Bridge{C['D']}              {C['Dim']}build prompt for chat{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[16]{C['D']} {C['Bold']}Extras{C['D']}                 {C['Dim']}compare, weekly, snippets{C['D']}
{C['Y']}│{C['D']}
{C['Bold']}{C['W']}├─── INFRASTRUCTURE ───────────────────────────────────────────┤{C['D']}
{C['Y']}│{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[18]{C['D']} {C['Bold']}Cleanup & Health{C['D']}       {C['Dim']}archive dead files{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[19]{C['D']} {C['Bold']}Network{C['D']}                {C['Dim']}providers, proxy, ssh{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[20]{C['D']} {C['Bold']}Proxy & Tasks{C['D']}          {C['Dim']}local proxy, HTTP tasks{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[21]{C['D']} {C['Bold']}Server & Tunnel{C['D']}        {C['Dim']}HTTP server, SOCKS5{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[22]{C['D']} {C['Bold']}Server Hub{C['D']}             {C['Dim']}auto cloud setup{C['D']}
{C['Y']}│{C['D']}  {C['Cy']}[23]{C['D']} {C['Bold']}Project Snapshot{C['D']}       {C['Dim']}export for any AI{C['D']}
{C['Y']}│{C['D']}
{C['Y']}└{'─' * 62}┘{C['D']}

  {C['Dim']}24 گزینه · 7 گروه · 100+ زیرمنو{C['D']}
""")


def show_menu1():
    clear()
    print(C["Cy"] + "  ┌─ [1] EXPLORE & SEARCH ─────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} جستجو و کاوش در پایگاه دانش (۴۱۸+ منبع)

   {C['Y']}[1]{C['D']}  جستجو در پایگاه        {C['Dim']}→ search <query>{C['D']}
       {C['Dim']}│{C['D']}
       {C['Dim']}├─{C['D']} متن کامل + عنوان
       {C['Dim']}├─{C['D']} ۱۵ نتیجه برتر
       {C['Dim']}└─{C['D']} امکان bookmark

   {C['Y']}[2]{C['D']}  پکیج‌های مرتبط         {C['Dim']}→ related <pkg>{C['D']}
       {C['Dim']}│{C['D']}
       {C['Dim']}├─{C['D']} Related (co-occurrence)
       {C['Dim']}└─{C['D']} Peers (same category)

   {C['Y']}[3]{C['D']}  پرسش (RAG)            {C['Dim']}→ ask <question>{C['D']}
       {C['Dim']}│{C['D']}
       {C['Dim']}├─{C['D']} BM25 scoring
       {C['Dim']}├─{C['D']} Sentence splitting
       {C['Dim']}└─{C['D']} Top 3 answers with source

   {C['Y']}[4]{C['D']}  مسیر در گراف           {C['Dim']}→ graph-path <a> <b>{C['D']}
       {C['Dim']}│{C['D']}
       {C['Dim']}└─{C['D']} کوتاه‌ترین مسیر با BFS

   {C['Y']}[5]{C['D']}  پیشنهاد import        {C['Dim']}→ suggest <file>{C['D']}
       {C['Dim']}│{C['D']}
       {C['Dim']}├─{C['D']} خواندن importهای فایل
       {C['Dim']}└─{C['D']} پیشنهاد بر اساس گراف

   {C['Y']}[6]{C['D']}  Graph Explorer         {C['Dim']}→ [7]{C['D']}

   {C['Y']}[7]{C['D']}  برترین منابع           {C['Dim']}→ top 25>{C['D']}

   {C['Y']}[8]{C['D']}  جستجوهای اخیر          {C['Dim']}→ تاریخچه{C['D']}

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu2():
    clear()
    print(C["Cy"] + "  ┌─ [2] COLLECT & SCAN ───────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} جذب منابع از اینترنت (۵ منبع فعال)

   {C['Y']}[1]{C['D']}  چرخه کشف               {C['Dim']}→ reset + run + rebuild{C['D']}
       {C['Dim']}└─{C['D']} ۲ چرخه، هر چرخه ۶ کوئری × ۵ منبع

   {C['Y']}[2]{C['D']}  reset health           {C['Dim']}→ فعال‌سازی منابع خاموش{C['D']}

   {C['Y']}[3]{C['D']}  Enrich                 {C['Dim']}→ دریافت README کامل{C['D']}
       {C['Dim']}└─{C['D']} نیازمند GitHub Token

   {C['Y']}[4]{C['D']}  Rebuild                {C['Dim']}→ دسته + گراف{C['D']}

   {C['Y']}[5]{C['D']}  Hunter (UCB)           {C['Dim']}→ انتخاب هوشمند کوئری{C['D']}
       {C['Dim']}│{C['D']}
       {C['Dim']}├─{C['D']} UCB = exploit + explore
       {C['Dim']}└─{C['D']} ۱۰ کوئری برتر

   {C['Y']}[6]{C['D']}  Suggest                {C['Dim']}→ پیشنهاد برای شکاف‌ها{C['D']}

   {C['Y']}[7]{C['D']}  Discover               {C['Dim']}→ k-means clustering{C['D']}

   {C['Y']}[8]{C['D']}  گزارش کوئری            {C['Dim']}→ top queries{C['D']}

   {C['Y']}[0]{C['D']}  بازگشت

   {C['Dim']}─── منابع ───{C['D']}
   GitHub · arXiv · StackOverflow · Dev.to · PapersWithCode
""")


def show_menu3():
    clear()
    print(C["Cy"] + "  ┌─ [3] LEARNING & GOALS ─────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} مسیر یادگیری شخصی‌سازی‌شده بر اساس منابع موجود

   {C['Y']}[1]{C['D']}  لیست اهداف
   {C['Y']}[2]{C['D']}  Backend
       {C['Dim']}└─{C['D']} Python → Web → ORM → API → Test → Deploy
   {C['Y']}[3]{C['D']}  ML
       {C['Dim']}└─{C['D']} Math → Data → ML → DL → NLP → MLOps
   {C['Y']}[4]{C['D']}  Data
       {C['Dim']}└─{C['D']} Pandas → SQL → Viz → Stats → Big Data
   {C['Y']}[5]{C['D']}  DevOps
       {C['Dim']}└─{C['D']} Linux → Auto → Docker → CI → Monitor
   {C['Y']}[6]{C['D']}  Security
       {C['Dim']}└─{C['D']} Basics → Python → Pentest → Malware → Defense
   {C['Y']}[7]{C['D']}  موضوع دلخواه
       {C['Dim']}└─{C['D']} ۴ سطح: مبتدی/متوسط/پیشرفته/پژوهش

   {C['Y']}[0]{C['D']}  بازگشت

   {C['Dim']}─── نحوه کار ───{C['D']}
   ۱. انتخاب هدف
   ۲. جستجو در resources
   ۳. دسته‌بندی بر اساس سختی
   ۴. نمایش ۴ سطح
   ۵. افزودن کوئری‌های خالی به صف
""")


def show_menu4():
    clear()
    print(C["Cy"] + "  ┌─ [4] AGENTS & SELF-EVOLVE ─────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} چهار ایجنت مستقل که پروژه را ارزیابی و بهبود می‌دهند

   {C['Y']}[1]{C['D']}  اجرای ۴ ایجنت
       {C['Dim']}│{C['D']}
       {C['Dim']}├─{C['D']} {C['G']}Hunter{C['D']}      کشف کوئری‌های جدید (MUTATORS)
       {C['Dim']}├─{C['D']} {C['G']}Judge{C['D']}       حذف منابع ضعیف (score < 0.05)
       {C['Dim']}├─{C['D']} {C['G']}Archivist{C['D']}   بازدسته + بازسازی گراف
       {C['Dim']}└─{C['D']} {C['G']}Critic{C['D']}      نقد سیستم

   {C['Y']}[2]{C['D']}  گزارش ایجنت‌ها          {C['Dim']}→ آخرین اجرا{C['D']}

   {C['Y']}[3]{C['D']}  تحلیل کد (Selfmod)
       {C['Dim']}│{C['D']}
       {C['Dim']}├─{C['D']} خطوط بلند
       {C['Dim']}├─{C['D']} توابع بلند
       {C['Dim']}├─{C['D']} importهای تکراری
       {C['Dim']}└─{C['D']} TODO/FIXME

   {C['Y']}[4]{C['D']}  تاریخچه تغییرات

   {C['Y']}[5]{C['D']}  Rollback                 {C['Dim']}→ بازگشت{C['D']}

   {C['Y']}[6]{C['D']}  Compress گراف            {C['Dim']}→ ادغام مشابه‌ها{C['D']}

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu5():
    clear()
    print(C["Cy"] + "  ┌─ [5] DATA & EXPORT ────────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} خروجی، آرشیو، و مقایسه

   {C['Y']}[1]{C['D']}  Export کامل              {C['Dim']}→ JSON + CSV + MD{C['D']}
   {C['Y']}[2]{C['D']}  گزارش MD                {C['Dim']}→ report.md{C['D']}
   {C['Y']}[3]{C['D']}  آمار کلی
   {C['Y']}[4]{C['D']}  دسته‌ها                   {C['Dim']}→ نمودار{C['D']}
   {C['Y']}[5]{C['D']}  لیست exports
   {C['Y']}[6]{C['D']}  ساخت snapshot
       {C['Dim']}└─{C['D']} ثبت لحظه‌ای آمار
   {C['Y']}[7]{C['D']}  Diff دو snapshot
       {C['Dim']}└─{C['D']} منابع + گراف + cooc
   {C['Y']}[8]{C['D']}  لیست snapshotها

   {C['Y']}[0]{C['D']}  بازگشت

   {C['Dim']}─── فرمت‌ها ───{C['D']}
   • JSON:    کامل برای پردازش
   • CSV:     برای Excel
   • MD:      برای خواندن
   • TAR.GZ:  برای بکاپ
""")


def show_menu6():
    clear()
    print(C["Cy"] + "  ┌─ [6] SERVERS ──────────────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} راه‌اندازی سرویس‌های محلی

   {C['Y']}[1]{C['D']}  Start API (:8081)
       {C['Dim']}└─{C['D']} /search, /related, /ask, /path, /suggest

   {C['Y']}[2]{C['D']}  Stop API

   {C['Y']}[3]{C['D']}  Graph Web (:8080)
       {C['Dim']}└─{C['D']} SVG interactive

   {C['Y']}[4]{C['D']}  DB Web (:8080)
       {C['Dim']}└─{C['D']} جستجو در مرورگر

   {C['Y']}[5]{C['D']}  Watch file
       {C['Dim']}└─{C['D']} مانیتور تغییرات

   {C['Y']}[6]{C['D']}  Text IDE (curses)

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu7():
    clear()
    print(C["Cy"] + "  ┌─ [7] GRAPH EXPLORER ───────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} کاوش در گراف دانش (۶۴۵ نود، ۱۷۷۰ یال)

   {C['Y']}[1]{C['D']}  برترین entityها         {C['Dim']}→ top 25{C['D']}

   {C['Y']}[2]{C['D']}  Related                {C['Dim']}→ co-occurrence{C['D']}
       {C['Dim']}└─{C['D']} پکیج‌های هم‌ذکر

   {C['Y']}[3]{C['D']}  Peers                  {C['Dim']}→ same category{C['D']}
       {C['Dim']}└─{C['D']} هم‌دسته در گراف

   {C['Y']}[4]{C['D']}  Neighbors              {C['Dim']}→ edges{C['D']}
       {C['Dim']}└─{C['D']} با جهت (→ / ←)

   {C['Y']}[5]{C['D']}  Shortest path          {C['Dim']}→ BFS{C['D']}

   {C['Y']}[6]{C['D']}  Filter by category

   {C['Y']}[7]{C['D']}  Export JSON

   {C['Y']}[8]{C['D']}  ASCII visualization
       {C['Dim']}└─{C['D']} نقشه گروه‌بندی‌شده

   {C['Y']}[9]{C['D']}  آمار تفصیلی

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu8():
    clear()
    print(C["Cy"] + "  ┌─ [8] BOOKMARKS & HISTORY ──────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} ذخیره و مشاهده تاریخچه

   {C['Y']}[1]{C['D']}  پکیج‌های bookmark       {C['Dim']}→ ستاره‌دار{C['D']}
   {C['Y']}[2]{C['D']}  کوئری‌های bookmark
   {C['Y']}[3]{C['D']}  جستجوهای اخیر          {C['Dim']}→ ۲۰ مورد{C['D']}
   {C['Y']}[4]{C['D']}  سؤالات اخیر
   {C['Y']}[5]{C['D']}  پکیج‌های اخیر
   {C['Y']}[6]{C['D']}  پاک کردن تاریخچه

   {C['Y']}[0]{C['D']}  بازگشت

   {C['Dim']}─── فایل‌ها ───{C['D']}
   panel_bookmarks.json
   panel_history.json
""")


def show_menu9():
    clear()
    print(C["Cy"] + "  ┌─ [9] SETTINGS ─────────────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} شخصی‌سازی

   {C['Y']}[1]{C['D']}  Theme
       {C['Dim']}├─{C['D']} default   (رنگ‌های استاندارد)
       {C['Dim']}├─{C['D']} green     (روشن‌تر)
       {C['Dim']}└─{C['D']} no-color  (بدون ANSI)

   {C['Y']}[2]{C['D']}  Confirm dangerous
       {C['Dim']}└─{C['D']} تأیید قبل از عملیات خطرناک

   {C['Y']}[3]{C['D']}  Reset config

   {C['Y']}[4]{C['D']}  View config

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu10():
    clear()
    print(C["Cy"] + "  ┌─ [10] SELF-UPGRADE ────────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} بهبود کد خود پنل

   {C['Y']}[1]{C['D']}  تحلیل کامل
       {C['Dim']}├─{C['D']} خطوط بلند
       {C['Dim']}├─{C['D']} توابع بلند
       {C['Dim']}└─{C['D']} docstring گم‌شده

   {C['Y']}[2]{C['D']}  لیست ارتقاها
       {C['Dim']}├─{C['D']} به‌روزرسانی هدر
       {C['Dim']}├─{C['D']} افزودن docstring
       {C['Dim']}├─{C['D']} فشرده‌سازی خطوط خالی
       {C['Dim']}├─{C['D']} importهای گم‌شده
       {C['Dim']}├─{C['D']} حذف import تکراری
       {C['Dim']}└─{C['D']} حذف فاصله انتهای خط

   {C['Y']}[3]{C['D']}  اجرای ارتقا (backup خودکار)

   {C['Y']}[4]{C['D']}  تاریخچه

   {C['Y']}[5]{C['D']}  Rollback آخرین

   {C['Y']}[6]{C['D']}  Rollback انتخابی

   {C['Y']}[7]{C['D']}  لیست backupها

   {C['Y']}[8]{C['D']}  Version bump
       {C['Dim']}└─{C['D']} patch / minor / major

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu11():
    clear()
    print(C["Cy"] + "  ┌─ [11] LEARN & KNOWLEDGE ───────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} استخراج دانش از منابع

   {C['Y']}[1]{C['D']}  Extract
       {C['Dim']}│{C['D']}
       {C['Dim']}├─{C['D']} تکنیک‌ها (techniques)
       {C['Dim']}├─{C['D']} مفاهیم (concepts)
       {C['Dim']}├─{C['D']} قطعات کد (snippets)
       {C['Dim']}└─{C['D']} سطح سختی

   {C['Y']}[2]{C['D']}  آمار دانش
   {C['Y']}[3]{C['D']}  مسیر یادگیری
   {C['Y']}[4]{C['D']}  تکنیک‌ها
   {C['Y']}[5]{C['D']}  Code snippets
   {C['Y']}[6]{C['D']}  گزارش گرافیک
   {C['Y']}[7]{C['D']}  چرخه خودکار

   {C['Y']}[0]{C['D']}  بازگشت

   {C['Dim']}─── الگوهای استخراج ───{C['D']}
   • pip install X
   • from X import
   • `backtick`
   • Name is description
""")


def show_menu12():
    clear()
    print(C["Cy"] + "  ┌─ [12] EXTENDED SOURCES ────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} منابع جدید

   {C['Y']}[1]{C['D']}  Papers with Code       {C['Dim']}→ مقاله + کد{C['D']}
   {C['Y']}[2]{C['D']}  Awesome Lists          {C['Dim']}→ لیست‌های منتخب{C['D']}
   {C['Y']}[3]{C['D']}  PyPI packages          {C['Dim']}→ متادیتا + README{C['D']}
   {C['Y']}[4]{C['D']}  RSS Feeds
       {C['Dim']}├─{C['D']} RealPython
       {C['Dim']}├─{C['D']} Python.org
       {C['Dim']}└─{C['D']} PyCoder
   {C['Y']}[5]{C['D']}  Graphics resources
   {C['Y']}[6]{C['D']}  همه با query

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu13():
    clear()
    print(C["Cy"] + "  ┌─ [13] GITHUB TOKEN ────────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} مدیریت توکن GitHub

   {C['Y']}[1]{C['D']}  Set / Update
       {C['Dim']}└─{C['D']} ذخیره در .env با chmod 600

   {C['Y']}[2]{C['D']}  Test
       {C['Dim']}└─{C['D']} نمایش user + rate limit

   {C['Y']}[3]{C['D']}  Delete

   {C['Y']}[4]{C['D']}  راهنما
       {C['Dim']}└─{C['D']} github.com/settings/tokens/new

   {C['Y']}[0]{C['D']}  بازگشت

   {C['Dim']}─── چرا لازم؟ ───{C['D']}
   بدون: 60 req/hour
   با:   5000 req/hour
""")


def show_menu14():
    clear()
    print(C["Cy"] + "  ┌─ [14] AI AGENT ────────────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} LLM داخل پنل — خودش patch می‌سازد و اعمال می‌کند

   {C['Y']}[1]{C['D']}  تنظیم provider + key
       {C['Dim']}├─{C['D']} groq         (فیلتر در ایران)
       {C['Dim']}├─{C['D']} openrouter   (کار می‌کند)
       {C['Dim']}├─{C['D']} together
       {C['Dim']}├─{C['D']} deepinfra    (کار می‌کند)
       {C['Dim']}└─{C['D']} openai

   {C['Y']}[2]{C['D']}  Test key

   {C['Y']}[3]{C['D']}  Feature جدید
       {C['Dim']}│{C['D']}
       {C['Dim']}├─{C['D']} خواسته → پرامپت
       {C['Dim']}├─{C['D']} LLM → کد + patch
       {C['Dim']}├─{C['D']} backup خودکار
       {C['Dim']}├─{C['D']} اعمال
       {C['Dim']}└─{C['D']} تست syntax → rollback اگر خطا

   {C['Y']}[4]{C['D']}  Bug fix
   {C['Y']}[5]{C['D']}  Upgrade
   {C['Y']}[6]{C['D']}  تاریخچه
   {C['Y']}[7]{C['D']}  Rollback آخرین
   {C['Y']}[8]{C['D']}  Rollback انتخابی

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu15():
    clear()
    print(C["Cy"] + "  ┌─ [15] AI BRIDGE ───────────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} ساخت پرامپت کامل برای بردن به AI خارجی

   {C['Y']}[1]{C['D']}  خواسته جدید
   {C['Y']}[2]{C['D']}  Bug fix
   {C['Y']}[3]{C['D']}  ارتقا

   {C['Y']}[4]{C['D']}  لیست خواسته‌ها
   {C['Y']}[5]{C['D']}  نمایش آخرین
   {C['Y']}[6]{C['D']}  Copy به clipboard
   {C['Y']}[7]{C['D']}  پاک کردن

   {C['Y']}[0]{C['D']}  بازگشت

   {C['Dim']}─── فرق با [14] ───{C['D']}
   [14] = خودکار (LLM داخل)
   [15] = دستی (پرامپت بساز، دستی بده به AI)

   {C['Dim']}─── پرامپت شامل ───{C['D']}
   • خواسته کاربر
   • وضعیت پروژه (نسخه، فایل‌ها، آمار)
   • دستورات موجود
   • قواعد کدنویسی
   • ذخیره در ai_prompts/
""")


def show_menu16():
    clear()
    print(C["Cy"] + "  ┌─ [16] EXTRAS ──────────────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} ابزارهای کاربردی

   {C['Y']}[1]{C['D']}  مقایسه دو پکیج
       {C['Dim']}└─{C['D']} category, score, stars, related

   {C['Y']}[2]{C['D']}  گزارش هفتگی
       {C['Dim']}└─{C['D']} منابع جدید، دسته‌ها، دانش

   {C['Y']}[3]{C['D']}  افزودن snippet
       {C['Dim']}└─{C['D']} ذخیره کد شخصی

   {C['Y']}[4]{C['D']}  جستجوی snippet

   {C['Y']}[5]{C['D']}  لیست snippetها

   {C['Y']}[6]{C['D']}  حذف snippet

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu17():
    clear()
    print(C["Cy"] + "  ┌─ [17] IDEAS & ADVISOR ─────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} پیشنهاد پروژه، مشاور پکیج، پیش‌بینی نیاز

   {C['Y']}[1]{C['D']}  پیشنهاد پروژه
       {C['Dim']}│{C['D']}
       {C['Dim']}├─{C['D']} web_api      → REST API
       {C['Dim']}├─{C['D']} web_ui       → Dashboard
       {C['Dim']}├─{C['D']} scraper      → Web crawler
       {C['Dim']}├─{C['D']} telegram_bot → Chatbot
       {C['Dim']}├─{C['D']} ml_classifier → ML model
       {C['Dim']}├─{C['D']} ml_llm       → LLM app
       {C['Dim']}├─{C['D']} async_service → Async
       {C['Dim']}├─{C['D']} game_2d      → Game
       {C['Dim']}├─{C['D']} graphics_visual → Plotting
       {C['Dim']}├─{C['D']} opencv_app   → Image
       {C['Dim']}├─{C['D']} cli_tool     → CLI
       {C['Dim']}├─{C['D']} data_pipeline → ETL
       {C['Dim']}└─{C['D']} automation   → Automation

   {C['Y']}[2]{C['D']}  مشاور پکیج
       {C['Dim']}└─{C['D']} ۳۳ کار: web framework، async، testing...

   {C['Y']}[3]{C['D']}  پیش‌بینی نیاز
       {C['Dim']}└─{C['D']} بر اساس پکیج‌های فعلی

   {C['Y']}[4]{C['D']}  پیش‌بینی از فایل کد

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu18():
    clear()
    print(C["Cy"] + "  ┌─ [18] CLEANUP & HEALTH ────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} تمیزکاری پروژه

   {C['Y']}[1]{C['D']}  گزارش سلامت
       {C['Dim']}├─{C['D']} فایل‌های اصلی
       {C['Dim']}├─{C['D']} features/
       {C['Dim']}├─{C['D']} تکراری‌ها (hash)
       {C['Dim']}└─{C['D']} بزرگ‌ترین فایل‌ها

   {C['Y']}[2]{C['D']}  پیش‌نمایش آرشیو      {C['Dim']}→ dry-run{C['D']}

   {C['Y']}[3]{C['D']}  آرشیو فایل‌های مرده
       {C['Dim']}├─{C['D']} fix_*.py
       {C['Dim']}├─{C['D']} migrate_*.py
       {C['Dim']}├─{C['D']} panel_good.py
       {C['Dim']}└─{C['D']} *.bak

   {C['Y']}[4]{C['D']}  لیست آرشیوها

   {C['Y']}[5]{C['D']}  بازگردانی

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu19():
    clear()
    print(C["Cy"] + "  ┌─ [19] NETWORK ─────────────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} تست و مدیریت شبکه

   {C['Y']}[1]{C['D']}  گزارش شبکه
       {C['Dim']}└─{C['D']} تست ۶ provider + زمان پاسخ

   {C['Y']}[2]{C['D']}  انتخاب خودکار
       {C['Dim']}└─{C['D']} بهترین provider در دسترس

   {C['Y']}[3]{C['D']}  تنظیم پروکسی HTTP
   {C['Y']}[4]{C['D']}  حذف پروکسی
   {C['Y']}[5]{C['D']}  افزودن تونل SSH
   {C['Y']}[6]{C['D']}  شروع/توقف تونل
   {C['Y']}[7]{C['D']}  راهنمای Cloudflare WARP

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu20():
    clear()
    print(C["Cy"] + "  ┌─ [20] PROXY & TASKS ───────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} پروکسی محلی + اجرای وظایف

   {C['Y']}[1]{C['D']}  افزودن پروکسی         {C['Dim']}→ upstream{C['D']}
   {C['Y']}[2]{C['D']}  لیست پروکسی‌ها
   {C['Y']}[3]{C['D']}  تست همه
   {C['Y']}[4]{C['D']}  انتخاب بهترین
   {C['Y']}[5]{C['D']}  فعال/غیرفعال کردن

   {C['Y']}[6]{C['D']}  شروع پروکسی محلی     {C['Dim']}→ :8899{C['D']}
   {C['Y']}[7]{C['D']}  توقف

   {C['Y']}[8]{C['D']}  اجرای وظایف
       {C['Dim']}├─{C['D']} GitHub zen
       {C['Dim']}├─{C['D']} Hacker News
       {C['Dim']}├─{C['D']} arXiv recent
       {C['Dim']}└─{C['D']} OpenRouter models

   {C['Y']}[9]{C['D']}  لیست وظایف

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu21():
    clear()
    print(C["Cy"] + "  ┌─ [21] SERVER & TUNNEL ─────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} سرور HTTP محلی + تونل SOCKS

   {C['Y']}[1]{C['D']}  Start Server          {C['Dim']}→ :8080{C['D']}
       {C['Dim']}│{C['D']}
       {C['Dim']}├─{C['D']} GET /health
       {C['Dim']}├─{C['D']} GET /info
       {C['Dim']}├─{C['D']} POST /echo
       {C['Dim']}└─{C['D']} GET /proxy?url=...

   {C['Y']}[2]{C['D']}  Stop Server
   {C['Y']}[3]{C['D']}  Start Tunnel          {C['Dim']}→ :1080 SOCKS5{C['D']}
   {C['Y']}[4]{C['D']}  Stop Tunnel
   {C['Y']}[5]{C['D']}  Test Tunnel
   {C['Y']}[6]{C['D']}  Config SSH
       {C['Dim']}├─{C['D']} host
       {C['Dim']}├─{C['D']} user
       {C['Dim']}├─{C['D']} port
       {C['Dim']}└─{C['D']} local_port
   {C['Y']}[7]{C['D']}  Status

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu22():
    clear()
    print(C["Cy"] + "  ┌─ [22] SERVER HUB ──────────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} راه‌اندازی خودکار سرور ابری (اجرای auto_setup.py)

   {C['Bold']}۷ فاز خودکار:{C['D']}
   {C['Dim']}│{C['D']}
   {C['Y']}[1]{C['D']}  تشخیص محیط
       {C['Dim']}└─{C['D']} python, ssh, ssh-keygen, curl, termux-open-url

   {C['Y']}[2]{C['D']}  تولید کلید SSH
       {C['Dim']}└─{C['D']} ed25519 در ~/evoscanner/ssh_keys/

   {C['Y']}[3]{C['D']}  انتخاب سرویس ابری
       {C['Dim']}├─{C['D']} Oracle Cloud Free    (4 ARM + 24GB)
       {C['Dim']}├─{C['D']} GitHub Codespaces    (2 core + 8GB)
       {C['Dim']}├─{C['D']} Google Cloud Shell
       {C['Dim']}├─{C['D']} Fly.io
       {C['Dim']}└─{C['D']} Railway

   {C['Y']}[4]{C['D']}  راهنمای ثبت‌نام + باز کردن مرورگر
       {C['Dim']}└─{C['D']} termux-open-url

   {C['Y']}[5]{C['D']}  دریافت IP/User
       {C['Dim']}└─{C['D']} ذخیره در .ssh_hosts.json

   {C['Y']}[6]{C['D']}  تست اتصال SSH

   {C['Y']}[7]{C['D']}  راه‌اندازی تونل + اتصال AI

   {C['Y']}[0]{C['D']}  بازگشت
""")


def show_menu23():
    clear()
    print(C["Cy"] + "  ┌─ [23] PROJECT SNAPSHOT ────────────────────────────────┐" + C["D"])
    print()
    print(f"""
   {C['Bold']}هدف:{C['D']} بسته کامل پروژه برای انتقال به هر AI

   {C['Y']}[1]{C['D']}  ساخت snapshot
       {C['Dim']}│{C['D']}
       {C['Dim']}├─{C['D']} README کامل
       {C['Dim']}├─{C['D']} تمام .py
       {C['Dim']}├─{C['D']} تمام .md, .json, .sh
       {C['Dim']}├─{C['D']} ماسک توکن‌ها
       {C['Dim']}└─{C['D']} ۳ خروجی: MD, JSON, TAR.GZ

   {C['Y']}[2]{C['D']}  لیست snapshotها
   {C['Y']}[3]{C['D']}  نمایش آخرین
   {C['Y']}[4]{C['D']}  Copy مسیر به clipboard
   {C['Y']}[5]{C['D']}  بررسی امنیت
   {C['Y']}[6]{C['D']}  حذف قدیمی‌ها

   {C['Y']}[0]{C['D']}  بازگشت

   {C['Dim']}─── کاربرد ───{C['D']}
   • بده به هر AI → بازسازی
   • بده به AI → ارتقا با آگاهی کامل
   • بکاپ امن
""")


MENUS = {
    "0": show_overview,
    "1": show_menu1,
    "2": show_menu2,
    "3": show_menu3,
    "4": show_menu4,
    "5": show_menu5,
    "6": show_menu6,
    "7": show_menu7,
    "8": show_menu8,
    "9": show_menu9,
    "10": show_menu10,
    "11": show_menu11,
    "12": show_menu12,
    "13": show_menu13,
    "14": show_menu14,
    "15": show_menu15,
    "16": show_menu16,
    "17": show_menu17,
    "18": show_menu18,
    "19": show_menu19,
    "20": show_menu20,
    "21": show_menu21,
    "22": show_menu22,
    "23": show_menu23,
}


def interactive():
    while True:
        show_overview()
        print()
        print(f"  {C['Y']}[0-23]{C['D']} {C['Dim']}نمایش جزئیات منو{C['D']}")
        print(f"  {C['Y']}[a]{C['D']}    {C['Dim']}همه منوها یکی‌یکی{C['D']}")
        print(f"  {C['Y']}[q]{C['D']}    {C['Dim']}خروج{C['D']}")
        print()
        try:
            c = input(f"{C['Bold']}> {C['D']}انتخاب: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return

        if c in ("q", "quit", "exit"):
            return
        elif c == "a":
            for k in sorted(MENUS.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                MENUS[k]()
                pause()
        elif c in MENUS:
            MENUS[c]()
            pause()


if __name__ == "__main__":
    try:
        interactive()
    except KeyboardInterrupt:
        clear()
        print("\nBye\n")

