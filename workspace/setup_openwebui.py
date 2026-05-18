import os

def setup_openwebui():
    print("==================================================")
    print(" 🛠️  OpenWebUI Integration for Degreefyd")
    print("==================================================")
    
    print("\n1. [HERMES SIDE] API Server is already ENABLED.")
    print("   - Port: 8080")
    print("   - Key:  degreefyd-secret-key")
    
    print("\n2. [ACTION REQUIRED] Run this command in your WSL/VPS terminal:")
    print("   (I cannot run docker from inside this agent)")
    print("-" * 50)
    print("docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway --name open-webui ghcr.io/open-webui/open-webui:main")
    print("-" * 50)
    
    print("\n3. [LOGIN DETAILS]")
    print("   - Open: http://localhost:3000 (Local) or http://vps-ip:3000 (VPS)")
    print("   - The first account you create will be the ADMIN.")
    
    print("\n4. [CONNECTION SETTINGS]")
    print("   Once logged into OpenWebUI:")
    print("   - Go to Settings > Connections")
    print("   - Add OpenAI API connection")
    print("   - Base URL: http://host.docker.internal:8080/v1")
    print("   - API Key:  degreefyd-secret-key")
    print("\n✅ Setup prepared. Your team can now create their own IDs and Passwords.")

if __name__ == "__main__":
    setup_openwebui()
