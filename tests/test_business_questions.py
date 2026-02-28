"""
Test suite demonstrating realistic business questions that can be answered
using the PeopleSoft MCP tools.

Each test represents a typical question that HR, Finance, or Management
might ask about workforce data.

Run with: uv run pytest tests/test_business_questions.py -v
"""
import pytest
import asyncio
from db import execute_query


class TestHeadcountAndOrganization:
    """Questions about workforce size and structure."""

    @pytest.mark.asyncio
    async def test_total_active_headcount(self):
        """
        Business Question: How many active employees do we have across the organization?
        Asked by: HR Leadership, Finance for budgeting
        """
        sql = """
            SELECT COUNT(DISTINCT J.EMPLID) AS ACTIVE_HEADCOUNT
            FROM PS_JOB J
            WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                            WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                            AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.HR_STATUS = 'A'
        """
        result = await execute_query(sql)
        assert "error" not in result
        assert result["results"][0]["ACTIVE_HEADCOUNT"] > 0
        print(f"\nActive Headcount: {result['results'][0]['ACTIVE_HEADCOUNT']}")

    @pytest.mark.asyncio
    async def test_headcount_by_company(self):
        """
        Business Question: How many employees are in each company/legal entity?
        Asked by: Finance, Legal, HR for entity-level reporting
        """
        sql = """
            SELECT 
                C.COMPANY,
                C.DESCR AS COMPANY_NAME,
                COUNT(DISTINCT J.EMPLID) AS EMPLOYEE_COUNT
            FROM PS_JOB J
            JOIN PS_COMPANY_TBL C ON J.COMPANY = C.COMPANY
                AND C.EFFDT = (SELECT MAX(C1.EFFDT) FROM PS_COMPANY_TBL C1 
                              WHERE C.COMPANY = C1.COMPANY AND C1.EFFDT <= SYSDATE)
            WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                            WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                            AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.HR_STATUS = 'A'
            GROUP BY C.COMPANY, C.DESCR
            ORDER BY EMPLOYEE_COUNT DESC
            FETCH FIRST 10 ROWS ONLY
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nTop 10 Companies by Headcount:")
        for row in result["results"]:
            print(f"  {row['COMPANY_NAME']}: {row['EMPLOYEE_COUNT']}")

    @pytest.mark.asyncio
    async def test_headcount_by_department(self):
        """
        Business Question: What is the headcount breakdown by department?
        Asked by: Department Managers, HR Business Partners
        """
        sql = """
            SELECT 
                J.DEPTID,
                D.DESCR AS DEPARTMENT_NAME,
                COUNT(DISTINCT J.EMPLID) AS EMPLOYEE_COUNT
            FROM PS_JOB J
            JOIN PS_DEPT_TBL D ON J.DEPTID = D.DEPTID
                AND D.EFFDT = (SELECT MAX(D1.EFFDT) FROM PS_DEPT_TBL D1 
                              WHERE D.DEPTID = D1.DEPTID AND D1.EFFDT <= SYSDATE)
            WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                            WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                            AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.HR_STATUS = 'A'
            GROUP BY J.DEPTID, D.DESCR
            ORDER BY EMPLOYEE_COUNT DESC
            FETCH FIRST 15 ROWS ONLY
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nTop 15 Departments by Headcount:")
        for row in result["results"]:
            print(f"  {row['DEPARTMENT_NAME']}: {row['EMPLOYEE_COUNT']}")


class TestTurnoverAndRetention:
    """Questions about employee movement and retention."""

    @pytest.mark.asyncio
    async def test_recent_hires(self):
        """
        Business Question: Who did we hire in the last 90 days?
        Asked by: HR Recruiting, Onboarding teams
        """
        sql = """
            SELECT 
                E.EMPLID,
                P.NAME,
                E.HIRE_DT,
                J.DEPTID,
                J.JOBCODE,
                J.COMPANY
            FROM PS_EMPLOYMENT E
            JOIN PS_PERSONAL_DATA P ON E.EMPLID = P.EMPLID
            JOIN PS_JOB J ON E.EMPLID = J.EMPLID AND E.EMPL_RCD = J.EMPL_RCD
                AND J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                              WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                              AND J1.EFFDT <= SYSDATE)
                AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                               WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                               AND J.EFFDT = J2.EFFDT)
            WHERE E.HIRE_DT >= SYSDATE - 90
            AND J.HR_STATUS = 'A'
            ORDER BY E.HIRE_DT DESC
            FETCH FIRST 20 ROWS ONLY
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nRecent Hires (last 90 days): {len(result['results'])} employees")
        for row in result["results"][:5]:
            print(f"  {row['NAME']} - Hired: {row['HIRE_DT']}")

    @pytest.mark.asyncio
    async def test_terminations_this_year(self):
        """
        Business Question: How many employees have left this year, and what were the reasons?
        Asked by: HR Leadership, for turnover analysis
        """
        sql = """
            SELECT 
                J.ACTION_REASON,
                AR.DESCR AS REASON_DESCRIPTION,
                COUNT(*) AS TERMINATION_COUNT
            FROM PS_JOB J
            LEFT JOIN PS_ACTN_REASON_TBL AR ON J.ACTION = AR.ACTION 
                AND J.ACTION_REASON = AR.ACTION_REASON
                AND AR.EFFDT = (SELECT MAX(AR1.EFFDT) FROM PS_ACTN_REASON_TBL AR1 
                               WHERE AR.ACTION = AR1.ACTION AND AR.ACTION_REASON = AR1.ACTION_REASON 
                               AND AR1.EFFDT <= SYSDATE)
            WHERE J.ACTION = 'TER'
            AND J.EFFDT >= TRUNC(SYSDATE, 'YEAR')
            GROUP BY J.ACTION_REASON, AR.DESCR
            ORDER BY TERMINATION_COUNT DESC
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nTerminations This Year by Reason:")
        total = sum(row["TERMINATION_COUNT"] for row in result["results"])
        for row in result["results"]:
            print(f"  {row['REASON_DESCRIPTION'] or row['ACTION_REASON']}: {row['TERMINATION_COUNT']}")
        print(f"  TOTAL: {total}")

    @pytest.mark.asyncio
    async def test_employees_on_leave(self):
        """
        Business Question: How many employees are currently on leave?
        Asked by: HR Operations, Managers
        """
        sql = """
            SELECT 
                J.EMPL_STATUS,
                X.XLATLONGNAME AS STATUS_NAME,
                COUNT(DISTINCT J.EMPLID) AS EMPLOYEE_COUNT
            FROM PS_JOB J
            LEFT JOIN PSXLATITEM X ON X.FIELDNAME = 'EMPL_STATUS' AND X.FIELDVALUE = J.EMPL_STATUS
                AND X.EFFDT = (SELECT MAX(X1.EFFDT) FROM PSXLATITEM X1 
                              WHERE X1.FIELDNAME = 'EMPL_STATUS' AND X1.FIELDVALUE = J.EMPL_STATUS 
                              AND X1.EFFDT <= SYSDATE)
            WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                            WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                            AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.EMPL_STATUS IN ('L', 'P', 'S')
            GROUP BY J.EMPL_STATUS, X.XLATLONGNAME
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nEmployees Currently on Leave:")
        for row in result["results"]:
            print(f"  {row['STATUS_NAME']}: {row['EMPLOYEE_COUNT']}")


class TestCompensationAnalysis:
    """Questions about pay and compensation."""

    @pytest.mark.asyncio
    async def test_average_salary_by_department(self):
        """
        Business Question: What is the average salary by department?
        Asked by: Finance, Compensation team, HR Analytics
        """
        sql = """
            SELECT 
                J.DEPTID,
                D.DESCR AS DEPARTMENT_NAME,
                COUNT(DISTINCT J.EMPLID) AS EMPLOYEE_COUNT,
                ROUND(AVG(J.ANNUAL_RT), 2) AS AVG_ANNUAL_SALARY,
                ROUND(MIN(J.ANNUAL_RT), 2) AS MIN_SALARY,
                ROUND(MAX(J.ANNUAL_RT), 2) AS MAX_SALARY
            FROM PS_JOB J
            JOIN PS_DEPT_TBL D ON J.DEPTID = D.DEPTID
                AND D.EFFDT = (SELECT MAX(D1.EFFDT) FROM PS_DEPT_TBL D1 
                              WHERE D.DEPTID = D1.DEPTID AND D1.EFFDT <= SYSDATE)
            WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                            WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                            AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.HR_STATUS = 'A'
            AND J.ANNUAL_RT > 0
            GROUP BY J.DEPTID, D.DESCR
            HAVING COUNT(DISTINCT J.EMPLID) >= 5
            ORDER BY AVG_ANNUAL_SALARY DESC
            FETCH FIRST 10 ROWS ONLY
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nTop 10 Departments by Average Salary:")
        for row in result["results"]:
            print(f"  {row['DEPARTMENT_NAME']}: ${row['AVG_ANNUAL_SALARY']:,.2f} avg ({row['EMPLOYEE_COUNT']} employees)")

    @pytest.mark.asyncio
    async def test_salary_by_job_code(self):
        """
        Business Question: What is the salary range for each job code?
        Asked by: Compensation team, Recruiters for offer planning
        """
        sql = """
            SELECT 
                J.JOBCODE,
                JC.DESCR AS JOB_TITLE,
                COUNT(DISTINCT J.EMPLID) AS EMPLOYEE_COUNT,
                ROUND(AVG(J.ANNUAL_RT), 2) AS AVG_SALARY,
                ROUND(MIN(J.ANNUAL_RT), 2) AS MIN_SALARY,
                ROUND(MAX(J.ANNUAL_RT), 2) AS MAX_SALARY
            FROM PS_JOB J
            JOIN PS_JOBCODE_TBL JC ON J.JOBCODE = JC.JOBCODE AND J.SETID_JOBCODE = JC.SETID
                AND JC.EFFDT = (SELECT MAX(JC1.EFFDT) FROM PS_JOBCODE_TBL JC1 
                               WHERE JC.SETID = JC1.SETID AND JC.JOBCODE = JC1.JOBCODE 
                               AND JC1.EFFDT <= SYSDATE)
            WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                            WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                            AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.HR_STATUS = 'A'
            AND J.ANNUAL_RT > 0
            GROUP BY J.JOBCODE, JC.DESCR
            HAVING COUNT(DISTINCT J.EMPLID) >= 3
            ORDER BY AVG_SALARY DESC
            FETCH FIRST 15 ROWS ONLY
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nTop 15 Job Codes by Average Salary:")
        for row in result["results"]:
            print(f"  {row['JOB_TITLE']}: ${row['AVG_SALARY']:,.2f} (range: ${row['MIN_SALARY']:,.2f} - ${row['MAX_SALARY']:,.2f})")


class TestWorkforceDemographics:
    """Questions about workforce composition."""

    @pytest.mark.asyncio
    async def test_workforce_by_location(self):
        """
        Business Question: How is our workforce distributed across locations?
        Asked by: Facilities, HR for remote work planning
        """
        sql = """
            SELECT 
                J.LOCATION,
                L.DESCR AS LOCATION_NAME,
                L.CITY,
                L.STATE,
                COUNT(DISTINCT J.EMPLID) AS EMPLOYEE_COUNT
            FROM PS_JOB J
            JOIN PS_LOCATION_TBL L ON J.LOCATION = L.LOCATION AND J.SETID_LOCATION = L.SETID
                AND L.EFFDT = (SELECT MAX(L1.EFFDT) FROM PS_LOCATION_TBL L1 
                              WHERE L.SETID = L1.SETID AND L.LOCATION = L1.LOCATION 
                              AND L1.EFFDT <= SYSDATE)
            WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                            WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                            AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.HR_STATUS = 'A'
            GROUP BY J.LOCATION, L.DESCR, L.CITY, L.STATE
            ORDER BY EMPLOYEE_COUNT DESC
            FETCH FIRST 15 ROWS ONLY
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nTop 15 Locations by Headcount:")
        for row in result["results"]:
            print(f"  {row['LOCATION_NAME']} ({row['CITY']}, {row['STATE']}): {row['EMPLOYEE_COUNT']}")

    @pytest.mark.asyncio
    async def test_full_time_vs_part_time(self):
        """
        Business Question: What is the ratio of full-time to part-time employees?
        Asked by: HR Planning, Finance for FTE calculations
        """
        sql = """
            SELECT 
                J.FULL_PART_TIME,
                X.XLATLONGNAME AS EMPLOYMENT_TYPE,
                COUNT(DISTINCT J.EMPLID) AS EMPLOYEE_COUNT
            FROM PS_JOB J
            LEFT JOIN PSXLATITEM X ON X.FIELDNAME = 'FULL_PART_TIME' AND X.FIELDVALUE = J.FULL_PART_TIME
                AND X.EFFDT = (SELECT MAX(X1.EFFDT) FROM PSXLATITEM X1 
                              WHERE X1.FIELDNAME = 'FULL_PART_TIME' AND X1.FIELDVALUE = J.FULL_PART_TIME 
                              AND X1.EFFDT <= SYSDATE)
            WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                            WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                            AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.HR_STATUS = 'A'
            GROUP BY J.FULL_PART_TIME, X.XLATLONGNAME
            ORDER BY EMPLOYEE_COUNT DESC
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nFull-Time vs Part-Time Breakdown:")
        total = sum(row["EMPLOYEE_COUNT"] for row in result["results"])
        for row in result["results"]:
            pct = (row["EMPLOYEE_COUNT"] / total * 100) if total > 0 else 0
            print(f"  {row['EMPLOYMENT_TYPE']}: {row['EMPLOYEE_COUNT']} ({pct:.1f}%)")

    @pytest.mark.asyncio
    async def test_regular_vs_temporary(self):
        """
        Business Question: How many regular vs temporary/contingent workers do we have?
        Asked by: HR, Procurement for contractor management
        """
        sql = """
            SELECT 
                J.REG_TEMP,
                X.XLATLONGNAME AS WORKER_TYPE,
                COUNT(DISTINCT J.EMPLID) AS EMPLOYEE_COUNT
            FROM PS_JOB J
            LEFT JOIN PSXLATITEM X ON X.FIELDNAME = 'REG_TEMP' AND X.FIELDVALUE = J.REG_TEMP
                AND X.EFFDT = (SELECT MAX(X1.EFFDT) FROM PSXLATITEM X1 
                              WHERE X1.FIELDNAME = 'REG_TEMP' AND X1.FIELDVALUE = J.REG_TEMP 
                              AND X1.EFFDT <= SYSDATE)
            WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                            WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                            AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.HR_STATUS = 'A'
            GROUP BY J.REG_TEMP, X.XLATLONGNAME
            ORDER BY EMPLOYEE_COUNT DESC
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nRegular vs Temporary Workers:")
        for row in result["results"]:
            print(f"  {row['WORKER_TYPE']}: {row['EMPLOYEE_COUNT']}")


class TestManagerialQuestions:
    """Questions managers commonly ask about their teams."""

    @pytest.mark.asyncio
    async def test_direct_reports_for_manager(self):
        """
        Business Question: Who reports to a specific manager?
        Asked by: Managers, HR Business Partners
        """
        # First, find a manager who has direct reports
        find_manager_sql = """
            SELECT J.SUPERVISOR_ID, COUNT(*) AS REPORT_COUNT
            FROM PS_JOB J
            WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                            WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                            AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.HR_STATUS = 'A'
            AND J.SUPERVISOR_ID IS NOT NULL
            GROUP BY J.SUPERVISOR_ID
            HAVING COUNT(*) > 3
            ORDER BY COUNT(*) DESC
            FETCH FIRST 1 ROW ONLY
        """
        manager_result = await execute_query(find_manager_sql)
        
        if manager_result.get("results"):
            manager_id = manager_result["results"][0]["SUPERVISOR_ID"]
            
            reports_sql = """
                SELECT 
                    J.EMPLID,
                    P.NAME,
                    J.JOBCODE,
                    JC.DESCR AS JOB_TITLE,
                    J.DEPTID
                FROM PS_JOB J
                JOIN PS_PERSONAL_DATA P ON J.EMPLID = P.EMPLID
                LEFT JOIN PS_JOBCODE_TBL JC ON J.JOBCODE = JC.JOBCODE AND J.SETID_JOBCODE = JC.SETID
                    AND JC.EFFDT = (SELECT MAX(JC1.EFFDT) FROM PS_JOBCODE_TBL JC1 
                                   WHERE JC.SETID = JC1.SETID AND JC.JOBCODE = JC1.JOBCODE 
                                   AND JC1.EFFDT <= SYSDATE)
                WHERE J.SUPERVISOR_ID = :1
                AND J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                              WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                              AND J1.EFFDT <= SYSDATE)
                AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                               WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                               AND J.EFFDT = J2.EFFDT)
                AND J.HR_STATUS = 'A'
                ORDER BY P.NAME
            """
            result = await execute_query(reports_sql, [manager_id])
            assert "error" not in result
            print(f"\nDirect Reports for Manager {manager_id}:")
            for row in result["results"]:
                print(f"  {row['NAME']} - {row['JOB_TITLE']}")

    @pytest.mark.asyncio
    async def test_span_of_control(self):
        """
        Business Question: Which managers have the most direct reports?
        Asked by: HR Leadership, for organizational design
        """
        sql = """
            SELECT 
                J.SUPERVISOR_ID,
                M.NAME AS MANAGER_NAME,
                COUNT(DISTINCT J.EMPLID) AS DIRECT_REPORTS
            FROM PS_JOB J
            JOIN PS_PERSONAL_DATA M ON J.SUPERVISOR_ID = M.EMPLID
            WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                            WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                            AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.HR_STATUS = 'A'
            AND J.SUPERVISOR_ID IS NOT NULL
            GROUP BY J.SUPERVISOR_ID, M.NAME
            ORDER BY DIRECT_REPORTS DESC
            FETCH FIRST 15 ROWS ONLY
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nTop 15 Managers by Span of Control:")
        for row in result["results"]:
            print(f"  {row['MANAGER_NAME']} ({row['SUPERVISOR_ID']}): {row['DIRECT_REPORTS']} direct reports")


class TestComplianceAndAudit:
    """Questions for compliance and audit purposes."""

    @pytest.mark.asyncio
    async def test_employees_without_supervisor(self):
        """
        Business Question: Which employees don't have a supervisor assigned?
        Asked by: HR Compliance, Audit
        """
        sql = """
            SELECT 
                J.EMPLID,
                P.NAME,
                J.DEPTID,
                J.JOBCODE,
                J.COMPANY
            FROM PS_JOB J
            JOIN PS_PERSONAL_DATA P ON J.EMPLID = P.EMPLID
            WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                            WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                            AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.HR_STATUS = 'A'
            AND (J.SUPERVISOR_ID IS NULL OR J.SUPERVISOR_ID = ' ')
            ORDER BY J.COMPANY, J.DEPTID
            FETCH FIRST 20 ROWS ONLY
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nEmployees Without Supervisor (first 20):")
        print(f"  Total found: {len(result['results'])}")
        for row in result["results"][:10]:
            print(f"  {row['NAME']} - Dept: {row['DEPTID']}, Company: {row['COMPANY']}")

    @pytest.mark.asyncio
    async def test_recent_job_changes(self):
        """
        Business Question: What job changes happened in the last 30 days?
        Asked by: HR Operations, Audit
        """
        sql = """
            SELECT 
                J.EMPLID,
                P.NAME,
                J.EFFDT,
                J.ACTION,
                X.XLATLONGNAME AS ACTION_DESC,
                J.ACTION_REASON,
                J.DEPTID,
                J.JOBCODE
            FROM PS_JOB J
            JOIN PS_PERSONAL_DATA P ON J.EMPLID = P.EMPLID
            LEFT JOIN PSXLATITEM X ON X.FIELDNAME = 'ACTION' AND X.FIELDVALUE = J.ACTION
                AND X.EFFDT = (SELECT MAX(X1.EFFDT) FROM PSXLATITEM X1 
                              WHERE X1.FIELDNAME = 'ACTION' AND X1.FIELDVALUE = J.ACTION
                              AND X1.EFFDT <= SYSDATE)
            WHERE J.EFFDT >= SYSDATE - 30
            ORDER BY J.EFFDT DESC
            FETCH FIRST 50 ROWS ONLY
        """
        result = await execute_query(sql)
        assert "error" not in result
        print(f"\nJob Changes in Last 30 Days:")
        print(f"  Total changes: {len(result['results'])}")
        for row in result["results"][:10]:
            print(f"  {row['EFFDT']}: {row['NAME']} - {row.get('ACTION_DESC', row['ACTION'])}")


# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
