from datetime import date
from typing import Union, Optional

from fastapi import Form
from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    openid: str
    student_number: str = Field(..., example="20220001")
    username: str = Field(..., example="小明")

    class Config:
        orm_mode = True


class UserCreate(UserSchema):
    pass


class UserUpdate(UserSchema):
    pass


class AdministratorSchema(BaseModel):
    id: int = Field(..., example=1)
    student_number: str = Field(..., example="20220001")
    administratorname: str = Field(..., example="管理员")
    hashed_password: str = Field(..., example="password_hash")

    class Config:
        orm_mode = True


class AdministratorCreate(AdministratorSchema):
    pass


class QuestionCreate(BaseModel):
    question: str = Field(..., example="这是一个问题吗？")
    name: str = Field(..., example="匿名")

    class Config:
        orm_mode = True


class QuestionCreate2(QuestionCreate):
    source: str

    class Config:
        orm_mode = True

class QuestionQuery(QuestionCreate):
    sn: int
    status: str
    date: date

    class Config:
        orm_mode = True


# 弹幕墙上的问题
class QuestionScreen(QuestionCreate):
    sn: int

    class Config:
        orm_mode = True


class QuestionUpdate(QuestionCreate):
    pass


class ReplySchema(BaseModel):
    # replyname: str = Field(..., example="小红")
    # content: str = Field(..., example="这是一个回复")
    # source: str = Field(..., example="20220002")
    # status: str = Field(..., example="待审批")
    # date: date = Field(..., example="2023-04-22")
    pass

    class Config:
        orm_mode = True


class ReplyUpdate(ReplySchema):
    pass


class TokenModel(BaseModel):
    token: str = None


# 登录请求体模型
class LoginModel(BaseModel):
    username: str = None
    password: str = None
    # code: str = None


# 后台发放token
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    student_number: Union[str, None] = None
    name: Union[str, None] = None


# 后台登录表单
class PasswordRequestForm:

    def __init__(
            self,
            username: str = Form(),
            password: str = Form()
    ):
        self.username = username
        self.password = password


# 管理员修改密码时使用
class ManagerMessage(BaseModel):
    student_number: str

    class Config:
        orm_mode = True


# 审核问题
class QuestionExamine(BaseModel):
    sn: int
    status: str


# 回复模型
class ReplyBase(BaseModel):
    name: Optional[str] = "匿名"
    content: Union[str, None] = "未知"


class ReplyCreate(ReplyBase):
    question_id: Optional[int] = 0

    class Config:
        orm_mode = True


class ReplyQuery(ReplyCreate):
    date: date
    status: str
    id: int


class OwnReplyQuery(BaseModel):
    id: int
    name: Optional[str] = "匿名"
    question_id: Optional[int] = 0

    class Config:
        orm_mode = True


# 通过回复查问题-响应体
class QuestionResponse(BaseModel):
    sn: int
    name: Optional[str] = "匿名"
    question: str
    date: date
    status: str

    class Config:
        orm_mode = True
