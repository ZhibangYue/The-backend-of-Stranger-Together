from datetime import timedelta

from fastapi.security import OAuth2PasswordRequestForm

from __strange_you_database__ import crud
from fastapi import Depends, HTTPException, Form
from requests import Session
from __strange_you_database__.database import SessionLocal
from fastapi import APIRouter

from __strange_you_database__.utils import *
from __strange_you_database__.schemas import *
from __strange_you_database__.crud import *

background = APIRouter(
    prefix="/background",
    tags=["background"],
    responses={404: {"description": "Not found"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/background/token")


# 解码并校验接收到的令牌，然后，返回当前用户。
async def get_current_manager(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
    manager = get_manager(db, student_number=student_number)
    if manager is None:
        raise credentials_exception
    return manager


@background.post("/token", status_code=200, response_model=Token, response_description="login successfully",
                 summary="交互文档登录")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    manager = authenticate_manager(form_data.username, form_data.password, db)
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": manager.student_number}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 登录
@background.post("/managers/login", status_code=200, response_model=Token, response_description="login successfully",
                 summary="登录")
async def login_for_access_token(form_data: PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    manager = authenticate_manager(form_data.username, form_data.password, db)
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": manager.student_number}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 添加管理员
@background.post("/managers/signin", status_code=201, response_description="created successfully", summary="注册")
async def signup(
        student_number: str = Form(..., max_length=12),
        password: str = Form(..., min_length=8, max_lengh=20),
        db=Depends(get_db)):
    if get_manager(db, student_number):
        raise HTTPException(detail="用户名已存在", status_code=400)
    hashed_password = hash_password(password)
    add_manager(db, student_number, "管理员", hashed_password)
    return {"message": "success", "detail": "注册成功", "data": {}}


# 管理员修改密码
@background.post("/manager/change-password", status_code=200,
                 response_description="changed successfully",
                 summary="修改密码")
async def change_password(password: str = Form(..., min_length=8, max_lengh=20), db: Session = Depends(get_db),
                          current_manager: ManagerMessage = Depends(get_current_manager)):
    hashed_password = hash_password(password)
    change_manager_password(db, current_manager.student_number, hashed_password)
    return {"message": "success", "detail": "修改成功", "data": {}}


# 创建用户
@background.post("/user")
def create_user00(
        user: UserCreate,
        current_manager: ManagerMessage = Depends(get_current_manager),
        db: Session = Depends(get_db)):
    db_user = crud.create_user(db=db, username=user.username, student_number=user.student_number, openid=user.openid)
    return db_user


# 通过学号查询用户
@background.get("/user/{student_number}", summary="通过学号查询用户")
def read_user(student_number: str,
              current_manager: ManagerMessage = Depends(get_current_manager),
              db: Session = Depends(get_db)):
    user = crud.get_user(db, student_number)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# 分页查询用户
@background.get("/users/all", response_model=List[UserSchema])
def read_users(skip: int = 0,
               limit: int = 100,
               current_manager: ManagerMessage = Depends(get_current_manager),
               db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


# 删除用户
@background.delete("/user/{student_number}")
def user_delete(student_number: int, current_manager: ManagerMessage = Depends(get_current_manager), db: Session = Depends(get_db)):
    return crud.delete_user(user_student_number=student_number, db=db)


# 删除多个用户
@background.delete("/users")
def delete_users(
        user_student_numbers: List[int],
        current_manager: ManagerMessage = Depends(get_current_manager),
        db: Session = Depends(get_db)):
    return crud.deleteUser(user_student_numbers=user_student_numbers, db=db)


# 根据学工号修改用户昵称
@background.put("/user")
def update_user(
        user_student_number: int, user_name: str,
        current_manager: ManagerMessage = Depends(get_current_manager),
        db: Session = Depends(get_db)):
    return crud.updateUser(user_student_number=user_student_number, user_name=user_name, db=db)


# 分页查询问题
@background.get("/questions", summary="分页查询问题")
def get_questions(page: int = 1, limit: int = 10, db: Session = Depends(get_db),
                  current_manager: ManagerMessage = Depends(get_current_manager)
                  ):
    questions = crud.get_questions(db, page=page, limit=limit)
    question_num = get_question_num(db)
    total_page = get_total_page(question_num, limit)
    if not questions:
        if page == 1:
            raise HTTPException(status_code=404, detail="获取失败，无更多信息")
        if page > total_page:
            page = total_page
            questions = crud.get_questions(db, page=page, limit=limit)
            if not questions:
                raise HTTPException(status_code=404, detail="获取失败，无更多信息")
    return {"message": "success", "detail": "获取成功",
            "data": {"question_information": questions,
                     "page_information": {
                         "page": page,
                         "total_page": total_page,
                         "num": len(questions),
                     }}}


# 通过序号查询问题
@background.get("/question", summary="通过序号查询问题")
def read_question(sn: int, db: Session = Depends(get_db),
                  current_manager: ManagerMessage = Depends(get_current_manager)
                  ):
    question = crud.get_sn(db=db, question_sn=sn)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


# 通过来源查询问题
@background.get("/questions/{source}")
def read_source_question(
        source: str,
        current_manager: ManagerMessage = Depends(get_current_manager),
        db: Session = Depends(get_db)):
    questions = crud.get_source_question(db=db, source=source)
    if questions is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return questions


@background.post("/question", status_code=201, summary="创建问题")
def post(
    question: QuestionCreate2,
    db: Session = Depends(get_db),
    current_manager: ManagerMessage = Depends(get_current_manager)):
    source = question.source
    user = get_user(db, source)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    create_question(question.question, question.name, source, db)
    return {"message": "Success"}


# 删除问题
@background.delete("/question", summary="删除问题")
def delete_question(question_sn: list, db: Session = Depends(get_db),
                    current_manager: ManagerMessage = Depends(get_current_manager)
                    ):
    crud.delete_question_by_manager(question_sn, db)
    return {"message": "Success", "detail": "删除成功"}


# 审核问题
@background.put("/question", summary="审核问题")
def examine_question(
        question: QuestionExamine,
        db: Session = Depends(get_db),
        current_manager: ManagerMessage = Depends(get_current_manager)
):
    result = crud.examine_question(db, question.sn, question.status)
    if not result:
        raise HTTPException(status_code=404, detail="此问题不存在")
    return {"message": "Success"}


# 查询问题的回复
@background.get("/replies", summary="查询问题的回复")
def get_replies(question_sn: int, page: int = 1, limit: int = 10, db: Session = Depends(get_db),
                current_manager: ManagerMessage = Depends(get_current_manager)
                ):
    reply = get_reply(db, question_sn=question_sn, page=page, limit=limit)
    num = get_reply_num(db, question_sn)
    total_page = get_total_page(num[0], limit)
    if not reply:
        if page == 1:
            raise HTTPException(status_code=404, detail="获取失败，无更多信息")
        if page > total_page:
            page = total_page
            reply = crud.get_reply(db, question_sn=question_sn, page=page, limit=limit)
            if not reply:
                raise HTTPException(status_code=404, detail="获取失败，无更多信息")
    return {"message": "success", "detail": "获取成功",
            "data": {
                "question_sn": question_sn,
                "reply_information": reply,
                "unexamined_replies": num[1],
                "page_information": {"page": page,
                                     "total_page": total_page,
                                     "num": len(reply)
                                     }}}


# 删除回复
@background.delete("/reply", summary="删除回复")
def delete_reply(
        reply_id: list,
        db: Session = Depends(get_db),
        current_manager: ManagerMessage = Depends(get_current_manager)
):
    crud.delete_reply_by_manager(reply_id, db)
    return {"message": "Success", "detail": "删除成功"}


# 批量删除

# 审核回复
@background.put("/reply", summary="审核回复")
def examine_question(
        reply: QuestionExamine,
        db: Session = Depends(get_db),
        current_manager: ManagerMessage = Depends(get_current_manager)
):
    result = crud.examine_reply(db, reply.sn, reply.status)
    if not result:
        raise HTTPException(status_code=404, detail="此回复不存在")
    return {"message": "Success", "detail": "审核完毕"}
# @router.get("/Replies")  # 查询所有回复
# def get_replies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     replies = crud.get_replies(db, skip=skip, limit=limit)
#     return replies
#
#

#
#
# @router.get("/sns/")  # 查询所有序列号
# def get_sns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     sns = crud.get_sns(db, skip=skip, limit=limit)
#     return sns
#
#
# @router.get("/users/")  # 查询所有用户
# def read_user(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = crud.get_users(db, skip=skip, limit=limit)
#     return users
#
#
# @router.delete("/user/")  # 删除用户
# def delete_user(user_student_number: str, db: Session = Depends(get_db)):
#     user = crud.delete_user(user_student_number, db)
#     return user
# @router.put("/reply_status/")  # 改回复状态
# def updateReplyStatus(status, reply_id: int, db=Depends(get_db)):
#     reply_status = crud.updateReplyStatus(status, reply_id, db)
#     return reply_status
