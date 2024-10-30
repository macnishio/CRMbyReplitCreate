import logging
import re
from typing import Union, Optional, Tuple
from flask import current_app

def analyze_iso2022jp_text(text: bytes) -> bool:
    """
    Analyze if text contains ISO-2022-JP markers and validate content
    Returns True if text appears to be valid ISO-2022-JP encoded
    """
    if not text:
        current_app.logger.debug(f"Empty content received in analyze_iso2022jp_text")
        return False
        
    # Check for ISO-2022-JP escape sequences
    has_jis_marker = b'$B' in text and b'(B' in text
    current_app.logger.debug(f"ISO-2022-JP markers check: start=$B ({text.count(b'$B')}), end=(B ({text.count(b'(B')})")
    
    # Additional validation - check if markers are properly paired
    if has_jis_marker:
        # Count occurrences of start/end markers
        start_markers = text.count(b'$B')
        end_markers = text.count(b'(B')
        
        current_app.logger.debug(f"ISO-2022-JP marker count: start={start_markers}, end={end_markers}")
        
        # Markers should be roughly balanced (allowing for some malformed content)
        if abs(start_markers - end_markers) > start_markers // 2:
            current_app.logger.debug("ISO-2022-JP markers are not properly balanced")
            return False
            
        # Check if content between markers looks valid
        parts = text.split(b'$B')
        for i, part in enumerate(parts[1:], 1):  # Skip first part before marker
            if b'(B' in part:
                jis_content = part.split(b'(B')[0]
                valid_bytes = sum(0x21 <= b <= 0x7E for b in jis_content)
                validity_ratio = valid_bytes / len(jis_content) if jis_content else 0
                current_app.logger.debug(f"Part {i} validity check: {validity_ratio:.2%} valid bytes")
                if validity_ratio < 0.7:  # At least 70% should be valid
                    current_app.logger.debug(f"Part {i} failed validity check")
                    return False
                    
        current_app.logger.debug("ISO-2022-JP content validation successful")
        return True
    return False

def convert_encoding(content: Union[str, bytes], default_encoding: str = 'utf-8') -> Tuple[str, Optional[str]]:
    """
    Convert content to proper encoding with Japanese encoding support
    Returns tuple of (decoded_content, encoding_used)
    """
    if content is None:
        current_app.logger.debug("Received None content in convert_encoding")
        return "", None
        
    if isinstance(content, str):
        current_app.logger.debug("Content is already string type")
        return content, 'text'
        
    if not isinstance(content, bytes):
        current_app.logger.debug(f"Content is neither string nor bytes: {type(content)}")
        return str(content), 'text'
        
    current_app.logger.debug(f"Processing bytes content of length {len(content)}")
    
    # First check specifically for ISO-2022-JP content
    if analyze_iso2022jp_text(content):
        try:
            decoded = content.decode('iso-2022-jp')
            if decoded and not all(c == '?' for c in decoded):
                current_app.logger.debug("Successfully decoded using ISO-2022-JP")
                return decoded, 'iso-2022-jp'
        except UnicodeDecodeError as e:
            current_app.logger.debug(f"ISO-2022-JP decoding failed: {str(e)}")
    
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
                current_app.logger.debug(f"Successfully decoded using {encoding}")
                return decoded, encoding
        except (UnicodeDecodeError, LookupError) as e:
            current_app.logger.debug(f"Failed to decode with {encoding}: {str(e)}")
            continue
            
    # Fallback to default encoding with error handling
    try:
        current_app.logger.debug(f"Falling back to {default_encoding} with replacement")
        return content.decode(default_encoding, errors='replace'), f'{default_encoding} (with replacements)'
    except Exception as e:
        current_app.logger.error(f"Failed to decode content: {str(e)}")
        return "(デコードできないコンテンツ)", 'failed'

def clean_email_content(content: Union[str, bytes]) -> str:
    """Clean and normalize email content"""
    current_app.logger.debug(f"Cleaning content of type: {type(content)}")
    
    decoded, encoding = convert_encoding(content)
    current_app.logger.debug(f"Content decoded using {encoding}")
    
    # Remove null bytes
    cleaned = decoded.replace('\x00', '')
    current_app.logger.debug(f"Removed {len(decoded) - len(cleaned)} null bytes")
    
    # Remove ANSI escape sequences
    original_length = len(cleaned)
    cleaned = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', cleaned)
    current_app.logger.debug(f"Removed {original_length - len(cleaned)} ANSI escape sequences")
    
    # Normalize newlines
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    
    current_app.logger.debug(f"Final cleaned content length: {len(cleaned)}")
    return cleaned.strip()
