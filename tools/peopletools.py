"""
PeopleTools semantic tools for understanding PeopleSoft architecture and configuration.
These tools query PeopleTools metadata tables to explain how the system works.
"""
from db import execute_query


def register_tools(mcp):
    """Register all PeopleTools tools with the MCP server."""
    mcp.tool()(get_record_definition)
    mcp.tool()(search_records)
    mcp.tool()(get_component_structure)
    mcp.tool()(get_component_pages)
    mcp.tool()(get_page_fields)
    mcp.tool()(get_page_field_bindings)
    mcp.tool()(get_peoplecode)
    mcp.tool()(get_permission_list_details)
    mcp.tool()(get_roles_for_permission_list)
    mcp.tool()(get_process_definition)
    mcp.tool()(get_application_engine_steps)
    mcp.tool()(get_integration_broker_services)
    mcp.tool()(get_message_definition)
    mcp.tool()(get_query_definition)
    mcp.tool()(get_sql_definition)
    mcp.tool()(search_sql_definitions)
    mcp.tool()(search_peoplecode)
    mcp.tool()(get_field_usage)
    mcp.tool()(get_translate_field_values)
    mcp.tool()(explain_peoplesoft_concept)


async def get_record_definition(record_name: str) -> dict:
    """
    Get complete definition of a PeopleSoft record including all fields,
    keys, and properties. Essential for understanding data structures.
    
    Args:
        record_name: The record name (e.g., 'JOB', 'PERSONAL_DATA')
                    Will automatically add PS_ prefix if not present
    
    Returns:
        Record metadata including type, fields, keys, and parent record
    """
    # Normalize record name
    if not record_name.upper().startswith("PS_"):
        record_name = record_name.upper()
    else:
        record_name = record_name.upper().replace("PS_", "")
    
    # Get record header info
    record_sql = """
        SELECT 
            R.RECNAME,
            R.RECTYPE,
            CASE R.RECTYPE 
                WHEN 0 THEN 'SQL Table'
                WHEN 1 THEN 'SQL View'
                WHEN 2 THEN 'Derived/Work Record'
                WHEN 3 THEN 'Sub Record'
                WHEN 5 THEN 'Dynamic View'
                WHEN 6 THEN 'Query View'
                WHEN 7 THEN 'Temporary Table'
                ELSE 'Unknown'
            END AS RECTYPE_DESC,
            R.RECDESCR,
            R.PARENTRECNAME,
            R.SQLTABLENAME,
            R.BUILDSEQNO,
            R.AUXFLAGMASK
        FROM PSRECDEFN R
        WHERE R.RECNAME = :1
    """
    record_result = await execute_query(record_sql, [record_name], fetch_one=True)
    
    if "error" in record_result or not record_result.get("results"):
        return {"error": f"Record '{record_name}' not found"}
    
    record_info = record_result["results"][0]
    
    # Get all fields with their properties
    fields_sql = """
        SELECT 
            F.FIELDNAME,
            F.FIELDNUM,
            F.USEEDIT,
            D.FIELDTYPE,
            CASE D.FIELDTYPE
                WHEN 0 THEN 'Character'
                WHEN 1 THEN 'Long Character'
                WHEN 2 THEN 'Number'
                WHEN 3 THEN 'Signed Number'
                WHEN 4 THEN 'Date'
                WHEN 5 THEN 'Time'
                WHEN 6 THEN 'DateTime'
                WHEN 8 THEN 'Image'
                WHEN 9 THEN 'Image Reference'
                ELSE 'Other'
            END AS FIELDTYPE_DESC,
            D.LENGTH,
            D.DECIMALPOS,
            DBMS_LOB.SUBSTR(D.DESCRLONG, 4000, 1) AS DESCRLONG
        FROM PSRECFIELD F
        JOIN PSDBFIELD D ON F.FIELDNAME = D.FIELDNAME
        WHERE F.RECNAME = :1
        ORDER BY F.FIELDNUM
    """
    fields_result = await execute_query(fields_sql, [record_name])
    
    # Get key fields (primary key is INDEXID = '_')
    keys_sql = """
        SELECT 
            K.FIELDNAME,
            K.KEYPOSN,
            K.INDEXID,
            CASE K.ASCDESC
                WHEN 0 THEN 'Ascending'
                WHEN 1 THEN 'Descending'
                ELSE 'Unknown'
            END AS SORT_ORDER,
            CASE K.INDEXID
                WHEN '_' THEN 'Primary Key'
                ELSE 'Alternate Key ' || K.INDEXID
            END AS KEY_TYPE
        FROM PSKEYDEFN K
        WHERE K.RECNAME = :1
        AND K.INDEXID = '_'
        ORDER BY K.KEYPOSN
    """
    keys_result = await execute_query(keys_sql, [record_name])
    
    # Get indexes
    indexes_sql = """
        SELECT 
            I.INDEXID,
            I.UNIQUEFLAG,
            I.CLUSTERFLAG,
            I.ACTIVEFLAG,
            I.PLATFORM_SBS
        FROM PSINDEXDEFN I
        WHERE I.RECNAME = :1
    """
    indexes_result = await execute_query(indexes_sql, [record_name])
    
    return {
        "record": record_info,
        "fields": fields_result.get("results", []),
        "keys": keys_result.get("results", []),
        "indexes": indexes_result.get("results", []),
        "field_count": len(fields_result.get("results", []))
    }


async def search_records(search_term: str, record_type: int | None = None) -> dict:
    """
    Search for PeopleSoft records by name or description.
    
    Args:
        search_term: Partial name or description to search for
        record_type: Optional filter by type (0=Table, 1=View, 2=Derived, 7=Temp)
    
    Returns:
        List of matching records with their types and descriptions
    """
    params = [f"%{search_term.upper()}%", f"%{search_term.upper()}%"]
    
    type_filter = ""
    if record_type is not None:
        type_filter = "AND R.RECTYPE = :3"
        params.append(record_type)
    
    sql = f"""
        SELECT 
            R.RECNAME,
            R.RECTYPE,
            CASE R.RECTYPE 
                WHEN 0 THEN 'SQL Table'
                WHEN 1 THEN 'SQL View'
                WHEN 2 THEN 'Derived/Work'
                WHEN 3 THEN 'Sub Record'
                WHEN 5 THEN 'Dynamic View'
                WHEN 6 THEN 'Query View'
                WHEN 7 THEN 'Temp Table'
                ELSE 'Unknown'
            END AS RECTYPE_DESC,
            R.RECDESCR,
            R.PARENTRECNAME
        FROM PSRECDEFN R
        WHERE (R.RECNAME LIKE :1 OR UPPER(R.RECDESCR) LIKE :2)
        {type_filter}
        ORDER BY R.RECNAME
        FETCH FIRST 50 ROWS ONLY
    """
    return await execute_query(sql, params)


async def get_component_structure(component_name: str) -> dict:
    """
    Get the structure of a PeopleSoft component including its pages,
    records, and navigation path.
    
    Args:
        component_name: The component name (e.g., 'JOB_DATA', 'PERSONAL_DATA')
    
    Returns:
        Component definition with pages, records, and menu navigation
    """
    component_name = component_name.upper()
    
    # Get component definition (SAVEWARN omitted - not in all PeopleTools versions)
    comp_sql = """
        SELECT 
            C.PNLGRPNAME AS COMPONENT_NAME,
            C.DESCR,
            C.MARKET,
            C.SEARCHRECNAME,
            C.ADDSRCHRECNAME,
            C.ACTIONS,
            C.PRIMARYACTION,
            C.DFLTACTION,
            C.DEFERPROC
        FROM PSPNLGRPDEFN C
        WHERE C.PNLGRPNAME = :1
    """
    comp_result = await execute_query(comp_sql, [component_name], fetch_one=True)
    
    if "error" in comp_result or not comp_result.get("results"):
        return {"error": f"Component '{component_name}' not found"}
    
    # Get pages in the component (SUBITEMNUM - ITEMNUM not in all PeopleTools versions)
    pages_sql = """
        SELECT 
            P.PNLNAME AS PAGE_NAME,
            P.SUBITEMNUM AS ITEMNUM,
            P.HIDDEN,
            P.ITEMLABEL,
            PD.DESCR AS PAGE_DESCR
        FROM PSPNLGROUP P
        LEFT JOIN PSPNLDEFN PD ON P.PNLNAME = PD.PNLNAME
        WHERE P.PNLGRPNAME = :1
        ORDER BY P.SUBITEMNUM
    """
    pages_result = await execute_query(pages_sql, [component_name])
    
    # Get menu navigation to this component
    menu_sql = """
        SELECT 
            M.MENUNAME,
            M.BARNAME,
            M.BARITEMNAME,
            M.ITEMNAME,
            M.ITEMLABEL,
            M.PNLGRPNAME AS COMPONENT
        FROM PSMENUITEM M
        WHERE M.PNLGRPNAME = :1
        ORDER BY M.MENUNAME, M.BARNAME
    """
    menu_result = await execute_query(menu_sql, [component_name])
    
    return {
        "component": comp_result.get("results", [{}])[0],
        "pages": pages_result.get("results", []),
        "menu_navigation": menu_result.get("results", [])
    }


async def get_component_pages(component_name: str) -> dict:
    """
    Get lightweight component-to-pages mapping. Uses only PSPNLGRPDEFN and
    PSPNLGROUP with version-safe columns.
    
    Args:
        component_name: The component name (e.g., 'JOB_DATA', 'ABSV_PLAN_TABLE')
    
    Returns:
        Component name, search record, and list of pages with item number and label
    """
    component_name = component_name.upper()
    
    comp_sql = """
        SELECT C.PNLGRPNAME, C.SEARCHRECNAME
        FROM PSPNLGRPDEFN C
        WHERE C.PNLGRPNAME = :1
    """
    comp_result = await execute_query(comp_sql, [component_name], fetch_one=True)
    
    if "error" in comp_result or not comp_result.get("results"):
        return {"error": f"Component '{component_name}' not found"}
    
    pages_sql = """
        SELECT P.PNLNAME, P.SUBITEMNUM AS ITEMNUM, P.ITEMLABEL
        FROM PSPNLGROUP P
        WHERE P.PNLGRPNAME = :1
        ORDER BY P.SUBITEMNUM
    """
    pages_result = await execute_query(pages_sql, [component_name])
    
    comp_info = comp_result["results"][0]
    return {
        "component_name": comp_info.get("PNLGRPNAME"),
        "search_record": comp_info.get("SEARCHRECNAME"),
        "pages": pages_result.get("results", [])
    }


async def get_page_fields(page_name: str) -> dict:
    """
    Get all fields defined on a PeopleSoft page with their properties.
    
    Args:
        page_name: The page name (e.g., 'JOB_DATA1', 'PERSONAL_DATA_1')
    
    Returns:
        Page definition with all field controls and their record/field bindings
    """
    page_name = page_name.upper()
    
    # Get page header
    page_sql = """
        SELECT 
            P.PNLNAME,
            P.VERSION,
            P.DESCR,
            P.PNLTYPE,
            CASE P.PNLTYPE
                WHEN 0 THEN 'Standard Page'
                WHEN 1 THEN 'Sub Page'
                WHEN 2 THEN 'Secondary Page'
                WHEN 3 THEN 'Popup Page'
                ELSE 'Unknown'
            END AS PNLTYPE_DESC,
            P.HELPCONTEXTNUM
        FROM PSPNLDEFN P
        WHERE P.PNLNAME = :1
    """
    page_result = await execute_query(page_sql, [page_name], fetch_one=True)
    
    if "error" in page_result or not page_result.get("results"):
        return {"error": f"Page '{page_name}' not found"}
    
    # Get fields on the page (DSPCTLFLDNAME/DSPCNTRLRECNAME omitted - not in all PeopleTools versions)
    fields_sql = """
        SELECT 
            F.FIELDNUM,
            F.FIELDTYPE,
            CASE F.FIELDTYPE
                WHEN 0 THEN 'Frame'
                WHEN 1 THEN 'Group Box'
                WHEN 2 THEN 'Static Text'
                WHEN 3 THEN 'Static Image'
                WHEN 4 THEN 'Edit Box'
                WHEN 5 THEN 'Drop Down'
                WHEN 6 THEN 'Long Edit'
                WHEN 7 THEN 'Check Box'
                WHEN 8 THEN 'Radio Button'
                WHEN 9 THEN 'Image'
                WHEN 10 THEN 'Scroll Bar'
                WHEN 11 THEN 'Scroll Area'
                WHEN 12 THEN 'Subpage'
                WHEN 14 THEN 'Push Button'
                WHEN 15 THEN 'Link'
                WHEN 17 THEN 'Grid'
                WHEN 19 THEN 'Tree'
                WHEN 26 THEN 'HTML Area'
                WHEN 29 THEN 'Chart'
                ELSE 'Other (' || F.FIELDTYPE || ')'
            END AS FIELD_TYPE_DESC,
            F.RECNAME,
            F.FIELDNAME,
            F.LBLTEXT,
            F.OCCURSLEVEL
        FROM PSPNLFIELD F
        WHERE F.PNLNAME = :1
        ORDER BY F.OCCURSLEVEL, F.FIELDNUM
    """
    fields_result = await execute_query(fields_sql, [page_name])
    
    return {
        "page": page_result.get("results", [{}])[0],
        "fields": fields_result.get("results", []),
        "field_count": len(fields_result.get("results", []))
    }


async def get_page_field_bindings(page_name: str) -> dict:
    """
    Get simplified page field bindings: RECNAME, FIELDNAME, FIELDNUM, OCCURSLEVEL only.
    Lightweight alternative when full page field properties are not needed.
    
    Args:
        page_name: The page name (e.g., 'JOB_DATA1', 'ABSV_PLAN_TABLE')
    
    Returns:
        Page name and list of record/field bindings
    """
    page_name = page_name.upper()
    
    page_check_sql = """
        SELECT PNLNAME FROM PSPNLDEFN WHERE PNLNAME = :1
    """
    page_check = await execute_query(page_check_sql, [page_name], fetch_one=True)
    
    if "error" in page_check or not page_check.get("results"):
        return {"error": f"Page '{page_name}' not found"}
    
    bindings_sql = """
        SELECT F.RECNAME, F.FIELDNAME, F.FIELDNUM, F.OCCURSLEVEL
        FROM PSPNLFIELD F
        WHERE F.PNLNAME = :1
        ORDER BY F.OCCURSLEVEL, F.FIELDNUM
    """
    bindings_result = await execute_query(bindings_sql, [page_name])
    
    return {
        "page_name": page_name,
        "bindings": bindings_result.get("results", []),
        "binding_count": len(bindings_result.get("results", []))
    }


async def get_peoplecode(
    record_name: str, 
    field_name: str | None = None, 
    event: str | None = None,
    include_code: bool = True,
    max_code_length: int = 32000
) -> dict:
    """
    Get PeopleCode programs attached to a record/field, including the actual source code.
    
    Reads from PSPCMTXT which stores the PeopleCode source as CLOB. Use this to
    understand component logic, trace field behavior, or analyze customizations.
    
    Args:
        record_name: The record name (e.g., 'JOB', 'ABSV_REQUEST')
        field_name: Optional field name to filter (e.g., 'EMPLID', 'EFFDT')
        event: Optional event type filter. Common events:
               - RowInit: Fires when row is loaded
               - FieldChange: Fires when field value changes
               - FieldEdit: Validates field before accepting
               - SaveEdit: Validates before save
               - SavePreChange: Runs before database update
               - SavePostChange: Runs after database update
               - RowDelete: Fires when row is deleted
               - RowInsert: Fires when new row inserted
               - SearchInit: Fires on search page load
               - SearchSave: Fires when search is executed
        include_code: If True (default), returns actual PeopleCode source.
                     Set to False for just metadata/listing.
        max_code_length: Maximum characters of code to return per program (default 32000).
                        Use for large programs that may exceed response limits.
    
    Returns:
        List of PeopleCode programs with their events and source code.
        Programs are ordered by field name and event for logical reading.
    
    Example:
        # Get all PeopleCode for ABSV_REQUEST record
        get_peoplecode("ABSV_REQUEST")
        
        # Get just FieldChange events for BEGIN_DT field
        get_peoplecode("ABSV_REQUEST", "BEGIN_DT", "FieldChange")
        
        # List all events without code (for discovery)
        get_peoplecode("JOB", include_code=False)
    """
    record_name = record_name.upper()
    params = [record_name]
    
    field_filter = ""
    if field_name:
        field_filter = "AND OBJECTVALUE2 = :2"
        params.append(field_name.upper())
    
    event_filter = ""
    if event:
        event_idx = len(params) + 1
        event_filter = f"AND OBJECTVALUE3 = :{event_idx}"
        params.append(event)
    
    if include_code:
        # Use DBMS_LOB.SUBSTR to extract CLOB content
        # PSPCMTXT stores: OBJECTVALUE1=Record, OBJECTVALUE2=Field, OBJECTVALUE3=Event
        sql = f"""
            SELECT 
                OBJECTVALUE1 AS RECORD_NAME,
                OBJECTVALUE2 AS FIELD_NAME,
                OBJECTVALUE3 AS EVENT,
                PROGSEQ,
                DBMS_LOB.SUBSTR(PCTEXT, :code_len, 1) AS PEOPLECODE,
                DBMS_LOB.GETLENGTH(PCTEXT) AS CODE_LENGTH
            FROM PSPCMTXT
            WHERE OBJECTID1 = 1
            AND OBJECTVALUE1 = :1
            {field_filter}
            {event_filter}
            ORDER BY OBJECTVALUE2, OBJECTVALUE3, PROGSEQ
        """
        # Add max_code_length as first parameter
        params = [max_code_length] + params
    else:
        # Metadata only - faster for discovery
        sql = f"""
            SELECT 
                OBJECTVALUE1 AS RECORD_NAME,
                OBJECTVALUE2 AS FIELD_NAME,
                OBJECTVALUE3 AS EVENT,
                DBMS_LOB.GETLENGTH(PCTEXT) AS CODE_LENGTH
            FROM PSPCMTXT
            WHERE OBJECTID1 = 1
            AND OBJECTVALUE1 = :1
            {field_filter}
            {event_filter}
            ORDER BY OBJECTVALUE2, OBJECTVALUE3
        """
    
    result = await execute_query(sql, params)
    
    if "error" not in result:
        result["record_name"] = record_name
        result["program_count"] = len(result.get("results", []))
        if field_name:
            result["field_filter"] = field_name
        if event:
            result["event_filter"] = event
    
    return result


async def get_permission_list_details(permission_list: str) -> dict:
    """
    Get details of a permission list including pages, components, and query access.
    
    Args:
        permission_list: The permission list name
    
    Returns:
        Permission list definition with component and page access
    """
    permission_list = permission_list.upper()
    
    # Get permission list header
    header_sql = """
        SELECT 
            C.CLASSID AS PERMISSION_LIST,
            C.DESCR,
            C.CLASSDEFNTYPE,
            C.EFFDT
        FROM PSCLASSDEFN C
        WHERE C.CLASSID = :1
    """
    header_result = await execute_query(header_sql, [permission_list], fetch_one=True)
    
    if "error" in header_result or not header_result.get("results"):
        return {"error": f"Permission List '{permission_list}' not found"}
    
    # Get menu/component access
    component_sql = """
        SELECT 
            A.MENUNAME,
            A.BARNAME,
            A.BARITEMNAME,
            A.PNLGRPNAME AS COMPONENT,
            A.MARKET,
            A.AUTHVALUE
        FROM PSAUTHITEM A
        WHERE A.CLASSID = :1
        ORDER BY A.MENUNAME, A.PNLGRPNAME
        FETCH FIRST 100 ROWS ONLY
    """
    component_result = await execute_query(component_sql, [permission_list])
    
    # Get query access
    query_sql = """
        SELECT 
            Q.QRYNAME,
            Q.ACCESSLVL,
            CASE Q.ACCESSLVL
                WHEN 0 THEN 'No Access'
                WHEN 1 THEN 'Run Only'
                WHEN 2 THEN 'Read Only'
                WHEN 10 THEN 'Full Access'
                ELSE 'Other'
            END AS ACCESS_DESC
        FROM PSQRYACCLST Q
        WHERE Q.CLASSID = :1
        ORDER BY Q.QRYNAME
        FETCH FIRST 50 ROWS ONLY
    """
    query_result = await execute_query(query_sql, [permission_list])
    
    return {
        "permission_list": header_result.get("results", [{}])[0],
        "component_access": component_result.get("results", []),
        "query_access": query_result.get("results", [])
    }


async def get_roles_for_permission_list(permission_list: str) -> dict:
    """
    Find all roles that include a specific permission list.
    
    Args:
        permission_list: The permission list name
    
    Returns:
        List of roles containing this permission list
    """
    sql = """
        SELECT 
            RC.ROLENAME,
            R.DESCR AS ROLE_DESCR,
            RC.CLASSID AS PERMISSION_LIST
        FROM PSROLECLASS RC
        JOIN PSROLEDEFN R ON RC.ROLENAME = R.ROLENAME
        WHERE RC.CLASSID = :1
        ORDER BY RC.ROLENAME
    """
    return await execute_query(sql, [permission_list.upper()])


async def get_process_definition(process_name: str = None, process_type: str = None) -> dict:
    """
    Get process scheduler definitions.
    
    Args:
        process_name: Optional specific process name
        process_type: Optional filter by type (e.g., 'SQR Report', 'Application Engine')
    
    Returns:
        Process definitions with their configuration
    """
    params = []
    conditions = []
    
    if process_name:
        conditions.append("P.PRCSNAME LIKE :1")
        params.append(f"%{process_name.upper()}%")
    
    if process_type:
        idx = len(params) + 1
        conditions.append(f"P.PRCSTYPE LIKE :{idx}")
        params.append(f"%{process_type.upper()}%")
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    sql = f"""
        SELECT 
            P.PRCSTYPE,
            P.PRCSNAME,
            P.DESCR,
            P.PRCSCATEGORY,
            P.PRCSCLASS,
            P.OUTDESTTYPE,
            CASE P.OUTDESTTYPE
                WHEN 1 THEN 'None'
                WHEN 2 THEN 'File'
                WHEN 3 THEN 'Printer'
                WHEN 4 THEN 'Email'
                WHEN 5 THEN 'Web'
                WHEN 6 THEN 'Window'
                ELSE 'Other'
            END AS OUTPUT_TYPE_DESC,
            P.OUTDESTFORMAT
        FROM PS_PRCSDEFN P
        {where_clause}
        ORDER BY P.PRCSTYPE, P.PRCSNAME
        FETCH FIRST 50 ROWS ONLY
    """
    return await execute_query(sql, params if params else None)


async def get_application_engine_steps(ae_program: str) -> dict:
    """
    Get the steps and sections of an Application Engine program.
    
    Args:
        ae_program: The AE program name
    
    Returns:
        Program structure with sections, steps, and actions
    """
    ae_program = ae_program.upper()
    
    # Get AE program header (AE_CMD_BTN_ENABLED omitted - not in all PeopleTools versions)
    header_sql = """
        SELECT 
            A.AE_APPLID AS PROGRAM_NAME,
            A.DESCR,
            A.AE_DISABLE_RESTART,
            A.OBJECTOWNERID
        FROM PSAEAPPLDEFN A
        WHERE A.AE_APPLID = :1
    """
    header_result = await execute_query(header_sql, [ae_program], fetch_one=True)
    
    if "error" in header_result or not header_result.get("results"):
        return {"error": f"Application Engine '{ae_program}' not found"}
    
    # Get sections and steps (AE_SEQ_NUM, AE_ACTIVE_STATUS - AE_STEP_NBR/EFF_STATUS not in all PeopleTools versions)
    steps_sql = """
        SELECT 
            S.AE_SECTION AS SECTION_NAME,
            S.AE_STEP AS STEP_NAME,
            S.AE_SEQ_NUM AS STEP_ORDER,
            S.MARKET,
            S.EFFDT,
            S.AE_ACTIVE_STATUS AS EFF_STATUS,
            S.DESCR AS STEP_DESCR
        FROM PSAESTEPDEFN S
        WHERE S.AE_APPLID = :1
        ORDER BY S.AE_SECTION, S.AE_SEQ_NUM
    """
    steps_result = await execute_query(steps_sql, [ae_program])
    
    return {
        "program": header_result.get("results", [{}])[0],
        "steps": steps_result.get("results", [])
    }


async def get_integration_broker_services(service_name: str = None) -> dict:
    """
    Get Integration Broker service operations and their configuration.
    
    Args:
        service_name: Optional service name filter
    
    Returns:
        Service definitions with their operations
    """
    params = []
    where_clause = ""
    
    if service_name:
        where_clause = "WHERE IB_SERVICE LIKE :1"
        params.append(f"%{service_name.upper()}%")
    
    sql = f"""
        SELECT 
            S.IB_SERVICE,
            S.VERSION,
            S.DESCR,
            S.IB_OPERATIONNAME,
            S.IB_OPERATIONTYPE,
            CASE S.IB_OPERATIONTYPE
                WHEN 'A' THEN 'Asynchronous'
                WHEN 'S' THEN 'Synchronous'
                ELSE S.IB_OPERATIONTYPE
            END AS OPERATION_TYPE_DESC,
            S.REQUESTMSGNAME,
            S.RESPONSEMSGNAME,
            S.QUEUENAME
        FROM PSOPERATION S
        {where_clause}
        ORDER BY S.IB_SERVICE, S.IB_OPERATIONNAME
        FETCH FIRST 50 ROWS ONLY
    """
    return await execute_query(sql, params if params else None)


async def get_message_definition(message_name: str) -> dict:
    """
    Get the structure of an Integration Broker message.
    
    Args:
        message_name: The message name
    
    Returns:
        Message definition with parts and records
    """
    message_name = message_name.upper()
    
    # Get message header
    msg_sql = """
        SELECT 
            M.MSGNAME,
            M.VERSION,
            M.DESCR,
            M.MSGNODENAME,
            M.MSGSCHEMANAME,
            M.ACTV_FLAG
        FROM PSMSGDEFN M
        WHERE M.MSGNAME = :1
    """
    msg_result = await execute_query(msg_sql, [message_name], fetch_one=True)
    
    if "error" in msg_result or not msg_result.get("results"):
        return {"error": f"Message '{message_name}' not found"}
    
    # Get message parts/records
    parts_sql = """
        SELECT 
            P.MSGNAME,
            P.PARTNAME,
            P.RECNAME,
            P.PARTSORT,
            P.PARTTYPE
        FROM PSMSGPARTDEFN P
        WHERE P.MSGNAME = :1
        ORDER BY P.PARTSORT
    """
    parts_result = await execute_query(parts_sql, [message_name])
    
    return {
        "message": msg_result.get("results", [{}])[0],
        "parts": parts_result.get("results", [])
    }


async def get_query_definition(query_name: str) -> dict:
    """
    Get a PS Query definition including its records, fields, and criteria.
    
    Args:
        query_name: The query name
    
    Returns:
        Query definition with records, fields, and criteria
    """
    query_name = query_name.upper()
    
    # Get query header
    query_sql = """
        SELECT 
            Q.QRYNAME,
            Q.DESCR,
            Q.QRYTYPE,
            CASE Q.QRYTYPE
                WHEN 0 THEN 'User Query'
                WHEN 1 THEN 'Role Query'
                WHEN 2 THEN 'Public Query'
                ELSE 'Unknown'
            END AS QUERY_TYPE_DESC,
            Q.OPRID AS OWNER,
            Q.LASTUPDDTTM,
            Q.LASTUPDOPRID
        FROM PSQRYDEFN Q
        WHERE Q.QRYNAME = :1
    """
    query_result = await execute_query(query_sql, [query_name], fetch_one=True)
    
    if "error" in query_result or not query_result.get("results"):
        return {"error": f"Query '{query_name}' not found"}
    
    # Get query records
    records_sql = """
        SELECT 
            R.RECNAME,
            R.CORRNAME AS ALIAS,
            R.RECTYPE,
            R.PARENTREC,
            R.PARENTCORRNAME
        FROM PSQRYRECORD R
        WHERE R.QRYNAME = :1
        ORDER BY R.RECNAME
    """
    records_result = await execute_query(records_sql, [query_name])
    
    # Get query fields
    fields_sql = """
        SELECT 
            F.QRYNAME,
            F.FIELDNUM,
            F.RECNAME,
            F.FIELDNAME,
            F.HEADING,
            F.ORDERBYNUM,
            F.ORDERBYDESCFLG
        FROM PSQRYFIELD F
        WHERE F.QRYNAME = :1
        ORDER BY F.FIELDNUM
    """
    fields_result = await execute_query(fields_sql, [query_name])
    
    return {
        "query": query_result.get("results", [{}])[0],
        "records": records_result.get("results", []),
        "fields": fields_result.get("results", [])
    }


async def get_sql_definition(sql_id: str, max_length: int = 64000) -> dict:
    """
    Get the SQL text for a PeopleSoft SQL object by SQLID.
    
    PSSQLTEXTDEFN stores SQL used by views, App Engine programs, and PeopleCode
    (SQL.SQLID). Long SQL is split across multiple rows by SEQNUM.
    
    Args:
        sql_id: The SQL object ID (e.g. 'HR_ABSV_JOB_EFFDT', 'GP_PIN_SELECT')
        max_length: Maximum total characters to return (default 64000).
                    Use to avoid huge responses for very long SQL.
    
    Returns:
        SQL definition with sql_text (concatenated from all SEQNUM rows),
        sql_type, market, and row_count.
    
    Example:
        get_sql_definition("HR_ABSV_JOB_EFFDT")
    """
    sql_id = sql_id.upper()
    
    # Fetch all segments ordered by SEQNUM; use DBMS_LOB.SUBSTR for CLOB
    sql = """
        SELECT 
            SQLID,
            SQLTYPE,
            MARKET,
            SEQNUM,
            DBMS_LOB.SUBSTR(SQLTEXT, 14000, 1) AS SQLTEXT
        FROM PSSQLTEXTDEFN
        WHERE SQLID = :1
        ORDER BY SEQNUM
    """
    result = await execute_query(sql, [sql_id])
    
    if "error" in result:
        return result
    
    rows = result.get("results", [])
    if not rows:
        return {"error": f"SQL object '{sql_id}' not found"}
    
    # Concatenate SQL text from all segments
    segments = []
    total_len = 0
    for row in rows:
        txt = row.get("SQLTEXT") or ""
        if isinstance(txt, str) and total_len < max_length:
            remainder = max_length - total_len
            segments.append(txt[:remainder] if len(txt) > remainder else txt)
            total_len += len(txt)
        elif hasattr(txt, "read"):  # LOB object
            content = txt.read() if callable(getattr(txt, "read", None)) else str(txt)
            if total_len < max_length:
                remainder = max_length - total_len
                segments.append(content[:remainder] if len(content) > remainder else content)
                total_len += len(content)
    
    sql_text = "".join(segments)
    truncated = total_len >= max_length
    
    sql_type_desc = {
        "0": "Standard SQL",
        "1": "PeopleCode",
        "2": "COBOL",
        "3": "SQR",
    }
    
    return {
        "sql_id": sql_id,
        "sql_type": rows[0].get("SQLTYPE", ""),
        "sql_type_desc": sql_type_desc.get(rows[0].get("SQLTYPE", ""), "Unknown"),
        "market": rows[0].get("MARKET", ""),
        "sql_text": sql_text,
        "segment_count": len(rows),
        "truncated": truncated,
    }


async def search_sql_definitions(search_term: str, limit: int = 50) -> dict:
    """
    Search for SQL object IDs whose text contains the given term.
    
    Useful for discovering which SQL objects reference a table, field, or
    other identifier. Does not return full SQL text—use get_sql_definition
    for that.
    
    Args:
        search_term: Text to search for in SQL (e.g. 'PS_JOB', 'ABSV_REQUEST')
        limit: Maximum number of SQLIDs to return (default 50)
    
    Returns:
        List of matching SQLIDs with sql_type and market.
    
    Example:
        search_sql_definitions("PS_ABSV_REQUEST")
    """
    search_pattern = f"%{search_term.upper()}%"
    
    # Use DBMS_LOB.INSTR for CLOB search; ROWNUM for limit (bind var compatibility)
    sql = """
        SELECT * FROM (
            SELECT DISTINCT S.SQLID, S.SQLTYPE, S.MARKET
            FROM PSSQLTEXTDEFN S
            WHERE DBMS_LOB.INSTR(S.SQLTEXT, :1) > 0
            ORDER BY S.SQLID
        ) WHERE ROWNUM <= :2
    """
    result = await execute_query(sql, [search_pattern, limit])
    
    if "error" in result:
        return result
    
    rows = result.get("results", [])
    sql_type_desc = {"0": "Standard SQL", "1": "PeopleCode", "2": "COBOL", "3": "SQR"}
    
    return {
        "search_term": search_term,
        "matches": [
            {
                "sql_id": r["SQLID"],
                "sql_type": r.get("SQLTYPE", ""),
                "sql_type_desc": sql_type_desc.get(r.get("SQLTYPE", ""), "Unknown"),
                "market": r.get("MARKET", ""),
            }
            for r in rows
        ],
        "match_count": len(rows),
    }


async def search_peoplecode(search_term: str, search_in: str = "all") -> dict:
    """
    Search for text within PeopleCode programs.
    
    Args:
        search_term: Text to search for in PeopleCode
        search_in: Where to search - 'all', 'record', 'component', 'appengine'
    
    Returns:
        List of PeopleCode locations containing the search term
    """
    search_term_upper = search_term.upper()
    
    # Search in record PeopleCode
    if search_in in ("all", "record"):
        rec_sql = """
            SELECT 
                'Record' AS LOCATION_TYPE,
                P.RECNAME,
                P.FIELDNAME,
                P.EVENT,
                P.LASTUPDOPRID,
                P.LASTUPDDTTM
            FROM PSPCMPROG P
            WHERE UPPER(P.PROGTXT) LIKE :1
            FETCH FIRST 25 ROWS ONLY
        """
        rec_result = await execute_query(rec_sql, [f"%{search_term_upper}%"])
    else:
        rec_result = {"results": []}
    
    # Search in Component PeopleCode
    if search_in in ("all", "component"):
        comp_sql = """
            SELECT 
                'Component' AS LOCATION_TYPE,
                C.PNLGRPNAME AS COMPONENT,
                C.MARKET,
                C.EVENT,
                C.LASTUPDOPRID,
                C.LASTUPDDTTM
            FROM PSPCMPROG_COMP C
            WHERE UPPER(C.PROGTXT) LIKE :1
            FETCH FIRST 25 ROWS ONLY
        """
        comp_result = await execute_query(comp_sql, [f"%{search_term_upper}%"])
    else:
        comp_result = {"results": []}
    
    # Search in App Engine PeopleCode
    if search_in in ("all", "appengine"):
        ae_sql = """
            SELECT 
                'App Engine' AS LOCATION_TYPE,
                A.AE_APPLID AS PROGRAM,
                A.AE_SECTION AS SECTION,
                A.AE_STEP AS STEP
            FROM PSAESTEPMSGDEFN A
            WHERE UPPER(A.AE_PEOPLECODEPC) LIKE :1
            FETCH FIRST 25 ROWS ONLY
        """
        ae_result = await execute_query(ae_sql, [f"%{search_term_upper}%"])
    else:
        ae_result = {"results": []}
    
    return {
        "search_term": search_term,
        "record_peoplecode": rec_result.get("results", []),
        "component_peoplecode": comp_result.get("results", []),
        "appengine_peoplecode": ae_result.get("results", []),
        "total_found": (
            len(rec_result.get("results", [])) +
            len(comp_result.get("results", [])) +
            len(ae_result.get("results", []))
        )
    }


async def get_field_usage(field_name: str) -> dict:
    """
    Find all records that use a specific field - useful for impact analysis.
    
    Args:
        field_name: The field name to search for
    
    Returns:
        List of records containing this field and key information
    """
    field_name = field_name.upper()
    
    sql = """
        SELECT 
            F.RECNAME,
            R.RECTYPE,
            CASE R.RECTYPE 
                WHEN 0 THEN 'SQL Table'
                WHEN 1 THEN 'SQL View'
                WHEN 2 THEN 'Derived/Work'
                WHEN 7 THEN 'Temp Table'
                ELSE 'Other'
            END AS RECTYPE_DESC,
            F.FIELDNUM,
            F.USEEDIT,
            NVL2(K.FIELDNAME, 'Yes', 'No') AS IS_KEY
        FROM PSRECFIELD F
        JOIN PSRECDEFN R ON F.RECNAME = R.RECNAME
        LEFT JOIN PSKEYDEFN K ON F.RECNAME = K.RECNAME AND F.FIELDNAME = K.FIELDNAME
        WHERE F.FIELDNAME = :1
        ORDER BY R.RECTYPE, F.RECNAME
        FETCH FIRST 100 ROWS ONLY
    """
    result = await execute_query(sql, [field_name])
    
    if "error" not in result:
        result["field_name"] = field_name
        result["record_count"] = len(result.get("results", []))
    
    return result


async def get_translate_field_values(field_name: str) -> dict:
    """
    Get all translate values for a field with their effective dates.
    
    Args:
        field_name: The field name that uses translate values
    
    Returns:
        All translate values with descriptions and effective dates
    """
    sql = """
        SELECT 
            X.FIELDNAME,
            X.FIELDVALUE,
            X.EFFDT,
            X.EFF_STATUS,
            X.XLATLONGNAME,
            X.XLATSHORTNAME,
            X.LASTUPDDTTM
        FROM PSXLATITEM X
        WHERE X.FIELDNAME = :1
        ORDER BY X.FIELDVALUE, X.EFFDT DESC
    """
    return await execute_query(sql, [field_name.upper()])


async def explain_peoplesoft_concept(concept: str) -> dict:
    """
    Provide explanation of PeopleSoft/PeopleTools concepts based on actual
    system metadata and configuration.
    
    Args:
        concept: The concept to explain (e.g., 'effective_dating', 'component', 
                'record_types', 'security', 'integration_broker')
    
    Returns:
        Relevant system metadata that illustrates the concept
    """
    concept_lower = concept.lower()
    
    if "effective" in concept_lower or "effdt" in concept_lower:
        # Show tables with effective dating
        sql = """
            SELECT DISTINCT
                R.RECNAME,
                R.RECDESCR,
                CASE R.RECTYPE 
                    WHEN 0 THEN 'SQL Table'
                    WHEN 1 THEN 'SQL View'
                    ELSE 'Other'
                END AS RECTYPE
            FROM PSRECDEFN R
            JOIN PSRECFIELD F ON R.RECNAME = F.RECNAME
            WHERE F.FIELDNAME = 'EFFDT'
            AND R.RECTYPE IN (0, 1)
            ORDER BY R.RECNAME
            FETCH FIRST 30 ROWS ONLY
        """
        result = await execute_query(sql)
        result["concept"] = "Effective Dating"
        result["explanation"] = (
            "PeopleSoft uses effective-dated records to maintain history. "
            "EFFDT (Effective Date) marks when a row becomes active. "
            "To get current data, use: EFFDT = (SELECT MAX(EFFDT) WHERE EFFDT <= SYSDATE)"
        )
        return result
    
    elif "setid" in concept_lower or "tableset" in concept_lower:
        # Show SetID usage
        sql = """
            SELECT DISTINCT
                R.RECNAME,
                R.RECDESCR
            FROM PSRECDEFN R
            JOIN PSRECFIELD F ON R.RECNAME = F.RECNAME
            WHERE F.FIELDNAME = 'SETID'
            AND R.RECTYPE = 0
            ORDER BY R.RECNAME
            FETCH FIRST 30 ROWS ONLY
        """
        result = await execute_query(sql)
        result["concept"] = "SetID / TableSet Sharing"
        result["explanation"] = (
            "SetID enables sharing control tables across business units. "
            "Instead of duplicating data, BUs can share the same SetID. "
            "Use PS_SET_CNTRL_REC to find which SetID a BU uses for a record."
        )
        return result
    
    elif "record" in concept_lower and "type" in concept_lower:
        # Show record type distribution
        sql = """
            SELECT 
                R.RECTYPE,
                CASE R.RECTYPE 
                    WHEN 0 THEN 'SQL Table'
                    WHEN 1 THEN 'SQL View'
                    WHEN 2 THEN 'Derived/Work Record'
                    WHEN 3 THEN 'Sub Record'
                    WHEN 5 THEN 'Dynamic View'
                    WHEN 6 THEN 'Query View'
                    WHEN 7 THEN 'Temporary Table'
                    ELSE 'Unknown'
                END AS RECTYPE_DESC,
                COUNT(*) AS RECORD_COUNT
            FROM PSRECDEFN R
            GROUP BY R.RECTYPE
            ORDER BY R.RECTYPE
        """
        result = await execute_query(sql)
        result["concept"] = "PeopleSoft Record Types"
        result["explanation"] = (
            "Type 0 (SQL Table): Physical database tables. "
            "Type 1 (SQL View): Database views. "
            "Type 2 (Derived/Work): Runtime only, no DB storage. "
            "Type 7 (Temp Table): Used by App Engine for processing."
        )
        return result
    
    elif "security" in concept_lower or "permission" in concept_lower:
        # Show security structure
        sql = """
            SELECT 
                (SELECT COUNT(*) FROM PSCLASSDEFN) AS PERMISSION_LISTS,
                (SELECT COUNT(*) FROM PSROLEDEFN) AS ROLES,
                (SELECT COUNT(*) FROM PSOPRDEFN) AS USERS,
                (SELECT COUNT(*) FROM PSAUTHITEM) AS AUTH_ITEMS
            FROM DUAL
        """
        result = await execute_query(sql)
        result["concept"] = "PeopleSoft Security Model"
        result["explanation"] = (
            "Security flows: User -> Roles -> Permission Lists -> Access. "
            "Permission Lists grant access to components, pages, queries. "
            "Users can have multiple Roles, Roles can have multiple Permission Lists."
        )
        return result
    
    else:
        return {
            "concept": concept,
            "explanation": "Concept not found. Try: effective_dating, setid, record_types, security",
            "available_concepts": [
                "effective_dating", "setid", "tableset", "record_types", "security", "permission"
            ]
        }
