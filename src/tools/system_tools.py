import random
import time
import secrets
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class ComponentStatusInput(BaseModel):
    component_name: str = Field(description="The name of the system component to check (e.g., 'Satellite Link', 'Neural Core')")

@tool(args_schema=ComponentStatusInput)
def get_system_status(component_name: str) -> str:
    """Returns the current operational status of an Aetherial Systems component."""
    statuses = ["Operational", "Degraded Performance", "Under Maintenance", "Critical Alert"]
    status = random.choice(statuses)
    return f"Component '{component_name}' is currently: {status}. [Verified: {time.strftime('%H:%M:%S')}]"

class PasswordGenInput(BaseModel):
    length: int = Field(default=24, description="The desired length of the secure password")

@tool(args_schema=PasswordGenInput)
def generate_secure_password(length: int = 24) -> str:
    """Generates a high-entropy technical password for system configurations."""
    try:
        print(f"DEBUG: generate_secure_password received length={length} of type {type(length)}")
        # Explicitly ensure length is an integer
        clean_length = int(float(str(length)))
        print(f"DEBUG: clean_length={clean_length}")
    except Exception as e:
        print(f"DEBUG: Error in password tool: {e}")
        clean_length = 24
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+"
    password = ''.join(secrets.choice(alphabet) for i in range(clean_length))
    return f"Generated Secure Password: {password}"

class NetworkPingInput(BaseModel):
    hostname: str = Field(description="The hostname or IP address to ping")

@tool(args_schema=NetworkPingInput)
def test_network_latency(hostname: str) -> str:
    """Simulates a network ping to a specific technical hostname."""
    latency = random.uniform(5.0, 150.0)
    return f"Ping to '{hostname}': {latency:.2f}ms. Status: {'Stable' if latency < 100 else 'High Latency'}"
