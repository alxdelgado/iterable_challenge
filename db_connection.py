"""
Database Connection Module
Handles SQL database connections and query execution for Iterable integration
"""

import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages MySQL database connections and queries"""

    def __init__(self, host: str, user: str, password: str, database: str):
        """
        Initialize database connection parameters

        Args:
            host: Database host (e.g., localhost)
            user: Database username
            password: Database password
            database: Database name
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self) -> bool:
        """
        Establish connection to MySQL database

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                logger.info(f"Successfully connected to database: {self.database}")
                return True
        except Error as e:
            logger.error(f"Error connecting to database: {e}")
            return False

    def disconnect(self) -> None:
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute SELECT query and return results as list of dictionaries

        Args:
            query: SQL SELECT query to execute

        Returns:
            List of dictionaries containing query results, empty list if error
        """
        if not self.connection or not self.connection.is_connected():
            logger.error("Database connection not established")
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            logger.info(f"Query executed successfully, returned {len(results)} rows")
            return results
        except Error as e:
            logger.error(f"Error executing query: {e}")
            return []

    def get_pro_users_recent_engagement(self) -> List[Dict[str, Any]]:
        """
        Execute Phase 2 Query 2: Get pro plan users with recent pricing/settings page views
        Returns only the latest view per user in the last 7 days

        Returns:
            List of dictionaries with user and page view data
        """
        query = """
        WITH ranked_views AS (
            SELECT 
                c.id,
                c.email,
                c.first_name,
                c.last_name,
                c.plan_type,
                c.candidate,
                pv.page,
                pv.device,
                pv.browser,
                pv.location,
                pv.event_time,
                ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY pv.event_time DESC) as view_rank
            FROM customers c
            INNER JOIN page_views pv ON c.id = pv.user_id
            WHERE c.plan_type = 'pro'
                AND pv.page IN ('pricing', 'settings')
                AND pv.event_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        )
        SELECT 
            id,
            email,
            first_name,
            last_name,
            plan_type,
            candidate,
            page,
            device,
            browser,
            location,
            event_time
        FROM ranked_views
        WHERE view_rank = 1
        ORDER BY event_time DESC;
        """
        return self.execute_query(query)
