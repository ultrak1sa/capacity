import os

SQLALCHEMY_DATABASE_URI = os.environ.get('SUPERSET_SQLALCHEMY_DATABASE_URI')
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'your_secret_key')

FEATURE_FLAGS = {
    "DISABLE_SQLALCHEMY_WARNINGS": True,
}

SQLALCHEMY_BINDS = {
    "clickhouse": "clickhouse+http://default:@clickhouse:8123/default"
}