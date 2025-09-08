"""Base agent class"""

class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.initialized = False
        
    def initialize(self):
        """Initialize agent"""
        self.initialized = True
        # Allocate some memory for testing
        self.data = [0] * 10000
        return self
