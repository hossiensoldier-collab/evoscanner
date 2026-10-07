"""Neumorphism — سایه‌های نرم"""
import os, sys

# پس‌زمینه خاکستری تیره
BG = "\033[48;2;30;30;36m"
SHADOW_DARK = "\033[48;2;20;20;25m"
SHADOW_LIGHT = "\033[48;2;45;45;52m"
TEXT = "\033[38;2;200;200;210m"
ACCENT = "\033[38;2;120;180;255m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def banner():
    os.system("clear")
    print()
    print(BG + " " * 56 + RESET)
    print(BG + "  " + SHADOW_LIGHT + " " * 4 + RESET + BG + "  " +
          ACCENT + BOLD + "EvoScanner" + RESET + BG +
          " " * 30 + SHADOW_DARK + " " * 4 + RESET)
    print(BG + " " * 56 + RESET)
    print()


def soft_item(num, title, sub):
    """آیتم نرم"""
    # سایه بالا
    print(SHADOW_DARK + "  " + " " * 50 + RESET)
    # آیتم
    print(BG + "  " + ACCENT + f"[{num:>2}]" + RESET + BG + "  " +
          TEXT + BOLD + f"{title:<25s}" + RESET + BG + " " +
          DIM + sub + RESET)
    # سایه پایین
    print(SHADOW_LIGHT + "  " + " " * 50 + RESET)
    print()


def demo():
    banner()
    soft_item(1, "ASK", "سؤال · جستجو · مشاور")
    soft_item(2, "GET", "جذب منابع جدید")
    soft_item(3, "LEARN", "یادگیری · مسیر · دانش")
    soft_item(4, "EVOLVE", "خودارتقایی · AI")
    soft_item(5, "MANAGE", "سرور · تنظیمات")
    print(BG + "  " + ACCENT + "▶" + RESET + BG + " " +
          TEXT + "انتخاب: " + RESET, end="")
    sys.stdout.flush()
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    demo()

