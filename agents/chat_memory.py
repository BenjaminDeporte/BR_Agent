# agents/chat_memory.py

class ChatSessionHistory:
    """
    A simple in-memory chat session history to store user and agent messages.
    """
    def __init__(self):
        self.messages = []

    def add_user_message(self, msg: str):
        self.messages.append({"role": "user", "content": msg})

    def add_agent_message(self, msg: str):
        self.messages.append({"role": "assistant", "content": msg})

    def get_history(self):
        return self.messages

    def clear(self):
        self.messages = []
