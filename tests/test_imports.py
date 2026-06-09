def test_imports():
    import importlib

    modules = [
        'backend.database.connection',
        'backend.services.auth',
        'backend.services.cronograma',
        'backend.services.pomodoro',
    ]

    for m in modules:
        importlib.import_module(m)
