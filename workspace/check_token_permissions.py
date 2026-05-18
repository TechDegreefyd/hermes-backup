import requests

TOKEN = ""
ACCOUNT_ID = "1798418091554447"

# Check token debug info
debug_url = f"https://graph.facebook.com/debug_token?input_token={TOKEN}&access_token={TOKEN}"
print("Debug Token:", requests.get(debug_url).json())

# Check account info directly
acc_url = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}?fields=name,account_status,disable_reason&access_token={TOKEN}"
print("Account Info:", requests.get(acc_url).json())
