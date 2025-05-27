from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.core.config import settings
from src.users.domain.entities.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Get user ID from token without database lookup."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get full user from token with database lookup."""
    user_id = await get_current_user_id(token)
    user = await User.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


async def get_current_enabled_user(user: User = Depends(get_current_user)) -> User:
    """Check if user is enabled."""
    if not user.is_enabled_account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )
    return user


async def get_current_admin_user(
    user: User = Depends(get_current_enabled_user),
) -> User:
    """Check if user is admin."""
    if not any(role.name == "admin" for role in user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return user
