import pytest

import db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()


def test_register_and_login():
    ok, _ = db.register_user("alice_1", "password123")
    assert ok
    assert db.authenticate("alice_1", "password123") is not None


def test_wrong_password_rejected():
    db.register_user("alice_1", "password123")
    assert db.authenticate("alice_1", "wrongpass1") is None


def test_unknown_user_rejected():
    assert db.authenticate("ghost", "whatever123") is None


def test_duplicate_username_rejected():
    db.register_user("alice_1", "password123")
    ok, _ = db.register_user("ALICE_1", "password456")
    assert not ok


def test_weak_inputs_rejected():
    assert not db.register_user("ab", "password123")[0]
    assert not db.register_user("alice_1", "short")[0]
    assert not db.register_user("bad name!", "password123")[0]


def test_sql_injection_attempt_fails():
    db.register_user("alice_1", "password123")
    assert db.authenticate("' OR 1=1 --", "x") is None


def test_password_not_stored_in_plain_text():
    db.register_user("alice_1", "password123")
    with db._conn() as c:
        stored = c.execute("SELECT password_hash FROM users").fetchone()[0]
    assert "password123" not in stored and stored.startswith("pbkdf2$")


def test_tasks_are_per_user():
    db.register_user("alice_1", "password123")
    db.register_user("bob_1", "password123")
    a = db.authenticate("alice_1", "password123")
    b = db.authenticate("bob_1", "password123")
    db.save_task(a, "Alice's task")
    assert len(db.list_tasks(a)) == 1
    assert db.list_tasks(b) == []