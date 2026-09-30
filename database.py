import sqlite3
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "pocketsmart.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS recommendation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            planner_type TEXT NOT NULL,
            input_data TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS session_data (
            user_id INTEGER PRIMARY KEY,
            data TEXT NOT NULL DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS saved_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            recommendation_id INTEGER NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE CASCADE,

            FOREIGN KEY (recommendation_id)
            REFERENCES recommendation_history(id)
            ON DELETE CASCADE,

            UNIQUE(user_id, recommendation_id)
        )
        """
    )

    connection.commit()
    connection.close()


def add_recommendation(
    user_id,
    planner_type,
    input_data,
    recommendation
):
    connection = get_connection()
    cursor = connection.cursor()

    if not isinstance(input_data, str):
        input_data = json.dumps(
            input_data,
            ensure_ascii=False
        )

    cursor.execute(
        """
        INSERT INTO recommendation_history
        (
            user_id,
            planner_type,
            input_data,
            recommendation
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            planner_type,
            input_data,
            recommendation
        )
    )

    recommendation_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return recommendation_id


def get_history(user_id, limit=50):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            planner_type,
            input_data,
            recommendation,
            created_at
        FROM recommendation_history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            user_id,
            limit
        )
    )

    rows = cursor.fetchall()

    connection.close()

    history = []

    for row in rows:
        item = dict(row)

        try:
            item["input_data"] = json.loads(
                item["input_data"]
            )
        except Exception:
            pass

        history.append(item)

    return history


def get_recommendation(
    recommendation_id,
    user_id
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            planner_type,
            input_data,
            recommendation,
            created_at
        FROM recommendation_history
        WHERE id = ?
        AND user_id = ?
        """,
        (
            recommendation_id,
            user_id
        )
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    item = dict(row)

    try:
        item["input_data"] = json.loads(
            item["input_data"]
        )
    except Exception:
        pass

    return item


def get_session_data(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT data
        FROM session_data
        WHERE user_id = ?
        """,
        (user_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return {}

    try:
        return json.loads(row["data"])
    except Exception:
        return {}


def save_session_data(user_id, data):
    connection = get_connection()
    cursor = connection.cursor()

    data_json = json.dumps(
        data,
        ensure_ascii=False
    )

    cursor.execute(
        """
        INSERT INTO session_data
        (
            user_id,
            data,
            updated_at
        )
        VALUES (
            ?,
            ?,
            CURRENT_TIMESTAMP
        )

        ON CONFLICT(user_id)
        DO UPDATE SET
            data = excluded.data,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            data_json
        )
    )

    connection.commit()
    connection.close()


def save_recommendation(
    user_id,
    recommendation_id
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO saved_recommendations
        (
            user_id,
            recommendation_id
        )
        VALUES (?, ?)
        """,
        (
            user_id,
            recommendation_id
        )
    )

    connection.commit()
    connection.close()


def remove_saved_recommendation(
    user_id,
    recommendation_id
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM saved_recommendations
        WHERE user_id = ?
        AND recommendation_id = ?
        """,
        (
            user_id,
            recommendation_id
        )
    )

    connection.commit()
    connection.close()


def get_saved_recommendations(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            r.id,
            r.planner_type,
            r.input_data,
            r.recommendation,
            r.created_at,
            s.saved_at
        FROM saved_recommendations s

        JOIN recommendation_history r
        ON r.id = s.recommendation_id

        WHERE s.user_id = ?

        ORDER BY s.id DESC
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    connection.close()

    results = []

    for row in rows:
        item = dict(row)

        try:
            item["input_data"] = json.loads(
                item["input_data"]
            )
        except Exception:
            pass

        results.append(item)

    return results


init_database()