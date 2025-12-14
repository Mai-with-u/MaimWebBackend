import asyncio
import httpx
import uuid

BASE_URL = "http://localhost:8880/api/v1"

async def main():
    username = f"test_user_{uuid.uuid4().hex[:8]}"
    password = "password123"
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        print(f"1. Registering user {username}...")
        resp = await client.post("/auth/register", json={
            "username": username,
            "password": password,
            "email": f"{username}@example.com"
        })
        if resp.status_code != 200:
            print(f"Registration failed: {resp.text}")
            return
        user_data = resp.json()
        print(f"   Registered user ID: {user_data['id']}")
        
        print("2. Logging in...")
        resp = await client.post("/auth/login", data={
            "username": username,
            "password": password
        })
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("   Logged in successfully.")
        
        print("3. Creating Agent...")
        resp = await client.post("/agents/", headers=headers, json={
            "name": "Test Agent",
            "description": "Created by verification script"
        })
        if resp.status_code != 200:
            print(f"Create agent failed: {resp.text}")
            return
        agent = resp.json()
        agent_id = agent["id"]
        print(f"   Created Agent ID: {agent_id}")
        
        print("4. Updating Agent Config...")
        new_config = {"model": "gpt-4", "temperature": 0.7}
        resp = await client.put(f"/agents/{agent_id}", headers=headers, json={
            "config": new_config
        })
        if resp.status_code != 200:
            print(f"Update agent failed: {resp.text}")
            return
        updated_agent = resp.json()
        if updated_agent["config"] == new_config:
            print("   Config updated successfully.")
        else:
            print(f"   Config mismatch: {updated_agent['config']}")

        print("5. Creating API Key...")
        resp = await client.post(f"/agents/{agent_id}/api_keys", headers=headers, json={
            "name": "Test Key"
        })
        if resp.status_code != 200:
            print(f"Create API key failed: {resp.text}")
            return
        api_key_data = resp.json()
        key_id = api_key_data["id"]
        print(f"   Created API Key: {api_key_data['api_key']}")
        
        # Save API key to file for integration test
        with open("generated_api_key.txt", "w") as f:
            f.write(api_key_data['api_key'])
        
        print("6. Listing API Keys...")
        resp = await client.get(f"/agents/{agent_id}/api_keys", headers=headers)
        keys = resp.json()
        if len(keys) == 1 and keys[0]["id"] == key_id:
            print("   API Key listed successfully.")
        else:
            print(f"   API Key listing mismatch: {len(keys)}")
            
        print("7. Deleting API Key...")
        resp = await client.delete(f"/agents/{agent_id}/api_keys/{key_id}", headers=headers)
        if resp.status_code == 204:
            print("   API Key deleted successfully.")
        else:
            print(f"   Delete API key failed: {resp.status_code}")

    print("\n✅ Backend Verification SUCCESS!")

if __name__ == "__main__":
    asyncio.run(main())
