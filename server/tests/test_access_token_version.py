import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

from core.security import create_access_token
from features.auth.dependencies import get_current_user


class AccessTokenVersionTests(unittest.IsolatedAsyncioTestCase):
    async def test_accepts_token_with_current_version(self):
        user_id = uuid4()
        user = SimpleNamespace(id=user_id, token_version=2)

        class FakeUserRepository:
            def __init__(self, _db):
                pass

            async def get(self, _user_id):
                return user

        token = create_access_token(
            {"sub": str(user_id), "token_version": user.token_version}
        )
        with patch(
            "features.auth.dependencies.UserRepository", FakeUserRepository
        ):
            result = await get_current_user(db=None, token=token)

        self.assertIs(result, user)

    async def test_rejects_token_issued_before_version_increment(self):
        user_id = uuid4()
        user = SimpleNamespace(id=user_id, token_version=3)

        class FakeUserRepository:
            def __init__(self, _db):
                pass

            async def get(self, _user_id):
                return user

        token = create_access_token(
            {"sub": str(user_id), "token_version": user.token_version - 1}
        )
        with patch(
            "features.auth.dependencies.UserRepository", FakeUserRepository
        ):
            with self.assertRaises(HTTPException) as raised:
                await get_current_user(db=None, token=token)

        self.assertEqual(raised.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
