#!/usr/bin/env python3
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Splash Screen for VDV463 Validator UI

Displays a splash screen at application startup with logo and version information.
Uses PySide6 for cross-platform compatibility.
"""

import sys
from pathlib import Path

from i18n import t
from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen


def get_base_path() -> Path:
    """
    Get the base path for resources (schemas, rules, media).
    """
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
        return base
    else:
        return Path(__file__).parent.parent


BASE_PATH = get_base_path()


def get_validator_version() -> str:
    """Extract version from pyproject.toml or validator."""
    try:
        pyproject_path = BASE_PATH / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("version"):
                        return line.split("=")[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return "1.0.0"


class CustomSplashScreen(QSplashScreen):
    """
    Custom splash screen with PySide6.
    """

    def __init__(self, timeout_ms: int = 2500):
        pixmap = QPixmap(500, 350)
        pixmap.fill(QColor("#2c3e50"))
        super().__init__(pixmap)

        self.timeout_ms = timeout_ms
        self.loading_dots = 0
        self.version = get_validator_version()

        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self._draw_splash()

        if timeout_ms > 0:
            self.close_timer = QTimer()
            self.close_timer.timeout.connect(self.close)
            self.close_timer.setSingleShot(True)
            self.close_timer.start(timeout_ms)

        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._update_animation)
        self.anim_timer.start(400)

    def _draw_splash(self) -> None:
        pixmap = QPixmap(500, 350)
        pixmap.fill(QColor("#2c3e50"))
        painter = QPainter(pixmap)

        logo_path = BASE_PATH / "media" / "logo.png"
        y = 30

        if logo_path.exists():
            logo = QPixmap(str(logo_path))
            if not logo.isNull():
                logo = logo.scaledToWidth(120, Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap((500 - logo.width()) // 2, y, logo)
                y += logo.height() + 20

        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("white"))
        painter.drawText(QRect(0, y, 500, 40), Qt.AlignmentFlag.AlignCenter, "VDV463 JSON Validator")
        y += 45

        subtitle_font = QFont("Arial", 10)
        painter.setFont(subtitle_font)
        painter.setPen(QColor("#bdc3c7"))
        painter.drawText(QRect(0, y, 500, 30), Qt.AlignmentFlag.AlignCenter, t("app_subtitle"))
        y += 40

        version_font = QFont("Arial", 11)
        painter.setFont(version_font)
        painter.setPen(QColor("#ecf0f1"))
        painter.drawText(QRect(0, y, 500, 30), Qt.AlignmentFlag.AlignCenter, f"Version {self.version}")
        y += 35

        loading_font = QFont("Arial", 9)
        painter.setFont(loading_font)
        painter.setPen(QColor("#95a5a6"))
        painter.drawText(QRect(0, y, 500, 30), Qt.AlignmentFlag.AlignCenter, f"Loading{'.' * self.loading_dots}")

        painter.end()
        self.setPixmap(pixmap)

    def _update_animation(self) -> None:
        self.loading_dots = (self.loading_dots + 1) % 4
        self._draw_splash()

    def closeEvent(self, event) -> None:
        self.anim_timer.stop()
        if hasattr(self, 'close_timer'):
            self.close_timer.stop()
        super().closeEvent(event)


class SplashScreen:
    """Wrapper for backward compatibility."""

    def __init__(self, master=None, timeout_ms: int = 2500):
        self.timeout_ms = timeout_ms
        self.splash = None

    def show(self) -> None:
        if self.splash is None:
            self.splash = CustomSplashScreen(self.timeout_ms)
            self.splash.show()

    def close(self) -> None:
        if self.splash:
            self.splash.close()

    def update(self) -> None:
        QApplication.processEvents()
