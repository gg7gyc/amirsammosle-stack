from flask import Flask, request, jsonify, render_template_string
import json, uuid, os
from datetime import datetime, timedelta

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html dir="rtl">
<head>
    <title>پنل VPN</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: Tahoma, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 600px; margin: auto; }
        .header {
            background: white;
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card {
            background: white;
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            margin: 5px 0;
        }
        button:hover { opacity: 0.9; }
        .user-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }
        .link-box {
            background: #f1f3f5;
            padding: 10px;
            border-radius: 5px;
            word-break: break-all;
            font-size: 12px;
            margin: 5px 0;
        }
        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            margin: 2px;
            background: #d4edda;
            color: #155724;
        }
        h2, h3 { color: #333; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 پنل VPN</h1>
            <p>ساخت و مدیریت کانفیگ</p>
        </div>
        
        <div class="card">
            <h3>➕ ساخت کاربر جدید</h3>
            <form onsubmit="createUser(event)">
                <input type="text" id="username" placeholder="نام کاربری" required>
                <input type="number" id="limit" placeholder="حجم (GB)" value="10" required>
                <input type="number" id="days" placeholder="مدت زمان (روز)" value="30" required>
                <button type="submit">ساخت کانفیگ</button>
            </form>
            <div id="result"></div>
        </div>
        
        <div class="card">
            <h3>👥 کاربران</h3>
            {% for user in users %}
            <div class="user-card">
                <strong>{{ user.username }}</strong>
                <span class="badge">{{ user.limit }}GB</span>
                <span class="badge">{{ user.expire }}</span>
                <div class="link-box">{{ user.sub_link }}</div>
                <button onclick="copyLink('{{ user.sub_link }}')">📋 کپی لینک</button>
                <a href="/delete/{{ user.id }}"><button style="background:#dc3545">🗑️ حذف</button></a>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <script>
        function createUser(e) {
            e.preventDefault();
            fetch('/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username: document.getElementById('username').value,
                    limit: document.getElementById('limit').value,
                    days: document.getElementById('days').value
                })
            })
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    document.getElementById('result').innerHTML = `
                        <div class="link-box">${d.sub_link}</div>
                        <button onclick="copyLink('${d.sub_link}')">📋 کپی</button>
                    `;
                    setTimeout(() => location.reload(), 2000);
                }
            });
        }
        
        function copyLink(link) {
            navigator.clipboard.writeText(link);
            alert('✅ کپی شد!');
        }
    </script>
</body>
</html>
"""

def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)

@app.route('/')
def index():
    users = load_users()
    return render_template_string(HTML, users=users)

@app.route('/create', methods=['POST'])
def create():
    try:
        data = request.json
        username = data['username']
        limit_gb = int(data['limit'])
        days = int(data['days'])
        
        user_uuid = str(uuid.uuid4())
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost:5000')
        
        sub_link = f"https://{railway_domain}/sub/{username}/{user_uuid}"
        
        users = load_users()
        user_data = {
            "id": len(users) + 1,
            "username": username,
            "uuid": user_uuid,
            "limit": limit_gb,
            "used": 0,
            "expire": (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d"),
            "sub_link": sub_link,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        users.append(user_data)
        save_users(users)
        
        return jsonify({"success": True, "sub_link": sub_link})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/sub/<username>/<uuid>')
def subscription(username, uuid):
    users = load_users()
    for u in users:
        if u['username'] == username and u['uuid'] == uuid:
            railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost:5000')
            sub_content = f"vless://{uuid}@{railway_domain}:443?encryption=none&security=tls&type=ws&host={railway_domain}&path=%2F#VPN-{username}\n"
            return sub_content, 200, {'Content-Type': 'text/plain'}
    return "Not Found", 404

@app.route('/delete/<int:user_id>')
def delete(user_id):
    users = load_users()
    users = [u for u in users if u['id'] != user_id]
    save_users(users)
    return "<script>alert('حذف شد'); window.location='/'</script>"

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
