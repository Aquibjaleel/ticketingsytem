#! usr/bin/python3
# -*- coding: utf8 -*-

import json
import os
import platform

from scripts.create_json import config_file
from scripts.create_json import WriteConfigJson
from scripts.create_json import check_db_connection

# AKV integration
from application.services.security import SecureConfig

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfiguration(object):
    # Only ensure JSON exists if not in a CI build environment
    if not os.environ.get('TF_BUILD'):
        WriteConfigJson.json_exists()

    DEBUG = False
    TESTING = False
    EXPLAIN_TEMPLATE_LOADING = False

    # --- 1. LOAD DATA WITH FALLBACKS ---
    config_data = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
        except (json.JSONDecodeError, KeyError):
            if not os.environ.get('TF_BUILD'):
                raise KeyError('The file config.json appears incorrectly formatted.')

    # --- 2. DATABASE & CORE CONFIG ---
    SECRET_KEY = os.environ.get('SECRET_KEY', config_data.get('SECRET_KEY', 'default-dev-key'))
    
    db_username = config_data.get('db_username', 'dummy')
    db_password = config_data.get('db_password', 'dummy')
    db_url = config_data.get('db_url', 'localhost')
    db_port = config_data.get('db_port', '5432')
    db_name = config_data.get('db_name', 'dummy_db')
    db_type = config_data.get('db_type', 1) 
    db_driver = config_data.get('db_driver', '')

    db_dialect = None
    SQLALCHEMY_DATABASE_URI = None

    sql_os_path_prefix = '///' if platform.system() == 'Windows' else '////'

    if db_type == 1:
        db_dialect = 'sqlite'
        db_path = os.path.join(basedir, db_name)
        SQLALCHEMY_DATABASE_URI = f'{db_dialect}:{sql_os_path_prefix}{db_path}'
    else:
        if db_type == 2: db_dialect = 'postgresql'
        if db_type == 3: db_dialect = 'mysql'
        SQLALCHEMY_DATABASE_URI = f'{db_dialect}+{db_driver}://{db_username}:{db_password}@{db_url}:{db_port}/{db_name}'

    # --- 3. AI SERVICE CONFIGURATION (Fail-Fast Logic) ---
    # Initialize secure layer for Vault Decryption
    security = SecureConfig()
    
    encrypted_blob = config_data.get('ai_api_key_encrypted')
    decrypted_vault_key = security.decrypt(encrypted_blob)

    AI_API_KEY = (
        decrypted_vault_key or 
        os.environ.get('AI_API_KEY') or 
        config_data.get('ai_api_key')
    )
    AI_ENDPOINT = os.environ.get('AI_ENDPOINT') or config_data.get('ai_endpoint')
    AI_PROVIDER = os.environ.get('AI_PROVIDER') or config_data.get('ai_provider')

    # Validation: Only enforce strictly if NOT in a build environment
    if not os.environ.get('TF_BUILD'):
        if not AI_API_KEY or not AI_ENDPOINT:
            missing = [k for k, v in {"AI_API_KEY": AI_API_KEY, "AI_ENDPOINT": AI_ENDPOINT}.items() if not v]
            raise ConnectionAbortedError(f"CRITICAL BOOT ERROR: Missing AI config: {', '.join(missing)}")
        
        masked_key = f"{AI_API_KEY[:4]}...{AI_API_KEY[-4:]}"
        print(f"AI Service initialized at {AI_ENDPOINT} (Key: {masked_key})")

    # --- 4. APP INTERNALS ---
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    ADMIN_GROUP_NAME = 'flicket_admin'
    SUPER_USER_GROUP_NAME = 'super_user'

    WEBHOME = '/'
    FLICKET = WEBHOME
    FLICKET_API = WEBHOME + 'flicket-api/'
    FLICKET_REST_API = WEBHOME + 'flicket-rest-api'
    ADMINHOME = '/flicket_admin/'

    NOTIFICATION = {
        'name': 'notification',
        'username': 'notification',
        'password': config_data.get('NOTIFICATION_USER_PASSWORD', 'dummy_pass'),
        'email': 'admin@localhost'
    }

    SUPPORTED_LANGUAGES = {'en': 'English', 'fr': 'Francais'}
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'

    # --- 5. CONDITIONAL DB CHECK ---
    if not os.environ.get('TF_BUILD'):
        check_db_connection(SQLALCHEMY_DATABASE_URI)


class TestConfiguration(BaseConfiguration):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'test.db')
    WTF_CSRF_ENABLED = False
    TESTING = True
    SESSION_PROTECTION = None
    LOGIN_DISABLED = False
    SERVER_NAME = 'localhost:5001'
    config_data = {"db_username": "", "db_port": "", "db_password": "",
                   "db_name": "", "db_url": ""}