import codecs
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.services.exceptions import FileTooLargeError, InvalidFileError, StorageError

ALLOWED_EXTENSIONS = {".pdf", ".md"}
CHUNK_SIZE = 1024 * 1024
PDF_SIGNATURE = b"%PDF-"


def get_extension(filename: str | None) -> str:
    extension = Path(filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise InvalidFileError("Only PDF and Markdown files are supported")
    return extension


def get_upload_path(document_id: str, extension: str) -> Path:
    return get_settings().UPLOAD_DIR / f"{document_id}{extension}"


async def save_upload(file: UploadFile, document_id: str) -> Path:
    settings = get_settings()
    extension = get_extension(file.filename)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = get_upload_path(document_id, extension)
    decoder = codecs.getincrementaldecoder("utf-8")()
    size = 0

    try:
        with open(path, "wb") as f:
            while chunk := await file.read(CHUNK_SIZE):
                if size == 0 and extension == ".pdf" and not chunk.startswith(PDF_SIGNATURE):
                    raise InvalidFileError("File is not a valid PDF")
                size += len(chunk)
                if size > settings.MAX_UPLOAD_SIZE:
                    raise FileTooLargeError("File is too large")
                if extension == ".md":
                    decoder.decode(chunk)
                f.write(chunk)
            if size == 0:
                raise InvalidFileError("File is empty")
            if extension == ".md":
                decoder.decode(b"", final=True)
    except UnicodeDecodeError:
        path.unlink(missing_ok=True)
        raise InvalidFileError("Markdown file must be UTF-8 text") from None
    except StorageError:
        path.unlink(missing_ok=True)
        raise

    return path
