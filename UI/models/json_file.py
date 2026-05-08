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

"""JSONFile model for managing loaded JSON files."""

import json
from pathlib import Path

from vdv463_validator import ValidationResult


class JSONFile:
    """Represents a loaded JSON file."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.content: str | None = None
        self.data: dict | None = None
        self.modified: bool = False
        self.validation_result: ValidationResult | None = None

        self.load()

    def load(self) -> None:
        """Load file content."""
        try:
            with open(self.filepath, encoding="utf-8") as f:
                self.content = f.read()
                self.data = json.loads(self.content)
        except Exception as e:
            raise OSError(f"Failed to load {self.filepath}: {e}") from e

    def save(self, filepath: Path | None = None) -> None:
        """Save file content."""
        target = filepath or self.filepath
        with open(target, "w", encoding="utf-8") as f:
            f.write(self.content)  # type: ignore[arg-type]
        self.modified = False
        if filepath:
            self.filepath = filepath

    def get_display_name(self) -> str:
        """Get display name for UI."""
        name = self.filepath.name
        if self.modified:
            name += " *"
        return name
