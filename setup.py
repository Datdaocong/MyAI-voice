"""Project bootstrap helpers."""

from pathlib import Path


if __name__ == "__main__":
    Path("temp_audio").mkdir(exist_ok=True)
    print("Created temp_audio directory.")
