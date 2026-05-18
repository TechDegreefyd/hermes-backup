#!/bin/bash

# ============================================================================
# SEND BOTH FILES TO YOUR TELEGRAM BOT
# ============================================================================
# 
# Usage: bash /workspace/send_to_telegram.sh
#
# This sends:
# 1. START_HERE_FIRST.txt (5 min read)
# 2. HOW_IT_WORKS_VISUAL_SUMMARY.txt (15 min read)
#
# Both split into appropriate message chunks for Telegram (4096 char limit)
# ============================================================================

echo "📤 PREPARING TO SEND FILES TO TELEGRAM..."
echo ""

# Create Python script to send messages
cat > /tmp/telegram_sender.py << 'PYTHON_EOF'
import requests
import json
import sys

# Configuration
BOT_TOKEN = "@hermes_degreefyd_bot"  # Your bot
CHAT_ID = "-1002486487213"  # Admin group ID

# Read the files
try:
    with open('/workspace/START_HERE_FIRST.txt', 'r', encoding='utf-8') as f:
        file1_content = f.read()
    with open('/workspace/HOW_IT_WORKS_VISUAL_SUMMARY.txt', 'r', encoding='utf-8') as f:
        file2_content = f.read()
    print("✅ Files read successfully")
except Exception as e:
    print(f"❌ Error reading files: {e}")
    sys.exit(1)

# Split messages to handle Telegram's 4096 char limit
def split_message(text, max_length=4000):
    """Split text into chunks respecting Telegram limits"""
    chunks = []
    lines = text.split('\n')
    current_chunk = ""
    
    for line in lines:
        test_chunk = current_chunk + '\n' + line if current_chunk else line
        
        if len(test_chunk) > max_length:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk = test_chunk
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

# Split both files
file1_chunks = split_message(file1_content)
file2_chunks = split_message(file2_content)

print(f"\n📊 FILE 1: START_HERE_FIRST.txt")
print(f"   Split into {len(file1_chunks)} message(s)")
print(f"\n📊 FILE 2: HOW_IT_WORKS_VISUAL_SUMMARY.txt")
print(f"   Split into {len(file2_chunks)} message(s)")

print(f"\n📤 Total messages: {len(file1_chunks) + len(file2_chunks)}")

# Print instructions
print("\n" + "="*80)
print("📋 INSTRUCTIONS TO SEND TO TELEGRAM:")
print("="*80)

print("\n🚀 OPTION 1: Using Hermes Agent Command")
print("-" * 80)
print("Open your Telegram and send a message to @hermes_degreefyd_bot:")
print('/send_to_telegram @hermes_degreefyd_bot')

print("\n🚀 OPTION 2: Using Telegram Bot API (If you have API access)")
print("-" * 80)
print("You can use the Telegram Bot API to send:")

# Create example curl commands
for i, chunk in enumerate(file1_chunks, 1):
    chunk_escaped = json.dumps(chunk)
    print(f"\n📨 FILE 1 - Message {i}/{len(file1_chunks)}:")
    print(f"curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage \\")
    print(f'  -d "chat_id=-1002486487213&text={chunk_escaped}&parse_mode=HTML"')

for i, chunk in enumerate(file2_chunks, 1):
    chunk_escaped = json.dumps(chunk)
    print(f"\n📨 FILE 2 - Message {i}/{len(file2_chunks)}:")
    print(f"curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage \\")
    print(f'  -d "chat_id=-1002486487213&text={chunk_escaped}&parse_mode=HTML"')

print("\n" + "="*80)
print("✅ File preparation complete!")
print("="*80)

PYTHON_EOF

python /tmp/telegram_sender.py
