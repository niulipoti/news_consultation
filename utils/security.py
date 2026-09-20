from passlib.context import CryptContext

#创建密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


#密码加密

def get_password_hash(password: str):
  return pwd_context.hash(password)


#密码验证: verify 返回值是布尔型 true/false
def verify_password(plain_password: str, hashed_password: str):
  return pwd_context.verify(plain_password, hashed_password)