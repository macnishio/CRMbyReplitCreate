import logging
import re
from typing import Union, Optional, Tuple

def analyze_iso2022jp_text(text: bytes) -> bool:
    """
    Analyze if text contains ISO-2022-JP markers and validate content
    Returns True if text appears to be valid ISO-2022-JP encoded
    """
    if not text:
        return False
        
    # Check for ISO-2022-JP escape sequences
    has_jis_marker = b'$B' in text and b'(B' in text
    
    # Additional validation - check if markers are properly paired
    if has_jis_marker:
        # Count occurrences of start/end markers
        start_markers = text.count(b'$B')
        end_markers = text.count(b'(B')
        
        # Markers should be roughly balanced (allowing for some malformed content)
        if abs(start_markers - end_markers) > start_markers // 2:
            return False
            
        # Check if content between markers looks valid
        parts = text.split(b'$B')
        for part in parts[1:]:  # Skip first part before marker
            if b'(B' in part:
                jis_content = part.split(b'(B')[0]
                # Valid JIS content should mostly be in expected byte ranges
                valid_bytes = sum(0x21 <= b <= 0x7E for b in jis_content)
                if valid_bytes < len(jis_content) * 0.7:  # At least 70% should be valid
                    return False
                    
        return True
    return False

def convert_encoding(content: Union[str, bytes], default_encoding: str = 'utf-8') -> Tuple[str, Optional[str]]:
    """
    Convert content to proper encoding with Japanese encoding support
    Returns tuple of (decoded_content, encoding_used)
    """
    if content is None:
        return "", None
        
    if isinstance(content, str):
        return content, 'text'
        
    if not isinstance(content, bytes):
        return str(content), 'text'
        
    # First check specifically for ISO-2022-JP content
    if analyze_iso2022jp_text(content):
        try:
            decoded = content.decode('iso-2022-jp')
            if decoded and not all(c == '?' for c in decoded):
                return decoded, 'iso-2022-jp'
        except UnicodeDecodeError:
            pass
    
    # List of encodings to try in order of preference
    encodings = [
        'iso-2022-jp',  # JIS
        'shift_jis',    # SJIS
        'euc_jp',       # EUC-JP
        'utf-8',        # UTF-8
        'cp932'         # Microsoft's Japanese encoding
    ]
    
    # Try each encoding
    for encoding in encodings:
        try:
            decoded = content.decode(encoding)
            # Verify decoded content is valid
            if decoded and not all(c == '?' for c in decoded):
                return decoded, encoding
        except (UnicodeDecodeError, LookupError):
            continue
            
    # Fallback to default encoding with error handling
    try:
        return content.decode(default_encoding, errors='replace'), f'{default_encoding} (with replacements)'
    except Exception as e:
        logging.error(f"Failed to decode content: {str(e)}")
        return "(デコードできないコンテンツ)", 'failed'

def clean_email_content(content: Union[str, bytes]) -> str:
    """Clean and normalize email content"""
    decoded, _ = convert_encoding(content)
    
    # Remove null bytes
    cleaned = decoded.replace('\x00', '')
    
    # Remove ANSI escape sequences
    cleaned = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', cleaned)
    
    # Normalize newlines
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    
    return cleaned.strip()
