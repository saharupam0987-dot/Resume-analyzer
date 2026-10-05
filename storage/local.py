import os
import uuid
from pathlib import Path
from typing import BinaryIO, Union


class LocalFileStorage:
    """Local file storage abstraction.
    Designed with an interchangeable interface for future S3/cloud storage migration.
    """

    def __init__(self, base_dir: Union[str, Path] = None):
        if base_dir is None:
            env_dir = os.getenv("STORAGE_DIR")
            if env_dir:
                base_dir = Path(env_dir)
            else:
                # Default to project_root / uploads
                base_dir = Path(__file__).resolve().parent.parent / "uploads"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_content: Union[bytes, BinaryIO], original_filename: str) -> str:
        """Save a file into local storage and return its absolute path.

        Args:
            file_content: Raw bytes or a file-like binary stream.
            original_filename: Original name of the uploaded file.

        Returns:
            Absolute path string to the saved file.
        """
        clean_name = Path(original_filename).name
        unique_prefix = uuid.uuid4().hex[:8]
        safe_filename = f"{unique_prefix}_{clean_name}"
        target_path = self.base_dir / safe_filename

        if isinstance(file_content, (bytes, bytearray)):
            with open(target_path, "wb") as f:
                f.write(file_content)
        else:
            with open(target_path, "wb") as f:
                f.write(file_content.read())

        return str(target_path.resolve())

    def get_file_path(self, filename_or_path: str) -> str:
        """Get the absolute path of a stored file."""
        path = Path(filename_or_path)
        if path.is_absolute():
            return str(path)
        return str((self.base_dir / filename_or_path).resolve())

    def file_exists(self, filename_or_path: str) -> bool:
        """Check if a file exists in storage."""
        path = Path(self.get_file_path(filename_or_path))
        return path.exists() and path.is_file()

    def delete_file(self, filename_or_path: str) -> bool:
        """Safely delete a stored file if it exists."""
        try:
            path = Path(self.get_file_path(filename_or_path))
            if path.exists() and path.is_file():
                path.unlink()
                return True
            return False
        except Exception:
            return False


# Global default storage singleton
default_storage = LocalFileStorage()
