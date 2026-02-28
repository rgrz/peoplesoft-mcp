"""
Schema introspection tools for PeopleSoft MCP.
These tools allow dynamic discovery of the PeopleSoft data model.
"""
from db import execute_query, execute_query_with_limit


def register_tools(mcp):
    """Register all introspection tools with the MCP server."""
    
    @mcp.tool()
    async def describe_table(table_name: str) -> dict:
        """
        Get the structure of a PeopleSoft table/record including all fields, 
        their types, lengths, and descriptions.
        
        Use this tool FIRST when you need to understand what fields are available
        in a table before writing queries.
        
        :param table_name: The PeopleSoft record name (e.g., 'PERSONAL_DATA', 'JOB', 'DEPT_TBL').
                          Can include or exclude the 'PS_' prefix.
        :return: List of fields with their properties
        """
        clean_name = table_name.upper().replace("PS_", "")
        
        sql = """
            SELECT 
                RF.FIELDNAME,
                RF.FIELDNUM,
                DF.FIELDTYPE,
                DF.LENGTH,
                DF.DECIMALPOS,
                DF.DESCRLONG AS DESCRIPTION,
                CASE WHEN RF.USEEDIT LIKE '%K%' THEN 'Y' ELSE 'N' END AS IS_KEY,
                CASE WHEN RF.USEEDIT LIKE '%R%' THEN 'Y' ELSE 'N' END AS IS_REQUIRED,
                CASE WHEN DF.FIELDTYPE = 1 THEN 'XLAT' ELSE NULL END AS HAS_TRANSLATE
            FROM PSRECFIELD RF
            JOIN PSDBFIELD DF ON RF.FIELDNAME = DF.FIELDNAME
            WHERE RF.RECNAME = :1
            ORDER BY RF.FIELDNUM
        """
        
        result = await execute_query(sql, [clean_name])
        
        if "error" in result:
            return result
            
        if not result.get("results"):
            return {"error": f"Table '{table_name}' not found. Try list_tables() to search for tables."}
        
        field_type_map = {
            0: "CHARACTER",
            1: "LONG_CHARACTER", 
            2: "NUMBER",
            3: "SIGNED_NUMBER",
            4: "DATE",
            5: "TIME",
            6: "DATETIME",
            8: "IMAGE",
            9: "IMAGE_REF"
        }
        
        fields = []
        for row in result["results"]:
            field = {
                "field_name": row["FIELDNAME"],
                "position": row["FIELDNUM"],
                "type": field_type_map.get(row["FIELDTYPE"], f"UNKNOWN({row['FIELDTYPE']})"),
                "length": row["LENGTH"],
                "decimals": row["DECIMALPOS"] if row["DECIMALPOS"] else None,
                "description": row["DESCRIPTION"],
                "is_key": row["IS_KEY"] == "Y",
                "is_required": row["IS_REQUIRED"] == "Y",
                "has_translate_values": row["FIELDTYPE"] == 1 or row["HAS_TRANSLATE"] == "XLAT"
            }
            fields.append(field)
        
        return {
            "table_name": f"PS_{clean_name}",
            "record_name": clean_name,
            "field_count": len(fields),
            "fields": fields
        }

    @mcp.tool()
    async def list_tables(
        pattern: str | None = None, 
        module: str | None = None,
        limit: int = 50
    ) -> dict:
        """
        Search for PeopleSoft tables/records by name pattern or module.
        
        :param pattern: Optional search pattern (e.g., 'EMPLOYEE', 'JOB', 'GP_RSLT').
                       Searches with wildcards automatically.
        :param module: Optional module filter. Values:
                      - 'HR' or 'CORE': Core HR tables (PERSONAL_DATA, JOB, DEPT, etc.)
                      - 'GP' or 'PAYROLL': Global Payroll tables (GP_*)
                      - 'EP' or 'PERFORMANCE': ePerformance tables (EP_*)
                      - 'BN' or 'BENEFITS': Benefits tables (BEN_*, DEPENDENT_*)
                      - 'SYSTEM': PeopleTools system tables (PS* without underscore)
        :param limit: Maximum number of results (default 50)
        :return: List of matching tables with descriptions
        """
        conditions = ["R.RECTYPE = 0"]
        params = []
        
        if pattern:
            clean_pattern = pattern.upper().replace("PS_", "").replace("*", "%").replace("?", "_")
            if "%" not in clean_pattern:
                clean_pattern = f"%{clean_pattern}%"
            conditions.append("R.RECNAME LIKE :1")
            params.append(clean_pattern)
        
        if module:
            module_upper = module.upper()
            if module_upper in ("HR", "CORE"):
                conditions.append("""
                    (R.RECNAME LIKE 'PERSONAL%' OR R.RECNAME LIKE 'JOB%' 
                     OR R.RECNAME LIKE 'DEPT%' OR R.RECNAME LIKE 'LOCATION%'
                     OR R.RECNAME LIKE 'COMPANY%' OR R.RECNAME LIKE 'EMPLOYMENT%'
                     OR R.RECNAME LIKE 'ADDRESS%' OR R.RECNAME LIKE 'POSITION%'
                     OR R.RECNAME LIKE 'COMPENSATION%' OR R.RECNAME LIKE 'CONTRACT%')
                """)
            elif module_upper in ("GP", "PAYROLL"):
                conditions.append("R.RECNAME LIKE 'GP\\_%' ESCAPE '\\'")
            elif module_upper in ("EP", "PERFORMANCE"):
                conditions.append("R.RECNAME LIKE 'EP\\_%' ESCAPE '\\'")
            elif module_upper in ("BN", "BENEFITS"):
                conditions.append("""
                    (R.RECNAME LIKE 'BEN\\_%' ESCAPE '\\' 
                     OR R.RECNAME LIKE 'DEPENDENT%' 
                     OR R.RECNAME LIKE 'BENEF%')
                """)
            elif module_upper == "SYSTEM":
                conditions.append("R.RECNAME NOT LIKE '%\\_%' ESCAPE '\\'")
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
            SELECT 
                R.RECNAME,
                R.RECDESCR,
                R.PARENTRECNAME,
                (SELECT COUNT(*) FROM PSRECFIELD RF WHERE RF.RECNAME = R.RECNAME) AS FIELD_COUNT
            FROM PSRECDEFN R
            WHERE {where_clause}
            ORDER BY R.RECNAME
            FETCH FIRST :limit ROWS ONLY
        """
        params.append(limit)
        
        result = await execute_query(sql, params)
        
        if "error" in result:
            return result
        
        tables = []
        for row in result["results"]:
            tables.append({
                "record_name": row["RECNAME"],
                "table_name": f"PS_{row['RECNAME']}",
                "description": row["RECDESCR"],
                "parent_record": row["PARENTRECNAME"] if row["PARENTRECNAME"] else None,
                "field_count": row["FIELD_COUNT"]
            })
        
        return {
            "count": len(tables),
            "tables": tables
        }

    @mcp.tool()
    async def get_translate_values(field_name: str) -> dict:
        """
        Get all valid translate values for a PeopleSoft field.
        
        Many PeopleSoft fields use single or double letter codes that have
        specific meanings. This tool decodes those values.
        
        Common examples:
        - SEX: 'M' = Male, 'F' = Female
        - HR_STATUS: 'A' = Active, 'I' = Inactive
        - EMPL_STATUS: 'A' = Active, 'T' = Terminated, 'L' = Leave, etc.
        - MAR_STATUS: 'S' = Single, 'M' = Married, 'D' = Divorced
        
        :param field_name: The field name to look up (e.g., 'SEX', 'HR_STATUS', 'EMPL_STATUS')
        :return: List of valid values with their short and long descriptions
        """
        clean_name = field_name.upper()
        
        sql = """
            SELECT 
                X.FIELDVALUE,
                X.XLATSHORTNAME,
                X.XLATLONGNAME,
                X.EFF_STATUS,
                X.EFFDT
            FROM PSXLATITEM X
            WHERE X.FIELDNAME = :1
            AND X.EFFDT = (
                SELECT MAX(X2.EFFDT) 
                FROM PSXLATITEM X2 
                WHERE X2.FIELDNAME = X.FIELDNAME 
                AND X2.FIELDVALUE = X.FIELDVALUE
                AND X2.EFFDT <= SYSDATE
            )
            ORDER BY X.FIELDVALUE
        """
        
        result = await execute_query(sql, [clean_name])
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {
                "field_name": clean_name,
                "message": f"No translate values found for '{clean_name}'. This field may not use translate values.",
                "values": []
            }
        
        values = []
        for row in result["results"]:
            values.append({
                "code": row["FIELDVALUE"],
                "short_name": row["XLATSHORTNAME"],
                "long_name": row["XLATLONGNAME"],
                "active": row["EFF_STATUS"] == "A"
            })
        
        return {
            "field_name": clean_name,
            "value_count": len(values),
            "values": values
        }

    @mcp.tool()
    async def get_table_indexes(table_name: str) -> dict:
        """
        Get the index keys for a PeopleSoft table to help write efficient queries.
        
        Understanding indexes helps you:
        - Write WHERE clauses that use indexed fields for better performance
        - Understand the logical key structure of a table
        - Know which fields uniquely identify a row
        
        Common PeopleSoft key patterns:
        - Simple: EMPLID (employee ID only)
        - Effective-dated: EMPLID, EMPL_RCD, EFFDT, EFFSEQ
        - SetID-based: SETID, DEPTID, EFFDT
        
        :param table_name: The PeopleSoft record name (e.g., 'JOB', 'PERSONAL_DATA')
        :return: List of indexes with their key fields
        """
        clean_name = table_name.upper().replace("PS_", "")
        
        sql = """
            SELECT 
                K.INDEXID,
                K.KEYPOSN,
                K.FIELDNAME,
                CASE K.INDEXID 
                    WHEN '_' THEN 'PRIMARY'
                    WHEN 'A' THEN 'ALTERNATE_A'
                    WHEN 'B' THEN 'ALTERNATE_B'
                    WHEN 'C' THEN 'ALTERNATE_C'
                    ELSE 'INDEX_' || K.INDEXID
                END AS INDEX_TYPE
            FROM PSKEYDEFN K
            WHERE K.RECNAME = :1
            ORDER BY K.INDEXID, K.KEYPOSN
        """
        
        result = await execute_query(sql, [clean_name])
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {"error": f"No indexes found for table '{table_name}'. The table may not exist."}
        
        indexes = {}
        for row in result["results"]:
            idx_id = row["INDEXID"]
            if idx_id not in indexes:
                indexes[idx_id] = {
                    "index_id": idx_id,
                    "index_type": row["INDEX_TYPE"],
                    "fields": []
                }
            indexes[idx_id]["fields"].append({
                "position": row["KEYPOSN"],
                "field_name": row["FIELDNAME"]
            })
        
        primary_keys = []
        if "_" in indexes:
            primary_keys = [f["field_name"] for f in indexes["_"]["fields"]]
        
        return {
            "table_name": f"PS_{clean_name}",
            "record_name": clean_name,
            "primary_key_fields": primary_keys,
            "indexes": list(indexes.values())
        }

    @mcp.tool()
    async def get_table_relationships(table_name: str) -> dict:
        """
        Find tables related to the specified table by analyzing shared key fields.
        
        This helps discover:
        - Parent/child relationships
        - Common join patterns
        - Related configuration tables
        
        :param table_name: The PeopleSoft record name to analyze
        :return: List of potentially related tables grouped by relationship type
        """
        clean_name = table_name.upper().replace("PS_", "")
        
        key_sql = """
            SELECT K.FIELDNAME
            FROM PSKEYDEFN K
            WHERE K.RECNAME = :1 AND K.INDEXID = '_'
            ORDER BY K.KEYPOSN
        """
        
        key_result = await execute_query(key_sql, [clean_name])
        
        if "error" in key_result:
            return key_result
        
        if not key_result.get("results"):
            return {"error": f"Table '{table_name}' not found or has no primary key."}
        
        key_fields = [r["FIELDNAME"] for r in key_result["results"]]
        
        if not key_fields:
            return {"message": "No key fields found for this table."}
        
        placeholders = ", ".join([f":{i+1}" for i in range(len(key_fields))])
        
        related_sql = f"""
            SELECT DISTINCT 
                RF.RECNAME,
                RD.RECDESCR,
                COUNT(*) AS SHARED_KEY_COUNT
            FROM PSRECFIELD RF
            JOIN PSRECDEFN RD ON RF.RECNAME = RD.RECNAME
            WHERE RF.FIELDNAME IN ({placeholders})
            AND RF.RECNAME != :rec_name
            AND RD.RECTYPE = 0
            GROUP BY RF.RECNAME, RD.RECDESCR
            HAVING COUNT(*) >= 1
            ORDER BY COUNT(*) DESC, RF.RECNAME
            FETCH FIRST 30 ROWS ONLY
        """
        
        params = key_fields + [clean_name]
        related_result = await execute_query(related_sql, params)
        
        if "error" in related_result:
            return related_result
        
        related_tables = []
        for row in related_result["results"]:
            related_tables.append({
                "record_name": row["RECNAME"],
                "table_name": f"PS_{row['RECNAME']}",
                "description": row["RECDESCR"],
                "shared_key_fields": row["SHARED_KEY_COUNT"],
                "relationship_strength": "strong" if row["SHARED_KEY_COUNT"] >= len(key_fields) else "partial"
            })
        
        return {
            "source_table": f"PS_{clean_name}",
            "key_fields": key_fields,
            "related_table_count": len(related_tables),
            "related_tables": related_tables
        }
