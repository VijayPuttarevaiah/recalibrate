# Import passlib to handle password hashing and verification
from passlib.context import CryptContext

# Configure the CryptContext to use the bcrypt algorithm for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Function to generate a secure hash of a plain text password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Function to verify a plain text password against its stored hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
