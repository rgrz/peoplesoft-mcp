"""
ePerformance semantic tools for PeopleSoft MCP.
High-level tools for performance reviews and appraisals.
"""
from db import execute_query


def register_tools(mcp):
    """Register all ePerformance tools with the MCP server."""
    
    @mcp.tool()
    async def get_performance_reviews(
        employee_id: str,
        year: int | None = None,
        status: str | None = None
    ) -> dict:
        """
        Get performance appraisals for an employee.
        
        Status codes:
        - 'INP': In Progress
        - 'COMP': Completed
        - 'CANC': Cancelled
        - 'PEND': Pending
        
        :param employee_id: The employee ID (EMPLID)
        :param year: Optional filter by review year
        :param status: Optional filter by status code
        :return: List of performance reviews
        """
        conditions = ["A.EMPLID = :1"]
        params = [employee_id.upper()]
        param_idx = 2
        
        if year:
            conditions.append(f"EXTRACT(YEAR FROM A.EP_APPR_END_DT) = :{param_idx}")
            params.append(year)
            param_idx += 1
        
        if status:
            conditions.append(f"A.EP_APPR_STATUS = :{param_idx}")
            params.append(status.upper())
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
            SELECT 
                A.EP_APPR_ID,
                A.EMPLID,
                P.NAME AS EMPLOYEE_NAME,
                A.EP_REVIEWER_ID,
                R.NAME AS REVIEWER_NAME,
                A.EP_APPR_TYPE,
                T.DESCR AS APPR_TYPE_DESCR,
                A.EP_APPR_STATUS,
                A.EP_APPR_BEGIN_DT,
                A.EP_APPR_END_DT,
                A.EP_APPR_DUE_DT,
                A.EP_OVERALL_RATING,
                A.LAST_UPDATE_DTTM
            FROM PS_EP_APPR A
            JOIN PS_PERSONAL_DATA P ON A.EMPLID = P.EMPLID
            LEFT JOIN PS_PERSONAL_DATA R ON A.EP_REVIEWER_ID = R.EMPLID
            LEFT JOIN PS_EP_APPR_TYPE_TB T ON A.EP_APPR_TYPE = T.EP_APPR_TYPE
                AND T.EFFDT = (SELECT MAX(T1.EFFDT) FROM PS_EP_APPR_TYPE_TB T1 
                              WHERE T.EP_APPR_TYPE = T1.EP_APPR_TYPE AND T1.EFFDT <= SYSDATE)
            WHERE {where_clause}
            ORDER BY A.EP_APPR_END_DT DESC
        """
        
        result = await execute_query(sql, params)
        
        if "error" in result:
            return result
        
        if not result.get("results"):
            return {"message": f"No performance reviews found for employee '{employee_id}'."}
        
        status_map = {
            "INP": "In Progress",
            "COMP": "Completed",
            "CANC": "Cancelled",
            "PEND": "Pending"
        }
        
        reviews = []
        for row in result["results"]:
            reviews.append({
                "appraisal_id": row["EP_APPR_ID"],
                "employee_id": row["EMPLID"],
                "employee_name": row["EMPLOYEE_NAME"],
                "reviewer_id": row["EP_REVIEWER_ID"],
                "reviewer_name": row["REVIEWER_NAME"],
                "appraisal_type": row["EP_APPR_TYPE"],
                "appraisal_type_description": row["APPR_TYPE_DESCR"],
                "status": row["EP_APPR_STATUS"],
                "status_description": status_map.get(row["EP_APPR_STATUS"], "Unknown"),
                "period_start": str(row["EP_APPR_BEGIN_DT"]) if row["EP_APPR_BEGIN_DT"] else None,
                "period_end": str(row["EP_APPR_END_DT"]) if row["EP_APPR_END_DT"] else None,
                "due_date": str(row["EP_APPR_DUE_DT"]) if row["EP_APPR_DUE_DT"] else None,
                "overall_rating": row["EP_OVERALL_RATING"],
                "last_updated": str(row["LAST_UPDATE_DTTM"]) if row["LAST_UPDATE_DTTM"] else None
            })
        
        return {
            "employee_id": employee_id.upper(),
            "review_count": len(reviews),
            "reviews": reviews
        }

    @mcp.tool()
    async def get_review_details(appraisal_id: str) -> dict:
        """
        Get detailed ratings, goals, and comments for a specific performance review.
        
        :param appraisal_id: The appraisal ID (EP_APPR_ID)
        :return: Complete review details including sections, items, and ratings
        """
        header_sql = """
            SELECT 
                A.EP_APPR_ID,
                A.EMPLID,
                P.NAME AS EMPLOYEE_NAME,
                A.EP_REVIEWER_ID,
                R.NAME AS REVIEWER_NAME,
                A.EP_APPR_TYPE,
                A.EP_APPR_STATUS,
                A.EP_APPR_BEGIN_DT,
                A.EP_APPR_END_DT,
                A.EP_OVERALL_RATING,
                A.EP_OVERALL_COMMENT
            FROM PS_EP_APPR A
            JOIN PS_PERSONAL_DATA P ON A.EMPLID = P.EMPLID
            LEFT JOIN PS_PERSONAL_DATA R ON A.EP_REVIEWER_ID = R.EMPLID
            WHERE A.EP_APPR_ID = :1
        """
        
        header_result = await execute_query(header_sql, [appraisal_id])
        
        if "error" in header_result:
            return header_result
        
        if not header_result.get("results"):
            return {"error": f"Appraisal '{appraisal_id}' not found."}
        
        header = header_result["results"][0]
        
        sections_sql = """
            SELECT 
                S.EP_APPR_ID,
                S.EP_SECTION_ID,
                S.EP_SECTION_TYPE,
                S.EP_SECT_RATING,
                S.EP_SECT_WEIGHT
            FROM PS_EP_APPR_SECTION S
            WHERE S.EP_APPR_ID = :1
            ORDER BY S.EP_SECTION_ID
        """
        
        sections_result = await execute_query(sections_sql, [appraisal_id])
        
        items_sql = """
            SELECT 
                I.EP_APPR_ID,
                I.EP_SECTION_ID,
                I.EP_ITEM_ID,
                I.EP_TITLE,
                I.EP_RATING,
                I.EP_WEIGHT,
                I.EP_COMMENT_TXT
            FROM PS_EP_APPR_ITEM I
            WHERE I.EP_APPR_ID = :1
            ORDER BY I.EP_SECTION_ID, I.EP_ITEM_ID
        """
        
        items_result = await execute_query(items_sql, [appraisal_id])
        
        sections_map = {}
        if sections_result.get("results"):
            for row in sections_result["results"]:
                sections_map[row["EP_SECTION_ID"]] = {
                    "section_id": row["EP_SECTION_ID"],
                    "section_type": row["EP_SECTION_TYPE"],
                    "section_rating": row["EP_SECT_RATING"],
                    "section_weight": float(row["EP_SECT_WEIGHT"]) if row["EP_SECT_WEIGHT"] else None,
                    "items": []
                }
        
        if items_result.get("results"):
            for row in items_result["results"]:
                section_id = row["EP_SECTION_ID"]
                if section_id in sections_map:
                    sections_map[section_id]["items"].append({
                        "item_id": row["EP_ITEM_ID"],
                        "title": row["EP_TITLE"],
                        "rating": row["EP_RATING"],
                        "weight": float(row["EP_WEIGHT"]) if row["EP_WEIGHT"] else None,
                        "comment": row["EP_COMMENT_TXT"]
                    })
        
        return {
            "appraisal_id": header["EP_APPR_ID"],
            "employee_id": header["EMPLID"],
            "employee_name": header["EMPLOYEE_NAME"],
            "reviewer_id": header["EP_REVIEWER_ID"],
            "reviewer_name": header["REVIEWER_NAME"],
            "appraisal_type": header["EP_APPR_TYPE"],
            "status": header["EP_APPR_STATUS"],
            "period_start": str(header["EP_APPR_BEGIN_DT"]) if header["EP_APPR_BEGIN_DT"] else None,
            "period_end": str(header["EP_APPR_END_DT"]) if header["EP_APPR_END_DT"] else None,
            "overall_rating": header["EP_OVERALL_RATING"],
            "overall_comment": header["EP_OVERALL_COMMENT"],
            "sections": list(sections_map.values())
        }

    @mcp.tool()
    async def search_reviews(
        reviewer_id: str | None = None,
        department: str | None = None,
        status: str | None = None,
        year: int | None = None,
        limit: int = 50
    ) -> dict:
        """
        Search performance reviews by various criteria.
        
        :param reviewer_id: Filter by reviewer's employee ID
        :param department: Filter by employee's department
        :param status: Filter by status ('INP', 'COMP', 'CANC', 'PEND')
        :param year: Filter by review year
        :param limit: Maximum results (default 50)
        :return: List of matching reviews
        """
        conditions = []
        params = []
        param_idx = 1
        
        if reviewer_id:
            conditions.append(f"A.EP_REVIEWER_ID = :{param_idx}")
            params.append(reviewer_id.upper())
            param_idx += 1
        
        if department:
            conditions.append(f"""
                A.EMPLID IN (
                    SELECT J.EMPLID FROM PS_JOB J
                    WHERE J.DEPTID = :{param_idx}
                    AND J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 
                                  WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD 
                                  AND J1.EFFDT <= SYSDATE)
                    AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 
                                   WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD 
                                   AND J.EFFDT = J2.EFFDT)
                    AND J.EMPL_RCD = 0
                )
            """)
            params.append(department.upper())
            param_idx += 1
        
        if status:
            conditions.append(f"A.EP_APPR_STATUS = :{param_idx}")
            params.append(status.upper())
            param_idx += 1
        
        if year:
            conditions.append(f"EXTRACT(YEAR FROM A.EP_APPR_END_DT) = :{param_idx}")
            params.append(year)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
            SELECT 
                A.EP_APPR_ID,
                A.EMPLID,
                P.NAME AS EMPLOYEE_NAME,
                A.EP_REVIEWER_ID,
                R.NAME AS REVIEWER_NAME,
                A.EP_APPR_TYPE,
                A.EP_APPR_STATUS,
                A.EP_APPR_END_DT,
                A.EP_OVERALL_RATING
            FROM PS_EP_APPR A
            JOIN PS_PERSONAL_DATA P ON A.EMPLID = P.EMPLID
            LEFT JOIN PS_PERSONAL_DATA R ON A.EP_REVIEWER_ID = R.EMPLID
            WHERE {where_clause}
            ORDER BY A.EP_APPR_END_DT DESC
            FETCH FIRST :{param_idx} ROWS ONLY
        """
        params.append(limit)
        
        result = await execute_query(sql, params)
        
        if "error" in result:
            return result
        
        reviews = []
        for row in result["results"]:
            reviews.append({
                "appraisal_id": row["EP_APPR_ID"],
                "employee_id": row["EMPLID"],
                "employee_name": row["EMPLOYEE_NAME"],
                "reviewer_id": row["EP_REVIEWER_ID"],
                "reviewer_name": row["REVIEWER_NAME"],
                "appraisal_type": row["EP_APPR_TYPE"],
                "status": row["EP_APPR_STATUS"],
                "period_end": str(row["EP_APPR_END_DT"]) if row["EP_APPR_END_DT"] else None,
                "overall_rating": row["EP_OVERALL_RATING"]
            })
        
        return {
            "count": len(reviews),
            "reviews": reviews
        }
