"""
Core HR semantic tools for PeopleSoft MCP.
High-level tools for employee, job, and organizational data.
"""
from db import execute_query, execute_query_with_limit


def register_tools(mcp):
    """Register all HR tools with the MCP server."""
    
    @mcp.tool()
    async def get_employee(employee_id: str) -> dict:
        """
        Get comprehensive employee profile including personal data, current job, 
        department, and employment status.
        
        This is the primary tool for getting employee information. It returns:
        - Personal details (name, birthdate, address, etc.)
        - Current job information (department, position, manager, etc.)
        - Employment status and dates
        
        :param employee_id: The employee ID (EMPLID)
        :return: Complete employee profile
        """
        sql = """
            SELECT 
                P.EMPLID,
                P.NAME,
                P.NAME_DISPLAY,
                P.LAST_NAME,
                P.FIRST_NAME,
                P.MIDDLE_NAME,
                P.BIRTHDATE,
                P.SEX,
                P.MAR_STATUS,
                J.EMPL_RCD,
                J.EFFDT AS JOB_EFFDT,
                J.HR_STATUS,
                J.EMPL_STATUS,
                J.DEPTID,
                D.DESCR AS DEPARTMENT_NAME,
                J.JOBCODE,
                JC.DESCR AS JOB_TITLE,
                J.LOCATION,
                L.DESCR AS LOCATION_NAME,
                J.COMPANY,
                C.DESCR AS COMPANY_NAME,
                J.SUPERVISOR_ID,
                J.POSITION_NBR,
                J.COMPRATE,
                J.ANNUAL_RT,
                J.MONTHLY_RT,
                J.REG_TEMP,
                J.FULL_PART_TIME,
                E.HIRE_DT,
                E.LAST_HIRE_DT,
                E.TERMINATION_DT
            FROM PS_PERSONAL_DATA P
            LEFT JOIN PS_JOB J ON P.EMPLID = J.EMPLID
                AND J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                              WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                              AND J1.EFFDT <= SYSDATE)
                AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                               WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                               AND J.EFFDT = J2.EFFDT)
                AND J.EMPL_RCD = (SELECT MAX(J3.EMPL_RCD) FROM PS_JOB J3 
                                 WHERE J.EMPLID = J3.EMPLID)
            LEFT JOIN PS_EMPLOYMENT E ON P.EMPLID = E.EMPLID AND J.EMPL_RCD = E.EMPL_RCD
            LEFT JOIN PS_DEPT_TBL D ON J.DEPTID = D.DEPTID
                AND D.EFFDT = (SELECT MAX(D1.EFFDT) FROM PS_DEPT_TBL D1 
                              WHERE D.DEPTID = D1.DEPTID AND D1.EFFDT <= SYSDATE)
            LEFT JOIN PS_JOBCODE_TBL JC ON J.JOBCODE = JC.JOBCODE AND J.SETID_JOBCODE = JC.SETID
                AND JC.EFFDT = (SELECT MAX(JC1.EFFDT) FROM PS_JOBCODE_TBL JC1 
                               WHERE JC.SETID = JC1.SETID AND JC.JOBCODE = JC1.JOBCODE 
                               AND JC1.EFFDT <= SYSDATE)
            LEFT JOIN PS_LOCATION_TBL L ON J.LOCATION = L.LOCATION AND J.SETID_LOCATION = L.SETID
                AND L.EFFDT = (SELECT MAX(L1.EFFDT) FROM PS_LOCATION_TBL L1 
                              WHERE L.SETID = L1.SETID AND L.LOCATION = L1.LOCATION 
                              AND L1.EFFDT <= SYSDATE)
            LEFT JOIN PS_COMPANY_TBL C ON J.COMPANY = C.COMPANY
                AND C.EFFDT = (SELECT MAX(C1.EFFDT) FROM PS_COMPANY_TBL C1 
                              WHERE C.COMPANY = C1.COMPANY AND C1.EFFDT <= SYSDATE)
            WHERE P.EMPLID = :1
        """
        
        result = await execute_query(sql, [employee_id.upper()])
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {"error": f"Employee '{employee_id}' not found."}
        
        row = result["results"][0]
        
        return {
            "employee_id": row["EMPLID"],
            "personal": {
                "name": row["NAME"],
                "display_name": row["NAME_DISPLAY"],
                "last_name": row["LAST_NAME"],
                "first_name": row["FIRST_NAME"],
                "middle_name": row["MIDDLE_NAME"],
                "birthdate": str(row["BIRTHDATE"]) if row["BIRTHDATE"] else None,
                "sex": row["SEX"],
                "marital_status": row["MAR_STATUS"]
            },
            "job": {
                "empl_rcd": row["EMPL_RCD"],
                "effective_date": str(row["JOB_EFFDT"]) if row["JOB_EFFDT"] else None,
                "hr_status": row["HR_STATUS"],
                "empl_status": row["EMPL_STATUS"],
                "department_id": row["DEPTID"],
                "department_name": row["DEPARTMENT_NAME"],
                "job_code": row["JOBCODE"],
                "job_title": row["JOB_TITLE"],
                "location": row["LOCATION"],
                "location_name": row["LOCATION_NAME"],
                "company": row["COMPANY"],
                "company_name": row["COMPANY_NAME"],
                "supervisor_id": row["SUPERVISOR_ID"],
                "position_number": row["POSITION_NBR"],
                "reg_temp": row["REG_TEMP"],
                "full_part_time": row["FULL_PART_TIME"]
            },
            "compensation": {
                "comp_rate": float(row["COMPRATE"]) if row["COMPRATE"] else None,
                "annual_rate": float(row["ANNUAL_RT"]) if row["ANNUAL_RT"] else None,
                "monthly_rate": float(row["MONTHLY_RT"]) if row["MONTHLY_RT"] else None
            },
            "employment": {
                "hire_date": str(row["HIRE_DT"]) if row["HIRE_DT"] else None,
                "last_hire_date": str(row["LAST_HIRE_DT"]) if row["LAST_HIRE_DT"] else None,
                "termination_date": str(row["TERMINATION_DT"]) if row["TERMINATION_DT"] else None
            }
        }

    @mcp.tool()
    async def search_employees(
        name: str | None = None,
        department: str | None = None,
        company: str | None = None,
        location: str | None = None,
        job_code: str | None = None,
        status: str = "active",
        limit: int = 50
    ) -> dict:
        """
        Search for employees by various criteria.
        
        :param name: Search by employee name (partial match supported)
        :param department: Filter by department ID
        :param company: Filter by company code
        :param location: Filter by location code
        :param job_code: Filter by job code
        :param status: Filter by status: 'active' (default), 'inactive', 'terminated', or 'all'
        :param limit: Maximum results to return (default 50)
        :return: List of matching employees with basic info
        """
        conditions = []
        params = []
        param_idx = 1
        
        if name:
            conditions.append(f"UPPER(P.NAME) LIKE :{param_idx}")
            params.append(f"%{name.upper()}%")
            param_idx += 1
        
        if department:
            conditions.append(f"J.DEPTID = :{param_idx}")
            params.append(department.upper())
            param_idx += 1
        
        if company:
            conditions.append(f"J.COMPANY = :{param_idx}")
            params.append(company.upper())
            param_idx += 1
        
        if location:
            conditions.append(f"J.LOCATION = :{param_idx}")
            params.append(location.upper())
            param_idx += 1
        
        if job_code:
            conditions.append(f"J.JOBCODE = :{param_idx}")
            params.append(job_code.upper())
            param_idx += 1
        
        if status.lower() == "active":
            conditions.append("J.HR_STATUS = 'A'")
        elif status.lower() == "inactive":
            conditions.append("J.HR_STATUS = 'I'")
        elif status.lower() == "terminated":
            conditions.append("J.EMPL_STATUS = 'T'")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
            SELECT 
                P.EMPLID,
                P.NAME,
                J.DEPTID,
                J.COMPANY,
                J.LOCATION,
                J.JOBCODE,
                J.HR_STATUS,
                J.EMPL_STATUS,
                J.SUPERVISOR_ID
            FROM PS_PERSONAL_DATA P
            JOIN PS_JOB J ON P.EMPLID = J.EMPLID
                AND J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                              WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                              AND J1.EFFDT <= SYSDATE)
                AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                               WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                               AND J.EFFDT = J2.EFFDT)
                AND J.EMPL_RCD = (SELECT MAX(J3.EMPL_RCD) FROM PS_JOB J3 
                                 WHERE J.EMPLID = J3.EMPLID)
            WHERE {where_clause}
            ORDER BY P.NAME
            FETCH FIRST :{param_idx} ROWS ONLY
        """
        params.append(limit)
        
        result = await execute_query(sql, params)
        
        if "error" in result:
            return result
        
        employees = []
        for row in result["results"]:
            employees.append({
                "employee_id": row["EMPLID"],
                "name": row["NAME"],
                "department": row["DEPTID"],
                "company": row["COMPANY"],
                "location": row["LOCATION"],
                "job_code": row["JOBCODE"],
                "hr_status": row["HR_STATUS"],
                "empl_status": row["EMPL_STATUS"],
                "supervisor_id": row["SUPERVISOR_ID"]
            })
        
        return {
            "count": len(employees),
            "employees": employees
        }

    @mcp.tool()
    async def get_job_history(employee_id: str, limit: int = 50) -> dict:
        """
        Get the complete job history for an employee showing all effective-dated changes.
        
        This shows every job change including:
        - Position changes
        - Department transfers
        - Promotions/demotions
        - Salary changes
        - Status changes (leave, return to work, termination, etc.)
        
        :param employee_id: The employee ID (EMPLID)
        :param limit: Maximum number of history records (default 50)
        :return: Chronological list of job changes
        """
        sql = """
            SELECT 
                J.EMPLID,
                J.EMPL_RCD,
                J.EFFDT,
                J.EFFSEQ,
                J.ACTION,
                A.DESCR AS ACTION_DESCR,
                J.ACTION_REASON,
                AR.DESCR AS REASON_DESCR,
                J.DEPTID,
                J.JOBCODE,
                J.LOCATION,
                J.COMPANY,
                J.HR_STATUS,
                J.EMPL_STATUS,
                J.COMPRATE,
                J.ANNUAL_RT,
                J.SUPERVISOR_ID,
                J.POSITION_NBR
            FROM PS_JOB J
            LEFT JOIN PS_ACTION_TBL A ON J.ACTION = A.ACTION
                AND A.EFFDT = (SELECT MAX(A1.EFFDT) FROM PS_ACTION_TBL A1 
                              WHERE A.ACTION = A1.ACTION AND A1.EFFDT <= SYSDATE)
            LEFT JOIN PS_ACTN_REASON_TBL AR ON J.ACTION = AR.ACTION AND J.ACTION_REASON = AR.ACTION_REASON
                AND AR.EFFDT = (SELECT MAX(AR1.EFFDT) FROM PS_ACTN_REASON_TBL AR1 
                               WHERE AR.ACTION = AR1.ACTION AND AR.ACTION_REASON = AR1.ACTION_REASON 
                               AND AR1.EFFDT <= SYSDATE)
            WHERE J.EMPLID = :1
            ORDER BY J.EFFDT DESC, J.EFFSEQ DESC, J.EMPL_RCD DESC
            FETCH FIRST :2 ROWS ONLY
        """
        
        result = await execute_query(sql, [employee_id.upper(), limit])
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {"error": f"No job history found for employee '{employee_id}'."}
        
        history = []
        for row in result["results"]:
            history.append({
                "effective_date": str(row["EFFDT"]) if row["EFFDT"] else None,
                "effective_sequence": row["EFFSEQ"],
                "empl_rcd": row["EMPL_RCD"],
                "action": row["ACTION"],
                "action_description": row["ACTION_DESCR"],
                "action_reason": row["ACTION_REASON"],
                "reason_description": row["REASON_DESCR"],
                "department": row["DEPTID"],
                "job_code": row["JOBCODE"],
                "location": row["LOCATION"],
                "company": row["COMPANY"],
                "hr_status": row["HR_STATUS"],
                "empl_status": row["EMPL_STATUS"],
                "comp_rate": float(row["COMPRATE"]) if row["COMPRATE"] else None,
                "annual_rate": float(row["ANNUAL_RT"]) if row["ANNUAL_RT"] else None,
                "supervisor_id": row["SUPERVISOR_ID"],
                "position_number": row["POSITION_NBR"]
            })
        
        return {
            "employee_id": employee_id.upper(),
            "record_count": len(history),
            "history": history
        }

    @mcp.tool()
    async def get_org_chart(
        department_id: str | None = None,
        manager_id: str | None = None,
        company: str | None = None,
        max_depth: int = 3
    ) -> dict:
        """
        Get organizational hierarchy showing reporting relationships.
        
        You can start from:
        - A specific department (all employees in that dept with their managers)
        - A specific manager (all direct and indirect reports)
        - A company (top-level org structure)
        
        :param department_id: Starting department ID
        :param manager_id: Starting manager's employee ID
        :param company: Company code to filter by
        :param max_depth: Maximum depth of hierarchy to retrieve (default 3)
        :return: Hierarchical organization structure
        """
        if manager_id:
            sql = """
                SELECT 
                    J.EMPLID,
                    P.NAME,
                    J.DEPTID,
                    J.JOBCODE,
                    J.SUPERVISOR_ID,
                    J.COMPANY,
                    LEVEL AS DEPTH
                FROM PS_JOB J
                JOIN PS_PERSONAL_DATA P ON J.EMPLID = P.EMPLID
                WHERE J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                                WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                                AND J1.EFFDT <= SYSDATE)
                AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                               WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                               AND J.EFFDT = J2.EFFDT)
                AND J.EMPL_RCD = 0
                AND J.HR_STATUS = 'A'
                START WITH J.EMPLID = :1
                CONNECT BY PRIOR J.EMPLID = J.SUPERVISOR_ID AND LEVEL <= :2
                ORDER SIBLINGS BY P.NAME
            """
            params = [manager_id.upper(), max_depth]
        elif department_id:
            sql = """
                SELECT 
                    J.EMPLID,
                    P.NAME,
                    J.DEPTID,
                    J.JOBCODE,
                    J.SUPERVISOR_ID,
                    J.COMPANY,
                    1 AS DEPTH
                FROM PS_JOB J
                JOIN PS_PERSONAL_DATA P ON J.EMPLID = P.EMPLID
                WHERE J.DEPTID = :1
                AND J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                              WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                              AND J1.EFFDT <= SYSDATE)
                AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                               WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                               AND J.EFFDT = J2.EFFDT)
                AND J.EMPL_RCD = 0
                AND J.HR_STATUS = 'A'
                ORDER BY P.NAME
            """
            params = [department_id.upper()]
        else:
            return {"error": "Please provide either department_id or manager_id to generate org chart."}
        
        result = await execute_query(sql, params)
        
        if "error" in result:
            return result
        
        employees = []
        for row in result["results"]:
            employees.append({
                "employee_id": row["EMPLID"],
                "name": row["NAME"],
                "department": row["DEPTID"],
                "job_code": row["JOBCODE"],
                "reports_to": row["SUPERVISOR_ID"],
                "company": row["COMPANY"],
                "depth": row["DEPTH"]
            })
        
        return {
            "starting_point": manager_id or department_id,
            "employee_count": len(employees),
            "employees": employees
        }

    @mcp.tool()
    async def get_department_info(department_id: str) -> dict:
        """
        Get detailed information about a department including its current employees.
        
        :param department_id: The department ID (DEPTID)
        :return: Department details and employee list
        """
        dept_sql = """
            SELECT 
                D.SETID,
                D.DEPTID,
                D.EFFDT,
                D.DESCR,
                D.DESCRSHORT,
                D.MANAGER_ID,
                P.NAME AS MANAGER_NAME,
                D.LOCATION,
                D.COMPANY
            FROM PS_DEPT_TBL D
            LEFT JOIN PS_PERSONAL_DATA P ON D.MANAGER_ID = P.EMPLID
            WHERE D.DEPTID = :1
            AND D.EFFDT = (SELECT MAX(D1.EFFDT) FROM PS_DEPT_TBL D1 
                          WHERE D.SETID = D1.SETID AND D.DEPTID = D1.DEPTID 
                          AND D1.EFFDT <= SYSDATE)
            FETCH FIRST 1 ROW ONLY
        """
        
        dept_result = await execute_query(dept_sql, [department_id.upper()])
        
        if "error" in dept_result:
            return dept_result
        
        if not dept_result.get("results"):
            return {"error": f"Department '{department_id}' not found."}
        
        dept = dept_result["results"][0]
        
        emp_sql = """
            SELECT 
                J.EMPLID,
                P.NAME,
                J.JOBCODE,
                J.HR_STATUS
            FROM PS_JOB J
            JOIN PS_PERSONAL_DATA P ON J.EMPLID = P.EMPLID
            WHERE J.DEPTID = :1
            AND J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                          WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                          AND J1.EFFDT <= SYSDATE)
            AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                           WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                           AND J.EFFDT = J2.EFFDT)
            AND J.EMPL_RCD = 0
            AND J.HR_STATUS = 'A'
            ORDER BY P.NAME
        """
        
        emp_result = await execute_query(emp_sql, [department_id.upper()])
        
        employees = []
        if emp_result.get("results"):
            for row in emp_result["results"]:
                employees.append({
                    "employee_id": row["EMPLID"],
                    "name": row["NAME"],
                    "job_code": row["JOBCODE"]
                })
        
        return {
            "department_id": dept["DEPTID"],
            "description": dept["DESCR"],
            "short_description": dept["DESCRSHORT"],
            "effective_date": str(dept["EFFDT"]) if dept["EFFDT"] else None,
            "manager_id": dept["MANAGER_ID"],
            "manager_name": dept["MANAGER_NAME"],
            "location": dept["LOCATION"],
            "company": dept["COMPANY"],
            "active_employee_count": len(employees),
            "employees": employees
        }
