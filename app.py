from flask import Flask, render_template, request, jsonify
import asyncio
import time
import json
import os
import sys
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ==========================================
# CORRECT IMPORT - pyquotex (NOT quotexpy)
# ==========================================
try:
    from pyquotex import Quotex
    from pyquotex.utils.account_type import AccountType
    from pyquotex.utils.operation_type import OperationType
    from pyquotex.utils import asset_parse
    print("[✓] pyquotex loaded successfully!")
except ImportError as e:
    print(f"[!] Import error: {e}")
    print("[!] Installing pyquotex from GitHub...")
    import subprocess
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", 
        "git+https://github.com/cleitonleonel/pyquotex.git"
    ])
    from pyquotex import Quotex
    from pyquotex.utils.account_type import AccountType
    from pyquotex.utils.operation_type import OperationType
    from pyquotex.utils import asset_parse
    print("[✓] pyquotex installed and loaded!")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({
        'status': 'online',
        'library': 'pyquotex',
        'time': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/api/check_balance', methods=['POST'])
async def check_balance():
    """100% AUTO balance check using pyquotex"""
    client = None
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password required'
            })
        
        print(f"\n{'='*50}")
        print(f"[*] Connecting: {email[:25]}...")
        
        # Create Quotex client with CORRECT class name
        client = Quotex(
            email=email,
            password=password,
            headless=True
        )
        
        # Connect to Quotex WebSocket
        print("[*] Establishing WebSocket connection...")
        check_connect = await client.connect()
        
        if check_connect:
            print("[✓] Connected to Quotex WebSocket!")
            
            # Switch to PRACTICE (Demo) account
            print("[*] Switching to DEMO account...")
            client.change_account(AccountType.PRACTICE)
            
            # Get real balance
            print("[*] Fetching balance...")
            balance = await client.get_balance()
            print(f"[💰] LIVE BALANCE: ${balance}")
            
            # Close connection
            client.close()
            
            return jsonify({
                'success': True,
                'balance': f'${float(balance):,.2f}',
                'account': 'DEMO',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'auto': True,
                'library': 'pyquotex'
            })
        else:
            if client:
                client.close()
            return jsonify({
                'success': False,
                'error': '❌ Login failed! Check email and password.'
            })
            
    except Exception as e:
        if client:
            try:
                client.close()
            except:
                pass
        print(f"[✗] Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        })

@app.route('/api/refill_demo', methods=['POST'])
async def refill_demo():
    """Refill demo balance to $10,000"""
    client = None
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        client = Quotex(email=email, password=password, headless=True)
        check_connect = await client.connect()
        
        if check_connect:
            client.change_account(AccountType.PRACTICE)
            await client.edit_practice_balance(10000)
            balance = await client.get_balance()
            client.close()
            
            return jsonify({
                'success': True,
                'balance': f'${float(balance):,.2f}',
                'message': 'Demo balance refilled to $10,000'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Connection failed'
            })
            
    except Exception as e:
        if client:
            try:
                client.close()
            except:
                pass
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
