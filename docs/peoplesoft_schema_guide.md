# PeopleSoft Schema Guide by Module

Quick reference for finding tables by functional area. Use the MCP tools (`describe_table`, `get_record_definition`) for detailed field information.

---

## Core HR / Workforce Administration

### Employee Data
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_PERSONAL_DATA | Employee personal info (name, DOB, etc.) | EMPLID |
| PS_PERSON | Person entity (minimal, links to other tables) | EMPLID |
| PS_NAMES | Name history (with name types) | EMPLID, NAME_TYPE, EFFDT |
| PS_ADDRESSES | Address history by type | EMPLID, ADDRESS_TYPE, EFFDT |
| PS_PERSONAL_PHONE | Phone numbers | EMPLID, PHONE_TYPE |
| PS_EMAIL_ADDRESSES | Email addresses | EMPLID, E_ADDR_TYPE |
| PS_PERS_NID | National IDs (SSN, etc.) | EMPLID, COUNTRY, NATIONAL_ID_TYPE |
| PS_DIVERSITY | Diversity/EEO data | EMPLID |

### Employment & Job
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_JOB | Job history (position, dept, salary, status) | EMPLID, EMPL_RCD, EFFDT, EFFSEQ |
| PS_EMPLOYMENT | Employment record header (hire dates) | EMPLID, EMPL_RCD |
| PS_PER_ORG_ASGN | Person-org assignment | EMPLID, EMPL_RCD, EFFDT |
| PS_COMPENSATION | Compensation components | EMPLID, EMPL_RCD, EFFDT, COMP_RATECD |
| PS_CONTRACT | Contract details | EMPLID, EMPL_RCD, CONTRACT_NUM, EFFDT |

### Organization
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_COMPANY_TBL | Company/legal entity setup | COMPANY, EFFDT |
| PS_DEPT_TBL | Department definitions | SETID, DEPTID, EFFDT |
| PS_LOCATION_TBL | Work locations | SETID, LOCATION, EFFDT |
| PS_JOBCODE_TBL | Job code definitions | SETID, JOBCODE, EFFDT |
| PS_POSITION_DATA | Position management | POSITION_NBR, EFFDT |
| PS_SAL_GRADE_TBL | Salary grades | SETID, SAL_ADMIN_PLAN, GRADE, EFFDT |
| PS_PAYGROUP_TBL | Pay group setup | COMPANY, PAYGROUP, EFFDT |

### Dependents & Beneficiaries
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_DEPENDENT_BENEF | Dependents and beneficiaries | EMPLID, DEPENDENT_BENEF |
| PS_DEP_BENEF_NID | Dependent national IDs | EMPLID, DEPENDENT_BENEF, COUNTRY |
| PS_HEALTH_DEPENDNT | Health coverage dependents | EMPLID, EMPL_RCD, PLAN_TYPE, DEPENDENT_BENEF |

---

## Global Payroll (GP)

### Calendar & Processing
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_GP_CAL_RUN | Calendar run (payroll batch) | CAL_RUN_ID |
| PS_GP_CAL_RUN_DTL | Calendars in a run | CAL_RUN_ID, CAL_ID |
| PS_GP_CALENDAR | Calendar definitions | CAL_ID |
| PS_GP_PYE_PRC_STAT | Payee processing status | EMPLID, CAL_RUN_ID, EMPL_RCD |
| PS_GP_PYE_SEG_STAT | Payee segment status | EMPLID, CAL_RUN_ID, EMPL_RCD, GP_PAYGROUP |

### Results
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_GP_RSLT_ERN_DED | Earnings & deductions results | EMPLID, CAL_RUN_ID, EMPL_RCD, PIN_NUM |
| PS_GP_RSLT_ACUM | Accumulator results | EMPLID, CAL_RUN_ID, EMPL_RCD, PIN_NUM |
| PS_GP_RSLT_PIN | Supporting element results | EMPLID, CAL_RUN_ID, EMPL_RCD, PIN_NUM |
| PS_GP_RSLT_ABS | Absence results | EMPLID, CAL_RUN_ID, EMPL_RCD |
| PS_GP_RSLT_PI_DATA | Positive input results | EMPLID, CAL_RUN_ID, EMPL_RCD |

### Payments & Banking
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_GP_PAYMENT | Payment results | EMPLID, CAL_RUN_ID, EMPL_RCD, PMT_KEY1 |
| PS_GP_NET_DIST | Net pay distribution | EMPLID, CAL_RUN_ID, EMPL_RCD |
| PS_GP_NET_DIST_DTL | Bank account split | EMPLID, EMPL_RCD, EFFDT, ACCOUNT_ID |
| PS_PYE_BANKACCT | Payee bank accounts | EMPLID, ACCOUNT_ID |

### Configuration
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_GP_PIN | Element (PIN) definitions | PIN_NUM |
| PS_GP_ELEM_DFN | Element type definitions | PIN_NUM |
| PS_GP_PAYGROUP | Pay group setup | GP_PAYGROUP |
| PS_GP_PYENT | Pay entity setup | PAY_ENTITY |
| PS_GP_RUN_TYPE | Run type definitions | RUN_TYPE |

### Triggers & Retro
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_GP_RTO_TRGR | Retro triggers | EMPLID, EMPL_RCD, TRGR_EVENT_ID |
| PS_GP_SEG_TRGR | Segmentation triggers | EMPLID, EMPL_RCD, TRGR_EVENT_ID |
| PS_GP_MESSAGES | Payroll messages/errors | EMPLID, CAL_RUN_ID, MSG_SEQ |

---

## Absence Management

### Absence Data
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_GP_ABS_EVENT | Absence events | EMPLID, EMPL_RCD, BGN_DT, PIN_TAKE_NUM |
| PS_GP_ABS_ENTL | Absence entitlements | EMPLID, EMPL_RCD, PIN_NUM |
| PS_GP_ABS_OVRD | Absence overrides | EMPLID, EMPL_RCD, PIN_NUM |
| PS_ABSENCE_HIST | Absence history (UK/legacy) | EMPLID, EMPL_RCD, BEGIN_DT |

### Vacation (ABSV module)
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_ABSV_REQUEST | Vacation requests | EMPLID, EMPL_RCD, BEGIN_DT |
| PS_ABSV_ACCRUAL | Vacation accrual balances | EMPLID, EMPL_RCD, PLAN_TYPE, ABSV_ACCRUAL_DT |
| PS_ABSV_PERIOD | Accrual period setup | COMPANY, PLAN_TYPE, BENEFIT_PLAN |
| PS_ABSV_PLAN_TBL | Vacation plan configuration | PLAN_TYPE, BENEFIT_PLAN |

---

## Benefits Administration

### Enrollment
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_BEN_PROG_PARTIC | Benefit program participation | EMPLID, EMPL_RCD, BENEFIT_PROGRAM, EFFDT |
| PS_HEALTH_BENEFIT | Health plan enrollment | EMPLID, EMPL_RCD, PLAN_TYPE, EFFDT |
| PS_LIFE_ADD_BEN | Life/AD&D enrollment | EMPLID, EMPL_RCD, PLAN_TYPE, EFFDT |
| PS_SAVINGS_PLAN | Savings/401k enrollment | EMPLID, EMPL_RCD, PLAN_TYPE, EFFDT |
| PS_FSA_BENEFIT | FSA enrollment | EMPLID, EMPL_RCD, PLAN_TYPE, EFFDT |

### Configuration
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_BENEF_PLAN_TBL | Benefit plan definitions | SETID, BENEFIT_PLAN, PLAN_TYPE, EFFDT |
| PS_BENEFIT_PROGRAM | Benefit program setup | BENEFIT_PROGRAM, EFFDT |
| PS_BEN_DEFN_COST | Benefit costs/rates | (various keys) |

---

## ePerformance

### Appraisals
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_EP_APPR | Performance documents | EP_APPR_ID |
| PS_EP_APPR_ROLE | Roles in appraisal | EP_APPR_ID, EP_ROLE |
| PS_EP_APPR_SECTION | Appraisal sections | EP_APPR_ID, EP_SECTION_ID |
| PS_EP_APPR_ITEM | Evaluation items | EP_APPR_ID, EP_SECTION_ID, EP_ITEM_ID |
| PS_EP_APPR_SUBITEM | Item sub-components | EP_APPR_ID, EP_SECTION_ID, EP_ITEM_ID |
| PS_EP_APPR_COMMENT | Comments on items | EP_APPR_ID, EP_SECTION_ID |

### Configuration
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_EP_TMPL_DEFN | Template definitions | EP_TEMPLATE_ID |
| PS_EP_RATING_MDL | Rating models | RATING_MODEL |
| PS_EP_REVIEW_TYPE | Review type setup | EP_REVIEW_TYPE |

---

## PeopleTools System Tables

### Record/Field Metadata
| Table | Description | Key Fields |
|-------|-------------|------------|
| PSRECDEFN | Record definitions | RECNAME |
| PSRECFIELD | Fields in records | RECNAME, FIELDNAME |
| PSDBFIELD | Field properties | FIELDNAME |
| PSKEYDEFN | Index/key definitions | RECNAME, INDEXID, FIELDNAME |
| PSINDEXDEFN | Index properties | RECNAME, INDEXID |

### PeopleCode
| Table | Description | Key Fields |
|-------|-------------|------------|
| PSPCMPROG | PeopleCode metadata | OBJECTVALUE1, OBJECTVALUE2, OBJECTVALUE3 |
| PSPCMTXT | PeopleCode source (CLOB) | OBJECTVALUE1, OBJECTVALUE2, OBJECTVALUE3 |
| PSPCMNAME | PeopleCode references | (various) |

### Pages & Components
| Table | Description | Key Fields |
|-------|-------------|------------|
| PSPNLDEFN | Page definitions | PNLNAME |
| PSPNLFIELD | Fields on pages | PNLNAME, FIELDNUM |
| PSPNLGRPDEFN | Component definitions | PNLGRPNAME, MARKET |
| PSPNLGROUP | Pages in components | PNLGRPNAME, PNLNAME |
| PSMENUDEFN | Menu definitions | MENUNAME |
| PSMENUITEM | Menu items | MENUNAME, BARNAME, ITEMNAME |

### Security
| Table | Description | Key Fields |
|-------|-------------|------------|
| PSOPRDEFN | User definitions | OPRID |
| PSROLEDEFN | Role definitions | ROLENAME |
| PSROLEUSER | User-role mapping | ROLEUSER, ROLENAME |
| PSROLECLASS | Role-permission mapping | ROLENAME, CLASSID |
| PSCLASSDEFN | Permission list definitions | CLASSID |
| PSAUTHITEM | Component authorization | CLASSID, MENUNAME, PNLGRPNAME |

### Translate Values
| Table | Description | Key Fields |
|-------|-------------|------------|
| PSXLATDEFN | Translate field definitions | FIELDNAME |
| PSXLATITEM | Translate values | FIELDNAME, FIELDVALUE, EFFDT |
| PSXLATITEMLANG | Translated descriptions | FIELDNAME, FIELDVALUE, LANGUAGE_CD |

### Application Engine
| Table | Description | Key Fields |
|-------|-------------|------------|
| PSAEAPPLDEFN | AE program definitions | AE_APPLID |
| PSAESECTDEFN | AE section definitions | AE_APPLID, AE_SECTION |
| PSAESTEPDEFN | AE step definitions | AE_APPLID, AE_SECTION, AE_STEP |
| PSAESQLDEFN | AE SQL definitions | AE_APPLID, AE_SECTION, AE_STEP |
| PSAESTEPMSGDEFN | AE PeopleCode | AE_APPLID, AE_SECTION, AE_STEP |

### Process Scheduler
| Table | Description | Key Fields |
|-------|-------------|------------|
| PS_PRCSDEFN | Process definitions | PRCSTYPE, PRCSNAME |
| PSPRCSRQST | Process requests | PRCSINSTANCE |
| PS_PRCSRUNCNTL | Run control records | OPRID, RUN_CNTL_ID |
| PSPRCSPARMS | Process parameters | PRCSINSTANCE |

### Integration Broker
| Table | Description | Key Fields |
|-------|-------------|------------|
| PSOPERATION | Service operations | IB_OPERATIONNAME |
| PSMSGDEFN | Message definitions | MSGNAME, VERSION |
| PSMSGPARTDEFN | Message parts | MSGNAME, PARTNAME |
| PSMSGROUT | Message routing | IB_OPERATIONNAME |
| PSNODE | Node definitions | MSGNODENAME |

### Query Manager
| Table | Description | Key Fields |
|-------|-------------|------------|
| PSQRYDEFN | Query definitions | QRYNAME |
| PSQRYRECORD | Query records | QRYNAME, RECNAME |
| PSQRYFIELD | Query fields | QRYNAME, FIELDNUM |
| PSQRYCRITERIA | Query criteria | QRYNAME, CRITERIANUM |
| PSQRYACCLST | Query access | QRYNAME, CLASSID |

---

## Common Relationships

```
Employee Core:
  PERSONAL_DATA (1) ←→ (N) JOB ←→ (1) EMPLOYMENT

Job Lookups:
  JOB.COMPANY    → COMPANY_TBL.COMPANY
  JOB.DEPTID     → DEPT_TBL.DEPTID (via SETID)
  JOB.LOCATION   → LOCATION_TBL.LOCATION (via SETID)
  JOB.JOBCODE    → JOBCODE_TBL.JOBCODE (via SETID)

GP Processing:
  GP_CAL_RUN (1) → (N) GP_PYE_PRC_STAT → (N) GP_RSLT_ERN_DED
```

---

## Tips

1. **Always check SETID** - Most setup tables use SETID for data sharing
2. **Effective dating** - Most tables have EFFDT; use MAX(EFFDT) <= SYSDATE
3. **EFFSEQ for same-day changes** - JOB and similar tables have EFFSEQ
4. **RECNAME vs Table Name** - RECNAME is 'JOB', table name is 'PS_JOB'
5. **Use MCP tools** - `describe_table("JOB")` gives you live field info
