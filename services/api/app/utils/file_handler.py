import httpx
import os
import uuid
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Base directory for temporary files
TEMP_DIR = Path("/tmp/legaltech") if os.name != "nt" else Path(os.environ.get("TEMP", "C:\\temp")) / "legaltech"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

async def download_file(file_url: str) -> str:
    """
    Download a file from a URL and save it to a temporary location.
    Returns the absolute path to the temporary file.
    """
    temp_filename = f"{uuid.uuid4()}.tmp"
    temp_path = TEMP_DIR / temp_filename
    
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Downloading file from {file_url}")
            response = await client.get(file_url, follow_redirects=True)
            response.raise_for_status()
            
            with open(temp_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"File saved to {temp_path}")
            return str(temp_path.absolute())
        except Exception as e:
            logger.error(f"Failed to download file: {str(e)}")
            if temp_path.exists():
                temp_path.unlink()
            raise Exception(f"File download failed: {str(e)}")

def cleanup_file(file_path: str):
    """
    Delete a temporary file.
    """
    path = Path(file_path)
    if path.exists():
        try:
            path.unlink()
            logger.info(f"Cleaned up file {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")

async def decrypt_file(file_path: str, decryption_key: Optional[str] = None) -> str:
    """
    Placeholder for file decryption logic.
    In production, this would use AES-256-GCM with the provided key.
    For now, it just returns the original path.
    """
    if decryption_key:
        logger.info(f"Decrypting file {file_path} with provided key")
        # TODO: Implement AES-256-GCM decryption
    
    return file_path
