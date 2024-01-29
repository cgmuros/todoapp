from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path, Request, Form
from pydantic import BaseModel, Field
from database import engine, SessionLocal
from models import Users
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse
from .auth import get_current_user
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse



router = APIRouter(
    prefix="/user",
    tags=["user"],
)

class UserVerification(BaseModel):
    username: str
    password: str
    new_password: str = Field(min_length=5)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

templates = Jinja2Templates(directory="templates")

@router.get('/' , status_code=status.HTTP_200_OK)
async def get_user(
    user: user_dependency,
    db: db_dependency):

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")

    user_info = db.query(Users).filter(Users.id == user.get('id')).first()

    return user_info


@router.get("/password", status_code=status.HTTP_200_OK)
async def change_password_form(
    request: Request,
    db: Session = Depends(get_db)
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    # user_info = db.query(Users).filter(Users.id == user.get('id')).first()
    return templates.TemplateResponse("change_password.html", {"request": request, "user": user})


@router.post('/password', response_class=HTMLResponse)
async def change_password(
    request: Request,
    password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)):

    user = await get_current_user(request)
  
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    
    user_info = db.query(Users).filter(Users.id == user.get('id')).first()

    if not bcrypt_context.verify(password, user_info.hashed_password):
        return RedirectResponse(url="/auth", status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    
    user_info.hashed_password = bcrypt_context.hash(new_password)

    db.add(user_info)
    db.commit()

    msg = "Password Changed Successfully"
    return templates.TemplateResponse("change_password.html", {"request": request, "msg": msg, "user": user})
    


@router.put('/phone_number/{phone_number}' , status_code=status.HTTP_204_NO_CONTENT)
async def change_phone_number(
    user: user_dependency,
    db: db_dependency,
    phone_number: str):

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")

    user_info = db.query(Users).filter(Users.id == user.get('id')).first()

    user_info.phone_number = phone_number

    db.add(user_info)
    db.commit()


