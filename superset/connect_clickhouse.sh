#!/bin/bash
DB_NAME="ClickHouse"
SQLALCHEMY_URI="clickhouse+http://default:@clickhouse:8123/default"

python <<EOF
from superset.models.core import Database
from superset import app, db

with app.app_context():
    existing_db = db.session.query(Database).filter_by(database_name="$DB_NAME").first()
    if not existing_db:
        new_db = Database(
            database_name="$DB_NAME",
            sqlalchemy_uri="$SQLALCHEMY_URI",
            allow_csv_upload=True,
            allow_run_async=True,
            expose_in_sqllab=True,
        )
        db.session.add(new_db)
        db.session.commit()
        print(f"Database {DB_NAME} added successfully.")
    else:
        print(f"Database {DB_NAME} already exists.")
EOF
