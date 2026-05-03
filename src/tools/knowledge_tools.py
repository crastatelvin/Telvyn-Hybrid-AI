import os
import time
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class RememberFactInput(BaseModel):
    training_input: str = Field(description="The fact to remember, formatted as 'Title | Content'")

@tool(args_schema=RememberFactInput)
def remember_fact(training_input: str) -> str:
    """Saves a new fact to the internal knowledge base."""
    try:
        if "|" in training_input:
            fact_title, fact_content = training_input.split("|", 1)
        else:
            fact_title = "User Fact " + time.strftime("%H%M%S")
            fact_content = training_input
            
        safe_title = "".join([c if c.isalnum() else "_" for c in fact_title.strip().lower()])
        filename = f"trained_fact_{safe_title}.md"
        knowledge_dir = os.getenv("KNOWLEDGE_DIR", "./knowledge")
        
        if not os.path.exists(knowledge_dir):
            os.makedirs(knowledge_dir)
            
        filepath = os.path.join(knowledge_dir, filename)
        content = f"# Trained Fact: {fact_title.strip()}\n\nDate: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n{fact_content.strip()}\n"
        
        with open(filepath, "w") as f:
            f.write(content)
            
        return f"SUCCESS: New fact saved to '{filename}'. IMPORTANT: Tell the user they MUST click 'Sync Knowledge Base' in the sidebar for me to actually learn it."
    except Exception as e:
        return f"ERROR saving fact: {str(e)}"
