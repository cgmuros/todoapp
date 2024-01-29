from datetime import timedelta, datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from pydantic import BaseModel
from database import SessionLocal
from models import Users 
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

SECRET_KEY = '75094b6ffcb1b8193089c66704421b731e3bc35356277f0b717b6da672692504'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

templates = Jinja2Templates(directory="templates")


class LoginForm:
    def __init__(self, request: Request):
        self.request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        
    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get('email')
        self.password = form.get('password')

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})

    encoded_jwt = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(request: Request):
    try:
        token = request.cookies.get('access_token')
        if token is None:
            return None
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')

        if username is None or user_id is None:
            logout(request)
        return {'username': username, 'id': user_id, 'role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")


# @router.post("/", status_code=status.HTTP_201_CREATED)
# async def create_user(db: db_dependency, 
#                       create_user_request: CreateUserRequest):
#     create_user_model = Users(
#         username=create_user_request.username,
#         email=create_user_request.email,
#         first_name=create_user_request.first_name,
#         last_name=create_user_request.last_name,
#         hashed_password=bcrypt_context.hash(create_user_request.password),
#         role=create_user_request.role,
#         is_active=True,
#         phone_number=create_user_request.phone_number
#     )
    
#     db.add(create_user_model)
#     db.commit()


@router.post("/token", response_model=Token , status_code=status.HTTP_200_OK)
async def login_for_access_token(response: Response,
                                 form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return False
    
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=60))
    
    response.set_cookie(key="access_token", value=token, httponly=True)

    return True


@router.post("/" , response_class=HTMLResponse)
async def login(request: Request, 
                db: Session = Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse("/todo", status_code=status.HTTP_302_FOUND)

        validate_user_cookie = await login_for_access_token(response=response, form_data=form, db=db)

        if not validate_user_cookie:
            msg = "Incorrect User or Password"
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        return response
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})



@router.get("/", response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/logout")
async def logout(request: Request):
    msg = "Logout successfully"
    response = templates.TemplateResponse("login.html", {"request": request, "msg": msg})

    response.delete_cookie(key="access_token")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, 
                        email: str = Form(...),
                        username: str = Form(...),
                        first_name: str = Form(...),
                        last_name: str = Form(...),
                        password: str = Form(...),
                        password2: str = Form(...),
                        db: Session = Depends(get_db)):


    validation1 = db.query(Users).filter(Users.username == username).first()
    validation2 = db.query(Users).filter(Users.email == email).first()
    if password != password2 or validation1 is not None or validation2 is not None:
        msg = "Invalid registration request"
        return templates.TemplateResponse("register.html", {"request": request, "msg": msg})
    
    user_model = Users()
    user_model.username = username
    user_model.email = email
    user_model.first_name = first_name
    user_model.last_name = last_name
    user_model.hashed_password = bcrypt_context.hash(password)
    user_model.is_active = True

    db.add(user_model)
    db.commit()

    msg = "Register successfully"
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    
