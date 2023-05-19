from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship

from __strange_you_database__.database import Base


class User(Base):  # 用户表
    __tablename__ = "users"
    student_number = Column(String(12), primary_key=True, index=True)  # 学工号
    username = Column(String(20))
    openid = Column(String(30), nullable=True)


class Administrator(Base):  # 管理员表
    __tablename__ = "administrator"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_number = Column(String(12), index=True, unique=True)

    administratorname = Column(String(20))
    hashed_password = Column(String(200))


class Question(Base):
    __tablename__ = "question"
    sn = Column(Integer, primary_key=True, autoincrement=True, index=True)
    question = Column(String(200))
    source = Column(String(12), ForeignKey("users.student_number"), index=True)
    name = Column(String(10), default="匿名")
    status = Column(String(8), default="待审批")
    date = Column(Date)
    replies = relationship("Reply", back_populates="question")


class Reply(Base):
    __tablename__ = "reply"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))
    content = Column(String(1000))
    source = Column(String(12), ForeignKey("users.student_number"), index=True)
    status = Column(String(8), default="待审批")
    date = Column(Date)
    question_id = Column(Integer, ForeignKey("question.sn"))
    question = relationship("Question", back_populates="replies")
