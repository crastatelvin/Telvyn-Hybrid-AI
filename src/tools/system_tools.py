import random
import time
import secrets
from langchain_core.tools import tool

@tool
def get_system_status(component_name: str) -> str:
    """Returns the current operational status of an Aetherial Systems component. 
    Use this when the user asks about the health or status of a specific system."""
    statuses = ["Operational", "Degraded Performance", "Under Maintenance", "Critical Alert"]
    status = random.choice(statuses)
    return f"Component '{component_name}' is currently: {status}. [Verified: {time.strftime('%H:%M:%S')}]"

@tool
def generate_secure_password(length_input: str = "24") -> str:
    """Generates a high-entropy technical password for system configurations. 
    Input should be the desired length as a string."""
    try:
        length = int(str(length_input))
    except:
        length = 24
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+"
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return f"Generated Secure Password: {password}"

@tool
def test_network_latency(hostname: str) -> str:
    """Simulates a network ping to a specific technical hostname. 
    Use this when the user asks about connection speed or latency."""
    latency = random.uniform(5.0, 150.0)
    return f"Ping to '{hostname}': {latency:.2f}ms. Status: {'Stable' if latency < 100 else 'High Latency'}"
