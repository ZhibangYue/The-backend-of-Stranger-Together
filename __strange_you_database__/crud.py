import random
from datetime import date

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from __strange_you_database__ import models
from __strange_you_database__.database import SessionLocal
from fastapi import Depends, HTTPException
from typing import List
from __strange_you_database__.models import *
from __strange_you_database__.schemas import *


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_users(db: Session, skip=0, limit=0):  # 查询所有用户
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, student_number, username, openid: str = None):  # 创建用户
    db_user = models.User(student_number=student_number, username=username, openid=openid)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_administrator(db: Session, administrator_student_number=int):  # 查询管理员表
    return db.query(models.Administrator).filter(
        models.Administrator.student_number == administrator_student_number).first()


def create_administrator(db: Session, student_number, administratorname, hashed_password):  # 创建管理员表
    db_administrator = models.Administrator(student_number=student_number,
                                            administratorname=administratorname,
                                            hashed_password=hashed_password)
    db.add(db_administrator)
    db.commit()
    db.refresh(db_administrator)
    return db_administrator


def get_sn(db: Session, question_sn=int):  # 查询序列号
    return db.query(models.Question).filter(
        models.Question.sn == question_sn).first()


def get_sns(db: Session, skip=0, limit=0):  # 查询所有序列号
    return db.query(models.Question).offset(skip).limit(limit).all()


def create_question(question: str, name: str, source: str, db: Session):  # 创建问题表
    db_question = models.Question(
        question=question,
        source=source,
        name=name,
        status="待审批",
        date=date.today()
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


# def get_reply(db: Session, id=int):  # 查询回复
#     return db.query(models.Reply).filter(models.Reply.id == id).first()


def get_replies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Reply).offset(skip).limit(limit).all()


def delete_user(user_student_number=int, db=Depends(get_db)):  # 删除用户
    user = db.query(models.User).filter(models.User.student_number == user_student_number).first()
    if not user:
        raise HTTPException(detail="用户不存在,删除失败", status_code=400)
    db.delete(user)
    db.commit()
    return {"detail": "删除成功"}


def deleteUser(user_student_numbers: List[int], db=Depends(get_db)):  # 删除多个用户
    try:
        for user_student_number in user_student_numbers:
            users = db.query(models.User).filter(models.User.student_number == user_student_number).first()
            if users:
                db.delete(users)
                db.commit()
                db.close()
        return {"code": "0000", "message": "删除成功"}
    except ArithmeticError:
        return {"code": "0002", "message": "数据库错误"}


def get_source_question(db: Session, source: str):  # 查询问题
    return db.query(models.Question).filter(models.Question.source == source).all()


def get_source_reply(db: Session, source: str):  # 查询回复
    return db.query(models.Reply).filter(models.Reply.source == source).all()


# 根据user_student_number修改user_name
def updateUser(user_student_number=int, user_name=str, db=Depends(get_db)):
    try:
        user = db.query(models.User).filter(models.User.student_number == user_student_number).first()
        print(user)
        if user:
            models.User.name = user_name
            db.commit()
            db.close()
            return {"code": "0000", "message": "修改成功"}
        else:
            return {"code": "0001", "message": "学工号或昵称错误"}
    except ArithmeticError:
        return {"code": "0002", "message": "数据库错误"}


# def updateQuestionStatus(status, question_sn: int, db: Session):  # 改问题表审核状态
#     question_status = db.query(models.Reply).filter(models.Question.sn == question_sn).first()
#     question_status.status = status
#     db.commit()


def updateReplyStatus(status, reply_id: int, db: Session):  # 改回复表审核状态
    reply_status = db.query(models.Reply).filter(models.Reply.id == reply_id).first()
    reply_status.status = status
    db.commit()


# 按学号查找管理员
def get_manager(db: Session, student_number: str):
    return db.query(Administrator).filter(Administrator.student_number == student_number).first()


# 添加管理员
def add_manager(db: Session, student_number: str, name: str, hashed_password: str):  # 创建管理员表
    db_administrator = Administrator(student_number=student_number,
                                     administratorname=name,
                                     hashed_password=hashed_password)
    db.add(db_administrator)
    db.commit()
    db.refresh(db_administrator)
    return db_administrator


# 管理员修改密码
def change_manager_password(db: Session, student_number: str, hashed_password: str):
    manager = get_manager(db, student_number)
    manager.hashed_password = hashed_password
    db.commit()
    db.refresh(manager)


# 根据序号查找问题
def get_sn_question(db: Session, question_sn: int):
    return db.query(models.Question).filter(models.Question.sn == question_sn).first()


# 分页查找问题
def get_questions(db: Session, page: int, limit: int):
    skip = (page - 1) * limit
    return db.query(Question).offset(skip).limit(limit).all()


# 管理员删除回复
def delete_reply_by_manager(ids: list, db: Session):
    content = db.query(Reply).filter(Reply.id.in_(ids)).delete()
    # if not content:
    #     raise HTTPException(detail="回复不存在,删除失败", status_code=400)
    # db.delete(content)
    db.commit()
    return content


# 删除回复
def delete_reply(reply_id: int, source: str, db: Session):  # 删除回复
    content = db.query(models.Reply).filter(models.Reply.id == reply_id).first()
    if not content:
        raise HTTPException(detail="回复不存在,删除失败", status_code=400)
    if content.source != source:
        raise HTTPException(status_code=401, detail="权限不足，删除失败")
    db.delete(content)
    db.commit()
    return {"detail": "删除成功"}


# 查看自己提出的问题
def get_ones_questions(db: Session, source: str):
    return db.query(Question).filter(Question.source == source).all()


# 查看弹幕墙上的问题
def get_screen_questions(db: Session):
    total_count = db.query(func.count(Question.sn)).scalar()
    if total_count <= 14:
        random_offset = 1
    else:
        random_offset = random.randint(1, total_count - 14)
    return db.query(Question).filter(Question.status == "已通过").offset(random_offset - 1).limit(11).all()


# 查看自己发出的回复
def get_ones_replies(db: Session, source: str):
    return db.query(Reply).filter(Reply.source == source).all()


# 查找问题的所有回复
def get_all_replies(db: Session, question_sn: int):
    return db.query(Reply).filter(Reply.question_id == question_sn).all()


# 分页查找对应问题的回复
def get_reply(db: Session, question_sn: int, page: int, limit: int):
    skip = (page - 1) * limit
    return db.query(Reply).filter(Reply.question_id == question_sn).order_by(Reply.date.desc()) \
        .offset(skip).limit(limit).all()


# 通过问题分页查回复（新）
def get_reply_by_question(db: Session, id: int, sn: int):
    return db.query(Reply).filter(Reply.question_id == sn).offset(id - 1).first()


# 根据序号查回复
def get_reply_by_id(db: Session, id: int, student_number: str):
    reply = db.query(Reply).filter(Reply.id == id).first()
    if not reply:
        raise HTTPException(status_code=404, detail="此回复或已被删除")
    if reply.source != student_number:
        raise HTTPException(status_code=401, detail="权限不足，无法查看")
    return reply


# 根据回复查问题
def get_question_by_reply(db: Session, id: int, student_number: str):
    reply = get_reply_by_id(db, id, student_number)
    question_id = reply.question_id
    if question_id:
        question = db.query(Question).filter(Question.sn == question_id).first()
        if not question:
            question = {"name": "未知", "question": "原问题已被删除", "date": "未知"}
        elif question.status != "已通过":
            question = {"name": question.name, "question": "原问题审核尚未通过", "date": question.date}
        else:
            question = {"name": question.name, "question": question.question, "date": question.date}
    else:
        question = {"name": "未知", "question": "原问题已被删除", "date": "未知"}
    return {"question": question, "reply": reply}


# 创建回复
def create_question_reply(db: Session, reply: ReplyCreate, student_number: str):
    question_id = reply.question_id
    question = get_sn_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="不存在的问题")
    elif question.status != "已通过":
        raise HTTPException(status_code=400, detail="此问题审核尚未通过，暂无法回复")
    db_item = models.Reply(**reply.dict(), source=student_number, status="待审批", date=date.today())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


# 审核问题
def examine_question(db: Session, question_sn: int, status: str):
    question = db.query(Question).filter(Question.sn == question_sn).first()
    if not question:
        return False
    question.status = status
    db.commit()
    return True


# 审核回复
def examine_reply(db: Session, reply_id: int, status: str):
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if not reply:
        return False
    reply.status = status
    db.commit()
    return True


# 查询问题数
def get_question_num(db: Session):
    return db.query(Question).count()


# 查询通过的回复数
def get_accessible_reply_num(db: Session, sn: int):
    return db.query(Reply).filter(Reply.question_id == sn, Reply.status == "已通过").count()


# 查询回复数
def get_reply_num(db: Session, sn: int):
    total = db.query(Reply).filter(Reply.question_id == sn).count()
    left = db.query(Reply).filter(Reply.question_id == sn, Reply.status == "待审批").count()
    return total, left


# 计算总页数
def get_total_page(num: int, limit: int):
    if num <= limit:
        total_page = 1
    else:
        if num % limit == 0:
            total_page = num // limit
        else:
            total_page = (num // limit) + 1
    return total_page


# 前台根据学号查找用户
def get_user(db: Session, user_student_number: str):  # 查询用户
    return db.query(User).filter(User.student_number == user_student_number).first()


# 删除问题
def delete_question(db: Session, question_sn: int, student_number: str):  # 删除问题
    question = db.query(models.Question).filter(models.Question.sn == question_sn).first()
    if not question:
        raise HTTPException(detail="问题不存在,删除失败", status_code=400)
    if question.source != student_number:
        raise HTTPException(status_code=401, detail="权限不足，删除失败")
    db.delete(question)
    db.commit()
    return {"detail": "删除成功"}


# 管理员删除问题
def delete_question_by_manager(sn: list, db: Session):
    try:
        question = db.query(Question).filter(Question.sn.in_(sn)).delete()
    except IntegrityError:
        raise HTTPException(status_code=403, detail="请先删除该问题的回复")
    db.commit()
    return question
