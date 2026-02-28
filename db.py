"""
Database connection management for PeopleSoft MCP.
Provides centralized query execution with async support.
"""
import os
import oracledb
from typing import Any
from dotenv import load_dotenv

load_dotenv()


def get_connection_params() -> dict[str, str]:
    """Get database connection parameters from environment variables."""
    dsn = os.getenv("ORACLE_DSN")
    user = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    
    if not all([dsn, user, password]):
        raise ValueError(
            "Missing database credentials. Set ORACLE_DSN, ORACLE_USER, and ORACLE_PASSWORD environment variables."
        )
    
    return {"dsn": dsn, "user": user, "password": password}


async def execute_query(
    sql: str, 
    params: list[Any] | None = None,
    fetch_one: bool = False
) -> dict:
    """
    Execute a SQL query and return results as a dictionary.
    
    Args:
        sql: The SQL query to execute
        params: Optional list of bind parameters
        fetch_one: If True, return only the first row
        
    Returns:
        Dictionary with 'results' key containing list of row dicts,
        or 'error' key if an error occurred
    """
    if params is None:
        params = []
    
    try:
        conn_params = get_connection_params()
        async with oracledb.connect_async(
            user=conn_params["user"],
            password=conn_params["password"],
            dsn=conn_params["dsn"]
        ) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, params)
                
                if cursor.description is None:
                    return {"results": [], "message": "Query executed successfully (no results)"}
                
                columns = [col[0] for col in cursor.description]
                
                if fetch_one:
                    row = await cursor.fetchone()
                    if row:
                        return {"results": [dict(zip(columns, row))]}
                    return {"results": []}
                
                rows = await cursor.fetchall()
                return {"results": [dict(zip(columns, row)) for row in rows]}
                
    except oracledb.Error as e:
        return {"error": f"Database error: {str(e)}"}
    except ValueError as e:
        return {"error": str(e)}


async def execute_query_with_limit(
    sql: str,
    params: list[Any] | None = None,
    limit: int = 100
) -> dict:
    """
    Execute a query with a row limit to prevent accidentally fetching too much data.
    
    Args:
        sql: The SQL query to execute
        params: Optional list of bind parameters
        limit: Maximum number of rows to return (default 100)
        
    Returns:
        Dictionary with results and a flag indicating if results were truncated
    """
    if params is None:
        params = []
    
    try:
        conn_params = get_connection_params()
        async with oracledb.connect_async(
            user=conn_params["user"],
            password=conn_params["password"],
            dsn=conn_params["dsn"]
        ) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, params)
                
                if cursor.description is None:
                    return {"results": [], "truncated": False}
                
                columns = [col[0] for col in cursor.description]
                rows = await cursor.fetchmany(limit + 1)
                
                truncated = len(rows) > limit
                if truncated:
                    rows = rows[:limit]
                
                return {
                    "results": [dict(zip(columns, row)) for row in rows],
                    "truncated": truncated,
                    "row_count": len(rows)
                }
                
    except oracledb.Error as e:
        return {"error": f"Database error: {str(e)}"}
    except ValueError as e:
        return {"error": str(e)}
