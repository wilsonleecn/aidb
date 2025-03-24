from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import uuid

@dataclass
class Message:
    content: str
    role: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Conversation:
    conversation_id: str
    messages: List[Message]
    metadata: dict

class ChatLogger:
    def __init__(self):
        self.conversations = {}
        
    def create_conversation(self) -> str:
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = Conversation(
            conversation_id=conversation_id,
            messages=[],
            metadata={}
        )
        return conversation_id
            
    def add_message(self, conversation_id: str, content: str, role: str, metadata: Optional[dict] = None):
        # 如果会话不存在，使用提供的 conversation_id 创建新会话
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = Conversation(
                conversation_id=conversation_id,
                messages=[],
                metadata={}
            )
            
        message = Message(
            content=content,
            role=role,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        self.conversations[conversation_id].messages.append(message)
            
    def save_to_file(self, conversation_id: str, filename: str):
        if conversation_id not in self.conversations:
            raise KeyError(f"Conversation {conversation_id} not found")
            
        conversation = self.conversations[conversation_id]
        data = {
            "conversation_id": conversation.conversation_id,
            "messages": [
                {
                    "content": msg.content,
                    "role": msg.role,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in conversation.messages
            ],
            "metadata": conversation.metadata
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2) 