import asyncio
import httpx
import uuid
from typing import Dict, Any

BASE_URL = "http://localhost:8880/api/v1"

async def main():
    username = f"test_user_{uuid.uuid4().hex[:8]}"
    password = "password123"
    
    async with httpx.AsyncClient() as client:
        # 1. Register
        print(f"1. Registering user {username}...")
        resp = await client.post(f"{BASE_URL}/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": password
        })
        if resp.status_code != 200:
            print(f"Registration failed: {resp.text}")
            return
        
        # 2. Login
        print("2. Logging in...")
        resp = await client.post(f"{BASE_URL}/auth/login", data={
            "username": username,
            "password": password
        })
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create Agent
        print("3. Creating Agent...")
        resp = await client.post(f"{BASE_URL}/agents/", json={
            "name": "Integration Test Agent",
            "description": "Agent for integration testing"
        }, headers=headers)
        if resp.status_code != 200:
            print(f"Create agent failed: {resp.text}")
            return
        agent_id = resp.json()["id"]
        
        # 4. Create API Key
        print("4. Creating API Key...")
        resp = await client.post(f"{BASE_URL}/agents/{agent_id}/api_keys", json={
            "name": f"test_key_{uuid.uuid4().hex[:4]}",
            "description": "Key for testing connection",
            "permissions": ["chat"]
        }, headers=headers)
        
        if resp.status_code != 200:
            print(f"Create API key failed: {resp.text}")
            return
            
        key_data = resp.json()
        api_key_str = key_data["api_key"]
        print(f"   Created API Key: {api_key_str}")
        
        # Save to file
        with open("generated_api_key.txt", "w") as f:
            f.write(api_key_str)
        print("   Saved to generated_api_key.txt")

if __name__ == "__main__":
    asyncio.run(main())
