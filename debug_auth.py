from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Simulating the flow
password = "SynthPass123!"
hashed = get_password_hash(password)
print(f"Password: {password}")
print(f"Hashed: {hashed}")
verified = verify_password(password, hashed)
print(f"Verification: {verified}")

# Check against a potentially problematic case (e.g. whitespace)
print(f"Verification with whitespace: {verify_password(password + ' ', hashed)}")
