from flask import Blueprint, send_file, make_response
from io import BytesIO
from email_utils import track_email_open

bp = Blueprint('tracking', __name__)

@bp.route('/pixel/<tracking_id>.png')
def pixel(tracking_id):
    # Track the email open
    track_email_open(tracking_id)
    
    # Create a 1x1 transparent pixel
    pixel = BytesIO()
    pixel.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
    pixel.seek(0)
    
    response = make_response(send_file(pixel, mimetype='image/png'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response
