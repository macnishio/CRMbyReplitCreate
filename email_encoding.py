import logging
import re
from typing import Union, Tuple
from flask import current_app
import chardet
import unicodedata

def has_japanese_chars(text: str) -> bool:
    """Check if text contains Japanese characters."""
    ranges = [
        ('\u3040', '\u309F'),  # ひらがな
        ('\u30A0', '\u30FF'),  # カタカナ
        ('\u4E00', '\u9FFF'),  # 漢字
        ('\uFF00', '\uFFEF'),  # 全角文字
    ]
    return any(any(start <= char <= end for start, end in ranges) for char in text)

def convert_encoding(content: Union[str, bytes]) -> Tuple[str, str]:
    """Convert content encoding with improved detection and handling."""
    try:
        if isinstance(content, str):
            current_app.logger.debug("Content is already string type")
            return content, 'text'

        if not isinstance(content, bytes):
            current_app.logger.warning(f"Unexpected content type: {type(content)}")
            return str(content), 'str'

        encoding_attempts = [
            ('iso-2022-jp', 'strict'),
            ('utf-8', 'strict'),
            ('cp932', 'strict'),
            ('euc_jp', 'strict'),
            ('ascii', 'strict'),
            ('utf-8', 'replace'),
            ('cp932', 'replace'),
            ('iso-2022-jp', 'replace')
        ]

        detected = chardet.detect(content)
        if detected and detected['confidence'] > 0.8:
            try:
                return content.decode(detected['encoding'], errors='strict'), detected['encoding']
            except (UnicodeDecodeError, LookupError):
                current_app.logger.debug(f"Chardet detection failed for: {detected['encoding']}")

        if analyze_iso2022jp_text(content) or b"$B" in content or b"(B" in content:  # analyze_iso2022jp_textの結果に加え、$B/(B)マーカーの有無でも判定
            try:
                normalized = normalize_iso2022jp(content) # normalize関数を常に適用
                decoded = normalized.decode('iso-2022-jp', errors='strict')
                current_app.logger.debug("Successfully decoded ISO-2022-JP content")
                return decoded, 'iso-2022-jp'
            except UnicodeDecodeError:
                current_app.logger.debug("ISO-2022-JP decoding failed after normalization")

        for encoding, error_handler in encoding_attempts:
            try:
                decoded = content.decode(encoding, errors=error_handler)
                if has_japanese_chars(decoded) or all(ord(c) < 128 for c in decoded):
                    current_app.logger.debug(f"Decoded using {encoding}")
                    return decoded, encoding
            except (UnicodeDecodeError, LookupError):
                continue

        current_app.logger.warning("All decoding attempts failed, using utf-8 with replace")
        return content.decode('utf-8', errors='replace'), 'failed'

    except Exception as e:
        current_app.logger.error(f"Error in convert_encoding: {str(e)}", exc_info=True)
        return str(content), 'error'


def analyze_iso2022jp_text(content: bytes) -> bool:
    """Analyze content for ISO-2022-JP encoding markers."""
    try:
        if not isinstance(content, bytes):
            return False

        markers = {
            'ESC_JIS1983': content.count(b'\x1b$B'),
            'ESC_JIS1978': content.count(b'\x1b$@'),
            'ESC_JISX0201': content.count(b'\x1b(J'),
            'ESC_ASCII': content.count(b'\x1b(B'),
            'JIS_MARKER': content.count(b'$B'),
            'ASCII_MARKER': content.count(b'(B')
        }

        current_app.logger.debug(f"Found markers: {markers}")

        jis_ascii_pairs = min(markers['JIS_MARKER'], markers['ASCII_MARKER'])

        has_escape_sequences = any(markers[key] > 0 for key in ['ESC_JIS1983', 'ESC_JIS1978', 'ESC_JISX0201', 'ESC_ASCII'])
        has_marker_pairs = jis_ascii_pairs > 0

        return has_escape_sequences or has_marker_pairs

    except Exception as e:
        current_app.logger.error(f"Error in analyze_iso2022jp_text: {str(e)}", exc_info=True)
        return False

def normalize_iso2022jp(content: bytes) -> bytes:
    """Normalize ISO-2022-JP encoded content."""
    try:
        if not isinstance(content, bytes):
            return content

        normalized = content

        if b'$B' in content and b'\x1b$B' not in content:
            normalized = normalized.replace(b'$B', b'\x1b$B')
        if b'(B' in normalized and b'\x1b(B' not in normalized:
            normalized = normalized.replace(b'(B', b'\x1b(B')
        if b'(J' in normalized and b'\x1b(J' not in normalized:
            normalized = normalized.replace(b'(J', b'\x1b(J')
        if b'$@' in normalized and b'\x1b$@' not in normalized:
            normalized = normalized.replace(b'$@', b'\x1b$@')

        if normalized.endswith(b'\x1b$B') or normalized.endswith(b'\x1b(J'):
            normalized += b'\x1b(B'

        return normalized

    except Exception as e:
        current_app.logger.error(f"Error in normalize_iso2022jp: {str(e)}", exc_info=True)
        return content

def clean_email_content(content: Union[str, bytes]) -> str:
    """
    Clean and normalize email content with improved text handling

    Args:
        content: Email content as string or bytes

    Returns:
        str: Cleaned and normalized content
    """
    try:
        if not content:
            current_app.logger.debug("Empty content received")
            return ""

        # 文字列への変換（バイト列の場合）
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8', errors='replace')
                current_app.logger.debug("Converted bytes to string")
            except Exception as e:
                current_app.logger.warning(f"Error decoding bytes: {str(e)}")
                content = str(content)

        # 基本的なクリーニング
        cleaned = content

        # 改行の正規化
        cleaned = cleaned.replace('\r\n', '\n')\
                        .replace('\r', '\n')\
                        .replace('\u2028', '\n')\
                        .replace('\u2029', '\n\n') 

        # 空白文字の正規化
        cleaned = cleaned.replace('\u00A0', ' ')\
                        .replace('\u3000', ' ')\
                        .replace('\t', '    ') 

        # 制御文字とゼロ幅文字の削除
        cleaned = ''.join(
            char for char in cleaned 
            if not unicodedata.category(char).startswith(('C', 'Z'))
            and char not in ('\u200B', '\u200C', '\u200D', '\uFEFF')  # Zero-width characters
        )

        # 空行の正規化（3行以上の連続した改行を2行に）
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        # 行頭と行末の空白を削除（各行ごと）
        cleaned = '\n'.join(
            line.strip() 
            for line in cleaned.split('\n')
        )

        # 全体の前後の空白を削除
        cleaned = cleaned.strip()

        # 文字列の検証
        if not cleaned:
            current_app.logger.warning("Cleaning resulted in empty string")
            return ""

        # 日本語文字の存在確認（オプション）
        has_japanese = any('\u3040' <= c <= '\u309F' or  # ひらがな
                          '\u30A0' <= c <= '\u30FF' or  # カタカナ
                          '\u4E00' <= c <= '\u9FFF'     # 漢字
                          for c in cleaned)

        if has_japanese:
            current_app.logger.debug("Japanese characters detected in content")

        # 文字数の変化をログ
        char_diff = len(content) - len(cleaned)
        if char_diff > 0:
            current_app.logger.debug(f"Removed {char_diff} characters during cleaning")

        return cleaned

    except Exception as e:
        current_app.logger.error(
            f"Error cleaning email content: {str(e)}", 
            exc_info=True
        )
        # エラー時は元のコンテンツを安全に文字列化
        try:
            return str(content)
        except Exception as conv_error:
            current_app.logger.error(
                f"Error converting content to string: {str(conv_error)}"
            )
            return "(コンテンツのクリーニングに失敗しました)"

def remove_quoted_text(content: str) -> str:
    """
    Remove quoted text from email content

    Args:
        content: Email content

    Returns:
        str: Content with quoted text removed
    """
    try:
        # 引用パターンの定義
        quote_patterns = [
            r'(?m)^>+.*$',              # 標準的な引用 (> で始まる行)
            r'(?m)^On.*wrote:$',        # 英語の引用ヘッダー
            r'(?m)^\d{4}.*に.*様は書きました：$',  # 日本語の引用ヘッダー
            r'(?m)^-+ Original Message -+$',  # 元のメッセージ区切り
            r'(?m)^From:.*$\n.*$',      # Fromで始まる引用ヘッダー
        ]

        # パターンごとに処理
        cleaned = content
        for pattern in quote_patterns:
            cleaned = re.sub(pattern, '', cleaned)

        # 3行以上の空行を2行に
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        # 前後の空白を削除
        cleaned = cleaned.strip()

        return cleaned

    except Exception as e:
        current_app.logger.error(
            f"Error removing quoted text: {str(e)}", 
            exc_info=True
        )
        return content

def normalize_line_breaks(content: str) -> str:
    """
    Normalize line breaks in content

    Args:
        content: Text content

    Returns:
        str: Content with normalized line breaks
    """
    try:
        # 改行の正規化
        normalized = content.replace('\r\n', '\n')\
                          .replace('\r', '\n')

        # 連続した改行の正規化
        normalized = re.sub(r'\n{3,}', '\n\n', normalized)

        # 行の前後の空白を削除
        normalized = '\n'.join(
            line.strip() 
            for line in normalized.split('\n')
        )

        return normalized.strip()

    except Exception as e:
        current_app.logger.error(
            f"Error normalizing line breaks: {str(e)}", 
            exc_info=True
        )
        return content
