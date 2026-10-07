"""Server & Tunnel menu"""
import os, subprocess, sys
from pathlib import Path

BASE = Path(__file__).parent
PY = sys.executable
C = {"G":"\033[0;32m","R":"\033[0;31m","Y":"\033[1;33m",
     "Cy":"\033[0;36m","D":"\033[0m","Bold":"\033[1m","Dim":"\033[2m"}


def clear():
    os.system("clear")


def run(s, *a):
    try:
        subprocess.run([PY, str(BASE / s)] + list(a), cwd=str(BASE))
    except KeyboardInterrupt:
        print()


def check(s):
    try:
        r = subprocess.run([PY, str(BASE / s), "status"],
                           capture_output=True, text=True, cwd=str(BASE))
        return "running" in r.stdout
    except Exception:
        return False


def ask(p):
    try:
        return input(f"{C['Bold']}> {C['D']}{p}: ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def pause():
    try:
        input(f"\n{C['Dim']}Enter...{C['D']}")
    except (EOFError, KeyboardInterrupt):
        pass


def main():
    while True:
        clear()
        print()
        print(C["Cy"] + "  ==========================================" + C["D"])
        print(C["Cy"] + "  |     Server & SSH Tunnel  v1.0          |" + C["D"])
        print(C["Cy"] + "  ==========================================" + C["D"])
        print()
        srv = C["G"] + "RUN " + C["D"] if check("server.py") \
              else C["R"] + "STOP" + C["D"]
        tun = C["G"] + "RUN " + C["D"] if check("tunnel.py") \
              else C["R"] + "STOP" + C["D"]
        print(f"  Server: {srv}   Tunnel: {tun}")
        print()
        print(f"  {C['Y']}[1]{C['D']}  Start Server")
        print(f"  {C['Y']}[2]{C['D']}  Stop Server")
        print(f"  {C['Y']}[3]{C['D']}  Start Tunnel")
        print(f"  {C['Y']}[4]{C['D']}  Stop Tunnel")
        print(f"  {C['Y']}[5]{C['D']}  Test Tunnel")
        print(f"  {C['Y']}[6]{C['D']}  Config SSH")
        print(f"  {C['Y']}[7]{C['D']}  Status")
        print(f"  {C['Y']}[0]{C['D']}  Exit")
        print()
        print("  " + C["Dim"] + "-" * 42 + C["D"])
        c = ask("Choice")

        if c == "0":
            clear(); print("\nBye\n"); return
        elif c == "1": run("server.py", "start"); pause()
        elif c == "2": run("server.py", "stop"); pause()
        elif c == "3": run("tunnel.py", "start"); pause()
        elif c == "4": run("tunnel.py", "stop"); pause()
        elif c == "5": run("tunnel.py", "test"); pause()
        elif c == "6": run("tunnel.py", "config"); pause()
        elif c == "7":
            print(); print("Server:"); run("server.py", "status")
            print(); print("Tunnel:"); run("tunnel.py", "status")
            pause()


if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\n\nCancelled\n")
