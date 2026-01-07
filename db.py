from sqlmodel import SQLModel, Field, create_engine, Session, select, delete
from typing import Optional
from datetime import datetime

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role: str
    content: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)
SQLModel.metadata.create_all(engine)
#suboptimal
def save_message_db(msg:str, role:str):
    with Session(engine) as session:
        #making instances of message class that can be added to db
        msg_db = Message(role=role, content=msg)
        session.add(msg_db)
        session.commit()

def get_chat_history():
    with Session(engine) as session:
        #getting all messages, user experience is suboptimal, needs to be upgraded so that user can scroll up to the start of the big chat
        # also needs to be dynamic according to the n_ctx in model configuration
        statement = select(Message).order_by(Message.timestamp).limit(50)
        results = session.exec(statement).all()
        return results
def chat_reset():
    with Session(engine) as session:
        statement = delete(Message)
        session.exec(statement)
        session.commit()