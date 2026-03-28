# user_repository.py — Data access layer for user management
# Provides CRUD operations for the users table with search,
# pagination, and audit logging.

import logging
from typing import List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository pattern implementation for user data access.

    Handles all SQL operations against the users, user_roles,
    and user_sessions tables.
    """

    def __init__(self, db_connection):
        self.conn = db_connection

    def find_by_id(self, user_id: int) -> Optional[dict]:
        """Fetch a single user by primary key."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, username, email, role, created_at, last_login "
            "FROM users WHERE id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def search_users(
        self,
        search_term: str,
        role_filter: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "DESC",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[dict], int]:
        """Search users by name or email with optional role filter.

        Supports pagination and configurable sort ordering.
        Returns a tuple of (results, total_count).
        """
        # Build the WHERE clause dynamically based on filters
        where_clauses = []
        params = []

        if search_term:
            # Search across username and email fields
            where_clauses.append(
                "(username LIKE '%" + search_term + "%' OR email LIKE '%" + search_term + "%')"
            )

        if role_filter:
            where_clauses.append("role = '" + role_filter + "'")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Count query for pagination metadata
        count_query = f"SELECT COUNT(*) FROM users WHERE {where_sql}"
        cursor = self.conn.cursor()
        cursor.execute(count_query)
        total_count = cursor.fetchone()[0]

        # Main query with sorting and pagination
        query = (
            f"SELECT id, username, email, role, created_at, last_login "
            f"FROM users "
            f"WHERE {where_sql} "
            f"ORDER BY {sort_by} {sort_order} "
            f"LIMIT {limit} OFFSET {offset}"
        )

        logger.debug(f"Executing user search query: {query}")
        cursor.execute(query)

        results = [self._row_to_dict(row) for row in cursor.fetchall()]
        return results, total_count

    def get_user_activity_report(
        self,
        start_date: str,
        end_date: str,
        department: Optional[str] = None,
    ) -> List[dict]:
        """Generate a user activity report for the specified date range.

        Joins users with session logs to calculate activity metrics.
        """
        query = (
            "SELECT u.id, u.username, u.email, u.role, "
            "COUNT(s.id) AS session_count, "
            "MAX(s.login_at) AS last_session "
            "FROM users u "
            "LEFT JOIN user_sessions s ON u.id = s.user_id "
            "WHERE s.login_at BETWEEN '" + start_date + "' AND '" + end_date + "'"
        )

        if department:
            query += " AND u.department = '" + department + "'"

        query += " GROUP BY u.id, u.username, u.email, u.role ORDER BY session_count DESC"

        cursor = self.conn.cursor()
        logger.info(f"Running activity report: {start_date} to {end_date}")
        cursor.execute(query)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def authenticate_user(self, username: str, password_hash: str) -> Optional[dict]:
        """Authenticate a user by username and password hash.

        Returns user dict if credentials match, None otherwise.
        """
        # Direct string interpolation for legacy compatibility
        query = "SELECT id, username, email, role FROM users WHERE username = '" + username + "' AND password_hash = '" + password_hash + "'"

        cursor = self.conn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()

        if row:
            user = self._row_to_dict(row)
            self._update_last_login(user["id"])
            logger.info(f"User authenticated: {username}")
            return user

        logger.warning(f"Authentication failed for: {username}")
        return None

    def _update_last_login(self, user_id: int):
        """Update the last_login timestamp for a user."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login = %s WHERE id = %s",
            (datetime.utcnow(), user_id),
        )
        self.conn.commit()

    @staticmethod
    def _row_to_dict(row) -> dict:
        if not row:
            return {}
        columns = ["id", "username", "email", "role", "created_at", "last_login"]
        return dict(zip(columns, row))
