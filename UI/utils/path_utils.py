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

"""Path and resource utilities for the VDV463 Validator UI."""

import sys
from pathlib import Path


def get_base_path() -> Path:
    """
    Get the base path for resources (schemas, rules, media).
    Works correctly for both:
    - Development: Returns project root (parent of UI folder)
    - PyInstaller bundle: Returns _MEIPASS or executable directory
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable (PyInstaller)
        # sys._MEIPASS points to the temp folder where PyInstaller extracts files
        # For --onedir mode, resources are in _internal next to the exe
        base = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(
            sys.executable).parent  # type: ignore[attr-defined]

        # Check if we're in _internal (onedir mode)
        if (base / 'schemas').exists():
            return base
        # Check parent for onedir mode where exe is outside _internal
        if (base.parent / '_internal' / 'schemas').exists():
            return base.parent / '_internal'
        # Fallback: check next to executable
        exe_dir = Path(sys.executable).parent
        if (exe_dir / 'schemas').exists():
            return exe_dir
        if (exe_dir / '_internal' / 'schemas').exists():
            return exe_dir / '_internal'
        return base
    else:
        # Running as script - project root is parent of UI folder
        return Path(__file__).parent.parent.parent
