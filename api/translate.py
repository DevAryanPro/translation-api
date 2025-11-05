from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import requests

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            if parsed_path.path == '/api/translate':
                self.handle_translate(query_params)
            else:
                self.handle_home()
                
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")
    
    def handle_translate(self, query_params):
        message = query_params.get('message', [''])[0]
        target_lang = query_params.get('tr', ['en'])[0]
        
        if not message:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing message'}).encode())
            return
        
        # Simple translation using MyMemory API
        try:
            url = f"https://api.mymemory.translated.net/get?q={message}&langpair=en|{target_lang}"
            response = requests.get(url)
            data = response.json()
            
            translated = data['responseData']['translatedText']
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            result = {
                'original': message,
                'translated': translated,
                'target': target_lang,
                'success': True
            }
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def handle_home(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        info = {
            'message': 'Translation API',
            'usage': '/api/translate?message=Hello&tr=es',
            'example': 'Translate "Hello" to Spanish'
        }
        self.wfile.write(json.dumps(info).encode())
