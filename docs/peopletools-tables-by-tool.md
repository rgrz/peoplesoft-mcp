# PeopleTools Tables by Tool

This document lists every PeopleTools metadata table required to run each tool in `tools/peopletools.py`. Use this for database permissions, migration planning, or understanding tool dependencies.

---

## Tool → Tables Summary

| Tool | Required Tables |
|------|-----------------|
| `get_record_definition` | PSRECDEFN, PSRECFIELD, PSDBFIELD, PSKEYDEFN, PSINDEXDEFN |
| `search_records` | PSRECDEFN |
| `get_component_structure` | PSPNLGRPDEFN, PSPNLGROUP, PSPNLDEFN, PSMENUITEM |
| `get_component_pages` | PSPNLGRPDEFN, PSPNLGROUP |
| `get_page_fields` | PSPNLDEFN, PSPNLFIELD |
| `get_page_field_bindings` | PSPNLDEFN, PSPNLFIELD |
| `get_peoplecode` | PSPCMTXT |
| `get_permission_list_details` | PSCLASSDEFN, PSAUTHITEM, PSQRYACCLST |
| `get_roles_for_permission_list` | PSROLECLASS, PSROLEDEFN |
| `get_process_definition` | PS_PRCSDEFN |
| `get_application_engine_steps` | PSAEAPPLDEFN, PSAESTEPDEFN |
| `get_integration_broker_services` | PSOPERATION |
| `get_message_definition` | PSMSGDEFN, PSMSGPARTDEFN |
| `get_query_definition` | PSQRYDEFN, PSQRYRECORD, PSQRYFIELD |
| `get_sql_definition` | PSSQLTEXTDEFN |
| `search_sql_definitions` | PSSQLTEXTDEFN |
| `search_peoplecode` | PSPCMPROG, PSPCMPROG_COMP, PSAESTEPMSGDEFN |
| `get_field_usage` | PSRECFIELD, PSRECDEFN, PSKEYDEFN |
| `get_translate_field_values` | PSXLATITEM |
| `explain_peoplesoft_concept` | PSRECDEFN, PSRECFIELD, PSCLASSDEFN, PSROLEDEFN, PSOPRDEFN, PSAUTHITEM, DUAL |

---

## Master Table List (All Unique Tables)

To run **every** tool in peopletools.py, the database user must have SELECT access to:

| Table | Used By |
|-------|---------|
| PSDBFIELD | get_record_definition |
| PSRECDEFN | get_record_definition, search_records, get_field_usage, explain_peoplesoft_concept |
| PSRECFIELD | get_record_definition, get_field_usage, explain_peoplesoft_concept |
| PSKEYDEFN | get_record_definition, get_field_usage |
| PSINDEXDEFN | get_record_definition |
| PSPNLGRPDEFN | get_component_structure |
| PSPNLGROUP | get_component_structure |
| PSPNLDEFN | get_component_structure, get_page_fields |
| PSMENUITEM | get_component_structure |
| PSPNLFIELD | get_page_fields |
| PSPCMTXT | get_peoplecode |
| PSCLASSDEFN | get_permission_list_details, explain_peoplesoft_concept |
| PSAUTHITEM | get_permission_list_details, explain_peoplesoft_concept |
| PSQRYACCLST | get_permission_list_details |
| PSROLECLASS | get_roles_for_permission_list |
| PSROLEDEFN | get_roles_for_permission_list, explain_peoplesoft_concept |
| PS_PRCSDEFN | get_process_definition |
| PSAEAPPLDEFN | get_application_engine_steps |
| PSAESTEPDEFN | get_application_engine_steps |
| PSOPERATION | get_integration_broker_services |
| PSMSGDEFN | get_message_definition |
| PSMSGPARTDEFN | get_message_definition |
| PSQRYDEFN | get_query_definition |
| PSQRYRECORD | get_query_definition |
| PSQRYFIELD | get_query_definition |
| PSSQLTEXTDEFN | get_sql_definition, search_sql_definitions |
| PSPCMPROG | search_peoplecode |
| PSPCMPROG_COMP | search_peoplecode |
| PSAESTEPMSGDEFN | search_peoplecode |
| PSXLATITEM | get_translate_field_values |
| PSOPRDEFN | explain_peoplesoft_concept |
| DUAL | explain_peoplesoft_concept (Oracle system table) |

---

## Alphabetical Table List (for GRANT scripts)

```
DUAL
PSAEAPPLDEFN
PSAESTEPDEFN
PSAESTEPMSGDEFN
PSAUTHITEM
PSCLASSDEFN
PSDBFIELD
PSINDEXDEFN
PSKEYDEFN
PSMENUITEM
PSMSGDEFN
PSMSGPARTDEFN
PSOPERATION
PSOPRDEFN
PSQRYACCLST
PSQRYDEFN
PSQRYFIELD
PSQRYRECORD
PSRECDEFN
PSRECFIELD
PSROLEDEFN
PSROLECLASS
PSPNLDEFN
PSPNLFIELD
PSPNLGRPDEFN
PSPNLGROUP
PSPCMTXT
PSPCMPROG
PSPCMPROG_COMP
PSXLATITEM
PS_PRCSDEFN
PSSQLTEXTDEFN
```

**Total: 32 tables** (including DUAL; exclude DUAL for non-Oracle or if using a synonym).

---

## Notes

- **PSPCMTXT** and **PSSQLTEXTDEFN** contain CLOB columns; Oracle uses `DBMS_LOB.SUBSTR` and `DBMS_LOB.INSTR` in the tools.
- **DUAL** is an Oracle system table; other databases may not require it or use an equivalent.
- `explain_peoplesoft_concept` queries different tables depending on the concept (effective dating, SetID, record types, security). The master list above covers all branches.
- PeopleTools table names and schemas may vary by environment (e.g., `SYSADM.PSRECDEFN` vs `PS.PSRECDEFN`). Use the correct schema in your grants.
