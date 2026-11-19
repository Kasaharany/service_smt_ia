"""Serviço de autenticação local, com armazenamento de usuários em arquivo.

Projetado para um cenário simples (poucos administradores + acesso de
visitante), sem depender de um banco de dados externo. Senhas nunca são
guardadas em texto puro: usamos PBKDF2-HMAC-SHA256 com salt individual por
usuário. As contas-semente (nomes e senhas iniciais) vêm de variáveis de
ambiente (`config.settings.ADMIN_SEED_ACCOUNTS`) — nunca ficam hardcoded
no código-fonte.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets as pysecrets
from pathlib import Path
from typing import Optional

from config.settings import ADMIN_SEED_ACCOUNTS, BASE_DIR

USERS_FILE: Path = BASE_DIR / "data" / "users.json"
_PBKDF2_ITERATIONS = 200_000


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    ).hex()


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _load_raw() -> dict:
    if not USERS_FILE.exists():
        return {"users": []}
    with USERS_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_raw(data: dict) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with USERS_FILE.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def _create_user_record(username: str, password: str, role: str) -> dict:
    salt = pysecrets.token_bytes(16)
    return {
        "username": username,
        "role": role,
        "salt": salt.hex(),
        "password_hash": _hash_password(password, salt),
    }


def ensure_bootstrap_admins() -> None:
    """Cria as contas de administrador a partir das variáveis de ambiente,
    apenas se ainda não existir nenhum usuário cadastrado. Nunca sobrescreve
    um cadastro já existente (preserva trocas de senha feitas pelo usuário).
    """
    data = _load_raw()
    if data.get("users"):
        return

    users = [
        _create_user_record(account["name"], account["password"], "admin")
        for account in ADMIN_SEED_ACCOUNTS
        if account["name"] and account["password"]
    ]
    _save_raw({"users": users})


def authenticate(username: str, password: str) -> Optional[dict]:
    """Verifica usuário e senha. Retorna {"username", "role"} se válido,
    ou None caso usuário não exista ou a senha esteja incorreta."""
    if not username or not password:
        return None

    ensure_bootstrap_admins()
    data = _load_raw()
    target = _normalize_username(username)

    for user in data["users"]:
        if _normalize_username(user["username"]) != target:
            continue
        salt = bytes.fromhex(user["salt"])
        candidate_hash = _hash_password(password, salt)
        if hmac.compare_digest(candidate_hash, user["password_hash"]):
            return {"username": user["username"], "role": user["role"]}
        return None

    return None


def change_password(username: str, current_password: str, new_password: str) -> bool:
    """Troca a senha do próprio usuário, validando a senha atual primeiro.
    Retorna True se a troca foi concluída."""
    ensure_bootstrap_admins()
    data = _load_raw()
    target = _normalize_username(username)

    for user in data["users"]:
        if _normalize_username(user["username"]) != target:
            continue
        salt = bytes.fromhex(user["salt"])
        if not hmac.compare_digest(_hash_password(current_password, salt), user["password_hash"]):
            return False
        new_salt = pysecrets.token_bytes(16)
        user["salt"] = new_salt.hex()
        user["password_hash"] = _hash_password(new_password, new_salt)
        _save_raw(data)
        return True

    return False
