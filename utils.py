import re
import base64
import quopri
from email.header import decode_header

def decode_mime_words(s, depth=0):
    if depth > 10:  # 再帰の深さに制限を設ける
        return s

    def decode_part(part):
        if part.startswith('=?'):
            try:
                decoded_parts = decode_header(part)
                return ''.join(
                    (bytes.decode(text, charset or 'utf-8', errors='replace') if isinstance(text, bytes) else text)
                    for text, charset in decoded_parts
                )
            except:
                # decode_headerに失敗した場合、手動でデコードを試みる
                match = re.match(r'=\?(.+?)\?([BQ])\?(.+?)\?=', part)
                if match:
                    charset, encoding, encoded_text = match.groups()
                    if encoding.upper() == 'B':
                        decoded = base64.b64decode(encoded_text + '==').decode(charset, errors='replace')
                    elif encoding.upper() == 'Q':
                        decoded = quopri.decodestring(encoded_text).decode(charset, errors='replace')
                    return decoded
                return part
        elif '=?' in part:
            # 部分的にエンコードされている場合、再帰的に処理
            return decode_mime_words(part, depth + 1)
        return part

    # '=?' で始まる部分を探し、デコードする
    parts = re.split(r'(=\?[^?]+\?[BQbq]\?[^?]+\?=)', s)
    decoded_parts = [decode_part(part) for part in parts]
    
    # デコードされた部分を結合
    result = ''.join(decoded_parts)
    
    # 残っているエンコード部分があれば再帰的にデコード
    if '=?' in result and result != s:
        return decode_mime_words(result, depth + 1)
    
    # UTF-8でエンコードされた16進数表現を直接デコード
    utf8_hex_pattern = r'=([0-9A-Fa-f]{2})'
    if re.search(utf8_hex_pattern, result):
        try:
            result = re.sub(utf8_hex_pattern, lambda m: bytes.fromhex(m.group(1)).decode('utf-8'), result)
        except UnicodeDecodeError:
            # 不完全なUTF-8シーケンスの場合、可能な限りデコード
            hex_bytes = re.findall(utf8_hex_pattern, result)
            decoded_chars = []
            for i in range(0, len(hex_bytes), 3):
                try:
                    char = bytes.fromhex(''.join(hex_bytes[i:i+3])).decode('utf-8')
                    decoded_chars.append(char)
                except:
                    break
            result = result.split('=')[0] + ''.join(decoded_chars)
    
    return result.strip()