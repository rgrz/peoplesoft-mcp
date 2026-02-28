"""
Global Payroll semantic tools for PeopleSoft MCP.
High-level tools for payroll results, accumulators, and payment data.
"""
from db import execute_query, execute_query_with_limit


def register_tools(mcp):
    """Register all Global Payroll tools with the MCP server."""
    
    @mcp.tool()
    async def get_payroll_results(
        employee_id: str,
        calendar_run: str | None = None,
        element_type: str | None = None
    ) -> dict:
        """
        Get earnings and deductions results for an employee's payroll run.
        
        :param employee_id: The employee ID (EMPLID)
        :param calendar_run: Optional calendar run ID. If not provided, returns latest run.
        :param element_type: Optional filter: 'earnings', 'deductions', or 'all' (default)
        :return: Payroll results with earnings and deductions
        """
        conditions = ["R.EMPLID = :1"]
        params = [employee_id.upper()]
        param_idx = 2
        
        if calendar_run:
            conditions.append(f"R.CAL_RUN_ID = :{param_idx}")
            params.append(calendar_run.upper())
            param_idx += 1
        else:
            conditions.append("""
                R.CAL_RUN_ID = (
                    SELECT MAX(R2.CAL_RUN_ID) FROM PS_GP_RSLT_ERN_DED R2 
                    WHERE R2.EMPLID = R.EMPLID
                )
            """)
        
        if element_type and element_type.lower() == "earnings":
            conditions.append("PIN.PIN_TYPE = 'ER'")
        elif element_type and element_type.lower() == "deductions":
            conditions.append("PIN.PIN_TYPE = 'DD'")
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
            SELECT 
                R.EMPLID,
                R.CAL_RUN_ID,
                R.GP_PAYGROUP,
                R.CAL_ID,
                R.RSLT_SEG_NUM,
                R.PIN_NUM,
                PIN.PIN_NM AS ELEMENT_NAME,
                PIN.PIN_TYPE,
                PIN.DESCR AS ELEMENT_DESCR,
                R.SLICE_BGN_DT,
                R.SLICE_END_DT,
                R.CALC_RSLT_VAL AS AMOUNT,
                R.BASE_RSLT_VAL AS BASE_AMOUNT,
                R.RATE_RSLT_VAL AS RATE,
                R.UNIT_RSLT_VAL AS UNITS,
                R.PCT_RSLT_VAL AS PERCENTAGE
            FROM PS_GP_RSLT_ERN_DED R
            JOIN PS_GP_PIN PIN ON R.PIN_NUM = PIN.PIN_NUM
            WHERE {where_clause}
            ORDER BY PIN.PIN_TYPE, PIN.PIN_NM
        """
        
        result = await execute_query(sql, params)
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {"error": f"No payroll results found for employee '{employee_id}'."}
        
        earnings = []
        deductions = []
        
        cal_run_id = None
        for row in result["results"]:
            cal_run_id = row["CAL_RUN_ID"]
            item = {
                "element_name": row["ELEMENT_NAME"],
                "description": row["ELEMENT_DESCR"],
                "amount": float(row["AMOUNT"]) if row["AMOUNT"] else 0,
                "base_amount": float(row["BASE_AMOUNT"]) if row["BASE_AMOUNT"] else None,
                "rate": float(row["RATE"]) if row["RATE"] else None,
                "units": float(row["UNITS"]) if row["UNITS"] else None,
                "percentage": float(row["PERCENTAGE"]) if row["PERCENTAGE"] else None,
                "period_start": str(row["SLICE_BGN_DT"]) if row["SLICE_BGN_DT"] else None,
                "period_end": str(row["SLICE_END_DT"]) if row["SLICE_END_DT"] else None
            }
            
            if row["PIN_TYPE"] == "ER":
                earnings.append(item)
            else:
                deductions.append(item)
        
        total_earnings = sum(e["amount"] for e in earnings)
        total_deductions = sum(d["amount"] for d in deductions)
        
        return {
            "employee_id": employee_id.upper(),
            "calendar_run": cal_run_id,
            "summary": {
                "total_earnings": total_earnings,
                "total_deductions": total_deductions,
                "net_pay": total_earnings - total_deductions
            },
            "earnings": earnings,
            "deductions": deductions
        }

    @mcp.tool()
    async def get_payroll_status(calendar_run: str) -> dict:
        """
        Get the processing status for all employees in a payroll calendar run.
        
        Status codes:
        - 'I': Identified
        - 'C': Calculated
        - 'F': Finalized
        - 'P': Paid
        
        :param calendar_run: The calendar run ID (CAL_RUN_ID)
        :return: Summary of payroll processing status
        """
        sql = """
            SELECT 
                S.CAL_RUN_ID,
                S.EMPLID,
                P.NAME,
                S.GP_PAYGROUP,
                S.CAL_ID,
                S.PYE_PRC_STATUS AS STATUS,
                S.SEL_STAT AS SELECTION_STATUS,
                S.CALC_ACTION,
                S.RSLT_VER_NUM,
                S.RSLT_REV_NUM
            FROM PS_GP_PYE_PRC_STAT S
            JOIN PS_PERSONAL_DATA P ON S.EMPLID = P.EMPLID
            WHERE S.CAL_RUN_ID = :1
            ORDER BY S.PYE_PRC_STATUS, P.NAME
        """
        
        result = await execute_query(sql, [calendar_run.upper()])
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {"error": f"No payroll run found with ID '{calendar_run}'."}
        
        status_map = {
            "I": "Identified",
            "C": "Calculated", 
            "F": "Finalized",
            "P": "Paid"
        }
        
        status_counts = {"I": 0, "C": 0, "F": 0, "P": 0}
        employees = []
        
        for row in result["results"]:
            status = row["STATUS"]
            if status in status_counts:
                status_counts[status] += 1
            
            employees.append({
                "employee_id": row["EMPLID"],
                "name": row["NAME"],
                "paygroup": row["GP_PAYGROUP"],
                "calendar": row["CAL_ID"],
                "status": status,
                "status_description": status_map.get(status, "Unknown"),
                "version": row["RSLT_VER_NUM"],
                "revision": row["RSLT_REV_NUM"]
            })
        
        return {
            "calendar_run": calendar_run.upper(),
            "total_employees": len(employees),
            "status_summary": {
                "identified": status_counts["I"],
                "calculated": status_counts["C"],
                "finalized": status_counts["F"],
                "paid": status_counts["P"]
            },
            "employees": employees
        }

    @mcp.tool()
    async def get_accumulator_balances(
        employee_id: str,
        accum_type: str | None = None,
        calendar_run: str | None = None
    ) -> dict:
        """
        Get accumulator balances (YTD, MTD, etc.) for an employee.
        
        Accumulators track cumulative values like:
        - Year-to-date earnings
        - Year-to-date taxes
        - Lifetime pension contributions
        - Month-to-date hours worked
        
        :param employee_id: The employee ID (EMPLID)
        :param accum_type: Optional filter by accumulator type (e.g., 'YTD', 'MTD', 'QTD')
        :param calendar_run: Optional calendar run ID. If not provided, returns latest.
        :return: Accumulator balances
        """
        conditions = ["A.EMPLID = :1"]
        params = [employee_id.upper()]
        param_idx = 2
        
        if calendar_run:
            conditions.append(f"A.CAL_RUN_ID = :{param_idx}")
            params.append(calendar_run.upper())
            param_idx += 1
        else:
            conditions.append("""
                A.CAL_RUN_ID = (
                    SELECT MAX(A2.CAL_RUN_ID) FROM PS_GP_RSLT_ACUM A2 
                    WHERE A2.EMPLID = A.EMPLID
                )
            """)
        
        if accum_type:
            conditions.append(f"PIN.PIN_NM LIKE '%' || :{param_idx} || '%'")
            params.append(accum_type.upper())
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
            SELECT 
                A.EMPLID,
                A.CAL_RUN_ID,
                A.PIN_NUM,
                PIN.PIN_NM AS ACCUM_NAME,
                PIN.DESCR AS ACCUM_DESCR,
                A.ACM_FROM_DT AS PERIOD_START,
                A.ACM_THRU_DT AS PERIOD_END,
                A.CALC_RSLT_VAL AS BALANCE,
                A.USER_ADJ_VAL AS USER_ADJUSTMENT,
                A.CALC_ADJ_VAL AS CALC_ADJUSTMENT
            FROM PS_GP_RSLT_ACUM A
            JOIN PS_GP_PIN PIN ON A.PIN_NUM = PIN.PIN_NUM
            WHERE {where_clause}
            AND A.CALC_RSLT_VAL != 0
            ORDER BY PIN.PIN_NM
        """
        
        result = await execute_query(sql, params)
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {"message": f"No accumulator balances found for employee '{employee_id}'."}
        
        accumulators = []
        cal_run_id = None
        
        for row in result["results"]:
            cal_run_id = row["CAL_RUN_ID"]
            accumulators.append({
                "name": row["ACCUM_NAME"],
                "description": row["ACCUM_DESCR"],
                "balance": float(row["BALANCE"]) if row["BALANCE"] else 0,
                "user_adjustment": float(row["USER_ADJUSTMENT"]) if row["USER_ADJUSTMENT"] else 0,
                "calc_adjustment": float(row["CALC_ADJUSTMENT"]) if row["CALC_ADJUSTMENT"] else 0,
                "period_start": str(row["PERIOD_START"]) if row["PERIOD_START"] else None,
                "period_end": str(row["PERIOD_END"]) if row["PERIOD_END"] else None
            })
        
        return {
            "employee_id": employee_id.upper(),
            "calendar_run": cal_run_id,
            "accumulator_count": len(accumulators),
            "accumulators": accumulators
        }

    @mcp.tool()
    async def get_payment_info(
        employee_id: str,
        calendar_run: str | None = None
    ) -> dict:
        """
        Get payment preparation and payment details for an employee.
        
        :param employee_id: The employee ID (EMPLID)
        :param calendar_run: Optional calendar run ID. If not provided, returns latest.
        :return: Payment details including net pay and payment method
        """
        conditions = ["PMT.EMPLID = :1"]
        params = [employee_id.upper()]
        
        if calendar_run:
            conditions.append("PMT.CAL_RUN_ID = :2")
            params.append(calendar_run.upper())
        else:
            conditions.append("""
                PMT.CAL_RUN_ID = (
                    SELECT MAX(P2.CAL_RUN_ID) FROM PS_GP_PAYMENT P2 
                    WHERE P2.EMPLID = PMT.EMPLID
                )
            """)
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
            SELECT 
                PMT.EMPLID,
                PMT.CAL_RUN_ID,
                PMT.GP_PAYGROUP,
                PMT.PAY_ENTITY,
                PMT.PYMT_DT AS PAYMENT_DATE,
                PMT.GP_PMT_AMT AS PAYMENT_AMOUNT,
                PMT.CURRENCY_CD,
                PMT.PYMT_STATUS AS PAYMENT_STATUS,
                PMT.BANK_CD,
                PMT.ACCOUNT_NUM,
                PMT.PYMT_ID
            FROM PS_GP_PAYMENT PMT
            WHERE {where_clause}
            ORDER BY PMT.PYMT_DT DESC
        """
        
        result = await execute_query(sql, params)
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {"message": f"No payment records found for employee '{employee_id}'."}
        
        payments = []
        for row in result["results"]:
            payments.append({
                "calendar_run": row["CAL_RUN_ID"],
                "paygroup": row["GP_PAYGROUP"],
                "pay_entity": row["PAY_ENTITY"],
                "payment_date": str(row["PAYMENT_DATE"]) if row["PAYMENT_DATE"] else None,
                "amount": float(row["PAYMENT_AMOUNT"]) if row["PAYMENT_AMOUNT"] else 0,
                "currency": row["CURRENCY_CD"],
                "status": row["PAYMENT_STATUS"],
                "bank_code": row["BANK_CD"],
                "account_number": row["ACCOUNT_NUM"][-4:] if row["ACCOUNT_NUM"] else None,
                "payment_id": row["PYMT_ID"]
            })
        
        return {
            "employee_id": employee_id.upper(),
            "payment_count": len(payments),
            "payments": payments
        }

    @mcp.tool()
    async def list_calendar_runs(
        pay_entity: str | None = None,
        year: int | None = None,
        status: str | None = None,
        limit: int = 20
    ) -> dict:
        """
        List payroll calendar runs with their status.
        
        :param pay_entity: Optional filter by pay entity
        :param year: Optional filter by year
        :param status: Optional filter by status ('open', 'closed', 'finalized')
        :param limit: Maximum results (default 20)
        :return: List of calendar runs
        """
        conditions = []
        params = []
        param_idx = 1
        
        if pay_entity:
            conditions.append(f"CG.PAY_ENTITY = :{param_idx}")
            params.append(pay_entity.upper())
            param_idx += 1
        
        if year:
            conditions.append(f"EXTRACT(YEAR FROM CG.RUN_FINALIZED_TS) = :{param_idx} OR EXTRACT(YEAR FROM CG.RUN_OPEN_TS) = :{param_idx}")
            params.append(year)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
            SELECT 
                CG.CAL_RUN_ID,
                CG.DESCR,
                CG.PAY_ENTITY,
                CG.RUN_OPEN_TS,
                CG.RUN_FINALIZED_TS,
                CG.CALC_TYPE,
                (SELECT COUNT(DISTINCT EMPLID) FROM PS_GP_PYE_PRC_STAT 
                 WHERE CAL_RUN_ID = CG.CAL_RUN_ID) AS EMPLOYEE_COUNT
            FROM PS_GP_CAL_RUN CG
            WHERE {where_clause}
            ORDER BY CG.CAL_RUN_ID DESC
            FETCH FIRST :{param_idx} ROWS ONLY
        """
        params.append(limit)
        
        result = await execute_query(sql, params)
        
        if "error" in result:
            return result
        
        runs = []
        for row in result["results"]:
            runs.append({
                "calendar_run_id": row["CAL_RUN_ID"],
                "description": row["DESCR"],
                "pay_entity": row["PAY_ENTITY"],
                "opened": str(row["RUN_OPEN_TS"]) if row["RUN_OPEN_TS"] else None,
                "finalized": str(row["RUN_FINALIZED_TS"]) if row["RUN_FINALIZED_TS"] else None,
                "calc_type": row["CALC_TYPE"],
                "employee_count": row["EMPLOYEE_COUNT"]
            })
        
        return {
            "count": len(runs),
            "calendar_runs": runs
        }
