# SOC 2 Trust Services Criteria — Complete Control Reference

**Source**: AICPA 2017 Trust Services Criteria (with Revised Points of Focus — 2022)  
**Source URL**: https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022  
**Azure Policy Initiative**: `SOC_2.json` — Azure/azure-policy GitHub, built-in-policies/policySetDefinitions/Regulatory Compliance/  
**Azure Policy Release**: 9371a67f (#1499), last updated ~6 months ago  
**Verification**: Microsoft Learn — "Details of the System and Organization Controls (SOC) 2 Regulatory Compliance built-in initiative"  
**Retrieved**: March 2026  

---

## Overview of TSC Structure

The SOC 2 framework is organized into:
1. **Common Criteria (CC1–CC9)** — Required for ALL SOC 2 engagements
2. **Additional Criteria** — Selected based on applicable Trust Service Categories:
   - **A1** — Availability
   - **C1** — Confidentiality
   - **PI1** — Processing Integrity
   - **P1–P8** — Privacy

---

## PART 1: COMMON CRITERIA (CC) — All Categories

### CC1 — Control Environment
*The entity demonstrates a commitment to integrity and ethical values; the board demonstrates independence and exercises oversight; management establishes structure, authority, and responsibility; attracts, develops, and retains competent individuals; and holds individuals accountable.*

| Control ID | Description |
|------------|-------------|
| **CC1.1** | COSO Principle 1: The entity demonstrates a commitment to integrity and ethical values. |
| **CC1.2** | COSO Principle 2: The board of directors demonstrates independence from management and exercises oversight of the development and performance of internal control. |
| **CC1.3** | COSO Principle 3: Management establishes, with board oversight, structures, reporting lines, and appropriate authorities and responsibilities in pursuit of objectives. |
| **CC1.4** | COSO Principle 4: The entity demonstrates a commitment to attract, develop, and retain competent individuals in alignment with objectives. |
| **CC1.5** | COSO Principle 5: The entity holds individuals accountable for their internal control responsibilities in the pursuit of objectives. |

---

### CC2 — Communication and Information
*The entity obtains or generates and uses relevant, quality information to support the functioning of internal control; internally communicates information, including objectives and responsibilities for internal control; and communicates with external parties regarding matters affecting the functioning of internal control.*

| Control ID | Description |
|------------|-------------|
| **CC2.1** | COSO Principle 13: The entity obtains or generates and uses relevant, quality information to support the functioning of internal control. |
| **CC2.2** | COSO Principle 14: The entity internally communicates information, including objectives and responsibilities for internal control, necessary to support the functioning of internal control. |
| **CC2.3** | COSO Principle 15: The entity communicates with external parties regarding matters affecting the functioning of internal control. |

---

### CC3 — Risk Assessment
*The entity specifies objectives with sufficient clarity to enable the identification and assessment of risks relating to objectives; identifies risks to achievement of objectives across the entity and analyzes risks as a basis for determining how they should be managed; considers the potential for fraud in assessing risks; and identifies and assesses changes that could significantly impact the system of internal control.*

| Control ID | Description |
|------------|-------------|
| **CC3.1** | COSO Principle 6: The entity specifies objectives with sufficient clarity to enable the identification and assessment of risks relating to objectives. |
| **CC3.2** | COSO Principle 7: The entity identifies risks to the achievement of its objectives across the entity and analyzes risks as a basis for determining how the risks should be managed. |
| **CC3.3** | COSO Principle 8: The entity considers the potential for fraud in assessing risks to the achievement of objectives. |
| **CC3.4** | COSO Principle 9: The entity identifies and assesses changes that could significantly impact the system of internal control. |

---

### CC4 — Monitoring Activities
*The entity selects, develops, and performs ongoing and/or separate evaluations to ascertain whether the components of internal control are present and functioning; and evaluates and communicates internal control deficiencies in a timely manner.*

| Control ID | Description |
|------------|-------------|
| **CC4.1** | COSO Principle 16: The entity selects, develops, and performs ongoing and/or separate evaluations to ascertain whether the components of internal control are present and functioning. |
| **CC4.2** | COSO Principle 17: The entity evaluates and communicates internal control deficiencies in a timely manner to those parties responsible for taking corrective action, including senior management and the board of directors, as appropriate. |

---

### CC5 — Control Activities
*The entity selects and develops control activities that contribute to the mitigation of risks to the achievement of objectives to acceptable levels; selects and develops general technology control activities to support the achievement of objectives; and deploys control activities through policies that establish what is expected and procedures that put policies into action.*

| Control ID | Description |
|------------|-------------|
| **CC5.1** | COSO Principle 10: The entity selects and develops control activities that contribute to the mitigation of risks to the achievement of objectives to acceptable levels. |
| **CC5.2** | COSO Principle 11: The entity also selects and develops general control activities over technology to support the achievement of objectives. |
| **CC5.3** | COSO Principle 12: The entity deploys control activities through policies that establish what is expected and in procedures that put policies into action. |

---

### CC6 — Logical and Physical Access Controls ⭐ HIGH RELEVANCE TO AZURE
*The entity implements logical access security; authorizes users; manages access; restricts physical access; manages removable media; protects against external threats; restricts transmission; and prevents unauthorized software.*

| Control ID | Description |
|------------|-------------|
| **CC6.1** | The entity implements logical access security software, infrastructure, and architectures over protected information assets to protect them from security events to meet the entity's objectives. *(Logical access controls, multi-factor authentication, password controls, encryption keys management)* |
| **CC6.2** | Prior to issuing system credentials and granting system access, the entity registers and authorizes new internal and external users whose access is administered by the entity. *(User registration, credential issuance, access provisioning processes)* |
| **CC6.3** | The entity authorizes, modifies, or removes access to data, software, functions, and other protected information assets based on approved and documented access rules. *(Role-based access control, access reviews, de-provisioning, least privilege)* |
| **CC6.4** | The entity restricts physical access to facilities and protected information assets (including those in data centers) to authorized personnel to meet the entity's objectives. *(Physical security, data center access, badge systems, visitor logs)* |
| **CC6.5** | The entity discontinues logical and physical protections over physical assets only after the ability to read or recover data and software from those assets has been diminished and is no longer required to meet the entity's objectives. *(Media disposal, data destruction, secure decommissioning)* |
| **CC6.6** | The entity implements logical access security measures to protect against threats from sources outside its system boundaries. *(Firewalls, network security groups, WAF, perimeter security, intrusion detection)* |
| **CC6.7** | The entity restricts the transmission, movement, and removal of information to authorized internal and external users and processes, and protects it during transmission, movement, or removal to meet the entity's objectives. *(TLS/encryption in transit, DLP, private endpoints, VPN)* |
| **CC6.8** | The entity implements controls to prevent or detect and act upon the introduction of unauthorized or malicious software to meet the entity's objectives. *(Antimalware, Defender for Cloud, endpoint protection, container security)* |

---

### CC7 — System Operations ⭐ HIGH RELEVANCE TO AZURE
*The entity detects and monitors; evaluates vulnerabilities; monitors for anomalies; evaluates security events; responds to incidents; and recovers from identified security incidents.*

| Control ID | Description |
|------------|-------------|
| **CC7.1** | To meet its objectives, the entity uses detection and monitoring procedures to identify (1) changes to configurations that result in the introduction of new vulnerabilities, and (2) susceptibilities to newly discovered vulnerabilities. *(Configuration monitoring, vulnerability scanning, Azure Security Center, Defender for Cloud)* |
| **CC7.2** | The entity monitors system components and the operation of those components for anomalies that are indicative of malicious acts, natural disasters, and errors affecting the entity's ability to meet its objectives; anomalies are analyzed to determine whether they represent security events. *(Log Analytics, Azure Monitor, SIEM integration, anomaly detection)* |
| **CC7.3** | The entity evaluates security events to determine whether they could or have resulted in a failure of the entity to meet its objectives (security incidents) and, if so, takes actions to prevent or address such failures. *(Incident triage, security event classification, SOC operations)* |
| **CC7.4** | The entity responds to identified security incidents by executing a defined incident response program to understand, contain, remediate, and communicate security incidents, as appropriate. *(Incident response playbooks, containment procedures, forensics, notification)* |
| **CC7.5** | The entity identifies, develops, and implements activities to recover from identified security incidents. *(Recovery procedures, lessons learned, post-incident review, system restoration)* |

---

### CC8 — Change Management ⭐ HIGH RELEVANCE TO AZURE
*The entity authorizes, designs, develops, tests, approves, and implements changes to infrastructure, data, software, and procedures.*

| Control ID | Description |
|------------|-------------|
| **CC8.1** | The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, and implements changes to infrastructure, data, software, and procedures to meet its change management objectives. *(Change management process, CI/CD controls, infrastructure-as-code review, deployment approvals, rollback capability, Azure DevOps pipelines)* |

---

### CC9 — Risk Mitigation
*The entity identifies, selects, and develops risk mitigation activities; and assesses and manages risks associated with business disruption, as well as vendor and business partner risk.*

| Control ID | Description |
|------------|-------------|
| **CC9.1** | The entity identifies, selects, and develops risk mitigation activities for risks arising from potential business disruptions. *(BCP, disaster recovery, Azure availability zones, geo-redundant storage)* |
| **CC9.2** | The entity assesses and manages risks associated with vendors and business partners. *(Third-party risk management, vendor assessments, supply chain security, Azure Marketplace security)* |

---

## PART 2: ADDITIONAL CRITERIA

### A1 — Availability ⭐ HIGH RELEVANCE TO AZURE
*Applies when Availability is a selected Trust Service Category*

| Control ID | Description |
|------------|-------------|
| **A1.1** | The entity maintains, monitors, and evaluates current processing capacity and use of system components (infrastructure, data, and software) to manage capacity demand and to enable the implementation of additional capacity to help meet its objectives. *(Capacity planning, auto-scaling, Azure Monitor metrics, quota monitoring, resource health)* |
| **A1.2** | The entity authorizes, designs, develops or acquires, implements, operates, approves, maintains, and monitors environmental protections, software, data backup processes, and recovery infrastructure to meet its recovery time and recovery point objectives. *(Backup policies, geo-redundant backups, RTO/RPO targets, Azure Backup, Azure Site Recovery, BCDR)* |
| **A1.3** | The entity tests recovery plan procedures supporting system recovery to meet its objectives. *(DR testing, backup restoration tests, failover drills, runbook validation)* |

---

### C1 — Confidentiality
*Applies when Confidentiality is a selected Trust Service Category*

| Control ID | Description |
|------------|-------------|
| **C1.1** | The entity identifies and maintains confidential information to meet the entity's objectives related to confidentiality. *(Data classification, sensitivity labels, data inventory)* |
| **C1.2** | The entity disposes of confidential information to meet the entity's objectives related to confidentiality. *(Secure deletion, data retention policies, Key Vault key destruction)* |

---

### PI1 — Processing Integrity
*Applies when Processing Integrity is a selected Trust Service Category*

| Control ID | Description |
|------------|-------------|
| **PI1.1** | The entity obtains or generates, uses, and communicates relevant, quality information regarding the objectives related to processing, including definitions of data processed and product and service specifications, to support the use of products and services. |
| **PI1.2** | The entity implements policies and procedures over system inputs, including controls over completeness and accuracy, to result in products, services, and reporting to meet the entity's objectives. |
| **PI1.3** | The entity implements policies and procedures over system processing to result in products, services, and reporting to meet the entity's objectives. |
| **PI1.4** | The entity implements policies and procedures to make available or deliver output completely, accurately, and timely in accordance with specifications to meet the entity's objectives. |
| **PI1.5** | The entity implements policies and procedures to store inputs, items in processing, and outputs completely, accurately, and timely in accordance with system specifications to meet the entity's objectives. |

---

### P1–P8 — Privacy
*Applies when Privacy is a selected Trust Service Category*

| Control ID | Description |
|------------|-------------|
| **P1.1** | The entity provides notice to data subjects about its privacy practices to meet the entity's objectives related to privacy. |
| **P2.1** | The entity communicates choices available regarding the collection, use, retention, disclosure, and disposal of personal information to the data subjects and the consequences, if any, of each choice. |
| **P3.1** | Personal information is collected consistent with the entity's objectives related to privacy. |
| **P3.2** | For information requiring explicit consent, the entity communicates the need for such consent, as well as the consequences of a failure to provide consent, and obtains the consent prior to collection of the information to meet the entity's objectives related to privacy. |
| **P4.1** | The entity limits the use of personal information to the purposes identified in the entity's objectives related to privacy. |
| **P4.2** | The entity retains personal information consistent with the entity's objectives related to privacy. |
| **P4.3** | The entity securely disposes of personal information to meet the entity's objectives related to privacy. |
| **P5.1** | The entity grants identified and authenticated data subjects the ability to access their stored personal information for review and, upon request, provides physical or electronic copies of that information to data subjects to meet the entity's objectives related to privacy. |
| **P5.2** | The entity corrects, amends, or appends personal information based on information provided by data subjects and communicates such information to third parties, as committed or required, to meet the entity's objectives related to privacy. |
| **P6.1** | The entity discloses personal information to third parties with the explicit consent of data subjects, and such consent is obtained prior to disclosure to meet the entity's objectives related to privacy. |
| **P6.2** | The entity creates and retains a complete, accurate, and timely record of authorized disclosures of personal information to meet the entity's objectives related to privacy. |
| **P6.3** | The entity creates and retains a complete, accurate, and timely record of detected or reported unauthorized disclosures of personal information to meet the entity's objectives related to privacy. |
| **P6.4** | The entity implements policies and procedures consistent with its privacy notice to ensure that personal information is protected during the design, development, implementation, and maintenance of processes and systems. |
| **P6.5** | The entity obtains privacy commitments from vendors and other third parties who have access to personal information to meet the entity's objectives related to privacy. |
| **P6.6** | The entity provides notification of breaches and incidents to affected data subjects, regulators, and others to meet the entity's objectives related to privacy. |
| **P6.7** | The entity provides data subjects with an accounting of the personal information held and disclosure made upon request to meet the entity's objectives related to privacy. |
| **P7.1** | The entity collects and maintains accurate, up-to-date, complete, and relevant personal information to meet the entity's objectives related to privacy. |
| **P8.1** | The entity implements a process for receiving, addressing, resolving, and communicating the resolution of inquiries, complaints, and disputes from data subjects and others and periodically monitors compliance to meet the entity's objectives related to privacy. |

---

## Azure Policy SOC 2 Built-In Initiative Groups

The `SOC_2.json` policy set definition groups controls by the TSC category names as they appear in Azure's compliance dashboard:

| Azure Group Name | Maps to TSC |
|-----------------|-------------|
| `Additional Criteria For Availability` | A1.1, A1.2, A1.3 |
| `Additional Criteria For Confidentiality` | C1.1, C1.2 |
| `Control Environment` | CC1.x |
| `Communication and Information` | CC2.x |
| `Risk Assessment` | CC3.x |
| `Monitoring Activities` | CC4.x |
| `Control Activities` | CC5.x |
| `Logical and Physical Access Controls` | CC6.x |
| `System Operations` | CC7.x |
| `Change Management` | CC8.1 |
| `Risk Mitigation` | CC9.x |
| `Processing Integrity` | PI1.x |
| `Privacy` | P1–P8 |
