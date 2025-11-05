from flask import Flask, request, jsonify
import requests
import json
from googletrans import Translator
import time
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

class TranslationAPI:
    def __init__(self):
        self.supported_languages = {
            # ... (same as above)
            'hi': 'Hindi', 'tr': 'Turkish', 'ja': 'Japanese', 'ko': 'Korean',
            'ar': 'Arabic', 'fr': 'French', 'de': 'German', 'it': 'Italian',
            'pt': 'Portuguese', 'ru': 'Russian', 'zh': 'Chinese'
        }
    
    def translate(self, text, target_lang):
        """Enhanced translation with multiple fallbacks"""
        methods = [self._translate_google, self._translate_libre]
        
        for method in methods:
            try:
                result = method(text, target_lang)
                if result and result.strip():
                    return result
            except Exception as e:
                logging.warning(f"Translation method {method.__name__} failed: {e}")
                continue
        
        return None
    
    def _translate_google(self, text, dest_lang):
        """Google Translate with retry logic"""
        for attempt in range(3):
            try:
                translator = Translator()
                translation = translator.translate(text, dest=dest_lang)
                return translation.text
            except Exception as e:
                if attempt == 2:  # Last attempt
                    raise e
                time.sleep(0.5)
        return None
    
    def _translate_libre(self, text, dest_lang):
        """LibreTranslate fallback"""
        try:
            url = "https://libretranslate.de/translate"
            payload = {
                "q": text,
                "source": "auto",
                "target": dest_lang,
                "format": "text"
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json().get("translatedText")
            return None
        except:
            return None

# Initialize translator
translator_api = TranslationAPI()

@app.route('/api/translate', methods=['GET', 'POST'])
def translate_endpoint():
    """Enhanced translation endpoint"""
    try:
        # Support both GET and POST
        if request.method == 'POST':
            data = request.get_json() or {}
            message = data.get('message', '')
            target_lang = data.get('tr', 'en')
        else:
            message = request.args.get('message', '')
            target_lang = request.args.get('tr', 'en')
        
        # Validate input
        if not message.strip():
            return jsonify({
                'error': 'Message cannot be empty',
                'example': '/api/translate?message=Hello World&tr=hi'
            }), 400
        
        if target_lang not in translator_api.supported_languages:
            return jsonify({
                'error': f'Unsupported language: {target_lang}',
                'supported_languages': list(translator_api.supported_languages.keys())
            }), 400
        
        # Handle large texts by chunking
        chunk_size = 3500
        chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]
        
        translated_chunks = []
        for chunk in chunks:
            translated = translator_api.translate(chunk, target_lang)
            if translated:
                translated_chunks.append(translated)
            else:
                return jsonify({
                    'error': 'Translation service temporarily unavailable'
                }), 503
            time.sleep(0.2)  # Rate limiting
        
        final_translation = ' '.join(translated_chunks)
        
        return jsonify({
            'success': True,
            'original': message,
            'translated': final_translation,
            'target_language': translator_api.supported_languages[target_lang],
            'target_code': target_lang,
            'length': len(message)
        })
        
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

# Same other endpoints as previous version...
@app.route('/api/languages')
def languages():
    return jsonify(translator_api.supported_languages)

def handler(request=None, context=None):
    return app
