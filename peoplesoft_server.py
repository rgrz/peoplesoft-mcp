"""
PeopleSoft MCP Server - A Model Context Protocol server for querying PeopleSoft databases.
"""
import os
from pathlib import Path
from fastmcp import FastMCP
from db import execute_query, execute_query_with_limit

mcp = FastMCP("peoplesoft-mcp")

REFERENCE_DIR = Path(__file__).parent / "Reference_Documents"


@mcp.resource("peoplesoft://schema-guide")
def get_schema_guide() -> str:
    """
    PeopleSoft Schema Guide - Lists all major tables organized by module 
    (HR, Payroll, Performance, Benefits, System).
    """
    path = REFERENCE_DIR / "peoplesoft_schema_guide.md"
    return path.read_text()


@mcp.resource("peoplesoft://concepts")
def get_concepts_guide() -> str:
    """
    PeopleSoft Concepts Primer - Explains effective dating, EMPLID/EMPL_RCD,
    SetID, translate values, and action codes.
    """
    path = REFERENCE_DIR / "peoplesoft_concepts.md"
    return path.read_text()


@mcp.resource("peoplesoft://query-examples")
def get_query_examples() -> str:
    """
    SQL Query Examples - Real-world PeopleSoft query patterns including
    effective-dated queries, joins, and common HR/Payroll queries.
    """
    path = REFERENCE_DIR / "sql_query_examples.yaml"
    return path.read_text()


@mcp.resource("peoplesoft://key-tables")
def get_key_tables() -> str:
    """
    Key Tables Reference - Quick reference for the most important 
    PeopleSoft tables with their indexes and key columns.
    """
    path = REFERENCE_DIR / "key_tables.yaml"
    return path.read_text()


@mcp.resource("peoplesoft://peopletools-guide")
def get_peopletools_guide() -> str:
    """
    PeopleTools Architecture Guide - Explains records, pages, components,
    PeopleCode events, security, Process Scheduler, Application Engine,
    and Integration Broker.
    """
    path = REFERENCE_DIR / "peopletools_guide.md"
    return path.read_text()


@mcp.tool()
async def query_peoplesoft_db(sql_query: str, parameters: list | None = None) -> dict:
    """
    Query PeopleSoft Oracle Database directly.
    
    When working with a PeopleSoft database, follow these guidelines in order:

    1. FIRST, always check the record structure and fields:
       - Use: SELECT RECNAME, FIELDNAME FROM PSRECFIELD WHERE RECNAME = 'YOUR_TABLE'
       - This shows all fields in a record/table and helps prevent invalid field errors
    
    2. SECOND, check field properties and translations:
       - For field details: SELECT * FROM PSDBFIELD WHERE FIELDNAME = 'YOUR_FIELD'
       - For code translations: 
           * ALWAYS check PSXLATITEM and PSXLATITEMLANG for single/double letter codes
           * Example: 'M'/'F' for SEX, 'SP'/'C' for RELATIONSHIP, 'Y'/'N' for flags
           * Query: SELECT FIELDNAME, FIELDVALUE, XLATLONGNAME, XLATSHORTNAME 
                   FROM PSXLATITEM 
                   WHERE FIELDNAME = 'YOUR_FIELD'
       - Understanding field properties ensures correct data handling
    
    3. THIRD, review table indexes for performance:
       - Use: SELECT * FROM PSKEYDEFN WHERE RECNAME = 'YOUR_TABLE'
       - Knowing indexes helps write efficient queries using indexed fields

    4. FINALLY, write your query using the discovered structure
       - Example finding employee data:
         1. Check PSRECFIELD for PS_PERSONAL_DATA fields
         2. Look up important fields in PSDBFIELD
         3. Check PSKEYDEFN for PS_PERSONAL_DATA indexes
         4. Write optimized query using indexed fields
         5. Don't forget to join with PSXLATITEM for any code fields

    AVAILABLE RESOURCES:
    - Use describe_table() to get table structure
    - Use list_tables() to search for tables
    - Use get_translate_values() to decode field codes
    - Use get_table_indexes() for performance optimization
    
    :param sql_query: SQL query to execute (e.g., SELECT * FROM PS_EMPLOYEE WHERE EMPLID = :1)
    :param parameters: List of query parameters (optional)
    :return: A dictionary containing query results or an error message
    """
    if parameters is None:
        parameters = []
    return await execute_query(sql_query, parameters)


# Import and register tools from modules
from tools.introspection import register_tools as register_introspection_tools
register_introspection_tools(mcp)

from tools.hr import register_tools as register_hr_tools
register_hr_tools(mcp)

from tools.payroll import register_tools as register_payroll_tools
register_payroll_tools(mcp)

from tools.performance import register_tools as register_performance_tools
register_performance_tools(mcp)

from tools.benefits import register_tools as register_benefits_tools
register_benefits_tools(mcp)

from tools.peopletools import register_tools as register_peopletools_tools
register_peopletools_tools(mcp)


if __name__ == "__main__":
    mcp.run()
