# Key PeopleSoft HCM GP 9.2 Tables

### Workforce Administration
- **PS_PERSONAL_DATA**: Employee personal info (name, address, birthdate, etc.)
- **PS_JOB**: Job history, compensation, department, status.
- **PS_COMPANY_TBL**: Company setup and configuration.
- **PS_ADDRESS**: Stores address details for various entities in PeopleSoft.
- **PS_DEPT_TBL**: Contains information about all organizational departments.
- **PS_JOBCODE_TBL**: Defines standard job classifications and their attributes.
- **PS_LOCATION_TBL**: Holds data for physical operating locations.
- **PS_COMPANY_TBL**: Identifies and describes legal company entities.
- **PS_PAYGROUP**: Groups employees for payroll processing based on frequency and rules.
- **PS_CONTRACT**: Records details of employee contracts and agreements.
- **PS_COMPENSATION**: Records compensation details for employees, including salary, hourly rate, and pay components.
- **PS_EMPLOYMENT**: Stores employment history and status details for each employee record number.
- **PS_DEPENDENT_BENEF**: Lists dependents and beneficiaries associated with an employee for benefits purposes.


### Global Payroll 
- **PS_GP_PYE_PRC_STAT**: Stores the status of resolved calendars for each payee, indicating the progress of payroll calculation.
- **PS_GP_PYE_SEG_STAT**: Contains the status of resolved segments (e.g., periods, pay components) for each payee within a calendar.
- **PS_GP_RSLT_ERN_DED**: The core table for calculated earnings and deductions, storing the detailed results of payroll processing for each payee and element.
- **PS_GP_RSLT_ACUM**: Holds the results of accumulator calculations, which track cumulative values for earnings, deductions, and other elements.
- **PS_GP_RSLT_PIN**: Stores the resolved values of supporting elements like variables, formulas, and brackets during payroll calculation.
- **PS_GP_RSLT_PI_DATA**: Contains the results of positive input (one-time earnings or deductions) processed during payroll.
- **PS_GP_RSLT_ABS**: Stores the calculated results of absence takes (e.g., daily hours of sick leave) from Absence Management for payroll.
- **PS_GP_MESSAGES**: Records any error or warning messages generated for payees during the payroll calculation process.
- **PS_GP_PMT_PREPARE**: Stores details for the payment preparation process for a calendar group, leading to actual payments.
- **PS_GP_PAYMENT**: Contains the results of payment processing, including payment amounts and method.
- **PS_GP_GL_DATA**: Holds the results of the Global Payroll to General Ledger interface, used for posting payroll expenses to the financial system.
- **PS_GP_RTO_TRGR**: Stores retroactive triggers, indicating changes that require recalculation of prior periods.
- **PS_GP_SEG_TRGR**: Contains segmentation triggers, which indicate a need to recalculate a payee's payroll due to changes in their employment or data segmentation.
- **PS_GP_PI_MNL_DATA**: Records manually entered positive input (one-time earnings/deductions) for a payee.

### ePerformance
- **PS_EP_APPR**: The central table for performance documents (appraisals), storing general data like appraisal ID, employee ID, manager ID, and review period dates.
- **PS_EP_APPR_ROLE**: Stores details about the roles participating in a specific performance document (e.g., employee, manager, peer, HR).
- **PS_EP_APPR_SECTION**: Contains data for each section within a performance document, such as goals, competencies, or overall summary.
- **PS_EP_APPR_ITEM**: Holds the individual evaluation items within each section of a performance document, along with their ratings and comments.
- **PS_EP_APPR_SUBITEM**: Stores details for sub-items or detailed components within a performance item, if applicable.

### Key PeopleTools Tables that define Table/Record structure
- **PSRECFIELD**: Table/record definitions with its Columns/fields (metadata).
- **PSDBFIELD**: Field/column definitions (metadata).
- **PSRECDEFN**: Table/record definitions (metadata).
- **PSKEYDEFN**: Stores the index key information.
- **PSOPTIONS**: This table is used to turn off or on the change control enabling feature.
- **PSOPRDEFN**: This table holds the PeopleSoft Oprid's/passwords info with symbolic id.
- **PSXLATDEFN**: Holds the translate fieldname and version number for caching.
- **PSXLATDEFNLANG**: Holds the translate fieldname with different languages than the base language.

- **PSROLECLASS**: Provides the permission lists associated to each role.
- **PSROLEUSER**: Gives information about the roles assigned to the Oprid's.
- **PSRELEASE**: This table holds the application release details.
- **PSSTATUS**: This table gives the PeopleTools information.


## Other PeopleSoft System Tables
- **PSMPDEFN**: Contains info about mobilepages.
- **PSMSGAGTDEFN**: Refers to the activity object.
- **PSMSGCATDEFN**: Related to Messages – Message catalogs.
- **PSMSGDEFN**: Stores Application Message definitions.
- **PSLOCK**: This table is used for version control.
- **PSDDLDEFPARMS**: This table holds the storage structure of the tables for db platforms.
- **PSGATEWAY**: This table holds the gateway URL.
- **PSIDXDDLPARM**: This table holds the storage structure of the indexes for db platforms.
- **PSPACKAGEDEFN**: This table holds the application packages definitions.
- **PS_CDM_DIST_NODE**: This table holds the report node information which contains the report repository details.
- **PS_CDM_DISTSTATUS**: Contains the definition of report status.
- **PS_CDM_LIST**: Contains the process instance details. Should be in synch with PS_CDM_AUTH.
- **PS_PRCSDEFN**: Contains process type and process names.
- **PSACTIVITYDEFN**: Activity definitions are stored.
- **PSAESECTDEFN**: Stores the application engine section definitions.
- **PSAESTEPDEFN**: Stores the application engine step definitions.
- **PSAESTEPMSGDEFN**: Stores the messages of the AE programs.
- **PSPCMPROG**: PeopleCode programs are stored.
- **PSSQLTEXTDEFN**: Application engine SQL is stored.
- **PSAEAPPLDEFN**: Application engine program name is stored.
- **PSMENUDEFN**: Menu names are stored.
- **PSPNLDEFN**: Page names are stored.
- **PSPNLGROUP**: Stores component definitions.
- **PSBCDEFN**: Stores component interface names.
- **PSBUSPROCDEFN**: Stores Business process definitions.
- **PS_APPR_RULE_HDR**: Stores Approval rule set definitions.
- **PSCHNLDEFN**: Stores channel definitions.
- **PSEVENTDEFN**: Changing the column value of active to 0 leads to disabling activities.
- **PSFLDFIELDDEFN**: Filelayout is stored.
- **PSFILEREDEFN**: File reference is stored.
- **PSINDEXDEFN**: Index information is stored.
- **PSIODEFN**: Stores business interlink information.
