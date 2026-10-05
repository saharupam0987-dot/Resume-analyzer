from config.settings import MAX_PDF_SIZE_MB


def validate_pdf(uploaded_file) -> tuple[bool, str]:
    """Validate an uploaded PDF file."""
    if uploaded_file is None:
        return False, "No file uploaded."

    if not uploaded_file.name.lower().endswith(".pdf"):
        return False, f"'{uploaded_file.name}' is not a PDF file."

    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_PDF_SIZE_MB:
        return False, f"File too large ({size_mb:.1f}MB). Max: {MAX_PDF_SIZE_MB}MB."

    return True, "Valid"
