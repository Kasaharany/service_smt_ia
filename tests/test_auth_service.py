import json

import pytest

from services import auth_service


@pytest.fixture(autouse=True)
def isolated_users_file(tmp_path, monkeypatch):
    """Isola cada teste em um arquivo de usuários temporário, e garante que
    as contas-semente usadas nos testes não dependam de variáveis de
    ambiente reais."""
    users_file = tmp_path / "users.json"
    monkeypatch.setattr(auth_service, "USERS_FILE", users_file)
    monkeypatch.setattr(
        auth_service,
        "ADMIN_SEED_ACCOUNTS",
        [
            {"name": "Admin Um", "password": "senha-um-123"},
            {"name": "Admin Dois", "password": "senha-dois-456"},
        ],
    )
    return users_file


class TestAuthenticate:
    def test_valid_credentials_return_user(self):
        user = auth_service.authenticate("Admin Um", "senha-um-123")
        assert user == {"username": "Admin Um", "role": "admin"}

    def test_login_is_case_and_whitespace_insensitive_on_username(self):
        user = auth_service.authenticate("  admin UM  ", "senha-um-123")
        assert user is not None
        assert user["username"] == "Admin Um"

    def test_login_ignores_accents_on_username(self):
        user = auth_service.authenticate("Ádmin Üm", "senha-um-123")
        assert user is not None
        assert user["username"] == "Admin Um"

    def test_wrong_password_returns_none(self):
        assert auth_service.authenticate("Admin Um", "senha-errada") is None

    def test_unknown_username_returns_none(self):
        assert auth_service.authenticate("Ninguem", "qualquer") is None

    def test_empty_credentials_return_none(self):
        assert auth_service.authenticate("", "") is None
        assert auth_service.authenticate("Admin Um", "") is None

    def test_password_is_never_stored_in_plaintext(self, isolated_users_file):
        auth_service.authenticate("Admin Um", "senha-um-123")
        raw = json.loads(isolated_users_file.read_text())
        for user in raw["users"]:
            assert "senha-um-123" not in json.dumps(user)
            assert "password" not in user
            assert "password_hash" in user and "salt" in user


class TestEnsureBootstrapAdmins:
    def test_creates_users_file_from_seed_accounts(self, isolated_users_file):
        assert not isolated_users_file.exists()
        auth_service.ensure_bootstrap_admins()
        raw = json.loads(isolated_users_file.read_text())
        usernames = {u["username"] for u in raw["users"]}
        assert usernames == {"Admin Um", "Admin Dois"}

    def test_does_not_overwrite_existing_users(self, isolated_users_file):
        auth_service.ensure_bootstrap_admins()
        auth_service.change_password("Admin Um", "senha-um-123", "nova-senha")

        # Mesmo chamando de novo, não deve recriar/perder a senha alterada
        auth_service.ensure_bootstrap_admins()

        assert auth_service.authenticate("Admin Um", "nova-senha") is not None
        assert auth_service.authenticate("Admin Um", "senha-um-123") is None


class TestChangePassword:
    def test_successful_change_allows_login_with_new_password(self):
        assert auth_service.change_password("Admin Um", "senha-um-123", "outra-senha")
        assert auth_service.authenticate("Admin Um", "outra-senha") is not None
        assert auth_service.authenticate("Admin Um", "senha-um-123") is None

    def test_wrong_current_password_fails_and_keeps_old_password_valid(self):
        assert not auth_service.change_password("Admin Um", "senha-errada", "outra-senha")
        assert auth_service.authenticate("Admin Um", "senha-um-123") is not None

    def test_unknown_user_fails(self):
        assert not auth_service.change_password("Ninguem", "x", "y")
