# PeopleSoft SQL Metadata Research

Research on PeopleSoft metadata tables for SQL objects and Application Engine actions, using the user-peoplesoft MCP server.

---

## 1. PSSQLDEFN — SQL Object Registry (Metadata Header)

### Schema

| Column        | Type      | Length | Description                                  |
|---------------|-----------|--------|----------------------------------------------|
| SQLID         | CHARACTER | 30     | Unique identifier for the SQL object         |
| SQLTYPE       | CHARACTER | 1      | Type of SQL (0, 1, 2, 6)                     |
| VERSION       | NUMBER    | 10     | PeopleTools version for caching              |
| LASTUPDOPRID  | CHARACTER | 30     | User who last updated                        |
| LASTUPDDTTM   | DATETIME  | 26     | Last update timestamp                        |
| ENABLEEFFDT   | CHARACTER | 1      | Y/N — effective date enabled                 |
| OBJECTOWNERID | CHARACTER | 4      | Object owner (HHR, HEP, etc.)                |

### Sample Rows

```
SQLID: HR_SRCH_DR  3ByDMgr Step01b S    SQLTYPE: 1  (AE SQL)
SQLID: AL_COST_UNIT_VW                   SQLTYPE: 2  (View)
SQLID: EPO_SYNDICATGetSubImStep06  S    SQLTYPE: 1  (AE SQL)
SQLID: EOCF_EVTSRC_VW                   SQLTYPE: 2  (View)
```

### Relationship to PSSQLTEXTDEFN

- **PSSQLDEFN** = registry/header: one row per SQL object (SQLID + SQLTYPE).
- **PSSQLTEXTDEFN** = actual SQL text: one or more rows per object (SQLID + SQLTYPE + EFFDT + SEQNUM).
- Join: `PSSQLDEFN.SQLID = PSSQLTEXTDEFN.SQLID AND PSSQLDEFN.SQLTYPE = PSSQLTEXTDEFN.SQLTYPE`.

---

## 2. PSSQLTEXTDEFN — SQL Text Storage (CLOB)

### Schema

| Column  | Type           | Length | Description                                          |
|---------|----------------|--------|------------------------------------------------------|
| SQLID   | CHARACTER      | 30     | Same as PSSQLDEFN                                    |
| SQLTYPE | CHARACTER      | 1      | Same as PSSQLDEFN                                    |
| MARKET  | CHARACTER      | 3      | GBL, etc.                                            |
| DBTYPE  | CHARACTER      | 1      | Platform: 0=SQLBase, 1=DB2, 2=Oracle, 7=Microsoft    |
| EFFDT   | DATE           | 10     | Effective date (for effective-dated SQL)             |
| SEQNUM  | NUMBER         | 3      | Segment number — long SQL split across rows          |
| SQLTEXT | LONG_CHARACTER | CLOB   | The actual SQL text                                  |

### SQLTYPE Values (observed)

| Value | Meaning              | Usage                                             |
|-------|----------------------|---------------------------------------------------|
| 0     | Standard SQL         | PeopleCode SQL.SQLID, generic embedded SQL        |
| 1     | Application Engine   | AE SQL actions (Select, Update, Insert, Delete)   |
| 2     | SQL View             | Record SQL View definitions                       |
| 6     | PS Query / XSLT      | Query definitions, AE XSLT/XML                    |

### Sample Queries

**Distinct SQLTYPE:**
```sql
SELECT DISTINCT SQLTYPE FROM PSSQLTEXTDEFN ORDER BY SQLTYPE;
-- Returns: 0, 1, 2, 6
```

**SQL text (CLOB) — use DBMS_LOB.SUBSTR for Oracle:**
```sql
SELECT SQLID, SQLTYPE, DBMS_LOB.SUBSTR(SQLTEXT, 500, 1) AS SQLTEXT_SAMPLE
FROM PSSQLTEXTDEFN
WHERE SQLID = 'GPES_TAX_10TMAIN    Step01  S' AND SQLTYPE = '1';
```

### How Objects Are Referenced

- **Views:** Record with RECTYPE=1 (SQL View) uses SQLID from PSSQLTEXTDEFN (SQLTYPE=2).
- **PeopleCode:** `SQL.SQLID("MY_SQL_ID")` references SQLTYPE=0.
- **Application Engine:** PSAESTMTDEFN.SQLID points to PSSQLTEXTDEFN (SQLTYPE=1) for SQL steps.

---

## 3. SQL-Related Tables (PSRECDEFN)

Records whose names contain "SQL" or related AE/SQL patterns:

### Core PeopleTools SQL Tables

| Record          | Description                     |
|-----------------|---------------------------------|
| **PSSQLDEFN**   | SQL Object Defn (header)        |
| **PSSQLTEXTDEFN** | SQL Object Text (CLOB)        |
| PSSQLDESCR      | SQL Object Description          |
| PSSQLHASH       | SQL hash (change detection)     |
| PSSQLLANG       | SQL Object Defn (related lang)  |
| PSSQLDEL        | SQL Object deletion tracking    |
| **PSAESTMTDEFN**| AE Statement Defn               |
| PSAESQLTIMINGS  | AE SQL timing metrics           |
| PSADSSQLREF     | Analytics SQL references        |

### Application Engine

| Record      | Description                |
|-------------|----------------------------|
| PSAESTMTDEFN | AE Statement Defn          |
| AE_STMT_TBL  | AE Statement Table         |
| AE_STMT_B_TBL| AE Statement Chunk Table   |
| GP_AESQL_VW  | AE SQL Statements view     |

### Other SQL-Related Records

- **TL_SQL_OBJECT**, TL_SQL_TABLES, TL_SQL_WHERE, etc. — Time & Labor SQL objects
- **GPFR_AF_SQLENTY**, GPFR_AF_SQL_FLD — GP (Global Payroll) SQL entities
- **MC_DEFN_SQL**, MC_TYPE_SQL — Mass Change SQL
- **HR_SCRTY_SQLDFN**, HR_SCRTY_SQLTXT — Security SQL objects

---

## 4. PSAESTMTDEFN — AE Statement Definition

### Schema

| Column            | Type      | Length | Description                                      |
|-------------------|-----------|--------|--------------------------------------------------|
| AE_APPLID         | CHARACTER | 12     | AE program name                                  |
| AE_SECTION        | CHARACTER | 8      | Section name (e.g. MAIN)                         |
| MARKET            | CHARACTER | 3      | GBL, etc.                                        |
| DBTYPE            | CHARACTER | 1      | Database platform                                |
| EFFDT             | DATE      | 10     | Effective date                                   |
| AE_STEP           | CHARACTER | 8      | Step name                                        |
| AE_STMT_TYPE      | CHARACTER | 1      | Statement type (S, P, D, C, H, N, W, M, X)       |
| AE_REUSE_STMT     | CHARACTER | 1      | N=Normal, S=Save Stmt, Y=Use Binds               |
| AE_DO_SELECT_TYPE | CHARACTER | 1      | F=Select and Fetch, R=Re-Select (for Do Select)  |
| SQLID             | CHARACTER | 30     | Links to PSSQLTEXTDEFN (when AE_STMT_TYPE='S')   |
| DESCR             | CHARACTER | 30     | Short description                                |
| DESCRLONG         | CLOB      | —      | Long description                                 |

### AE_STMT_TYPE Values

| Code | Meaning                 | SQLID Used?      |
|------|-------------------------|------------------|
| S    | Select                  | Yes              |
| U    | Update/Insert/Delete    | Yes              |
| D    | Do Select               | Yes (Do Select SQL) |
| P    | PeopleCode              | No (blank)       |
| C    | Comments                | No               |
| H    | Do When                 | No               |
| N    | Do Until                | No               |
| W    | Do While                | No               |
| M    | (Message)               | —                |
| X    | (Other)                 | —                |

### Sample: GPES_TAX_10T

**Steps (PSAESTEPDEFN):**
| AE_SECTION | AE_STEP | AE_SEQ_NUM | DESCR        |
|------------|---------|------------|--------------|
| MAIN       | Step01  | 1          | initialization |
| MAIN       | Step02  | 2          | Delete        |

**Statements (PSAESTMTDEFN):**
| AE_STEP | AE_STMT_TYPE | SQLID                         | DESCR              |
|---------|--------------|-------------------------------|--------------------|
| Step01  | S (Select)   | GPES_TAX_10TMAIN    Step01  S | SQL description    |
| Step02  | P (PeopleCode)| (blank)                      | PeopleCode description |

**SQL text for Step01 (from PSSQLTEXTDEFN):**
```sql
%SelectInit(GPES_TAX190_AET.OPRID, ...) SELECT OPRID, RUN_CNTL_ID, ... 
FROM PS_GPES_RC_TAX WHERE OPRID = %Bind(OPRID) AND RUN_CNTL_ID = %Bind(RUN_CNTL_ID)
```

- **SQL steps (S, U, D):** SQLID is populated → join to PSSQLTEXTDEFN for SQL text.
- **PeopleCode steps (P):** SQLID is blank → code in PSPCMTXT via PSPCMPROG (OBJECTVALUE1 = AE_APPLID, etc.).

---

## 5. Relationships and Join Path

### Architecture Diagram (Text)

```
PSAEAPPLDEFN (AE Program)
    |
    v
PSAESTEPDEFN (AE Step: Section, Step, Seq, Do When, etc.)
    |
    +--[1:1 or 0..1]--> PSAESTMTDEFN (AE Statement: Type, SQLID, Descr)
    |                       |
    |                       +--[When AE_STMT_TYPE in (S,U,D)]--> SQLID
    |                                                               |
    |                                                               v
    |                                                       PSSQLDEFN (SQL header)
    |                                                               |
    |                                                               +--[1:N]--> PSSQLTEXTDEFN (SQL text, CLOB)
    |
    +--[When AE_STMT_TYPE = P]--> PeopleCode in PSPCMTXT (no SQLID)
```

### Join Path: AE Step → SQL Text

```sql
-- Full trace: AE program → steps → statements → SQL text
SELECT 
    S.AE_APPLID,
    S.AE_SECTION,
    S.AE_STEP,
    S.AE_SEQ_NUM,
    ST.AE_STMT_TYPE,
    ST.SQLID,
    DBMS_LOB.SUBSTR(T.SQLTEXT, 500, 1) AS SQLTEXT_SAMPLE
FROM PSAESTEPDEFN S
JOIN PSAESTMTDEFN ST 
  ON S.AE_APPLID = ST.AE_APPLID 
  AND S.AE_SECTION = ST.AE_SECTION 
  AND S.AE_STEP = ST.AE_STEP
  AND S.EFFDT = ST.EFFDT
  AND NVL(S.MARKET,' ') = NVL(ST.MARKET,' ')
LEFT JOIN PSSQLTEXTDEFN T 
  ON ST.SQLID = T.SQLID 
  AND ST.SQLTYPE = T.SQLTYPE
  AND T.EFFDT = (SELECT MAX(EFFDT) FROM PSSQLTEXTDEFN 
                 WHERE SQLID = T.SQLID AND SQLTYPE = T.SQLTYPE 
                 AND (T.SQLTYPE != '2' OR EFFDT <= SYSDATE))
WHERE S.AE_APPLID = 'GPES_TAX_10T'
ORDER BY S.AE_SECTION, S.AE_SEQ_NUM;
```

### Simplified Join (current row for effective-dated SQL)

```sql
-- Step → Statement
FROM PSAESTEPDEFN S
JOIN PSAESTMTDEFN ST 
  ON S.AE_APPLID = ST.AE_APPLID 
  AND S.AE_SECTION = ST.AE_SECTION 
  AND S.AE_STEP = ST.AE_STEP

-- Statement → SQL text (when SQLID populated)
LEFT JOIN PSSQLTEXTDEFN T 
  ON ST.SQLID = RTRIM(T.SQLID) 
  AND T.SQLTYPE = '1'  -- AE SQL
  AND T.MARKET = 'GBL'
  AND T.EFFDT = (SELECT MAX(EFFDT) FROM PSSQLTEXTDEFN 
                 WHERE SQLID = T.SQLID AND SQLTYPE = T.SQLTYPE AND MARKET = T.MARKET)
```

**Note:** PSAESTMTDEFN does not store SQLTYPE; it uses SQLID only. When looking up AE SQL in PSSQLTEXTDEFN, use SQLTYPE='1'. The SQLID format for AE is typically: `{AE_APPLID}{AE_SECTION}{AE_STEP} {S|U|D}` (e.g. `GPES_TAX_10TMAIN    Step01  S`).

---

## 6. Recommendations for New MCP Tools

### 6.1 `get_ae_statement_details`

**Purpose:** Return AE statements with SQL text for a given program.

**Parameters:** `ae_applid`, optional `section`, `step`.

**Returns:**
- AE steps with their statement types
- For SQL steps: full SQL text from PSSQLTEXTDEFN
- For PeopleCode steps: reference to get_peoplecode (OBJECTVALUE1=AE_APPLID, etc.)

**Tables:** PSAESTEPDEFN, PSAESTMTDEFN, PSSQLTEXTDEFN.

### 6.2 `get_sql_object_by_id`

**Purpose:** Alias or enhanced version of existing `get_sql_definition` that also returns PSSQLDEFN metadata (ENABLEEFFDT, OBJECTOWNERID, LASTUPDDTTM).

**Enhancement:** Join PSSQLDEFN + PSSQLTEXTDEFN to provide both header and text in one call.

### 6.3 `search_ae_sql_by_table`

**Purpose:** Find AE programs/steps that reference a given table in their SQL.

**Approach:** Use `search_sql_definitions(table_name)` then filter results where SQLTYPE='1', then join to PSAESTMTDEFN on SQLID to get AE_APPLID, AE_SECTION, AE_STEP.

**Tables:** PSSQLTEXTDEFN, PSAESTMTDEFN.

### 6.4 `get_sql_references`

**Purpose:** Given an SQLID, list all references (AE steps, PeopleCode, views).

**Approach:**
- AE: `SELECT * FROM PSAESTMTDEFN WHERE SQLID = :1`
- Views: `SELECT RECNAME FROM PSRECDEFN R JOIN PSRECFIELD F ON R.RECNAME=F.RECNAME` where view definition uses SQLID (view text in PSSQLTEXTDEFN)
- PeopleCode: search PSPCMTXT for `SQL.SQLID("...")` or similar

---

## Summary

| Table         | Role                          | Key Columns                              |
|---------------|-------------------------------|------------------------------------------|
| PSSQLDEFN     | SQL object registry (header)  | SQLID, SQLTYPE, ENABLEEFFDT              |
| PSSQLTEXTDEFN | SQL text storage (CLOB)       | SQLID, SQLTYPE, SEQNUM, SQLTEXT          |
| PSAESTEPDEFN  | AE step definition            | AE_APPLID, AE_SECTION, AE_STEP, AE_SEQ_NUM |
| PSAESTMTDEFN  | AE statement (SQL or PeopleCode) | AE_APPLID, AE_SECTION, AE_STEP, AE_STMT_TYPE, SQLID |

**Join path:** `PSAESTEPDEFN` → `PSAESTMTDEFN` (same APPLID/SECTION/STEP) → `PSSQLTEXTDEFN` (when SQLID populated and AE_STMT_TYPE in S,U,D).
