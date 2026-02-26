from app.database import engine, SessionLocal, Base


def test_engine_is_created():
    assert engine is not None


def test_session_factory_returns_session():
    session = SessionLocal()
    try:
        assert session is not None
        assert session.bind is not None
    finally:
        session.close()


def test_base_has_metadata():
    assert Base.metadata is not None
