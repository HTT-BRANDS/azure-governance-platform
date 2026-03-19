# NIST Cybersecurity Framework (CSF) 2.0 — Complete Control Reference

**Source**: NIST Cybersecurity Framework Version 2.0 (NIST CSWP 29)  
**Published**: February 26, 2024 (2-year anniversary celebrated February 2026)  
**Source URL**: https://www.nist.gov/cyberframework  
**NIST CPRT Tool**: https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/CSF_2_0_0/home  
**Azure Policy Initiative**: `NIST_CSF_v2.0.json` — Azure/azure-policy GitHub (version 1.5.0)  
**GitHub path**: built-in-policies/policySetDefinitions/Regulatory Compliance/NIST_CSF_v2.0.json  
**Policy Set ID**: `/providers/Microsoft.Authorization/policySetDefinitions/184a0e05-7b06-4a68-bbbe-13b8353bc613`  
**Retrieved**: March 2026  

---

## Overview: CSF 2.0 vs 1.1 Key Changes

| Aspect | CSF 1.1 | CSF 2.0 |
|--------|---------|---------|
| Functions | 5 (ID, PR, DE, RS, RC) | **6** — added GV (GOVERN) |
| Scope | Primarily critical infrastructure | **Any organization of any size/sector** |
| Supply Chain | Limited | **Expanded (GV.SC)** |
| Categories renamed | PR.AC → **PR.AA** (Access Control → Identity Mgmt, Auth, Access Control) | Multiple renamed |
| Publication | 2018 | **February 26, 2024** |

---

## PART 1: ALL SIX FUNCTIONS WITH ALL CATEGORIES

---

### GV — GOVERN (NEW in CSF 2.0)
*"The organization's cybersecurity risk management strategy, expectations, and policy are established, communicated, and monitored"*

| Category ID | Category Name | Description |
|-------------|--------------|-------------|
| **GV.OC** | Organizational Context | The circumstances — mission, stakeholder expectations, dependencies, and legal, regulatory, and contractual requirements — surrounding the organization's cybersecurity risk management decisions are understood |
| **GV.RM** | Risk Management Strategy | The organization's priorities, constraints, risk tolerance and appetite statements, and assumptions are established, communicated, and used to support operational risk decisions |
| **GV.RR** | Roles, Responsibilities, and Authorities | Cybersecurity roles, responsibilities, and authorities to foster accountability, performance assessment, and continuous improvement are established and communicated |
| **GV.PO** | Policy | Organizational cybersecurity policy is established, communicated, and enforced |
| **GV.OV** | Oversight | Results of organization-wide cybersecurity risk management activities and performance are used to inform, improve, and adjust the risk management strategy |
| **GV.SC** | Cybersecurity Supply Chain Risk Management | Cyber supply chain risk management processes are identified, established, managed, monitored, and improved by organizational stakeholders |

**GV subcategories referenced in Azure Policy:**

| Subcategory ID | Description |
|---------------|-------------|
| **GV.OC-04** | Organizational cybersecurity policy is established based on the organization's mission and objectives and addresses roles, responsibilities, and risk |
| **GV.SC-07** | The risks posed by a supplier, their products and services, and other third parties are understood and recorded in the cybersecurity risk register; risks are prioritized based on their potential impact |

---

### ID — IDENTIFY
*"The organization's current cybersecurity risks are understood"*

| Category ID | Category Name | Description |
|-------------|--------------|-------------|
| **ID.AM** | Asset Management | Assets (data, hardware, software, systems, facilities, services, people) that enable the organization to achieve business purposes are identified and managed consistent with their relative importance to organizational objectives and the organization's risk strategy |
| **ID.RA** | Risk Assessment | The cybersecurity risk to the organization, assets, and individuals is understood by the organization |
| **ID.IM** | Improvement | Improvements to organizational cybersecurity risk management processes, procedures and activities are identified across all CSF Functions |

**ID subcategories referenced in Azure Policy:**

| Subcategory ID | Description |
|---------------|-------------|
| **ID.AM-01** | Inventories of hardware managed by the organization are maintained |
| **ID.RA-01** | Vulnerabilities in assets are identified, validated, and recorded |
| **ID.RA-07** | Changes and exceptions are managed, assessed for risk impact, prioritized, and approved |

**Additional ID subcategories (full CSF 2.0, not all in Azure built-in):**

| Subcategory ID | Description |
|---------------|-------------|
| **ID.AM-02** | Inventories of software, services, and systems managed by the organization are maintained |
| **ID.AM-03** | Representations of the organization's authorized network communication and internal and external network data flows are maintained |
| **ID.AM-04** | Inventories of services provided by suppliers are maintained |
| **ID.AM-05** | Assets are prioritized based on classification, criticality, resources, and impact on the mission |
| **ID.AM-07** | Inventories of data and corresponding metadata for designated data types are maintained |
| **ID.AM-08** | Systems, hardware, software, services, and data are managed throughout their life cycles |
| **ID.RA-02** | Cyber threat intelligence is received from information sharing forums and sources |
| **ID.RA-03** | Internal and external threats to the organization are identified and recorded |
| **ID.RA-04** | Potential impacts and likelihoods of threats exploiting vulnerabilities are identified and recorded |
| **ID.RA-05** | Threats, vulnerabilities, likelihoods, and impacts are used to understand inherent risk and inform risk response prioritization |
| **ID.RA-06** | Risk responses are chosen, prioritized, planned, tracked, and communicated |
| **ID.RA-08** | Processes for receiving, analyzing, and responding to vulnerability disclosures are established |
| **ID.RA-09** | The authenticity and integrity of hardware and software are assessed prior to acquisition and use |
| **ID.RA-10** | Critical suppliers are assessed prior to acquisition |
| **ID.IM-01** | Improvements are identified from evaluations |
| **ID.IM-02** | Improvements are identified from security tests and exercises, including those done in coordination with suppliers and relevant third parties |
| **ID.IM-03** | Improvements are identified from execution of operational processes, procedures, and activities |
| **ID.IM-04** | Incident response plans and other cybersecurity plans that affect operations are established, communicated, maintained, and improved |

---

### PR — PROTECT
*"Safeguards to manage the organization's cybersecurity risks are used"*

| Category ID | Category Name | Description |
|-------------|--------------|-------------|
| **PR.AA** | Identity Management, Authentication, and Access Control | Access to physical and logical assets is limited to authorized users, services, and hardware and managed commensurate with the assessed risk of unauthorized access |
| **PR.AT** | Awareness and Training | The organization's personnel are provided with cybersecurity awareness and training so that they can perform their cybersecurity-related tasks |
| **PR.DS** | Data Security | Data are managed consistent with the organization's risk strategy to protect the confidentiality, integrity, and availability of information |
| **PR.PS** | Platform Security | The hardware, software (e.g., firmware, operating systems, applications), and services of physical and virtual platforms are managed consistent with the organization's risk strategy to protect their confidentiality, integrity, and availability |
| **PR.IR** | Technology Infrastructure Resilience | Security architectures are managed with the organization's risk strategy to protect asset confidentiality, integrity, and availability, and organizational resilience |

**PR subcategories referenced in Azure Policy:**

| Subcategory ID | Description |
|---------------|-------------|
| **PR.AA** | Identity Management, Authentication, and Access Control (full category) |
| **PR.AA-01** | Identities and credentials for authorized users, services, and hardware are managed by the organization |
| **PR.AA-05** | Access permissions, entitlements, and authorizations are defined in a policy, managed, enforced, and reviewed, and incorporate the principles of least privilege and separation of duties |
| **PR.DS** | Data Security (full category) |
| **PR.DS-01** | The confidentiality, integrity, and availability of data-at-rest are protected |
| **PR.DS-02** | The confidentiality, integrity, and availability of data-in-transit are protected |
| **PR.PS-02** | Software on assets is maintained to reduce exploitability and risk |
| **PR.PS-04** | Log records are generated to enable monitoring, forensics, and incident response, and to support compliance reporting |
| **PR.PS-05** | Installation and execution of unauthorized software are prevented |

**Additional PR subcategories (full CSF 2.0):**

| Subcategory ID | Description |
|---------------|-------------|
| **PR.AA-02** | Identities are proofed and bound to credentials based on the context of interactions |
| **PR.AA-03** | Users, services, and hardware are authenticated |
| **PR.AA-04** | Identity assertions are protected, conveyed, and verified |
| **PR.AA-06** | Physical access to assets is managed, monitored, and enforced commensurate with risk |
| **PR.AT-01** | Personnel are provided with awareness and training so that they possess the knowledge and skills to perform general tasks with cybersecurity risks in mind |
| **PR.AT-02** | Individuals in specialized roles are provided with awareness and training so that they possess the knowledge and skills to perform relevant tasks with cybersecurity risks in mind |
| **PR.DS-03** | Hardware and software are managed to ensure the accuracy and integrity of data |
| **PR.DS-04** | Adequate capacity to ensure availability is maintained |
| **PR.DS-05** | Protections against data leaks are implemented |
| **PR.DS-06** | Integrity checking mechanisms are used to verify software, firmware, and information integrity |
| **PR.DS-07** | The development and testing environment(s) are separate from the production environment |
| **PR.DS-08** | Integrity checking mechanisms are used to verify hardware integrity |
| **PR.PS-01** | Configuration management practices are established and applied |
| **PR.PS-03** | Hardware is maintained to minimize the risk of exploitation |
| **PR.IR-01** | Networks and environments are protected from unauthorized logical access and usage |
| **PR.IR-02** | The organization's technology assets are protected from environmental threats |
| **PR.IR-03** | Mechanisms are implemented to achieve resilience requirements in normal and adverse situations |
| **PR.IR-04** | Adequate resource capacity to ensure availability is maintained |

---

### DE — DETECT
*"Possible cybersecurity attacks and compromises are found and analyzed"*

| Category ID | Category Name | Description |
|-------------|--------------|-------------|
| **DE.CM** | Continuous Monitoring | Assets are monitored to find anomalies, indicators of compromise, and other potentially adverse events |
| **DE.AE** | Adverse Event Analysis | Anomalies, indicators of compromise, and other potentially adverse events are analyzed to characterize the events and detect cybersecurity incidents |

**DE subcategories referenced in Azure Policy:**

| Subcategory ID | Description |
|---------------|-------------|
| **DE.CM** | Continuous Monitoring (full category) |
| **DE.CM-03** | Personnel activity and technology usage are monitored to find potentially adverse events |
| **DE.CM-09** | Computing hardware and software, runtime environments, and their data are monitored to find potentially adverse events |
| **DE.AE** | Adverse Event Analysis (full category) |
| **DE.AE-03** | Information is correlated from multiple sources |
| **DE.AE-06** | Information on adverse events is provided to authorized staff and tools |

**Additional DE subcategories (full CSF 2.0):**

| Subcategory ID | Description |
|---------------|-------------|
| **DE.CM-01** | Networks and network services are monitored to find potentially adverse events |
| **DE.CM-02** | The physical environment is monitored to find potentially adverse events |
| **DE.CM-06** | External service provider activities and services are monitored to find potentially adverse events |
| **DE.AE-02** | Potentially adverse events are analyzed to better understand associated activities |
| **DE.AE-04** | The estimated impact and scope of adverse events are understood |
| **DE.AE-07** | Cyber threat intelligence and other contextual information are integrated into the analysis |
| **DE.AE-08** | Incidents are declared when adverse events meet the defined incident criteria |

---

### RS — RESPOND
*"Actions regarding a detected cybersecurity incident are taken"*

| Category ID | Category Name | Description |
|-------------|--------------|-------------|
| **RS.MA** | Incident Management | Responses to detected cybersecurity incidents are managed |
| **RS.AN** | Incident Analysis | Investigations are conducted to ensure effective response and support forensics and recovery activities |
| **RS.CO** | Incident Response Reporting and Communication | Response activities are coordinated with internal and external stakeholders as required by laws, regulations, or policies |
| **RS.MI** | Incident Mitigation | Activities are performed to prevent expansion of an event and mitigate its effects |

**RS subcategories referenced in Azure Policy:**

| Subcategory ID | Description |
|---------------|-------------|
| **RS.CO-02** | Internal and external stakeholders are notified of incidents in a timely manner as required |
| **RS.CO-03** | Information is shared with designated internal and external stakeholders as established in the incident response plan |

**Additional RS subcategories (full CSF 2.0):**

| Subcategory ID | Description |
|---------------|-------------|
| **RS.MA-01** | The incident response plan is executed in coordination with relevant third parties once an incident is declared |
| **RS.MA-02** | Incident reports are triaged and validated |
| **RS.MA-03** | Incidents are categorized and prioritized |
| **RS.MA-04** | Incidents are escalated or elevated as needed |
| **RS.MA-05** | The criteria for initiating incident recovery are applied |
| **RS.AN-03** | Analysis is performed to establish what has taken place during an incident and the root cause of the incident |
| **RS.AN-06** | Actions performed during an investigation are recorded, and the records' integrity and provenance are preserved |
| **RS.AN-07** | Incident data and metadata are collected, and their integrity and provenance are preserved |
| **RS.AN-08** | An incident's magnitude is estimated and validated |
| **RS.CO-01** | The personnel responsible for executing the response plan are identified and have access to the plan |
| **RS.MI-01** | Incidents are contained |
| **RS.MI-02** | Incidents are eradicated |

---

### RC — RECOVER
*"Assets and operations affected by a cybersecurity incident are restored"*

| Category ID | Category Name | Description |
|-------------|--------------|-------------|
| **RC.RP** | Incident Recovery Plan Execution | Restoration activities are performed to ensure operational availability of systems and services affected by cybersecurity incidents |
| **RC.CO** | Incident Recovery Communication | Restoration activities are coordinated with internal and external parties |

**RC subcategories referenced in Azure Policy:**

| Subcategory ID | Description |
|---------------|-------------|
| **RC.RP** | Incident Recovery Plan Execution (full category) |
| **RC.RP-04** | The integrity of backups and other restoration assets is verified before using them for restoration |

**Additional RC subcategories (full CSF 2.0):**

| Subcategory ID | Description |
|---------------|-------------|
| **RC.RP-01** | The recovery portion of the incident response plan is executed once initiated from the incident response process |
| **RC.RP-02** | Recovery actions are selected, scoped, prioritized, and performed |
| **RC.RP-03** | The integrity of restored assets is verified, systems and services are restored, and normal operating status is confirmed |
| **RC.RP-05** | The functions of restored systems are verified |
| **RC.RP-06** | The end of incident recovery is declared based on criteria, and incident-related documentation is completed |
| **RC.CO-03** | Recovery activities and progress in restoring operational capabilities are communicated to designated internal and external stakeholders |
| **RC.CO-04** | Public updates on incident recovery are shared using approved methods and messaging |

---

## PART 2: Azure Policy NIST CSF v2.0 Group Mappings

Groups actually defined in Azure's built-in `NIST_CSF_v2.0.json` (version 1.5.0):

```
GV: GV.OC_04, GV.SC_07
ID: ID.AM_01, ID.RA_01, ID.RA_07
PR: PR.AA, PR.AA_01, PR.AA_05, PR.DS, PR.DS_01, PR.DS_02, PR.PS_02, PR.PS_04, PR.PS_05
DE: DE.CM, DE.CM_03, DE.CM_09, DE.AE, DE.AE_03, DE.AE_06
RS: RS.CO_02, RS.CO_03
RC: RC.RP, RC.RP_04
```

**Notable coverage gaps** (in full CSF 2.0 but NOT in Azure's built-in initiative):
- RS.MA (Incident Management) — not directly mapped
- RS.AN (Incident Analysis) — not directly mapped  
- RS.MI (Incident Mitigation) — not directly mapped
- RC.CO (Incident Recovery Communication) — not directly mapped
- Most GV subcategories (GV.RM, GV.RR, GV.PO, GV.OV)
- PR.AT (Awareness and Training) — not directly mapped
- PR.IR (Infrastructure Resilience) — not directly mapped
