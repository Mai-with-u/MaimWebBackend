import asyncio
import httpx
from src.core.settings import settings

# Base URL (assuming running on localhost:8000)
BASE_URL = "http://localhost:8000" + settings.API_V1_STR

async def test_flow():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Register
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        password = "testpassword"
        print(f"Registering user: {username}")
        
        response = await client.post(f"{settings.API_V1_STR}/auth/register", json={
            "username": username,
            "password": password,
            "email": f"{username}@example.com"
        })
        if response.status_code == 200:
             print("✅ Registration success")
        else:
             print(f"❌ Registration failed: {response.text}")
             return

        # 2. Login
        print("Logging in...")
        response = await client.post(f"{settings.API_V1_STR}/auth/login", data={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Login success")
        else:
            print(f"❌ Login failed: {response.text}")
            return
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create Agent
        print("Creating Agent...")
        agent_payload = {
            "name": "My First Agent",
            "description": "Created via API Test",
            "config": {"model": "gpt-4"}
        }
        response = await client.post(f"{settings.API_V1_STR}/agents/", json=agent_payload, headers=headers)
        if response.status_code == 200:
            agent_data = response.json()
            print(f"✅ Agent created: {agent_data['id']}")
        else:
            print(f"❌ Create Agent failed: {response.text}")
            return
            
        # 4. List Agents
        print("Listing Agents...")
        response = await client.get(f"{settings.API_V1_STR}/agents/", headers=headers)
        if response.status_code == 200 and len(response.json()) > 0:
            print(f"✅ List Agents success: Found {len(response.json())}")
        else:
             print(f"❌ List Agents failed or empty: {response.text}")

import uuid
if __name__ == "__main__":
    asyncio.run(test_flow())
