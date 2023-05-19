from datetime import date
from typing import Optional, List

from fastapi import FastAPI, HTTPException, APIRouter, Depends
from fastapi.security import HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status
from __strange_you_database__ import crud
from __strange_you_database__ import models
from __strange_you_database__ import schemas
from __strange_you_database__.database import SessionLocal, engine
from __strange_you_database__.utils import *
from __strange_you_database__.schemas import *
from __strange_you_database__.crud import *

app = FastAPI
infront = APIRouter(
    prefix="/infront",
    tags=["infront"],
    responses={404: {"description": "Not found"}},
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/infront/token")


# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     try:
#         # 从请求头中获取 JWT 访问令牌
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         # 解密后的数据应包含失效时间字段 exp
#         username: str = payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
#         token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_DAYS)
#         # 校验令牌是否已过期
#         expire = datetime.fromisoformat(payload["exp"])
#         if expire - datetime.utcnow() < token_expires:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
#     # 返回用户名，即当前登录用户
#     return username


# 解码并校验接收到的令牌，然后，返回当前用户。
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_number: str = payload.get("sub")
        if student_number is None:
            raise credentials_exception
        token_data = TokenData(student_number=student_number)
    except JWTError:
        raise credentials_exception
    user = get_user(db, student_number)
    if user is None:
        raise credentials_exception
    return user


@infront.post("/token", status_code=200, response_model=Token, response_description="login successfully",
              summary="交互文档登录")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 统一认证获取用户信息
    user_info = get_info_plus(form_data.username, form_data.password)
    # 先根据学号在数据库中查找用户
    user = get_user(db, form_data.username)
    # 添加到数据库里
    if not user:
        student_number = user_info["student_number"]
        name = user_info["name"]
        create_user(db, student_number, name)
    # 前台token有效期为30天
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.student_number}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 登录注册接口
@infront.post("/login", summary="登录注册")
def login(user: schemas.LoginModel, db: Session = Depends(get_db)):
    # 统一认证获取用户信息
    user_info = get_info_plus(user.username, user.password)
    # 先根据学号在数据库中查找用户
    user_old = get_user(db, user.username)
    # 添加到数据库里
    if not user_old:
        student_number = user_info["student_number"]
        name = user_info["name"]
        create_user(db, student_number, name)
    # 前台token有效期为30天
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    # 根据学号发放token（虽然写作username）
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 创建问题
@infront.post("/question", summary="创建问题")
def create_question(question: schemas.QuestionCreate,
                    current_user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    student_number = current_user.student_number
    db_question = crud.create_question(db=db, question=question.question, source=student_number, name=question.name)
    return db_question


# 查询自己的问题
@infront.get("/questions", response_model=List[QuestionQuery], summary="查询自己的问题")
def read_questions(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
):
    source = current_user.student_number
    questions = get_ones_questions(db, source)
    return questions


# 弹幕墙上的问题
@infront.get("/bullet-screen", response_model=List[QuestionScreen], summary="弹幕墙上的问题")
def bullet_screen(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
):
    questions = get_screen_questions(db)
    if not questions:
        raise HTTPException(status_code=404, detail="暂无可回复的问题")
    return questions


# 删除问题
@infront.delete("/question", summary="删除问题")
def question_delete(question_sn: int,
                    current_user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    student_number = current_user.student_number
    return delete_question(db, question_sn, student_number)


# 创建回复
@infront.post("/reply", summary="创建回复")
def create_reply(
        reply: ReplyCreate,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)):
    student_number = current_user.student_number
    create_question_reply(db, reply, student_number)
    return {"message": "Success"}


# 查询回复
@infront.get("/replies", response_model=List[OwnReplyQuery], summary="查询回复")
def read_replies(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
):
    source = current_user.student_number
    replies = get_ones_replies(db, source)
    if not replies:
        raise HTTPException(status_code=404, detail="当前未有回复")
    return replies


# 通过回复查问题
@infront.get("/reply-question", summary="通过回复查问题")
def read_reply(id: int,
               current_user=Depends(get_current_user),
               db: Session = Depends(get_db)):
    question = get_question_by_reply(db, id, current_user.student_number)
    return question


# 通过问题查回复
@infront.get("/question-reply", response_model=List[ReplyQuery], summary="通过问题查回复")
def read_replies_by_question(
        sn: int,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    student_number = current_user.student_number
    question = get_sn(db, sn)
    if not question:
        raise HTTPException(status_code=404, detail="此问题不存在")
    if question.source != student_number:
        raise HTTPException(status_code=401, detail="权限不足，无法查看")
    if question.status != "已通过":
        raise HTTPException(status_code=400, detail="审核未通过，暂无法回复")
    reply = get_all_replies(db, sn)
    return [x for x in reply if x.status == "已通过"]


# 分页查询回复
# @infront.get("/replies/all", response_model=List[schemas.ReplySchema])
# def read_replies(current_user=Depends(get_current_user), skip: int = 0, limit: int = 100,
#                  db: Session = Depends(get_db)):
#     replies = crud.get_replies(db, skip=skip, limit=limit)
#     return replies


# 删除回复
@infront.delete("/reply", summary="删除回复")
def reply_delete(reply_id: int,
                 current_user=Depends(get_current_user),
                 db: Session = Depends(get_db)):
    return crud.delete_reply(reply_id, current_user.student_number, db)


# 通过问题分页查回复（新）
@infront.get("/question/{sn}", summary="通过问题分页查回复")
def get_reply_(
        sn: int,
        id: int = 1,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    question = get_sn_question(db, sn)
    if not question:
        raise HTTPException(status_code=404, detail="此问题不存在")
    if question.source != current_user.student_number:
        raise HTTPException(status_code=401, detail="权限不足，无法查看")
    if question.status != "已通过":
        raise HTTPException(status_code=400, detail="审核未通过，暂无法回复")
    num = get_accessible_reply_num(db, sn)
    reply = get_reply_by_question(db,  id, sn)
    if not reply:
        raise HTTPException(status_code=404, detail="此回复不存在")
    return {
        "message": "Success",
        "detail": "查询成功",
        "data": {
            "total_num": num,
            "reply": reply,
            "question": question
        }
    }