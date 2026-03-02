# PeopleSoft Data Model Concepts

This guide explains fundamental PeopleSoft concepts essential for working with the database.

## Effective Dating

PeopleSoft uses **effective dating** to maintain history and future-dated changes. Instead of updating records, new rows are inserted with different effective dates.

### Key Fields

- **EFFDT** (Effective Date): When the row becomes active
- **EFFSEQ** (Effective Sequence): Breaks ties when multiple changes occur on the same date

### Getting Current Data

To get the current (active) row for an effective-dated table:

```sql
SELECT * FROM PS_JOB J
WHERE J.EMPLID = 'EMP001'
AND J.EFFDT = (
    SELECT MAX(J1.EFFDT) 
    FROM PS_JOB J1 
    WHERE J.EMPLID = J1.EMPLID 
    AND J.EMPL_RCD = J1.EMPL_RCD 
    AND J1.EFFDT <= SYSDATE  -- As of today
)
AND J.EFFSEQ = (
    SELECT MAX(J2.EFFSEQ) 
    FROM PS_JOB J2 
    WHERE J.EMPLID = J2.EMPLID 
    AND J.EMPL_RCD = J2.EMPL_RCD 
    AND J.EFFDT = J2.EFFDT
)
```

### Common Effective-Dated Tables

| Table | Key Fields |
|-------|-----------|
| PS_JOB | EMPLID, EMPL_RCD, EFFDT, EFFSEQ |
| PS_DEPT_TBL | SETID, DEPTID, EFFDT |
| PS_JOBCODE_TBL | SETID, JOBCODE, EFFDT |
| PS_LOCATION_TBL | SETID, LOCATION, EFFDT |
| PS_COMPANY_TBL | COMPANY, EFFDT |

---

## EMPLID and EMPL_RCD

### EMPLID (Employee ID)

The unique identifier for a person in PeopleSoft. One person = one EMPLID throughout their entire relationship with the organization.

### EMPL_RCD (Employment Record Number)

A person can have multiple concurrent jobs (employment records):

- **EMPL_RCD = 0**: Primary job
- **EMPL_RCD = 1, 2, ...**: Additional concurrent jobs

Example: A professor (EMPL_RCD=0) who also teaches evening classes (EMPL_RCD=1).

### Getting the Primary Job

```sql
SELECT * FROM PS_JOB 
WHERE EMPLID = 'EMP001' 
AND EMPL_RCD = 0
AND EFFDT = (SELECT MAX(EFFDT) FROM PS_JOB WHERE EMPLID = 'EMP001' AND EMPL_RCD = 0 AND EFFDT <= SYSDATE)
AND EFFSEQ = (SELECT MAX(EFFSEQ) FROM PS_JOB WHERE EMPLID = 'EMP001' AND EMPL_RCD = 0 AND EFFDT = PS_JOB.EFFDT)
```

### Getting All Jobs for an Employee

```sql
SELECT * FROM PS_JOB J
WHERE J.EMPLID = 'EMP001'
AND J.EFFDT = (SELECT MAX(J1.EFFDT) FROM PS_JOB J1 WHERE J.EMPLID = J1.EMPLID AND J.EMPL_RCD = J1.EMPL_RCD AND J1.EFFDT <= SYSDATE)
AND J.EFFSEQ = (SELECT MAX(J2.EFFSEQ) FROM PS_JOB J2 WHERE J.EMPLID = J2.EMPLID AND J.EMPL_RCD = J2.EMPL_RCD AND J.EFFDT = J2.EFFDT)
```

---

## SetID and TableSets

### What is a SetID?

SetID allows organizations to share configuration data across business units. Instead of duplicating department codes for each business unit, they share a SetID.

### Common SetID-based Tables

- PS_DEPT_TBL (Departments)
- PS_JOBCODE_TBL (Job Codes)
- PS_LOCATION_TBL (Locations)
- PS_SAL_GRADE_TBL (Salary Grades)

### How to Join SetID Tables

When joining to SetID-based tables from PS_JOB, use the corresponding SETID field:

```sql
SELECT J.*, D.DESCR AS DEPT_NAME
FROM PS_JOB J
JOIN PS_DEPT_TBL D ON J.DEPTID = D.DEPTID 
    AND J.SETID_DEPT = D.SETID  -- Use the SetID from PS_JOB
    AND D.EFFDT = (SELECT MAX(D1.EFFDT) FROM PS_DEPT_TBL D1 
                   WHERE D.SETID = D1.SETID AND D.DEPTID = D1.DEPTID 
                   AND D1.EFFDT <= SYSDATE)
```

### SetID Fields in PS_JOB

| SetID Field | Relates To |
|-------------|-----------|
| SETID_DEPT | PS_DEPT_TBL |
| SETID_JOBCODE | PS_JOBCODE_TBL |
| SETID_LOCATION | PS_LOCATION_TBL |
| SETID_SALARY | PS_SAL_GRADE_TBL |

---

## Translate Values (XLAT)

Many PeopleSoft fields use short codes instead of full values. These are stored in translate (XLAT) tables.

### Where Translate Values Are Stored

- **PSXLATITEM**: Current translate values with effective dating
- **PSXLATDEFN**: Field definitions that use translate values

### Common Translate Fields

| Field | Values |
|-------|--------|
| SEX | M=Male, F=Female, U=Unknown |
| HR_STATUS | A=Active, I=Inactive, D=Deceased |
| EMPL_STATUS | A=Active, T=Terminated, L=Leave, P=Leave with Pay, S=Suspended, R=Retired, D=Deceased |
| REG_TEMP | R=Regular, T=Temporary |
| FULL_PART_TIME | F=Full-Time, P=Part-Time |
| MAR_STATUS | S=Single, M=Married, D=Divorced, W=Widowed, U=Unknown |
| RELATIONSHIP | SP=Spouse, C=Child, P=Parent, DP=Domestic Partner |

### Looking Up Translate Values

```sql
SELECT FIELDVALUE, XLATLONGNAME, XLATSHORTNAME
FROM PSXLATITEM
WHERE FIELDNAME = 'HR_STATUS'
AND EFFDT = (SELECT MAX(EFFDT) FROM PSXLATITEM 
             WHERE FIELDNAME = 'HR_STATUS' AND EFFDT <= SYSDATE)
ORDER BY FIELDVALUE
```

### Joining Translate Values in Queries

```sql
SELECT P.EMPLID, P.NAME, P.SEX, X.XLATLONGNAME AS SEX_DESC
FROM PS_PERSONAL_DATA P
LEFT JOIN PSXLATITEM X ON X.FIELDNAME = 'SEX' AND X.FIELDVALUE = P.SEX
    AND X.EFFDT = (SELECT MAX(X1.EFFDT) FROM PSXLATITEM X1 
                   WHERE X1.FIELDNAME = 'SEX' AND X1.FIELDVALUE = P.SEX 
                   AND X1.EFFDT <= SYSDATE)
```

---

## Action and Action Reason Codes

Actions track what happened to an employee's job record. Every PS_JOB row has an ACTION.

### Common Actions

| Action | Description |
|--------|-------------|
| HIR | Hire |
| REH | Rehire |
| TER | Termination |
| PRO | Promotion |
| DEM | Demotion |
| XFR | Transfer |
| PAY | Pay Rate Change |
| LOA | Leave of Absence |
| RFL | Return from Leave |
| POS | Position Change |
| DTA | Data Change |

### Action Reasons

Actions can have specific reasons. For example, TER (Termination) might have reasons:
- RES = Resignation
- RET = Retirement
- DIS = Discharge
- LAY = Layoff
- DEC = Deceased

### Querying Actions

```sql
SELECT J.EMPLID, J.EFFDT, J.ACTION, A.DESCR AS ACTION_DESC,
       J.ACTION_REASON, AR.DESCR AS REASON_DESC
FROM PS_JOB J
LEFT JOIN PS_ACTION_TBL A ON J.ACTION = A.ACTION
    AND A.EFFDT = (SELECT MAX(A1.EFFDT) FROM PS_ACTION_TBL A1 
                   WHERE A.ACTION = A1.ACTION AND A1.EFFDT <= SYSDATE)
LEFT JOIN PS_ACTN_REASON_TBL AR ON J.ACTION = AR.ACTION AND J.ACTION_REASON = AR.ACTION_REASON
    AND AR.EFFDT = (SELECT MAX(AR1.EFFDT) FROM PS_ACTN_REASON_TBL AR1 
                   WHERE AR.ACTION = AR1.ACTION AND AR.ACTION_REASON = AR1.ACTION_REASON 
                   AND AR1.EFFDT <= SYSDATE)
WHERE J.EMPLID = 'EMP001'
ORDER BY J.EFFDT DESC
```

---

## Key System Tables

### Metadata Tables (PeopleTools)

| Table | Purpose |
|-------|---------|
| PSRECDEFN | Record/table definitions |
| PSRECFIELD | Fields in each record |
| PSDBFIELD | Field properties (type, length) |
| PSKEYDEFN | Index key definitions |
| PSXLATITEM | Translate values |
| PSXLATDEFN | Translate field definitions |

### Core HR Tables

| Table | Purpose |
|-------|---------|
| PS_PERSONAL_DATA | Employee personal info (one row per person) |
| PS_JOB | Job history (effective-dated, multiple rows) |
| PS_EMPLOYMENT | Employment summary (hire dates, termination dates) |
| PS_COMPENSATION | Compensation components |
| PS_DEPENDENT_BENEF | Dependents and beneficiaries |

### Configuration Tables

| Table | Purpose |
|-------|---------|
| PS_COMPANY_TBL | Company definitions |
| PS_DEPT_TBL | Department definitions |
| PS_LOCATION_TBL | Location definitions |
| PS_JOBCODE_TBL | Job code definitions |
| PS_ACTION_TBL | Action definitions |
| PS_ACTN_REASON_TBL | Action reason definitions |

---

## Tips for Writing Queries

1. **Always use effective dating** - Filter by EFFDT and EFFSEQ for current data
2. **Check for EMPL_RCD** - Decide if you want all jobs or just primary (0)
3. **Use SetID correctly** - Match the right SetID field when joining
4. **Decode translate values** - Join to PSXLATITEM for meaningful descriptions
5. **Check table indexes** - Query PSKEYDEFN to understand how to filter efficiently
6. **Test with FETCH FIRST** - Add `FETCH FIRST 10 ROWS ONLY` during development
