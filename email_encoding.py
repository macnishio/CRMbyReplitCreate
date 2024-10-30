import logging
import re
from typing import Union, Optional, Tuple
from flask import current_app

def analyze_iso2022jp_text(text: bytes) -> bool:
    """
    Analyze if text contains ISO-2022-JP markers and validate content.
    Returns True if text appears to be valid ISO-2022-JP encoded.
    """
    if not text:
        current_app.logger.debug("Empty content received in analyze_iso2022jp_text")
        return False

    # すべてのISO-2022-JP関連のエスケープシーケンスを定義
    ESC_SEQUENCES = {
        'ESC_JIS1978': b'\x1b$@',    # JIS X 0208-1978
        'ESC_JIS1983': b'\x1b$B',    # JIS X 0208-1983
        'ESC_ASCII': b'\x1b(B',      # ASCII
        'ESC_JISX0201': b'\x1b(J',   # JIS X 0201-1976 Roman
        'JIS_MARKER': b'$B',         # 代替JISマーカー
        'ASCII_MARKER': b'(B'        # 代替ASCIIマーカー
    }

    # マーカーの存在チェック
    markers_found = {name: count for name, seq in ESC_SEQUENCES.items() 
                    if (count := text.count(seq)) > 0}

    if markers_found:
        current_app.logger.debug(f"Found markers: {markers_found}")

        # 特定のパターンのチェック（例：$B...(B の繰り返し）
        if ESC_SEQUENCES['JIS_MARKER'] in text and ESC_SEQUENCES['ASCII_MARKER'] in text:
            marker_positions = []
            pos = 0
            while True:
                jis_pos = text.find(ESC_SEQUENCES['JIS_MARKER'], pos)
                if jis_pos == -1:
                    break
                ascii_pos = text.find(ESC_SEQUENCES['ASCII_MARKER'], jis_pos)
                if ascii_pos == -1:
                    break
                marker_positions.append((jis_pos, ascii_pos))
                pos = ascii_pos + 2

            if marker_positions:
                current_app.logger.debug(f"Found {len(marker_positions)} JIS-ASCII marker pairs")

        # 正規化の試行
        normalized = text
        if ESC_SEQUENCES['JIS_MARKER'] in text and ESC_SEQUENCES['ESC_JIS1983'] not in text:
            normalized = text.replace(ESC_SEQUENCES['JIS_MARKER'], ESC_SEQUENCES['ESC_JIS1983'])
        if ESC_SEQUENCES['ASCII_MARKER'] in text and ESC_SEQUENCES['ESC_ASCII'] not in text:
            normalized = normalized.replace(ESC_SEQUENCES['ASCII_MARKER'], ESC_SEQUENCES['ESC_ASCII'])

        try:
            # 正規化されたコンテンツでデコード試行
            decoded = normalized.decode('iso-2022-jp', errors='strict')
            if has_japanese_chars(decoded):
                current_app.logger.debug(f"Normalized decode successful: {len(decoded)} chars")
                return True
            else:
                current_app.logger.debug("Decoded but no Japanese characters found")
        except UnicodeDecodeError:
            current_app.logger.debug("Normalized decode failed, trying original content")
            try:
                # オリジナルコンテンツでデコード試行
                decoded = text.decode('iso-2022-jp', errors='strict')
                if has_japanese_chars(decoded):
                    current_app.logger.debug(f"Original decode successful: {len(decoded)} chars")
                    return True
                else:
                    current_app.logger.debug("Original decode succeeded but no Japanese characters found")
            except UnicodeDecodeError as e:
                current_app.logger.debug(f"All decode attempts failed: {str(e)}")
                return False

    current_app.logger.debug("No valid ISO-2022-JP markers found")
    return False

def has_japanese_chars(text: str) -> bool:
    """
    Check if text contains Japanese characters
    """
    ranges = [
        ('\u3040', '\u309F'),  # ひらがな
        ('\u30A0', '\u30FF'),  # カタカナ
        ('\u4E00', '\u9FFF'),  # 漢字
        ('\uFF00', '\uFFEF'),  # 全角文字
    ]
    return any(any(start <= char <= end for start, end in ranges) for char in text)

def convert_encoding(content: Union[str, bytes], default_encoding: str = 'utf-8') -> Tuple[str, Optional[str]]:
    """
    Convert content to proper encoding with Japanese encoding support.
    Returns tuple of (decoded_content, encoding_used)
    """
    if content is None:
        current_app.logger.debug("Received None content")
        return "", None

    if isinstance(content, str):
        current_app.logger.debug("Content is already string type")
        return content, 'text'

    if not isinstance(content, bytes):
        current_app.logger.debug(f"Content type is {type(content)}, converting to string")
        return str(content), 'text'

    current_app.logger.debug(f"Processing {len(content)} bytes")

    # ISO-2022-JPの検出とデコード
    if analyze_iso2022jp_text(content):
        try:
            # ESCシーケンスの正規化
            normalized = content.replace(b'$B', b'\x1b$B').replace(b'(B', b'\x1b(B')
            decoded = normalized.decode('iso-2022-jp', errors='strict')
            if has_japanese_chars(decoded):
                current_app.logger.debug("ISO-2022-JP decode successful")
                return decoded, 'iso-2022-jp'
        except UnicodeDecodeError:
            current_app.logger.debug("ISO-2022-JP decode failed, trying alternatives")

    # エンコーディング優先順位
    encodings = [
        ('cp932', 'strict'),          # Windows日本語
        ('shift_jis', 'strict'),      # Shift-JIS
        ('euc_jp', 'strict'),         # EUC-JP
        ('iso-2022-jp', 'strict'),    # ISO-2022-JP
        ('utf-8', 'strict'),          # UTF-8
        ('cp932', 'replace'),         # フォールバック
        ('shift_jis', 'replace'),
        ('euc_jp', 'replace'),
        ('iso-2022-jp', 'replace'),
        ('utf-8', 'replace')
    ]

    # 各エンコーディングを試行
    for encoding, error_handler in encodings:
        try:
            decoded = content.decode(encoding, errors=error_handler)
            if has_japanese_chars(decoded):
                current_app.logger.debug(f"Decoded using {encoding} ({error_handler})")
                return decoded, f"{encoding}{' (with replacements)' if error_handler == 'replace' else ''}"
        except (UnicodeDecodeError, LookupError):
            continue

    # 最終フォールバック
    try:
        fallback = content.decode(default_encoding, errors='replace')
        current_app.logger.debug("Using fallback encoding")
        return fallback, f'{default_encoding} (fallback)'
    except Exception as e:
        current_app.logger.error(f"Decoding failed: {str(e)}")
        return "(デコードできないコンテンツ)", 'failed'

def clean_email_content(content: Union[str, bytes]) -> str:
    current_app.logger.debug(f"Cleaning content of type: {type(content)}")

    # デコード処理
    decoded, encoding = convert_encoding(content)
    current_app.logger.debug(f"Decoded using {encoding}")

    if not decoded or encoding == 'failed':
        current_app.logger.warning("Decoding failed or empty content")
        return "(デコードできないコンテンツ)"

    # 日本語文字の存在確認を追加（オプション）
    has_japanese = any('\u3000' <= c <= '\u9fff' for c in decoded)
    if not has_japanese:
        current_app.logger.debug("No Japanese characters found in content")

    # 以下は現在の実装と同じ
    printable_chars = ''.join(char for char in decoded 
                            if ord(char) >= 32 or char in '\n\r\t')

    cleaned = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', printable_chars)
    cleaned = re.sub(r'\x1b[\$\(][BJ@]', '', cleaned)

    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    final = cleaned.strip()
    current_app.logger.debug(f"Cleaning complete: {len(final)} chars")
    return final

def debug_content(content: bytes) -> None:
    """
    Debug helper to analyze content encoding issues
    """
    print("=== Content Debug ===")
    print(f"Length: {len(content)} bytes")
    print(f"First 100 bytes (hex): {content[:100].hex()}")

    # 既知のマーカーをチェック
    markers = [
        (b'\x1b$@', "ESC$@ (JIS X 0208-1978)"),
        (b'\x1b$B', "ESC$B (JIS X 0208-1983)"),
        (b'\x1b(B', "ESC(B (ASCII)"),
        (b'\x1b(J', "ESC(J (JIS X 0201)"),
        (b'$B', "Plain $B"),
        (b'(B', "Plain (B")
    ]

    for marker, desc in markers:
        count = content.count(marker)
        if count > 0:
            print(f"Found {desc}: {count} occurrences")

    # 各エンコーディングでデコードを試行
    for encoding in ['utf-8', 'shift_jis', 'euc_jp', 'iso-2022-jp', 'cp932']:
        try:
            decoded = content.decode(encoding)
            print(f"\n{encoding} decode preview: {decoded[:100]}")
        except UnicodeDecodeError:
            print(f"{encoding} decode failed")

