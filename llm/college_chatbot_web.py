#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import csv
import re
import urllib.parse

class CollegeChatbot:
    def __init__(self, csv_path):
        self.colleges = self.load_data(csv_path)
        
    def load_data(self, csv_path):
        colleges = []
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                colleges.append({
                    'name': row.get('Institution Name_college', ''),
                    'state': row.get('State of Institution', ''),
                    'grad_rate': self.safe_float(row.get('Bachelor\'s Degree Graduation Rate Bachelor Degree Within 6 Years - Total')),
                    'net_price': self.safe_float(row.get('Average Net Price After Grants, 2020-21')),
                    'earnings': self.safe_float(row.get('Median Earnings of Students Working and Not Enrolled 10 Years After Entry')),
                    'gap': self.safe_float(row.get('Affordability Gap (net price minus income earned working 10 hrs at min wage)'))
                })
        return [c for c in colleges if any([c['grad_rate'], c['net_price'], c['earnings']])]
    
    def safe_float(self, value):
        try:
            return float(value) if value and value.strip() and value != '.' else None
        except:
            return None
    
    def find_college(self, name):
        name_lower = name.lower()
        matches = [c for c in self.colleges if name_lower in c['name'].lower()]
        return matches[0] if matches else None
    
    def get_top_colleges(self, metric, n=5, reverse=True):
        filtered = [c for c in self.colleges if c[metric] is not None]
        return sorted(filtered, key=lambda x: x[metric], reverse=reverse)[:n]
    
    def respond(self, question):
        q = question.lower()
        
        if 'tell me about' in q:
            college_name = re.search(r'about (.+)', q)
            if college_name:
                college = self.find_college(college_name.group(1))
                if college:
                    parts = [f"{college['name']} ({college['state']})"]
                    if college['grad_rate']: parts.append(f"Graduation Rate: {college['grad_rate']:.1f}%")
                    if college['net_price']: parts.append(f"Net Price: ${college['net_price']:,.0f}")
                    if college['earnings']: parts.append(f"Earnings: ${college['earnings']:,.0f}")
                    return "\n".join(parts)
                return "College not found."
        
        if 'best' in q and 'graduation' in q:
            top = self.get_top_colleges('grad_rate', 3)
            return "Top colleges by graduation rate:\n" + "\n".join([f"{i+1}. {c['name']} ({c['state']}) - {c['grad_rate']:.1f}%" for i, c in enumerate(top)])
        
        if 'cheapest' in q or 'affordable' in q:
            top = self.get_top_colleges('net_price', 3, False)
            return "Most affordable colleges:\n" + "\n".join([f"{i+1}. {c['name']} ({c['state']}) - ${c['net_price']:,.0f}" for i, c in enumerate(top)])
        
        if 'highest earning' in q:
            top = self.get_top_colleges('earnings', 3)
            return "Colleges with highest earnings:\n" + "\n".join([f"{i+1}. {c['name']} ({c['state']}) - ${c['earnings']:,.0f}" for i, c in enumerate(top)])
        
        if 'best value' in q:
            top = self.get_top_colleges('gap', 3, False)
            return "Best value colleges:\n" + "\n".join([f"{i+1}. {c['name']} ({c['state']}) - ${c['gap']:,.0f} gap" for i, c in enumerate(top)])
        
        return "Try asking: 'What are the best colleges by graduation rate?' or 'Tell me about Harvard'"

class ChatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = '''<!DOCTYPE html>
<html><head><title>College Chatbot</title></head>
<body style="font-family:Arial;max-width:800px;margin:50px auto;padding:20px">
<h1>College Comparison Chatbot</h1>
<div id="chat" style="height:400px;border:1px solid #ccc;padding:10px;overflow-y:scroll;margin:20px 0"></div>
<input type="text" id="input" placeholder="Ask about colleges..." style="width:70%;padding:10px">
<button onclick="send()" style="padding:10px 20px">Send</button>
<script>
function send(){
    const input = document.getElementById('input');
    const chat = document.getElementById('chat');
    const question = input.value;
    if(!question) return;
    
    chat.innerHTML += '<div><b>You:</b> ' + question + '</div>';
    input.value = '';
    
    fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({question: question})
    })
    .then(r => r.json())
    .then(data => {
        chat.innerHTML += '<div style="margin:10px 0;padding:10px;background:#f0f0f0"><b>Bot:</b><br>' + data.response.replace(/\\n/g, '<br>') + '</div>';
        chat.scrollTop = chat.scrollHeight;
    });
}
document.getElementById('input').addEventListener('keypress', function(e){
    if(e.key === 'Enter') send();
});
</script>
</body></html>'''
            self.wfile.write(html.encode())
    
    def do_POST(self):
        if self.path == '/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            response = bot.respond(data['question'])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'response': response}).encode())

bot = CollegeChatbot('../fronted/data/merged_clean.csv')

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8000), ChatHandler)
    print("College Chatbot running at http://localhost:8000")
    server.serve_forever()