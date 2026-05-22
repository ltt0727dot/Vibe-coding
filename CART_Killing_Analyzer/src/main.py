"""CAR-T 杀伤分析工具 — 程序入口"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from gui import MainWindow


def main():
    window = MainWindow()
    window.run()


if __name__ == "__main__":
    main()
