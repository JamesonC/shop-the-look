import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


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


def test_loads_vercel_preview_file(monkeypatch, tmp_path):
    env = tmp_path / '.env.preview'
    env.write_text(
        'PINECONE_API_KEY=preview_key\n'
        'PINECONE_INDEX_NAME=preview_index\n'
        'PINECONE_TOP_K=7\n'
    )

    # Simulate Vercel preview environment without ENVIRONMENT or DOTENV_PATH
    monkeypatch.setenv('VERCEL_ENV', 'preview')
    monkeypatch.delenv('ENVIRONMENT', raising=False)
    monkeypatch.delenv('DOTENV_PATH', raising=False)

    for var in ['PINECONE_API_KEY', 'PINECONE_INDEX_NAME', 'PINECONE_TOP_K']:
        monkeypatch.delenv(var, raising=False)

    monkeypatch.chdir(tmp_path)

    if 'api.config' in importlib.sys.modules:
        module = importlib.reload(importlib.import_module('api.config'))
    else:
        module = importlib.import_module('api.config')

    settings = module.Settings()
    assert settings.api_key == 'preview_key'
    assert settings.index_name == 'preview_index'
    assert settings.k == 7
