import importlib
import os

import pytest


def reload_config(monkeypatch, tmp_env):
    monkeypatch.setenv('DOTENV_PATH', str(tmp_env))
    for var in ['PINECONE_API_KEY', 'PINECONE_INDEX_NAME', 'PINECONE_TOP_K']:
        monkeypatch.delenv(var, raising=False)
    if 'api.config' in importlib.sys.modules:
        module = importlib.reload(importlib.import_module('api.config'))
    else:
        module = importlib.import_module('api.config')
    return module.Settings()


def test_loads_env_file(monkeypatch, tmp_path):
    env = tmp_path / '.env.development'
    env.write_text('PINECONE_API_KEY=key\nPINECONE_INDEX_NAME=index\nPINECONE_TOP_K=5\n')
    settings = reload_config(monkeypatch, env)
    assert settings.api_key == 'key'
    assert settings.index_name == 'index'
    assert settings.k == 5


def test_missing_var_raises(monkeypatch, tmp_path):
    env = tmp_path / '.env.development'
    env.write_text('PINECONE_INDEX_NAME=index\nPINECONE_TOP_K=5\n')
    with pytest.raises(EnvironmentError):
        reload_config(monkeypatch, env)
