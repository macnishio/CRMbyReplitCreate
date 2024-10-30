import logging
from typing import Union, Optional, Tuple

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
        
    # List of encodings to try in order of preference
    encodings = [
        'iso-2022-jp',  # JIS
        'shift_jis',    # SJIS
        'euc_jp',       # EUC-JP
        'utf-8',        # UTF-8
        'cp932'         # Microsoft's Japanese encoding
    ]
    
    # First check for ISO-2022-JP marker
    if b'$B' in content:
        try:
            return content.decode('iso-2022-jp'), 'iso-2022-jp'
        except UnicodeDecodeError:
            pass
    
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
    import re
    cleaned = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', cleaned)
    
    # Normalize newlines
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    
    return cleaned.strip()
