import os
import json
import yaml
import pandas as pd
from pypdf import PdfReader
from fastapi import UploadFile
from loguru import logger
from app.core.config import get_settings

settings = get_settings()


class DocumentService:
    """
    Handles document validation and text extraction
    for all supported file formats.
    Supported: PDF, TXT, CSV, Excel, JSON, YAML
    """

    def __init__(self):
        self.allowed_extensions = settings.get_allowed_extensions()
        self.max_file_size_bytes = (
            settings.max_file_size_mb * 1024 * 1024
        )
        logger.info(
            f"DocumentService initialized. "
            f"Allowed types: {self.allowed_extensions}"
        )

    # ─────────────────────────────────────────
    # PUBLIC METHOD — called by endpoints.py
    # ─────────────────────────────────────────

    async def validate_and_extract(
        self, file: UploadFile
    ) -> dict:
        """
        Main entry point.
        Validates the file then extracts text.
        Returns a dictionary with extracted content.
        """
        logger.info(f"Processing file: {file.filename}")

        # Step 1 — Validate file extension
        validation_result = self._validate_extension(
            file.filename
        )
        if not validation_result["valid"]:
            return validation_result

        # Step 2 — Read file contents into memory
        contents = await file.read()

        # Step 3 — Validate file size
        size_result = self._validate_size(
            contents, file.filename
        )
        if not size_result["valid"]:
            return size_result

        # Step 4 — Extract text based on file type
        file_extension = self._get_extension(file.filename)
        extract_result = self._extract_text(
            contents, file_extension, file.filename
        )

        return extract_result

    # ─────────────────────────────────────────
    # VALIDATION METHODS
    # ─────────────────────────────────────────

    def _validate_extension(self, filename: str) -> dict:
        """Check if file extension is allowed."""
        extension = self._get_extension(filename)

        if extension not in self.allowed_extensions:
            logger.warning(
                f"Rejected file: {filename}. "
                f"Extension '{extension}' not allowed."
            )
            return {
                "valid": False,
                "status": "error",
                "filename": filename,
                "message": (
                    f"File type '{extension}' is not supported. "
                    f"Allowed types: "
                    f"{', '.join(self.allowed_extensions)}"
                )
            }

        logger.info(
            f"Extension valid: {extension} for {filename}"
        )
        return {"valid": True}

    def _validate_size(
        self, contents: bytes, filename: str
    ) -> dict:
        """Check if file size is within allowed limit."""
        size_bytes = len(contents)
        size_kb = round(size_bytes / 1024, 2)
        size_mb = round(size_bytes / (1024 * 1024), 2)

        if size_bytes > self.max_file_size_bytes:
            logger.warning(
                f"Rejected file: {filename}. "
                f"Size {size_mb}MB exceeds limit of "
                f"{settings.max_file_size_mb}MB."
            )
            return {
                "valid": False,
                "status": "error",
                "filename": filename,
                "message": (
                    f"File size {size_mb}MB exceeds maximum "
                    f"allowed size of "
                    f"{settings.max_file_size_mb}MB."
                )
            }

        logger.info(
            f"Size valid: {size_kb}KB for {filename}"
        )
        return {"valid": True, "size_kb": size_kb}

    # ─────────────────────────────────────────
    # EXTRACTION METHODS
    # ─────────────────────────────────────────

    def _extract_text(
        self,
        contents: bytes,
        extension: str,
        filename: str
    ) -> dict:
        """Route to the correct extractor based on extension."""
        extractors = {
            "pdf":  self._extract_pdf,
            "txt":  self._extract_txt,
            "csv":  self._extract_csv,
            "xlsx": self._extract_excel,
            "json": self._extract_json,
            "yaml": self._extract_yaml,
            "yml":  self._extract_yaml,
        }

        extractor = extractors.get(extension)
        if not extractor:
            return {
                "valid": False,
                "status": "error",
                "filename": filename,
                "message": f"No extractor found for {extension}"
            }

        try:
            text = extractor(contents)
            size_kb = round(len(contents) / 1024, 2)

            if not text or len(text.strip()) == 0:
                return {
                    "valid": False,
                    "status": "error",
                    "filename": filename,
                    "message": (
                        "No text could be extracted from "
                        "this file. It may be empty or "
                        "image-based."
                    )
                }

            logger.info(
                f"Extracted {len(text)} characters "
                f"from {filename}"
            )
            return {
                "valid": True,
                "status": "success",
                "filename": filename,
                "file_type": extension,
                "content": text,
                "size_kb": size_kb,
                "char_count": len(text),
                "message": (
                    f"Successfully extracted "
                    f"{len(text)} characters."
                )
            }

        except Exception as e:
            logger.error(
                f"Extraction failed for {filename}: {str(e)}"
            )
            return {
                "valid": False,
                "status": "error",
                "filename": filename,
                "message": (
                    f"Failed to extract text: {str(e)}"
                )
            }

    def _extract_pdf(self, contents: bytes) -> str:
        """Extract text from PDF file."""
        import io
        reader = PdfReader(io.BytesIO(contents))
        text = ""
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page_text
        return text.strip()

    def _extract_txt(self, contents: bytes) -> str:
        """Extract text from TXT file."""
        return contents.decode("utf-8", errors="ignore").strip()

    def _extract_csv(self, contents: bytes) -> str:
        """Extract text from CSV file."""
        import io
        df = pd.read_csv(io.BytesIO(contents))
        return df.to_string(index=False)

    def _extract_excel(self, contents: bytes) -> str:
        """Extract text from Excel file."""
        import io
        df = pd.read_excel(io.BytesIO(contents))
        return df.to_string(index=False)

    def _extract_json(self, contents: bytes) -> str:
        """Extract text from JSON file."""
        data = json.loads(contents.decode("utf-8"))
        return json.dumps(data, indent=2)

    def _extract_yaml(self, contents: bytes) -> str:
        """Extract text from YAML file."""
        data = yaml.safe_load(contents.decode("utf-8"))
        return yaml.dump(data, default_flow_style=False)

    # ─────────────────────────────────────────
    # HELPER METHODS
    # ─────────────────────────────────────────

    def _get_extension(self, filename: str) -> str:
        """Extract and return lowercase file extension."""
        return filename.rsplit(".", 1)[-1].lower()

    def save_uploaded_file(
        self, contents: bytes, filename: str
    ) -> str:
        """Save uploaded file to uploads directory."""
        os.makedirs(settings.upload_dir, exist_ok=True)
        file_path = os.path.join(settings.upload_dir, filename)

        with open(file_path, "wb") as f:
            f.write(contents)

        logger.info(f"File saved to: {file_path}")
        return file_path