import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from __strange_you_database__ import models
from __strange_you_database__.database import engine
from app import infront, background
from fastapi import FastAPI

app = FastAPI(
    title="“陌生的你”后端接口文档"
)


app.include_router(background.background)
app.include_router(infront.infront)

app.mount("/dist", StaticFiles(directory="dist"), name="static")
app.mount("/assets", StaticFiles(directory="dist/assets"), name="static")


# 设置允许跨域请求的来源、方法和头部信息
origins = [
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="dist")


@app.get("/")
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == '__main__':
    uvicorn.run("main:app", reload=True)
