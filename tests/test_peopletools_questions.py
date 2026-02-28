"""
Test suite for PeopleTools semantic tools.
Contains realistic questions a technical consultant would ask when maintaining a PeopleSoft system.
"""
import asyncio
import pytest
from db import execute_query
from tools.peopletools import (
    get_record_definition,
    search_records,
    get_component_structure,
    get_page_fields,
    get_peoplecode,
    get_permission_list_details,
    get_roles_for_permission_list,
    get_process_definition,
    get_application_engine_steps,
    get_integration_broker_services,
    get_message_definition,
    get_query_definition,
    search_peoplecode,
    get_field_usage,
    get_translate_field_values,
    explain_peoplesoft_concept,
)


class TestRecordInvestigation:
    """
    Scenario: Consultant needs to understand record structures for customization or debugging.
    """

    @pytest.mark.asyncio
    async def test_understand_job_record_structure(self):
        """
        Question: I need to customize PS_JOB - what fields does it have and what are the keys?
        Context: Before adding a custom field or writing a query
        """
        result = await get_record_definition("JOB")
        
        assert "error" not in result
        assert result["record"]["RECTYPE_DESC"] == "SQL Table"
        assert result["field_count"] > 0
        assert len(result["keys"]) > 0
        
        print(f"\n=== PS_JOB Record Structure ===")
        print(f"Type: {result['record']['RECTYPE_DESC']}")
        print(f"Total Fields: {result['field_count']}")
        print(f"Primary Keys: {', '.join(k['FIELDNAME'] for k in result['keys'])}")
        print(f"\nFirst 10 fields:")
        for f in result["fields"][:10]:
            print(f"  {f['FIELDNAME']} ({f['FIELDTYPE_DESC']}, len={f['LENGTH']})")

    @pytest.mark.asyncio
    async def test_find_personal_data_tables(self):
        """
        Question: What tables store personal/employee information?
        Context: Need to find where employee data is stored for a report
        """
        result = await search_records("PERSONAL")
        
        assert "error" not in result
        assert len(result["results"]) > 0
        
        print(f"\n=== Records containing 'PERSONAL' ===")
        print(f"Found: {len(result['results'])} records")
        tables = [r for r in result["results"] if r["RECTYPE_DESC"] == "SQL Table"]
        views = [r for r in result["results"] if r["RECTYPE_DESC"] == "SQL View"]
        print(f"  SQL Tables: {len(tables)}")
        print(f"  SQL Views: {len(views)}")
        for r in result["results"][:10]:
            print(f"  {r['RECNAME']} ({r['RECTYPE_DESC']}): {r.get('RECDESCR', 'N/A')}")

    @pytest.mark.asyncio
    async def test_find_compensation_records(self):
        """
        Question: What records are related to compensation?
        Context: Building a compensation report or integration
        """
        result = await search_records("COMPENS")
        
        assert "error" not in result
        
        print(f"\n=== Compensation-related Records ===")
        print(f"Found: {len(result['results'])} records")
        for r in result["results"][:15]:
            print(f"  {r['RECNAME']} ({r['RECTYPE_DESC']})")

    @pytest.mark.asyncio
    async def test_understand_view_vs_table(self):
        """
        Question: Is EMPLOYEES a table or a view? What's its structure?
        Context: Determining if we can insert/update or only select
        """
        result = await search_records("EMPLOYEES", record_type=1)  # Views only
        
        assert "error" not in result
        
        print(f"\n=== Employee Views ===")
        print(f"Found: {len(result['results'])} views")
        for r in result["results"][:10]:
            print(f"  {r['RECNAME']}: {r.get('RECDESCR', 'N/A')}")


class TestImpactAnalysis:
    """
    Scenario: Consultant needs to assess impact before making changes.
    """

    @pytest.mark.asyncio
    async def test_where_is_emplid_used(self):
        """
        Question: Where is the EMPLID field used? I need to understand its scope.
        Context: Planning a change that affects employee identification
        """
        result = await get_field_usage("EMPLID")
        
        assert "error" not in result
        assert result["record_count"] > 0
        
        print(f"\n=== EMPLID Field Usage ===")
        print(f"Used in {result['record_count']} records")
        tables = [r for r in result["results"] if r["RECTYPE_DESC"] == "SQL Table"]
        key_tables = [r for r in result["results"] if r["IS_KEY"] == "Yes"]
        print(f"  In SQL Tables: {len(tables)}")
        print(f"  As Key Field: {len(key_tables)}")
        print(f"\nFirst 10 usages:")
        for r in result["results"][:10]:
            key_marker = " [KEY]" if r["IS_KEY"] == "Yes" else ""
            print(f"  {r['RECNAME']} ({r['RECTYPE_DESC']}){key_marker}")

    @pytest.mark.asyncio
    async def test_where_is_deptid_used(self):
        """
        Question: We're changing department structure - where is DEPTID used?
        Context: Major org restructuring, need full impact analysis
        """
        result = await get_field_usage("DEPTID")
        
        assert "error" not in result
        
        print(f"\n=== DEPTID Field Usage ===")
        print(f"Used in {result['record_count']} records")
        key_fields = [r for r in result["results"] if r["IS_KEY"] == "Yes"]
        print(f"  As Key Field in: {len(key_fields)} records")

    @pytest.mark.asyncio
    async def test_find_peoplecode_using_function(self):
        """
        Question: Where is CreateRowset used in PeopleCode? I need to review usage patterns.
        Context: Investigating performance issues or understanding coding patterns
        """
        result = await search_peoplecode("CREATEROWSET", search_in="record")
        
        assert "error" not in result
        
        print(f"\n=== PeopleCode Search: 'CREATEROWSET' ===")
        print(f"Found in {result['total_found']} locations")
        print(f"  Record PeopleCode: {len(result['record_peoplecode'])}")
        for r in result["record_peoplecode"][:10]:
            print(f"    {r['RECNAME']}.{r['FIELDNAME']}.{r['EVENT']}")


class TestComponentAnalysis:
    """
    Scenario: Consultant needs to understand component structure for customization.
    """

    @pytest.mark.asyncio
    async def test_understand_job_data_component(self):
        """
        Question: How is the JOB_DATA component structured? What pages does it have?
        Context: Need to add a custom page or understand navigation
        """
        result = await get_component_structure("JOB_DATA")
        
        if "error" in result:
            # Try alternate name
            result = await get_component_structure("JOB_DATA_SUMMARY")
        
        print(f"\n=== Component Structure ===")
        if "error" not in result:
            comp = result["component"]
            print(f"Component: {comp.get('COMPONENT_NAME', 'N/A')}")
            print(f"Description: {comp.get('DESCR', 'N/A')}")
            print(f"Search Record: {comp.get('SEARCHRECNAME', 'N/A')}")
            print(f"\nPages ({len(result['pages'])}):")
            for p in result["pages"]:
                hidden = " [HIDDEN]" if p.get("HIDDEN") == "Y" else ""
                print(f"  {p['PAGE_NAME']}{hidden}: {p.get('PAGE_DESCR', 'N/A')}")
            print(f"\nMenu Navigation ({len(result['menu_navigation'])}):")
            for m in result["menu_navigation"][:5]:
                print(f"  {m['MENUNAME']} > {m['BARNAME']} > {m['BARITEMNAME']}")
        else:
            print(f"Component not found - trying search")
            search = await search_records("JOB_DATA")
            print(f"Related records: {len(search.get('results', []))}")

    @pytest.mark.asyncio
    async def test_find_page_fields(self):
        """
        Question: What fields are on the PERSONAL_DATA page? What records do they come from?
        Context: Need to understand page layout for customization
        """
        # First find a personal data page
        sql = "SELECT PNLNAME FROM PSPNLDEFN WHERE PNLNAME LIKE '%PERSONAL%DATA%' FETCH FIRST 5 ROWS ONLY"
        pages = await execute_query(sql)
        
        print(f"\n=== Personal Data Pages ===")
        if pages.get("results"):
            page_name = pages["results"][0]["PNLNAME"]
            print(f"Analyzing page: {page_name}")
            
            result = await get_page_fields(page_name)
            if "error" not in result:
                print(f"Page Type: {result['page']['PNLTYPE_DESC']}")
                print(f"Total Fields: {result['field_count']}")
                
                # Group by field type
                field_types = {}
                for f in result["fields"]:
                    ft = f["FIELD_TYPE_DESC"]
                    field_types[ft] = field_types.get(ft, 0) + 1
                
                print(f"\nField Types:")
                for ft, count in sorted(field_types.items(), key=lambda x: -x[1])[:10]:
                    print(f"  {ft}: {count}")
        else:
            print("No personal data pages found")


class TestSecurityAnalysis:
    """
    Scenario: Consultant needs to understand or troubleshoot security.
    """

    @pytest.mark.asyncio
    async def test_find_permission_list_access(self):
        """
        Question: What does the ALLPANLS permission list grant access to?
        Context: Security audit or troubleshooting access issues
        """
        result = await get_permission_list_details("ALLPANLS")
        
        print(f"\n=== Permission List: ALLPANLS ===")
        if "error" not in result:
            pl = result["permission_list"]
            print(f"Description: {pl.get('DESCR', 'N/A')}")
            print(f"\nComponent Access ({len(result['component_access'])} items):")
            for c in result["component_access"][:10]:
                print(f"  {c['MENUNAME']} > {c['COMPONENT']}")
            print(f"\nQuery Access ({len(result['query_access'])} queries):")
            for q in result["query_access"][:5]:
                print(f"  {q['QRYNAME']}: {q['ACCESS_DESC']}")
        else:
            print(f"Permission list not found: {result.get('error')}")
            # Try to find any permission list
            sql = "SELECT CLASSID, DESCR FROM PSCLASSDEFN FETCH FIRST 5 ROWS ONLY"
            pls = await execute_query(sql)
            if pls.get("results"):
                print(f"Available permission lists: {[p['CLASSID'] for p in pls['results']]}")

    @pytest.mark.asyncio
    async def test_find_roles_for_permission_list(self):
        """
        Question: What roles include HCCPALL permission list?
        Context: Need to understand who has access to a feature
        """
        # First find a permission list that exists
        sql = "SELECT CLASSID FROM PSCLASSDEFN WHERE CLASSID LIKE '%ALL%' FETCH FIRST 1 ROW ONLY"
        pl_result = await execute_query(sql)
        
        print(f"\n=== Roles for Permission List ===")
        if pl_result.get("results"):
            pl_name = pl_result["results"][0]["CLASSID"]
            print(f"Checking permission list: {pl_name}")
            
            result = await get_roles_for_permission_list(pl_name)
            if "error" not in result and result.get("results"):
                print(f"Found in {len(result['results'])} roles:")
                for r in result["results"][:10]:
                    print(f"  {r['ROLENAME']}: {r.get('ROLE_DESCR', 'N/A')}")
            else:
                print("No roles found with this permission list")
        else:
            print("No permission lists found matching pattern")


class TestProcessScheduler:
    """
    Scenario: Consultant needs to understand batch processes.
    """

    @pytest.mark.asyncio
    async def test_find_application_engine_programs(self):
        """
        Question: What Application Engine programs exist for HR?
        Context: Need to understand batch processing landscape
        """
        result = await get_process_definition(process_name="HR", process_type="Application Engine")
        
        print(f"\n=== HR Application Engine Programs ===")
        if "error" not in result and result.get("results"):
            print(f"Found {len(result['results'])} programs:")
            for p in result["results"][:15]:
                print(f"  {p['PRCSNAME']}: {p.get('DESCR', 'N/A')}")
        else:
            # Try broader search
            result = await get_process_definition(process_type="Application Engine")
            if result.get("results"):
                print(f"All AE programs (first 15): {len(result['results'])}")
                for p in result["results"][:15]:
                    print(f"  {p['PRCSNAME']}: {p.get('DESCR', 'N/A')}")

    @pytest.mark.asyncio
    async def test_analyze_ae_program_structure(self):
        """
        Question: What's the structure of a specific Application Engine program?
        Context: Need to debug or modify batch processing
        """
        # Find an AE program
        sql = "SELECT AE_APPLID FROM PSAEAPPLDEFN WHERE ROWNUM <= 1"
        ae_result = await execute_query(sql)
        
        print(f"\n=== Application Engine Structure ===")
        if ae_result.get("results"):
            ae_name = ae_result["results"][0]["AE_APPLID"]
            print(f"Analyzing: {ae_name}")
            
            result = await get_application_engine_steps(ae_name)
            if "error" not in result:
                prog = result["program"]
                print(f"Description: {prog.get('DESCR', 'N/A')}")
                print(f"Restart Enabled: {'No' if prog.get('AE_DISABLE_RESTART') else 'Yes'}")
                
                # Group by section
                sections = {}
                for step in result["steps"]:
                    sec = step["SECTION_NAME"]
                    if sec not in sections:
                        sections[sec] = []
                    sections[sec].append(step)
                
                print(f"\nSections ({len(sections)}):")
                for sec_name, steps in list(sections.items())[:5]:
                    print(f"  {sec_name}: {len(steps)} steps")
        else:
            print("No Application Engine programs found")

    @pytest.mark.asyncio
    async def test_find_sqr_reports(self):
        """
        Question: What SQR reports are available?
        Context: Need to find or modify a report
        """
        result = await get_process_definition(process_type="SQR")
        
        print(f"\n=== SQR Reports ===")
        if "error" not in result and result.get("results"):
            print(f"Found {len(result['results'])} SQR reports:")
            for p in result["results"][:15]:
                print(f"  {p['PRCSNAME']}: {p.get('DESCR', 'N/A')}")
        else:
            print("No SQR reports found")


class TestIntegrationBroker:
    """
    Scenario: Consultant needs to understand integrations.
    """

    @pytest.mark.asyncio
    async def test_find_hr_integrations(self):
        """
        Question: What Integration Broker services exist for HR?
        Context: Building an integration or troubleshooting
        """
        result = await get_integration_broker_services("HR")
        
        print(f"\n=== HR Integration Services ===")
        if "error" not in result and result.get("results"):
            print(f"Found {len(result['results'])} services:")
            for s in result["results"][:10]:
                print(f"  {s['IB_SERVICE']}.{s['IB_OPERATIONNAME']} ({s['OPERATION_TYPE_DESC']})")
                print(f"    Request: {s.get('REQUESTMSGNAME', 'N/A')}")
        else:
            # Try broader search
            result = await get_integration_broker_services()
            if result.get("results"):
                print(f"All IB Services (first 15):")
                for s in result["results"][:15]:
                    print(f"  {s['IB_SERVICE']}: {s['IB_OPERATIONNAME']}")

    @pytest.mark.asyncio
    async def test_analyze_message_structure(self):
        """
        Question: What's the structure of an Integration Broker message?
        Context: Building or troubleshooting an integration
        """
        # Find a message
        sql = "SELECT MSGNAME FROM PSMSGDEFN WHERE ROWNUM <= 1"
        msg_result = await execute_query(sql)
        
        print(f"\n=== Message Structure ===")
        if msg_result.get("results"):
            msg_name = msg_result["results"][0]["MSGNAME"]
            print(f"Analyzing: {msg_name}")
            
            result = await get_message_definition(msg_name)
            if "error" not in result:
                msg = result["message"]
                print(f"Description: {msg.get('DESCR', 'N/A')}")
                print(f"Active: {'Yes' if msg.get('ACTV_FLAG') == 'A' else 'No'}")
                print(f"\nMessage Parts ({len(result['parts'])}):")
                for p in result["parts"]:
                    print(f"  {p['PARTNAME']}: Record={p.get('RECNAME', 'N/A')}")
        else:
            print("No messages found")


class TestQueryManager:
    """
    Scenario: Consultant needs to understand PS Query definitions.
    """

    @pytest.mark.asyncio
    async def test_find_employee_queries(self):
        """
        Question: What PS Queries exist for employee data?
        Context: Looking for existing reports to modify or use as reference
        """
        sql = """
            SELECT QRYNAME, DESCR, OPRID, QRYTYPE 
            FROM PSQRYDEFN 
            WHERE UPPER(QRYNAME) LIKE '%EMPL%' OR UPPER(DESCR) LIKE '%EMPLOYEE%'
            FETCH FIRST 15 ROWS ONLY
        """
        result = await execute_query(sql)
        
        print(f"\n=== Employee-related Queries ===")
        if result.get("results"):
            print(f"Found {len(result['results'])} queries:")
            for q in result["results"]:
                qtype = {0: "User", 1: "Role", 2: "Public"}.get(q.get("QRYTYPE"), "Unknown")
                print(f"  {q['QRYNAME']} ({qtype}): {q.get('DESCR', 'N/A')}")
        else:
            print("No employee queries found")

    @pytest.mark.asyncio
    async def test_analyze_query_structure(self):
        """
        Question: What records and fields does a specific query use?
        Context: Understanding query logic or migrating to custom SQL
        """
        # Find a query
        sql = "SELECT QRYNAME FROM PSQRYDEFN WHERE ROWNUM <= 1"
        qry_result = await execute_query(sql)
        
        print(f"\n=== Query Structure ===")
        if qry_result.get("results"):
            qry_name = qry_result["results"][0]["QRYNAME"]
            print(f"Analyzing: {qry_name}")
            
            result = await get_query_definition(qry_name)
            if "error" not in result:
                qry = result["query"]
                print(f"Owner: {qry.get('OWNER', 'N/A')}")
                print(f"Type: {qry.get('QUERY_TYPE_DESC', 'N/A')}")
                print(f"\nRecords ({len(result['records'])}):")
                for r in result["records"]:
                    print(f"  {r['RECNAME']} AS {r.get('ALIAS', 'N/A')}")
                print(f"\nFields ({len(result['fields'])}):")
                for f in result["fields"][:10]:
                    print(f"  {f['RECNAME']}.{f['FIELDNAME']}: {f.get('HEADING', 'N/A')}")
        else:
            print("No queries found")


class TestTranslateValues:
    """
    Scenario: Consultant needs to understand code values.
    """

    @pytest.mark.asyncio
    async def test_get_hr_status_values(self):
        """
        Question: What are all the possible HR_STATUS values?
        Context: Need to understand status codes for reporting or validation
        """
        result = await get_translate_field_values("HR_STATUS")
        
        print(f"\n=== HR_STATUS Translate Values ===")
        if "error" not in result and result.get("results"):
            print(f"Found {len(result['results'])} values:")
            seen = set()
            for v in result["results"]:
                if v["FIELDVALUE"] not in seen:
                    print(f"  {v['FIELDVALUE']}: {v['XLATLONGNAME']}")
                    seen.add(v["FIELDVALUE"])
        else:
            print("No translate values found")

    @pytest.mark.asyncio
    async def test_get_empl_status_values(self):
        """
        Question: What employee status values exist?
        Context: Understanding employment lifecycle states
        """
        result = await get_translate_field_values("EMPL_STATUS")
        
        print(f"\n=== EMPL_STATUS Translate Values ===")
        if "error" not in result and result.get("results"):
            seen = set()
            for v in result["results"]:
                if v["FIELDVALUE"] not in seen:
                    print(f"  {v['FIELDVALUE']}: {v['XLATLONGNAME']} ({v.get('XLATSHORTNAME', '')})")
                    seen.add(v["FIELDVALUE"])

    @pytest.mark.asyncio
    async def test_get_action_codes(self):
        """
        Question: What ACTION codes are defined?
        Context: Understanding personnel actions for reporting
        """
        result = await get_translate_field_values("ACTION")
        
        print(f"\n=== ACTION Translate Values ===")
        if "error" not in result and result.get("results"):
            seen = set()
            for v in result["results"][:20]:
                if v["FIELDVALUE"] not in seen:
                    print(f"  {v['FIELDVALUE']}: {v['XLATLONGNAME']}")
                    seen.add(v["FIELDVALUE"])


class TestConceptualUnderstanding:
    """
    Scenario: Consultant needs to understand PeopleSoft concepts.
    """

    @pytest.mark.asyncio
    async def test_explain_effective_dating(self):
        """
        Question: How does effective dating work? What tables use it?
        Context: New consultant learning the system
        """
        result = await explain_peoplesoft_concept("effective_dating")
        
        print(f"\n=== {result.get('concept', 'Concept')} ===")
        print(f"Explanation: {result.get('explanation', 'N/A')}")
        if result.get("results"):
            print(f"\nTables with EFFDT ({len(result['results'])} shown):")
            for r in result["results"][:10]:
                print(f"  {r['RECNAME']} ({r['RECTYPE']}): {r.get('RECDESCR', '')}")

    @pytest.mark.asyncio
    async def test_explain_setid(self):
        """
        Question: What is SetID and how is it used?
        Context: Understanding data sharing across business units
        """
        result = await explain_peoplesoft_concept("setid")
        
        print(f"\n=== {result.get('concept', 'Concept')} ===")
        print(f"Explanation: {result.get('explanation', 'N/A')}")
        if result.get("results"):
            print(f"\nTables with SETID ({len(result['results'])} shown):")
            for r in result["results"][:10]:
                print(f"  {r['RECNAME']}: {r.get('RECDESCR', '')}")

    @pytest.mark.asyncio
    async def test_explain_record_types(self):
        """
        Question: What types of records exist in PeopleSoft?
        Context: Understanding the difference between tables, views, and derived records
        """
        result = await explain_peoplesoft_concept("record_types")
        
        print(f"\n=== {result.get('concept', 'Concept')} ===")
        print(f"Explanation: {result.get('explanation', 'N/A')}")
        if result.get("results"):
            print(f"\nRecord Type Distribution:")
            for r in result["results"]:
                print(f"  Type {r['RECTYPE']} ({r['RECTYPE_DESC']}): {r['RECORD_COUNT']:,} records")

    @pytest.mark.asyncio
    async def test_explain_security(self):
        """
        Question: How does PeopleSoft security work?
        Context: Understanding permission model for troubleshooting
        """
        result = await explain_peoplesoft_concept("security")
        
        print(f"\n=== {result.get('concept', 'Concept')} ===")
        print(f"Explanation: {result.get('explanation', 'N/A')}")
        if result.get("results"):
            for r in result["results"]:
                print(f"  Permission Lists: {r.get('PERMISSION_LISTS', 'N/A'):,}")
                print(f"  Roles: {r.get('ROLES', 'N/A'):,}")
                print(f"  Users: {r.get('USERS', 'N/A'):,}")
                print(f"  Auth Items: {r.get('AUTH_ITEMS', 'N/A'):,}")


class TestPeopleCodeInvestigation:
    """
    Scenario: Consultant needs to understand or debug PeopleCode.
    """

    @pytest.mark.asyncio
    async def test_find_peoplecode_on_job_record(self):
        """
        Question: What PeopleCode is attached to the JOB record?
        Context: Debugging or understanding business logic
        """
        result = await get_peoplecode("JOB", include_code=False)
        
        print(f"\n=== PeopleCode on JOB Record ===")
        if "error" not in result and result.get("results"):
            # Group by event
            events = {}
            for pc in result["results"]:
                event = pc["EVENT"]
                if event not in events:
                    events[event] = []
                events[event].append(pc)
            
            print(f"Total programs: {len(result['results'])}")
            print(f"\nBy Event:")
            for event, pcs in sorted(events.items()):
                print(f"  {event}: {len(pcs)} programs")
                for pc in pcs[:3]:
                    print(f"    - {pc['FIELD_NAME']} ({pc.get('CODE_LENGTH', 0)} chars)")
        else:
            print("No PeopleCode found or error occurred")

    @pytest.mark.asyncio
    async def test_find_rowinsert_peoplecode(self):
        """
        Question: What happens when a new row is inserted on PERSONAL_DATA?
        Context: Understanding default value logic or validation
        """
        result = await get_peoplecode("PERSONAL_DATA", event="RowInsert", include_code=False)
        
        print(f"\n=== RowInsert PeopleCode on PERSONAL_DATA ===")
        if "error" not in result and result.get("results"):
            print(f"Found {len(result['results'])} programs:")
            for pc in result["results"]:
                print(f"  {pc['FIELD_NAME']}: {pc.get('CODE_LENGTH', 0)} characters")
        else:
            print("No RowInsert PeopleCode found")

    @pytest.mark.asyncio
    async def test_get_peoplecode_source_code(self):
        """
        Question: What is the actual PeopleCode logic for a specific field/event?
        Context: Need to understand, debug, or document business logic
        
        This test validates that get_peoplecode returns actual source code,
        not just metadata. The code is stored in PSPCMTXT as CLOBs.
        """
        # First find a record that has PeopleCode
        sql = """
            SELECT OBJECTVALUE1 AS RECORD_NAME, COUNT(*) AS PC_COUNT
            FROM PSPCMTXT
            WHERE OBJECTID1 = 1
            GROUP BY OBJECTVALUE1
            HAVING COUNT(*) > 0
            ORDER BY COUNT(*) DESC
            FETCH FIRST 1 ROW ONLY
        """
        find_result = await execute_query(sql)
        
        print(f"\n=== PeopleCode Source Code Test ===")
        
        if not find_result.get("results"):
            print("No PeopleCode found in database")
            return
        
        record_name = find_result["results"][0]["RECORD_NAME"]
        print(f"Testing with record: {record_name}")
        
        # Get PeopleCode WITH source code
        result = await get_peoplecode(record_name, include_code=True, max_code_length=4000)
        
        assert "error" not in result, f"Error getting PeopleCode: {result.get('error')}"
        assert result.get("results"), "No PeopleCode results returned"
        assert result.get("program_count", 0) > 0, "Program count should be > 0"
        
        # Verify we got actual source code, not just metadata
        first_pc = result["results"][0]
        assert "PEOPLECODE" in first_pc, "PEOPLECODE field missing - source not returned"
        assert first_pc["PEOPLECODE"], "PEOPLECODE field is empty"
        assert len(first_pc["PEOPLECODE"]) > 0, "PeopleCode source has no content"
        
        # The source should contain PeopleCode syntax (not a LOB object reference)
        source = first_pc["PEOPLECODE"]
        assert "oracledb" not in source.lower(), "Got LOB object reference instead of actual code"
        
        print(f"Record: {first_pc['RECORD_NAME']}")
        print(f"Field: {first_pc['FIELD_NAME']}")
        print(f"Event: {first_pc['EVENT']}")
        print(f"Code Length: {first_pc.get('CODE_LENGTH', len(source))} chars")
        print(f"\nFirst 500 chars of source:")
        print("-" * 50)
        print(source[:500])
        if len(source) > 500:
            print("...")
        print("-" * 50)

    @pytest.mark.asyncio
    async def test_get_peoplecode_metadata_only(self):
        """
        Question: What PeopleCode events exist on a record? (fast discovery)
        Context: Quick scan before diving into specific code
        
        Tests the include_code=False option for faster metadata-only queries.
        """
        # Find a record with PeopleCode
        sql = """
            SELECT OBJECTVALUE1 AS RECORD_NAME
            FROM PSPCMTXT
            WHERE OBJECTID1 = 1
            GROUP BY OBJECTVALUE1
            HAVING COUNT(*) >= 3
            FETCH FIRST 1 ROW ONLY
        """
        find_result = await execute_query(sql)
        
        print(f"\n=== PeopleCode Metadata Only Test ===")
        
        if not find_result.get("results"):
            print("No records with multiple PeopleCode programs found")
            return
        
        record_name = find_result["results"][0]["RECORD_NAME"]
        print(f"Testing with record: {record_name}")
        
        # Get metadata only (no source code)
        result = await get_peoplecode(record_name, include_code=False)
        
        assert "error" not in result, f"Error: {result.get('error')}"
        assert result.get("results"), "No results returned"
        
        # Verify PEOPLECODE field is NOT present (metadata only)
        first_pc = result["results"][0]
        assert "PEOPLECODE" not in first_pc, "PEOPLECODE should not be present with include_code=False"
        
        # Should still have metadata fields
        assert "RECORD_NAME" in first_pc
        assert "FIELD_NAME" in first_pc
        assert "EVENT" in first_pc
        assert "CODE_LENGTH" in first_pc
        
        print(f"Programs found: {result['program_count']}")
        print(f"\nEvents on {record_name}:")
        events = {}
        for pc in result["results"]:
            event = pc["EVENT"]
            events[event] = events.get(event, 0) + 1
        for event, count in sorted(events.items()):
            print(f"  {event}: {count} field(s)")

    @pytest.mark.asyncio
    async def test_get_peoplecode_specific_field_event(self):
        """
        Question: What exactly happens in the FieldChange event for EFFDT?
        Context: Debugging effective date logic on a specific record
        
        Tests filtering by specific field and event.
        """
        # Find a record with EFFDT FieldChange PeopleCode
        sql = """
            SELECT OBJECTVALUE1 AS RECORD_NAME
            FROM PSPCMTXT
            WHERE OBJECTID1 = 1
            AND OBJECTVALUE2 = 'EFFDT'
            AND OBJECTVALUE3 = 'FieldChange'
            FETCH FIRST 1 ROW ONLY
        """
        find_result = await execute_query(sql)
        
        print(f"\n=== PeopleCode Field/Event Filter Test ===")
        
        if not find_result.get("results"):
            # Try any field with FieldChange
            sql2 = """
                SELECT OBJECTVALUE1 AS RECORD_NAME, OBJECTVALUE2 AS FIELD_NAME
                FROM PSPCMTXT
                WHERE OBJECTID1 = 1
                AND OBJECTVALUE3 = 'FieldChange'
                FETCH FIRST 1 ROW ONLY
            """
            find_result = await execute_query(sql2)
            if not find_result.get("results"):
                print("No FieldChange PeopleCode found")
                return
            record_name = find_result["results"][0]["RECORD_NAME"]
            field_name = find_result["results"][0]["FIELD_NAME"]
        else:
            record_name = find_result["results"][0]["RECORD_NAME"]
            field_name = "EFFDT"
        
        print(f"Testing: {record_name}.{field_name}.FieldChange")
        
        # Get specific field/event combination
        result = await get_peoplecode(
            record_name, 
            field_name=field_name, 
            event="FieldChange",
            include_code=True,
            max_code_length=8000
        )
        
        assert "error" not in result, f"Error: {result.get('error')}"
        
        if not result.get("results"):
            print(f"No FieldChange PeopleCode found for {record_name}.{field_name}")
            return
        
        # Should only get results for the specified field/event
        for pc in result["results"]:
            assert pc["FIELD_NAME"] == field_name, f"Got wrong field: {pc['FIELD_NAME']}"
            assert pc["EVENT"] == "FieldChange", f"Got wrong event: {pc['EVENT']}"
        
        # Verify filters are included in response
        assert result.get("field_filter") == field_name
        assert result.get("event_filter") == "FieldChange"
        
        pc = result["results"][0]
        print(f"Found {result['program_count']} program(s)")
        print(f"\nSource code for {record_name}.{field_name}.FieldChange:")
        print("-" * 50)
        print(pc["PEOPLECODE"][:2000])
        if len(pc["PEOPLECODE"]) > 2000:
            print(f"... ({pc['CODE_LENGTH']} total chars)")
        print("-" * 50)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
