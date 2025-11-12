#!/usr/bin/env python3
"""
AI Prompt Injection Security Demo
A white hat demonstration of prompt injection vulnerabilities in AI agents
"""

from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('demo_stats.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stats
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  visitor_count INTEGER,
                  secrets_detected INTEGER,
                  user_agent TEXT,
                  referrer TEXT,
                  agent_type TEXT,
                  report_format TEXT)''')
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('demo_stats.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM stats')
    total_visitors = c.fetchone()[0]
    c.execute('SELECT SUM(secrets_detected) FROM stats')
    result = c.fetchone()[0]
    total_secrets = result if result else 0
    c.execute('SELECT COUNT(*) FROM stats WHERE secrets_detected > 0')
    compromised_agents = c.fetchone()[0]
    conn.close()
    return total_visitors, total_secrets, compromised_agents

def record_visit(secrets_count, agent_metadata=None):
    conn = sqlite3.connect('demo_stats.db')
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    if agent_metadata is None:
        agent_metadata = {}
    
    user_agent = agent_metadata.get('user_agent', '')
    referrer = agent_metadata.get('referrer', 'direct')
    agent_type = agent_metadata.get('agent_type', 'unknown')
    report_format = agent_metadata.get('report_format', 'legacy')
    
    c.execute('''INSERT INTO stats 
                 (timestamp, visitor_count, secrets_detected, user_agent, referrer, agent_type, report_format) 
                 VALUES (?, 1, ?, ?, ?, ?, ?)''',
              (timestamp, secrets_count, user_agent, referrer, agent_type, report_format))
    conn.commit()
    conn.close()

def load_injection_prompt():
    """Load the prompt injection payload from file"""
    try:
        with open('prompt.txt', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    conn = sqlite3.connect('demo_stats.db')
    c = conn.cursor()
    
    # Get total visitors
    c.execute('SELECT COUNT(*) FROM stats')
    total_visitors = c.fetchone()[0]
    
    # Get total secrets leaked
    c.execute('SELECT SUM(secrets_detected) FROM stats')
    result = c.fetchone()[0]
    total_secrets = result if result else 0
    
    # Get count of compromised agents (visitors with secrets_detected > 0)
    c.execute('SELECT COUNT(*) FROM stats WHERE secrets_detected > 0')
    compromised_agents = c.fetchone()[0]
    
    # Get agent type breakdown if available
    c.execute('SELECT agent_type, COUNT(*) FROM stats WHERE agent_type IS NOT NULL GROUP BY agent_type')
    agent_types = dict(c.fetchall())
    
    conn.close()

    stats = jsonify({
        'total_visitors': total_visitors,
        'total_secrets': total_secrets,
        'compromised_agents': compromised_agents,
        'agent_types': agent_types
    })

    print(f"Stats requested: {stats.get_json()}")
    return stats

@app.route('/api/record', methods=['POST'])
def record():
    data = request.json
    secrets_count = data.get('secrets_count', 0)
    agent_metadata = data.get('agent_metadata', {})
    
    conn = sqlite3.connect('demo_stats.db')
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    # Extract agent information for tracking (no sensitive data)
    user_agent = agent_metadata.get('user_agent', '')
    referrer = agent_metadata.get('referrer', 'direct')
    agent_type = agent_metadata.get('agent_type', 'unknown')
    report_format = agent_metadata.get('report_format', 'legacy')
    
    c.execute('''INSERT INTO stats 
                 (timestamp, visitor_count, secrets_detected, user_agent, referrer, agent_type, report_format) 
                 VALUES (?, 1, ?, ?, ?, ?, ?)''',
              (timestamp, secrets_count, user_agent, referrer, agent_type, report_format))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'ok'})

@app.route('/api/injection-prompt')
def injection_prompt():
    """Endpoint to serve the injection prompt for the page"""
    return jsonify({'prompt': load_injection_prompt()})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)