# PeopleSoft MCP Enhancement Research Report

**Date:** 2025-03-09  
**Targets:** JOB_DATA, USERMAINT components; GPES_TAX_10T AE; schema discovery  
**Environment:** PeopleSoft HCM, Oracle DB (user-peoplesoft MCP server)  
**Goal:** Test MCP tools against real data, document failures, and propose enhancements

---

## 1. Research Strategy Summary

The following flow was executed:

1. **Component JOB_DATA:** get_component_structure → get_page_fields (JOB_DATA1) → get_record_definition (JOB, EMPLMT_SRCH_ALL) → get_peoplecode (JOB)
2. **Component USERMAINT:** get_component_structure → get_page_fields (USER_GENERAL) → get_record_definition (PSOPRDEFN) → get_peoplecode (PSOPRDEFN)
3. **Application Engine GPES_TAX_10T:** get_application_engine_steps
4. **Schema discovery:** describe_table on PSPCMPROG, PSPCMTXT, PSAEAPPLDEFN, PSAESTEPDEFN, PSAESECTDEFN; query PSRECDEFN/PSDBFIELD patterns
5. **PeopleCode verification:** query PSPCMTXT for sample records; get_peoplecode for AAP_YEAR

---

## 2. Findings per Target

### 2.1 Component JOB_DATA

| Tool | Status | Notes |
|------|--------|------|
| get_component_structure | ✅ Success | Returns component, 12 pages, search record EMPLMT_SRCH_ALL |
| get_page_fields (JOB_DATA1) | ✅ Success | 89 fields, RECNAME/FIELDNAME bindings correct |
| get_record_definition (JOB) | ⚠️ Partial | Works structurally; **DESCRLONG returns LOB object refs** (`<oracledb.AsyncLOB object>`) instead of text |
| get_record_definition (EMPLMT_SRCH_ALL) | ⚠️ Partial | Same DESCRLONG LOB issue |
| get_peoplecode (JOB) | ✅ Success | Returns 0 programs—JOB has no record/field PeopleCode in this DB (expected) |

### 2.2 Component USERMAINT

| Tool | Status | Notes |
|------|--------|------|
| get_component_structure | ✅ Success | 7 pages, search record PSOPRDEFN_SRCH |
| get_page_fields (USER_GENERAL) | ✅ Success | 26 fields |
| get_record_definition (PSOPRDEFN) | ⚠️ Partial | Same DESCRLONG LOB issue |
| get_peoplecode (PSOPRDEFN) | ✅ Success | Returns 0 programs—PSOPRDEFN has no record/field PeopleCode in this DB (expected) |

### 2.3 Application Engine GPES_TAX_10T

| Tool | Status | Notes |
|------|--------|------|
| get_application_engine_steps | ✅ Success | Returns 2 steps (Step01, Step02) in MAIN section. Uses AE_SEQ_NUM, AE_ACTIVE_STATUS—version-safe columns. |

### 2.4 Schema Discovery

| Table | Column of interest | Finding |
|-------|--------------------|---------|
| **PSPCMTXT** | PCTEXT | CLOB; `DBMS_LOB.SUBSTR(PCTEXT, N, 1)` used correctly by get_peoplecode |
| **PSPCMPROG** | PROGTXT | LONG_CHARACTER (up to 28k); compiled/exported PeopleCode. PSPCMTXT = source, PSPCMPROG = compiled |
| **PSAEAPPLDEFN** | — | AE_APPLID, DESCR, AE_DISABLE_RESTART, OBJECTOWNERID present |
| **PSAESTEPDEFN** | AE_SEQ_NUM, AE_ACTIVE_STATUS | Both present; AE_STEP_NBR not used (version-safe) |
| **PSAESECTDEFN** | — | AE_SECTION, AE_APPLID, AE_SECTION_TYPE; not used by current AE tool |
| **PSRECFIELD + PSDBFIELD** | D.DESCRLONG | CLOB; selected directly → returns LOB handle, not text |

**PSPCMPROG vs PSPCMTXT:**
- **PSPCMTXT:** Source PeopleCode; column `PCTEXT` (CLOB). OBJECTID1=1 = Record/Field. Record name in OBJECTVALUE1 (no PS_ prefix).
- **PSPCMPROG:** Compiled PeopleCode; column `PROGTXT` (LONG_CHARACTER). Used for App Engine, Application Package, etc. get_peoplecode correctly uses PSPCMTXT.

---

## 3. Failures and Root Causes

### 3.1 LOB Handling in get_record_definition

**Symptom:** `DESCRLONG` in field output shows `<oracledb.AsyncLOB object at 0x...>` instead of description text.

**Root cause:** `tools/peopletools.py` line ~99 selects `D.DESCRLONG` directly. PSDBFIELD.DESCRLONG is CLOB. The `db.execute_query` layer returns row values as-is; oracledb returns CLOBs as LOB handles until read.

**Fix:** Use `DBMS_LOB.SUBSTR(D.DESCRLONG, 4000, 1)` in the fields SQL, or read LOBs in `db.py` before serialization.

### 3.2 LOB Handling in describe_table

**Symptom:** `description` field in describe_table output shows `<oracledb.AsyncLOB object>` for many fields.

**Root cause:** `tools/introspection.py` line 33 selects `DF.DESCRLONG AS DESCRIPTION`. Same CLOB handling issue.

**Fix:** Use `DBMS_LOB.SUBSTR(DF.DESCRLONG, 4000, 1) AS DESCRIPTION` in the SQL.

### 3.3 No Failures for Component/AE Tools

- get_component_structure, get_page_fields, get_application_engine_steps all succeeded. The codebase has been updated to use version-safe columns (SUBITEMNUM, AE_SEQ_NUM, AE_ACTIVE_STATUS) per reference.md.

---

## 4. Enhancement Recommendations

### 4.1 Fix DESCRLONG LOB Handling (High Priority)

**File:** `tools/peopletools.py`

**Change:** In `get_record_definition`, replace the fields query:

```sql
-- Current (line ~96):
D.DESCRLONG

-- Recommended:
DBMS_LOB.SUBSTR(D.DESCRLONG, 4000, 1) AS DESCRLONG
```

**File:** `tools/introspection.py`

**Change:** In `describe_table`:

```sql
-- Current (line ~33):
DF.DESCRLONG AS DESCRIPTION

-- Recommended:
DBMS_LOB.SUBSTR(DF.DESCRLONG, 4000, 1) AS DESCRIPTION
```

**Alternative:** Add LOB-to-string conversion in `db.py` for CLOB columns before building the result dict. This would fix all tools at once but requires detecting/outputting CLOB types.

---

### 4.2 Add get_component_pages (Simplified Component Tool)

**Purpose:** Lightweight component → pages mapping when full component structure isn’t needed. Uses only PSPNLGRPDEFN + PSPNLGROUP with version-safe columns.

**Proposed signature:**
```
get_component_pages(component_name: str) -> dict
```

**Returns:** `{ component_name, search_record, pages: [{ page_name, item_num, label }] }`

**SQL:**
```sql
SELECT C.PNLGRPNAME, C.SEARCHRECNAME 
FROM PSPNLGRPDEFN C WHERE C.PNLGRPNAME = :1;

SELECT P.PNLNAME, P.SUBITEMNUM AS ITEMNUM, P.ITEMLABEL 
FROM PSPNLGROUP P WHERE P.PNLGRPNAME = :1 ORDER BY P.SUBITEMNUM;
```

---

### 4.3 Add get_page_field_bindings (Simplified Page Fields)

**Purpose:** RECNAME/FIELDNAME/FIELDNUM only—avoids FIELDTYPE/LBLTEXT if those cause version issues elsewhere.

**Proposed signature:**
```
get_page_field_bindings(page_name: str) -> dict
```

**Returns:** `{ page_name, bindings: [{ recname, fieldname, fieldnum, occurslevel }] }`

**SQL:** Use RECNAME, FIELDNAME, FIELDNUM, OCCURSLEVEL from PSPNLFIELD only.

---

### 4.4 Extend get_application_engine_steps with Sections

**Purpose:** Include section metadata (PSAESECTDEFN) for AE structure.

**Change:** Join PSAESTEPDEFN with PSAESECTDEFN and return section-level attributes (AE_SECTION_TYPE, AE_PUBLIC_SW) when available.

---

### 4.5 Centralize LOB Handling in db.py (Optional)

**Purpose:** Avoid per-tool LOB handling.

**Approach:** Before building `dict(zip(columns, row))`, check each value: if it has `.read()` (LOB), call `value.read()` or `value.getvalue()` and replace. Handle `oracledb.AsyncLOB` specifically.

**Trade-off:** Slightly more logic in db layer; all tools benefit without per-query DBMS_LOB.

---

## 5. Summary

| Category | Status |
|----------|--------|
| Component structure | ✅ Working |
| Page fields | ✅ Working |
| Record definition | ⚠️ DESCRLONG LOB issue |
| PeopleCode | ✅ Working |
| Application Engine steps | ✅ Working |
| describe_table | ⚠️ DESCRLONG LOB issue |

**Immediate actions:**
1. ~~Fix DESCRLONG handling in get_record_definition and describe_table via DBMS_LOB.SUBSTR.~~ **Done** (2025-03-09)
2. ~~Add get_component_pages and get_page_field_bindings for leaner APIs.~~ **Done** (2025-03-09)
3. Optionally add centralized LOB handling in db.py for future CLOB columns.
