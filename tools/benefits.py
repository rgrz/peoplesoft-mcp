"""
Benefits semantic tools for PeopleSoft MCP.
High-level tools for benefit elections, dependents, and beneficiaries.
"""
from db import execute_query


def register_tools(mcp):
    """Register all Benefits tools with the MCP server."""
    
    @mcp.tool()
    async def get_benefit_elections(employee_id: str) -> dict:
        """
        Get current benefit plan elections for an employee.
        
        Shows active benefit enrollments including:
        - Health plans
        - Life insurance
        - Retirement plans
        - Other voluntary benefits
        
        :param employee_id: The employee ID (EMPLID)
        :return: List of benefit elections with plan details
        """
        sql = """
            SELECT 
                B.EMPLID,
                B.EMPL_RCD,
                B.BENEFIT_PROGRAM,
                BP.DESCR AS PROGRAM_NAME,
                B.PLAN_TYPE,
                PT.DESCR AS PLAN_TYPE_NAME,
                B.BENEFIT_PLAN,
                BPL.DESCR AS PLAN_NAME,
                B.COVERAGE_ELECT,
                B.COVERAGE_BEGIN_DT,
                B.COVERAGE_END_DT,
                B.DEDUCTION_END_DT,
                B.ANNUAL_PLEDGE,
                B.FLAT_DED_AMT
            FROM PS_BEN_PROG_PARTIC B
            LEFT JOIN PS_BEN_DEFN_PGM BP ON B.BENEFIT_PROGRAM = BP.BENEFIT_PROGRAM
                AND BP.EFFDT = (SELECT MAX(BP1.EFFDT) FROM PS_BEN_DEFN_PGM BP1 
                               WHERE BP.BENEFIT_PROGRAM = BP1.BENEFIT_PROGRAM AND BP1.EFFDT <= SYSDATE)
            LEFT JOIN PS_BENEF_PLAN_TBL BPL ON B.PLAN_TYPE = BPL.PLAN_TYPE AND B.BENEFIT_PLAN = BPL.BENEFIT_PLAN
                AND BPL.EFFDT = (SELECT MAX(BPL1.EFFDT) FROM PS_BENEF_PLAN_TBL BPL1 
                                WHERE BPL.PLAN_TYPE = BPL1.PLAN_TYPE AND BPL.BENEFIT_PLAN = BPL1.BENEFIT_PLAN 
                                AND BPL1.EFFDT <= SYSDATE)
            LEFT JOIN PS_PLAN_TYPE_TBL PT ON B.PLAN_TYPE = PT.PLAN_TYPE
            WHERE B.EMPLID = :1
            AND B.EFFDT = (SELECT MAX(B1.EFFDT) FROM PS_BEN_PROG_PARTIC B1 
                          WHERE B.EMPLID = B1.EMPLID AND B.EMPL_RCD = B1.EMPL_RCD 
                          AND B1.EFFDT <= SYSDATE)
            AND B.COVERAGE_ELECT IN ('E', 'W')
            ORDER BY B.PLAN_TYPE, B.BENEFIT_PLAN
        """
        
        result = await execute_query(sql, [employee_id.upper()])
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {"message": f"No benefit elections found for employee '{employee_id}'."}
        
        coverage_map = {
            "E": "Enrolled",
            "W": "Waived",
            "T": "Terminated"
        }
        
        elections = []
        for row in result["results"]:
            elections.append({
                "benefit_program": row["BENEFIT_PROGRAM"],
                "program_name": row["PROGRAM_NAME"],
                "plan_type": row["PLAN_TYPE"],
                "plan_type_name": row["PLAN_TYPE_NAME"],
                "benefit_plan": row["BENEFIT_PLAN"],
                "plan_name": row["PLAN_NAME"],
                "coverage_status": row["COVERAGE_ELECT"],
                "coverage_status_name": coverage_map.get(row["COVERAGE_ELECT"], "Unknown"),
                "coverage_begin": str(row["COVERAGE_BEGIN_DT"]) if row["COVERAGE_BEGIN_DT"] else None,
                "coverage_end": str(row["COVERAGE_END_DT"]) if row["COVERAGE_END_DT"] else None,
                "annual_pledge": float(row["ANNUAL_PLEDGE"]) if row["ANNUAL_PLEDGE"] else None,
                "flat_deduction": float(row["FLAT_DED_AMT"]) if row["FLAT_DED_AMT"] else None
            })
        
        return {
            "employee_id": employee_id.upper(),
            "election_count": len(elections),
            "elections": elections
        }

    @mcp.tool()
    async def get_dependents(employee_id: str) -> dict:
        """
        Get dependents and beneficiaries for an employee.
        
        Returns:
        - Dependent personal information
        - Relationship to employee
        - Benefits coverage status
        - National ID (if available)
        
        :param employee_id: The employee ID (EMPLID)
        :return: List of dependents with their details
        """
        sql = """
            SELECT 
                D.EMPLID,
                D.DEPENDENT_BENEF,
                D.NAME,
                D.BIRTHDATE,
                D.SEX,
                D.RELATIONSHIP,
                X.XLATLONGNAME AS RELATIONSHIP_NAME,
                D.DEP_BENEF_TYPE,
                CASE D.DEP_BENEF_TYPE 
                    WHEN 'D' THEN 'Dependent'
                    WHEN 'B' THEN 'Beneficiary'
                    WHEN 'O' THEN 'Both'
                    ELSE D.DEP_BENEF_TYPE
                END AS DEP_TYPE_NAME,
                D.MAR_STATUS,
                D.STUDENT,
                D.DISABLED,
                D.SAME_ADDRESS_EMPL,
                N.NATIONAL_ID,
                N.NATIONAL_ID_TYPE
            FROM PS_DEPENDENT_BENEF D
            LEFT JOIN PSXLATITEM X ON X.FIELDNAME = 'RELATIONSHIP' AND X.FIELDVALUE = D.RELATIONSHIP
                AND X.EFFDT = (SELECT MAX(X1.EFFDT) FROM PSXLATITEM X1 
                              WHERE X1.FIELDNAME = 'RELATIONSHIP' AND X1.FIELDVALUE = D.RELATIONSHIP 
                              AND X1.EFFDT <= SYSDATE)
            LEFT JOIN PS_DEP_BENEF_NID N ON D.EMPLID = N.EMPLID AND D.DEPENDENT_BENEF = N.DEPENDENT_BENEF
            WHERE D.EMPLID = :1
            ORDER BY D.NAME
        """
        
        result = await execute_query(sql, [employee_id.upper()])
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {"message": f"No dependents found for employee '{employee_id}'."}
        
        dependents = []
        for row in result["results"]:
            dependents.append({
                "dependent_id": row["DEPENDENT_BENEF"],
                "name": row["NAME"],
                "birthdate": str(row["BIRTHDATE"]) if row["BIRTHDATE"] else None,
                "sex": row["SEX"],
                "relationship": row["RELATIONSHIP"],
                "relationship_name": row["RELATIONSHIP_NAME"],
                "type": row["DEP_BENEF_TYPE"],
                "type_name": row["DEP_TYPE_NAME"],
                "marital_status": row["MAR_STATUS"],
                "is_student": row["STUDENT"] == "Y",
                "is_disabled": row["DISABLED"] == "Y",
                "same_address": row["SAME_ADDRESS_EMPL"] == "Y",
                "national_id_last4": row["NATIONAL_ID"][-4:] if row["NATIONAL_ID"] else None,
                "national_id_type": row["NATIONAL_ID_TYPE"]
            })
        
        return {
            "employee_id": employee_id.upper(),
            "dependent_count": len(dependents),
            "dependents": dependents
        }

    @mcp.tool()
    async def get_beneficiaries(employee_id: str, plan_type: str | None = None) -> dict:
        """
        Get beneficiary designations for an employee's benefit plans.
        
        :param employee_id: The employee ID (EMPLID)
        :param plan_type: Optional filter by plan type (e.g., '2A' for life insurance)
        :return: Beneficiary designations by plan
        """
        conditions = ["B.EMPLID = :1"]
        params = [employee_id.upper()]
        
        if plan_type:
            conditions.append("B.PLAN_TYPE = :2")
            params.append(plan_type.upper())
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
            SELECT 
                B.EMPLID,
                B.PLAN_TYPE,
                PT.DESCR AS PLAN_TYPE_NAME,
                B.BENEFIT_PLAN,
                BPL.DESCR AS PLAN_NAME,
                B.DEPENDENT_BENEF,
                D.NAME AS BENEFICIARY_NAME,
                D.RELATIONSHIP,
                X.XLATLONGNAME AS RELATIONSHIP_NAME,
                B.BENEF_PCT AS PERCENTAGE,
                B.FLAT_AMOUNT,
                B.CONTINGENT,
                B.EFFDT
            FROM PS_DEPEND_BENEF B
            JOIN PS_DEPENDENT_BENEF D ON B.EMPLID = D.EMPLID AND B.DEPENDENT_BENEF = D.DEPENDENT_BENEF
            LEFT JOIN PS_PLAN_TYPE_TBL PT ON B.PLAN_TYPE = PT.PLAN_TYPE
            LEFT JOIN PS_BENEF_PLAN_TBL BPL ON B.PLAN_TYPE = BPL.PLAN_TYPE AND B.BENEFIT_PLAN = BPL.BENEFIT_PLAN
                AND BPL.EFFDT = (SELECT MAX(BPL1.EFFDT) FROM PS_BENEF_PLAN_TBL BPL1 
                                WHERE BPL.PLAN_TYPE = BPL1.PLAN_TYPE AND BPL.BENEFIT_PLAN = BPL1.BENEFIT_PLAN 
                                AND BPL1.EFFDT <= SYSDATE)
            LEFT JOIN PSXLATITEM X ON X.FIELDNAME = 'RELATIONSHIP' AND X.FIELDVALUE = D.RELATIONSHIP
                AND X.EFFDT = (SELECT MAX(X1.EFFDT) FROM PSXLATITEM X1 
                              WHERE X1.FIELDNAME = 'RELATIONSHIP' AND X1.FIELDVALUE = D.RELATIONSHIP 
                              AND X1.EFFDT <= SYSDATE)
            WHERE {where_clause}
            AND B.EFFDT = (SELECT MAX(B1.EFFDT) FROM PS_DEPEND_BENEF B1 
                          WHERE B.EMPLID = B1.EMPLID AND B.PLAN_TYPE = B1.PLAN_TYPE 
                          AND B.BENEFIT_PLAN = B1.BENEFIT_PLAN AND B1.EFFDT <= SYSDATE)
            ORDER BY B.PLAN_TYPE, B.CONTINGENT, B.BENEF_PCT DESC
        """
        
        result = await execute_query(sql, params)
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {"message": f"No beneficiary designations found for employee '{employee_id}'."}
        
        plans = {}
        for row in result["results"]:
            plan_key = f"{row['PLAN_TYPE']}_{row['BENEFIT_PLAN']}"
            if plan_key not in plans:
                plans[plan_key] = {
                    "plan_type": row["PLAN_TYPE"],
                    "plan_type_name": row["PLAN_TYPE_NAME"],
                    "benefit_plan": row["BENEFIT_PLAN"],
                    "plan_name": row["PLAN_NAME"],
                    "primary_beneficiaries": [],
                    "contingent_beneficiaries": []
                }
            
            beneficiary = {
                "dependent_id": row["DEPENDENT_BENEF"],
                "name": row["BENEFICIARY_NAME"],
                "relationship": row["RELATIONSHIP"],
                "relationship_name": row["RELATIONSHIP_NAME"],
                "percentage": float(row["PERCENTAGE"]) if row["PERCENTAGE"] else None,
                "flat_amount": float(row["FLAT_AMOUNT"]) if row["FLAT_AMOUNT"] else None
            }
            
            if row["CONTINGENT"] == "Y":
                plans[plan_key]["contingent_beneficiaries"].append(beneficiary)
            else:
                plans[plan_key]["primary_beneficiaries"].append(beneficiary)
        
        return {
            "employee_id": employee_id.upper(),
            "plan_count": len(plans),
            "plans": list(plans.values())
        }

    @mcp.tool()
    async def get_benefit_costs(
        employee_id: str,
        as_of_date: str | None = None
    ) -> dict:
        """
        Get benefit cost information including employee and employer contributions.
        
        :param employee_id: The employee ID (EMPLID)
        :param as_of_date: Optional date (YYYY-MM-DD format). Defaults to current date.
        :return: Benefit costs by plan
        """
        sql = """
            SELECT 
                B.EMPLID,
                B.PLAN_TYPE,
                PT.DESCR AS PLAN_TYPE_NAME,
                B.BENEFIT_PLAN,
                BPL.DESCR AS PLAN_NAME,
                B.COVRG_CD,
                B.COVERAGE_BEGIN_DT,
                B.FLAT_DED_AMT AS EMPLOYEE_COST,
                B.DED_ADDL_AMT AS ADDITIONAL_COST
            FROM PS_BEN_PROG_PARTIC B
            LEFT JOIN PS_PLAN_TYPE_TBL PT ON B.PLAN_TYPE = PT.PLAN_TYPE
            LEFT JOIN PS_BENEF_PLAN_TBL BPL ON B.PLAN_TYPE = BPL.PLAN_TYPE AND B.BENEFIT_PLAN = BPL.BENEFIT_PLAN
                AND BPL.EFFDT = (SELECT MAX(BPL1.EFFDT) FROM PS_BENEF_PLAN_TBL BPL1 
                                WHERE BPL.PLAN_TYPE = BPL1.PLAN_TYPE AND BPL.BENEFIT_PLAN = BPL1.BENEFIT_PLAN 
                                AND BPL1.EFFDT <= SYSDATE)
            WHERE B.EMPLID = :1
            AND B.EFFDT = (SELECT MAX(B1.EFFDT) FROM PS_BEN_PROG_PARTIC B1 
                          WHERE B.EMPLID = B1.EMPLID AND B.EMPL_RCD = B1.EMPL_RCD 
                          AND B1.EFFDT <= SYSDATE)
            AND B.COVERAGE_ELECT = 'E'
            ORDER BY B.PLAN_TYPE
        """
        
        result = await execute_query(sql, [employee_id.upper()])
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {"message": f"No benefit costs found for employee '{employee_id}'."}
        
        costs = []
        total_employee_cost = 0
        
        for row in result["results"]:
            emp_cost = float(row["EMPLOYEE_COST"]) if row["EMPLOYEE_COST"] else 0
            add_cost = float(row["ADDITIONAL_COST"]) if row["ADDITIONAL_COST"] else 0
            
            costs.append({
                "plan_type": row["PLAN_TYPE"],
                "plan_type_name": row["PLAN_TYPE_NAME"],
                "benefit_plan": row["BENEFIT_PLAN"],
                "plan_name": row["PLAN_NAME"],
                "coverage_code": row["COVRG_CD"],
                "coverage_begin": str(row["COVERAGE_BEGIN_DT"]) if row["COVERAGE_BEGIN_DT"] else None,
                "employee_cost": emp_cost,
                "additional_cost": add_cost,
                "total_cost": emp_cost + add_cost
            })
            total_employee_cost += emp_cost + add_cost
        
        return {
            "employee_id": employee_id.upper(),
            "plan_count": len(costs),
            "total_employee_cost": total_employee_cost,
            "costs": costs
        }
