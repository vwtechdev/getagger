"""Thread-local do usuário corrente para auditoria (created_by/updated_by).

Preenchido pelo AuditMiddleware a cada requisição. Em comandos de gestão
sem requisição, retorna None (campos de auditoria ficam nulos).
"""
import threading

_thread_locals = threading.local()


def get_current_user():
    return getattr(_thread_locals, 'user', None)


def set_current_user(user):
    _thread_locals.user = user
