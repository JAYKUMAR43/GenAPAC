from backend.agents.router_agent import RouterAgent
from backend.database import SessionLocal, engine, Base

class AIEnvWrapper:
    """
    OpenEnv / RL Compatibility Wrapper
    Provides step(), reset(), and state() methods.
    """
    def __init__(self):
        # Ensure DB is created for the env
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        self.router = RouterAgent()
        self.current_state = None

    def reset(self):
        """
        Resets the environment state.
        """
        self.current_state = {"last_action": None, "last_reward": 0}
        return self.state()

    def step(self, action: str):
        """
        action: The user input text (e.g., "Add task buy milk")
        """
        response = self.router.handle(action, self.db)
        status = response.get("status", "error")
        
        # Define a simple reward function: +1 for success, -1 for error
        reward = 1 if status == "success" else -1
        
        # Done is always False for a continuous productivity agent
        done = False 
        
        self.current_state = {
            "last_action": action,
            "last_reward": reward,
            "response": response
        }
        
        info = {"intent": response.get("intent")}
        
        return self.state(), reward, done, info

    def state(self):
        return self.current_state
    
    def close(self):
        self.db.close()
