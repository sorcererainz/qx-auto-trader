from flask import Flask, render_template, request, jsonify
import asyncio
import time
import json
import os
import sys
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Import Quotex
try:
    from quotexpy import Quotex
    from quotexpy.utils.account_type import AccountType
    from quotexpy.utils.operation_type import OperationType
    from quotexpy.utils import asset_parse
    print("[✓] quotexpy loaded!")
except ImportError:
    print("[!] Installing quotexpy...")
    os.system("pip install git+https://github.com/cleitonleonel/pyquotex.git")
    from quotexpy import Quotex
    from quotexpy.utils.account_type import AccountType
    from quotexpy.utils.operation_type import OperationType
    from quotexpy.utils import asset_parse

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({
        'status': 'online',
        'library': 'quotexpy',
        'time': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/api/check_balance', methods=['POST'])
async def check_balance():
    """100% AUTO balance check using pyquotex"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password required'
            })
        
        print(f"[*] Connecting: {email[:20]}...")
        
        # Create Quotex client
        client = Quotex(
            email=email,
            password=password,
            headless=True
        )
        
        # Connect to Quotex WebSocket
        check_connect = await client.connect()
        
        if check_connect:
            print("[✓] Connected to Quotex!")
            
            # Switch to PRACTICE (Demo) account
            client.change_account(AccountType.PRACTICE)
            
            # Get real balance
            balance = await client.get_balance()
            print(f"[💰] Balance: ${balance}")
            
            # Close connection
            client.close()
            
            return jsonify({
                'success': True,
                'balance': f'${float(balance):,.2f}',
                'account': 'DEMO',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'auto': True
            })
        else:
            client.close()
            return jsonify({
                'success': False,
                'error': '❌ Invalid credentials or network error'
            })
            
    except Exception as e:
        print(f"[✗] Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        })

@app.route('/api/refill_demo', methods=['POST'])
async def refill_demo():
    """Refill demo balance"""
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
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
