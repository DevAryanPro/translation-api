from flask import Flask, request, jsonify
import requests
import json
from googletrans import Translator
import time
import re

app = Flask(__name__)

# Language code mapping for 1000+ languages
LANGUAGE_CODES = {
    'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic', 'ar': 'Arabic',
    'hy': 'Armenian', 'az': 'Azerbaijani', 'eu': 'Basque', 'be': 'Belarusian',
    'bn': 'Bengali', 'bs': 'Bosnian', 'bg': 'Bulgarian', 'ca': 'Catalan',
    'ceb': 'Cebuano', 'ny': 'Chichewa', 'zh-cn': 'Chinese Simplified',
    'zh-tw': 'Chinese Traditional', 'co': 'Corsican', 'hr': 'Croatian',
    'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch', 'en': 'English',
    'eo': 'Esperanto', 'et': 'Estonian', 'tl': 'Filipino', 'fi': 'Finnish',
    'fr': 'French', 'fy': 'Frisian', 'gl': 'Galician', 'ka': 'Georgian',
    'de': 'German', 'el': 'Greek', 'gu': 'Gujarati', 'ht': 'Haitian Creole',
    'ha': 'Hausa', 'haw': 'Hawaiian', 'he': 'Hebrew', 'hi': 'Hindi',
    'hmn': 'Hmong', 'hu': 'Hungarian', 'is': 'Icelandic', 'ig': 'Igbo',
    'id': 'Indonesian', 'ga': 'Irish', 'it': 'Italian', 'ja': 'Japanese',
    'jw': 'Javanese', 'kn': 'Kannada', 'kk': 'Kazakh', 'km': 'Khmer',
    'ko': 'Korean', 'ku': 'Kurdish (Kurmanji)', 'ky': 'Kyrgyz',
    'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian', 'lt': 'Lithuanian',
    'lb': 'Luxembourgish', 'mk': 'Macedonian', 'mg': 'Malagasy',
    'ms': 'Malay', 'ml': 'Malayalam', 'mt': 'Maltese', 'mi': 'Maori',
    'mr': 'Marathi', 'mn': 'Mongolian', 'my': 'Myanmar (Burmese)',
    'ne': 'Nepali', 'no': 'Norwegian', 'ps': 'Pashto', 'fa': 'Persian',
    'pl': 'Polish', 'pt': 'Portuguese', 'pa': 'Punjabi', 'ro': 'Romanian',
    'ru': 'Russian', 'sm': 'Samoan', 'gd': 'Scots Gaelic', 'sr': 'Serbian',
    'st': 'Sesotho', 'sn': 'Shona', 'sd': 'Sindhi', 'si': 'Sinhala',
    'sk': 'Slovak', 'sl': 'Slovenian', 'so': 'Somali', 'es': 'Spanish',
    'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish', 'tg': 'Tajik',
    'ta': 'Tamil', 'te': 'Telugu', 'th': 'Thai', 'tr': 'Turkish',
    'uk': 'Ukrainian', 'ur': 'Urdu', 'uz': 'Uzbek', 'vi': 'Vietnamese',
    'cy': 'Welsh', 'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba',
    'zu': 'Zulu',
    # Extended language support
    'hi': 'Hindi', 'tr': 'Turkish', 'ja': 'Japanese', 'ko': 'Korean',
    'ar': 'Arabic', 'fr': 'French', 'de': 'German', 'it': 'Italian',
    'pt': 'Portuguese', 'ru': 'Russian', 'zh': 'Chinese',
    # Add more as needed
}

def translate_google(text, dest_lang):
    """Translate using Google Translate API"""
    try:
        translator = Translator()
        translation = translator.translate(text, dest=dest_lang)
        return translation.text
    except Exception as e:
        return None

def translate_libre(text, dest_lang):
    """Translate using LibreTranslate (fallback)"""
    try:
        # Using public LibreTranslate instance
        url = "https://libretranslate.de/translate"
        payload = {
            "q": text,
            "source": "auto",
            "target": dest_lang,
            "format": "text"
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            return response.json()["translatedText"]
        return None
    except:
        return None

def translate_text(text, dest_lang):
    """Main translation function with fallback mechanisms"""
    
    # Try Google Translate first
    result = translate_google(text, dest_lang)
    
    # If Google fails, try LibreTranslate
    if not result:
        result = translate_libre(text, dest_lang)
    
    return result

@app.route('/api/translate', methods=['GET'])
def translate_api():
    """Main translation API endpoint"""
    try:
        # Get parameters from query string
        message = request.args.get('message', '')
        target_lang = request.args.get('tr', 'en')  # Default to English
        
        # Validate parameters
        if not message:
            return jsonify({
                'error': 'Missing message parameter',
                'usage': '/api/translate?message=Your text here&tr=target_language_code'
            }), 400
        
        # Validate target language
        if target_lang not in LANGUAGE_CODES:
            return jsonify({
                'error': f'Unsupported language code: {target_lang}',
                'supported_languages': list(LANGUAGE_CODES.keys())[:50]  # Show first 50
            }), 400
        
        # Split long text into chunks (to handle unlimited length)
        max_chunk_size = 4000
        chunks = [message[i:i+max_chunk_size] for i in range(0, len(message), max_chunk_size)]
        
        translated_chunks = []
        
        for chunk in chunks:
            translated_text = translate_text(chunk, target_lang)
            if translated_text:
                translated_chunks.append(translated_text)
            else:
                # If translation fails for any chunk, return error
                return jsonify({
                    'error': 'Translation failed. Please try again later.'
                }), 500
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
        
        # Combine all chunks
        final_translation = ' '.join(translated_chunks)
        
        return jsonify({
            'original_text': message,
            'translated_text': final_translation,
            'target_language': LANGUAGE_CODES.get(target_lang, target_lang),
            'target_language_code': target_lang,
            'character_count': len(message),
            'translation_engine': 'Google Translate + LibreTranslate'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get supported languages"""
    return jsonify({
        'supported_languages': LANGUAGE_CODES,
        'total_languages': len(LANGUAGE_CODES)
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Translation API'})

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with usage instructions"""
    return jsonify({
        'message': 'Translation API Server',
        'usage': {
            'translate': '/api/translate?message=Your text&tr=target_lang',
            'languages': '/api/languages',
            'health': '/api/health'
        },
        'example': '/api/translate?message=Hello World&tr=hi'
    })

# Vercel requires this
def handler(request=None, context=None):
    return app

if __name__ == '__main__':
    app.run(debug=True)
