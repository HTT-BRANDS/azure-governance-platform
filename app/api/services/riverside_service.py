"""
Riverside governance service for Microsoft 365 security posture.

This service provides executive-level visibility into the 72 Riverside security requirements
across tenant environments by:
- Aggregating Microsoft Graph, Entra ID, and compliance data
- Calculating maturity levels (Emerging 25%, Developing 50%, Mature 75%, Leading 95%)
- Tracking requirement-level status, evidence, and deadlines (Phase 1 Q3 2025, Phase 2 Q4 2025, Phase 3 Q1 2026)
- Identifying critical MFA, device, and conditional access gaps
- Enabling weekly executive reporting with trend analytics across 5 tenants (HTT, BCC, FN, TLL, DCE)
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# Enums

class RequirementLevel(Enum):
    """Maturity levels for security requirements."""
    EMERGING = "Emerging"
    DEVELOPING = "Developing"
    MATURE = "Mature"
    LEADING = "Leading"


class MFAStatus(Enum):
    """MFA enforcement status for users."""
    ENFORCED = "Enforced"
    AVAILABLE = "Available"
    PENDING = "Pending"
    NOT_CONFIGURED = "Not Configured"


class RequirementStatus(Enum):
    """Implementation status of security requirements."""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    AT_RISK = "At Risk"


class DeadlinePhase(Enum):
    """Implementation phases for Riverside requirements."""
    PHASE_1_Q3_2025 = "Phase 1: Q3 2025"
    PHASE_2_Q4_2025 = "Phase 2: Q4 2025"
    PHASE_3_Q1_2026 = "Phase 3: Q1 2026"


class RiversideRequirementCategory(Enum):
    """Categories of Riverside security requirements."""
    MFA_ENFORCEMENT = "MFA Enforcement"
    CONDITIONAL_ACCESS = "Conditional Access"
    PRIVILEGED_ACCESS = "Privileged Access"
    DEVICE_COMPLIANCE = "Device Compliance"
    THREAT_MANAGEMENT = "Threat Management"
    DATA_LOSS_PREVENTION = "Data Loss Prevention"
    LOGGING_MONITORING = "Logging & Monitoring"
    INCIDENT_RESPONSE = "Incident Response"


# Data Models

@dataclass
class RiversideRequirement:
    """Individual Riverside security requirement."""
    id: str
    category: RiversideRequirementCategory
    title: str
    description: str
    control_source: str
    control_reference: str
    maturity_level: RequirementLevel
    phase: DeadlinePhase
    target_date: date | None
    status: RequirementStatus = RequirementStatus.NOT_STARTED
    evidence_count: int = 0
    approval_status: str | None = None


@dataclass
class TenantRequirementTracker:
    """Tracks requirement status per tenant."""
    tenant_id: str
    tenant_name: str
    requirement: RiversideRequirement
    status: RequirementStatus
    evidence_submitted: int = 0
    last_updated: datetime | None = None
    compliance_notes: str | None = None


@dataclass
class RiversideComplianceSummary:
    """Overall compliance summary across all tenants."""
    overall_compliance_pct: float
    target_compliance_pct: float
    completed_requirements_count: int
    total_requirements_count: int


@dataclass
class MFAMaturityScore:
    """MFA maturity metrics."""
    overall_maturity: RequirementLevel
    enrollment_rate_pct: float
    admin_enforcement_pct: float
    privileged_user_enrollment_pct: float
    gap_count: int


@dataclass
class RiversideThreatMetrics:
    """Security threat metrics and trends."""
    phishing_attempts_30d: int
    malware_detected_30d: int
    spam_filtered_30d: int
    risk_score: float
    trend_direction: str


@dataclass
class TenantRiversideSummary:
    """Compliance summary for individual tenant."""
    tenant_id: str
    tenant_name: str
    overall_compliance_pct: float
    phase_1_completion_pct: float
    phase_2_completion_pct: float
    phase_3_completion_pct: float
    mfa_maturity: MFAMaturityScore
    threat_metrics: RiversideThreatMetrics
    critical_issues_count: int


@dataclass
class RiversideExecutiveSummary:
    """Executive-level summary across all tenants."""
    overall_compliance_pct: float
    phases_complete: list[str]
    completion_by_tenant: list[TenantRiversideSummary]
    mfa_maturity: MFAMaturityScore
    key_gaps: list[str]
    critical_alerts: list[str]
    last_updated: datetime


@dataclass
class AggregateMFAStatus:
    """Aggregated MFA status across environment."""
    total_users: int
    mfa_enforced_users: int
    mfa_available_users: int
    mfa_pending_users: int
    mfa_not_configured_users: int
    enforced_rate_pct: float
    admin_mfa_status: dict[str, MFAStatus]


# Constants

PHASE_1_TARGET_DATE = date(2025, 9, 30)
PHASE_2_TARGET_DATE = date(2025, 12, 31)
PHASE_3_TARGET_DATE = date(2026, 3, 31)

MFA_THRESHOLD_PERCENTAGES = {
    "Emerging": 25,
    "Developing": 50,
    "Mature": 75,
    "Leading": 95,
}


# 72 Riverside Security Requirements
REQUIREMENTS: list[RiversideRequirement] = [
    # MFA Enforcement (9)
    RiversideRequirement(
        id="MFA-001",
        category=RiversideRequirementCategory.MFA_ENFORCEMENT,
        title="Enforce MFA for all tenant administrators",
        description="Multi-factor authentication must be enforced for all users with administrative roles to prevent unauthorized access",
        control_source="NIST 800-171",
        control_reference="3.5.3",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="MFA-002",
        category=RiversideRequirementCategory.MFA_ENFORCEMENT,
        title="Enable per-user MFA for privileged roles",
        description="Enable MFA for users with privileged access rights including Security Admin, Exchange Admin, and SharePoint Admin roles",
        control_source="CIS Microsoft 365",
        control_reference="1.1.1",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="MFA-003",
        category=RiversideRequirementCategory.MFA_ENFORCEMENT,
        title="Disable MFA registration bypass",
        description="Disable the ability for users to bypass MFA registration during sign-in to ensure full coverage",
        control_source="Microsoft Security Baseline",
        control_reference="MFA-002",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="MFA-004",
        category=RiversideRequirementCategory.MFA_ENFORCEMENT,
        title="Deploy Microsoft Authenticator passwordless",
        description="Deploy Microsoft Authenticator app for passwordless sign-in to reduce password-based attack surface",
        control_source="Zero Trust Guidance",
        control_reference="ZT-101",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="MFA-005",
        category=RiversideRequirementCategory.MFA_ENFORCEMENT,
        title="Require MFA for device enrollment",
        description="Enforce MFA requirement before allowing devices to enroll in mobile device management",
        control_source="Entra ID",
        control_reference="Conditional Access",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="MFA-006",
        category=RiversideRequirementCategory.MFA_ENFORCEMENT,
        title="Enforce risk-based MFA triggers",
        description="Configure risk-based conditional access policies to require MFA based on sign-in risk levels",
        control_source="Identity Protection",
        control_reference="Risk Policy",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="MFA-007",
        category=RiversideRequirementCategory.MFA_ENFORCEMENT,
        title="Implement number matching for MFA",
        description="Enable number matching feature in MFA prompts to prevent MFA fatigue attacks",
        control_source="Microsoft Authenticator",
        control_reference="Security Features",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="MFA-008",
        category=RiversideRequirementCategory.MFA_ENFORCEMENT,
        title="MFA for third-party federation",
        description="Require MFA for federated identities accessing Microsoft 365 resources via third-party identity providers",
        control_source="Federated Identity",
        control_reference="Federated-Auth",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    RiversideRequirement(
        id="MFA-009",
        category=RiversideRequirementCategory.MFA_ENFORCEMENT,
        title="Passwordless MFA for all users",
        description="Achieve 100% passwordless authentication using FIDO2 keys, Microsoft Authenticator, or Windows Hello for Business",
        control_source="Zero Trust Maturity",
        control_reference="Passwordless",
        maturity_level=RequirementLevel.LEADING,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    # Conditional Access (9)
    RiversideRequirement(
        id="CA-001",
        category=RiversideRequirementCategory.CONDITIONAL_ACCESS,
        title="Block legacy authentication",
        description="Block legacy authentication protocols (SMTP, POP3, IMAP) that cannot support modern authentication",
        control_source="Conditional Access",
        control_reference="Legacy Blocking",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="CA-002",
        category=RiversideRequirementCategory.CONDITIONAL_ACCESS,
        title="Require device compliance for admin sessions",
        description="Require compliant device status for all administrative role sign-ins to privileged consoles and portals",
        control_source="Admin Privileges",
        control_reference="Device Compliance",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="CA-003",
        category=RiversideRequirementCategory.CONDITIONAL_ACCESS,
        title="Geolocation controls for privileged access",
        description="Implement location-based conditional access policies restricting privileged access to approved countries/regions",
        control_source="Location Controls",
        control_reference="Named Locations",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="CA-004",
        category=RiversideRequirementCategory.CONDITIONAL_ACCESS,
        title="Require MFA for cloud app access",
        description="Require MFA for all users accessing Microsoft 365 cloud applications from outside trusted locations",
        control_source="MFA Requirement",
        control_reference="Cloud Access",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="CA-005",
        category=RiversideRequirementCategory.CONDITIONAL_ACCESS,
        title="App-based conditional access policies",
        description="Create specific conditional access policies for high-risk applications (Entra ID, Exchange, SharePoint, Teams)",
        control_source="App Protection",
        control_reference="Target Apps",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="CA-006",
        category=RiversideRequirementCategory.CONDITIONAL_ACCESS,
        title="Session controls for sensitive apps",
        description="Configure session controls including app enforced restrictions, sign-in frequency, and persistent browser sessions",
        control_source="Session Controls",
        control_reference="Sensitive Apps",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="CA-007",
        category=RiversideRequirementCategory.CONDITIONAL_ACCESS,
        title="Impossible travel detection",
        description="Enable Entra ID sign-in risk detection for impossible travel scenarios indicating credential compromise",
        control_source="Identity Protection",
        control_reference="Risk Detection",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="CA-008",
        category=RiversideRequirementCategory.CONDITIONAL_ACCESS,
        title="Device compliance enforcement on BYOD",
        description="Enforce device compliance policies for personally-owned devices accessing corporate data",
        control_source="BYOD Policy",
        control_reference="Personal Devices",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    RiversideRequirement(
        id="CA-009",
        category=RiversideRequirementCategory.CONDITIONAL_ACCESS,
        title="Just-in-time access enforcement",
        description="Implement just-in-time privileged access with auto-expiration and approval workflows",
        control_source="PIM Integration",
        control_reference="JIT Access",
        maturity_level=RequirementLevel.LEADING,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    # Privileged Access (9)
    RiversideRequirement(
        id="PIM-001",
        category=RiversideRequirementCategory.PRIVILEGED_ACCESS,
        title="Entra ID PIM enabled for global admin",
        description="Enable Privileged Identity Management for Global Administrator role with required approvals for activation",
        control_source="Entra ID PIM",
        control_reference="Privileged Roles",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="PIM-002",
        category=RiversideRequirementCategory.PRIVILEGED_ACCESS,
        title="Global admin role assignment limit",
        description="Limit Global Administrator role assignments to maximum of 5 designated accounts across the tenant",
        control_source="Role Assignment",
        control_reference="Admin Limits",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="PIM-003",
        category=RiversideRequirementCategory.PRIVILEGED_ACCESS,
        title="Require approval for role activation",
        description="Configure approval workflow requiring approval from designated approvers for privileged role activation",
        control_source="PIM Approvals",
        control_reference="Activation Flow",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="PIM-004",
        category=RiversideRequirementCategory.PRIVILEGED_ACCESS,
        title="Role activation time limit",
        description="Set privileged role activation limits between 1-4 hours with automatic deactivation upon expiration",
        control_source="PIM Settings",
        control_reference="Time Limits",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="PIM-005",
        category=RiversideRequirementCategory.PRIVILEGED_ACCESS,
        title="Just-in-time access for critical actions",
        description="Implement elevation requirements for just-in-time access to perform critical administrative actions",
        control_source="Elevation Controls",
        control_reference="Critical Actions",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="PIM-006",
        category=RiversideRequirementCategory.PRIVILEGED_ACCESS,
        title="Role access reviewers rotation",
        description="Implement quarterly rotation of role access reviewers to prevent collusion and control concentration",
        control_source="Access Reviews",
        control_reference="Reviewer Rotation",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="PIM-007",
        category=RiversideRequirementCategory.PRIVILEGED_ACCESS,
        title="Emergency access break-glass account",
        description="Maintain secured emergency break-glass accounts with strict access logging for disaster recovery scenarios",
        control_source="Emergency Access",
        control_reference="Break Glass",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="PIM-008",
        category=RiversideRequirementCategory.PRIVILEGED_ACCESS,
        title="Privileged risk alerts automated responses",
        description="Configure automated remediation actions for detected privileged account risks and anomalies",
        control_source="Automated Response",
        control_reference="Risk Alerts",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    RiversideRequirement(
        id="PIM-009",
        category=RiversideRequirementCategory.PRIVILEGED_ACCESS,
        title="Continuous access evaluation for privileged",
        description="Implement continuous access evaluation for privileged sessions with real-time policy enforcement",
        control_source="Continuous Evaluation",
        control_reference="Real-time Enforcement",
        maturity_level=RequirementLevel.LEADING,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    # Device Compliance (9)
    RiversideRequirement(
        id="DC-001",
        category=RiversideRequirementCategory.DEVICE_COMPLIANCE,
        title="Intune device compliance policies",
        description="Deploy comprehensive Intune compliance policies covering OS version, encryption, health, and security settings",
        control_source="Microsoft Intune",
        control_reference="Compliance Policies",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DC-002",
        category=RiversideRequirementCategory.DEVICE_COMPLIANCE,
        title="Blocked non-compliant devices",
        description="Configure conditional access to block devices failing compliance checks from accessing corporate resources",
        control_source="Device Blocking",
        control_reference="Non-compliant Devices",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DC-003",
        category=RiversideRequirementCategory.DEVICE_COMPLIANCE,
        title="Supported OS version enforcement",
        description="Enforce minimum supported OS versions and block devices running unsupported or outdated operating systems",
        control_source="OS Compliance",
        control_reference="Version Requirements",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DC-004",
        category=RiversideRequirementCategory.DEVICE_COMPLIANCE,
        title="Disk encryption enforcement",
        description="Require BitLocker (Windows) or FileVault (Mac) encryption for all managed devices",
        control_source="Encryption Policy",
        control_reference="Data Protection",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DC-005",
        category=RiversideRequirementCategory.DEVICE_COMPLIANCE,
        title="Application allow-list enforcement",
        description="Implement application allow-listing policies blocking unauthorized applications on managed devices",
        control_source="App Control",
        control_reference="Allow-list Policy",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DC-006",
        category=RiversideRequirementCategory.DEVICE_COMPLIANCE,
        title="Compliant BYOD workflow",
        description="Establish workflow for registering and validating personally-owned devices before corporate access",
        control_source="BYOD Management",
        control_reference="Personal Device Flow",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DC-007",
        category=RiversideRequirementCategory.DEVICE_COMPLIANCE,
        title="Device attestation enforcement",
        description="Require device attestation validating compliance posture before granting access to sensitive applications",
        control_source="Attestation Policy",
        control_reference="Device Health",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DC-008",
        category=RiversideRequirementCategory.DEVICE_COMPLIANCE,
        title="Secure boot enforcement",
        description="Require Secure Boot and TPM 2.0 on all Windows devices for enhanced boot-time security",
        control_source="Boot Security",
        control_reference="Secure Boot",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DC-009",
        category=RiversideRequirementCategory.DEVICE_COMPLIANCE,
        title="Zero Trust device health scoring",
        description="Implement dynamic device health scoring influencing access decisions in real-time",
        control_source="Zero Trust Device",
        control_reference="Health Scoring",
        maturity_level=RequirementLevel.LEADING,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    # Threat Management (9)
    RiversideRequirement(
        id="TM-001",
        category=RiversideRequirementCategory.THREAT_MANAGEMENT,
        title="Microsoft Defender for Office 365",
        description="Deploy Defender for Office 365 Plan 2 with advanced threat protection for email and collaboration",
        control_source="Microsoft Defender",
        control_reference="MDO-365",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="TM-002",
        category=RiversideRequirementCategory.THREAT_MANAGEMENT,
        title="Anti-phishing policies",
        description="Configure anti-phishing policies with impersonation protection, spoof intelligence, and user education",
        control_source="Anti-phishing",
        control_reference="Phish Policies",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="TM-003",
        category=RiversideRequirementCategory.THREAT_MANAGEMENT,
        title="Safe Links enabled",
        description="Enable Safe Links protection for email and Office apps with time-of-click protection and URL rewrites",
        control_source="Safe Links",
        control_reference="Link Protection",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="TM-004",
        category=RiversideRequirementCategory.THREAT_MANAGEMENT,
        title="Safe Attachments enabled",
        description="Enable Safe Attachments scanning in detonation environment before delivering email attachments",
        control_source="Safe Attachments",
        control_reference="Attachment Scanning",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="TM-005",
        category=RiversideRequirementCategory.THREAT_MANAGEMENT,
        title="Automated incident response",
        description="Deploy automated incident response playbooks for common attack patterns and threats",
        control_source="AIR Playbooks",
        control_reference="Automation",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="TM-006",
        category=RiversideRequirementCategory.THREAT_MANAGEMENT,
        title="Threat hunting queries",
        description="Implement threat hunting queries in Microsoft Defender to proactively search for threats",
        control_source="Threat Hunting",
        control_reference="Advanced Hunting",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="TM-007",
        category=RiversideRequirementCategory.THREAT_MANAGEMENT,
        title="Simulation-based training",
        description="Implement security awareness through phishing simulations and targeted user training programs",
        control_source="Attack Simulation",
        control_reference="User Training",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="TM-008",
        category=RiversideRequirementCategory.THREAT_MANAGEMENT,
        title="XDR integration",
        description="Integrate Microsoft Defender XDR across endpoint, identity, and cloud for unified security operations",
        control_source="Defender XDR",
        control_reference="Unified Detection",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    RiversideRequirement(
        id="TM-009",
        category=RiversideRequirementCategory.THREAT_MANAGEMENT,
        title="AI-driven threat analytics",
        description="Deploy AI-powered threat analytics for anomaly detection, behavioral analysis, and predictive intelligence",
        control_source="AI Security",
        control_reference="Threat Intelligence",
        maturity_level=RequirementLevel.LEADING,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    # Data Loss Prevention (9)
    RiversideRequirement(
        id="DLP-001",
        category=RiversideRequirementCategory.DATA_LOSS_PREVENTION,
        title="DLP policies for sensitive data",
        description="Create DLP policies protecting PII, PHI, financial documents, and confidential corporate information",
        control_source="Microsoft Purview",
        control_reference="DLP Policies",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DLP-002",
        category=RiversideRequirementCategory.DATA_LOSS_PREVENTION,
        title="Document fingerprinting",
        description="Deploy exact data match (EDM) and document fingerprinting for template-based sensitive data detection",
        control_source="DLP Fingerprinting",
        control_reference="Data Matching",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DLP-003",
        category=RiversideRequirementCategory.DATA_LOSS_PREVENTION,
        title="Automatic classification",
        description="Enable trainable classifiers and automatic labeling for sensitive content across Microsoft 365",
        control_source="Data Classification",
        control_reference="Auto-labeling",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DLP-004",
        category=RiversideRequirementCategory.DATA_LOSS_PREVENTION,
        title="Endpoint DLP deployed",
        description="Deploy Endpoint DLP agents for monitoring and protecting data on Windows, Mac, and Linux devices",
        control_source="Endpoint DLP",
        control_reference="Endpoint Protection",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DLP-005",
        category=RiversideRequirementCategory.DATA_LOSS_PREVENTION,
        title="Cloud app security integration",
        description="Integrate Microsoft Cloud App Security (MCAS) for shadow IT discovery and CASB capabilities",
        control_source="Cloud App Security",
        control_reference="CASB Integration",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DLP-006",
        category=RiversideRequirementCategory.DATA_LOSS_PREVENTION,
        title="Data encryption enforced",
        description="Enforce encryption at rest and in transit for all Microsoft 365 services and customer data",
        control_source="Data Encryption",
        control_reference="Encryption Keys",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DLP-007",
        category=RiversideRequirementCategory.DATA_LOSS_PREVENTION,
        title="Data residency controls",
        description="Configure data residency and multi-geo controls ensuring data storage compliance with regional requirements",
        control_source="Data Residency",
        control_reference="Geo Controls",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DLP-008",
        category=RiversideRequirementCategory.DATA_LOSS_PREVENTION,
        title="Insider risk monitoring",
        description="Deploy insider risk management to monitor for data exfiltration, inappropriate access, and policy violations",
        control_source="Insider Risk",
        control_reference="User Monitoring",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    RiversideRequirement(
        id="DLP-009",
        category=RiversideRequirementCategory.DATA_LOSS_PREVENTION,
        title="Continuous data loss monitoring",
        description="Implement real-time continuous monitoring for data loss risks with automated alerting and containment",
        control_source="Continuous DLP",
        control_reference="Real-time Monitoring",
        maturity_level=RequirementLevel.LEADING,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    # Logging & Monitoring (9)
    RiversideRequirement(
        id="LM-001",
        category=RiversideRequirementCategory.LOGGING_MONITORING,
        title="Unified audit log enabled",
        description="Enable unified audit log recording across all Microsoft 365 services for comprehensive visibility",
        control_source="Compliance Center",
        control_reference="Audit Logging",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="LM-002",
        category=RiversideRequirementCategory.LOGGING_MONITORING,
        title="Log retention 365 days",
        description="Configure 365-day log retention for audit logs meeting regulatory compliance requirements",
        control_source="Log Retention",
        control_reference="Retention Policy",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="LM-003",
        category=RiversideRequirementCategory.LOGGING_MONITORING,
        title="Alert configuration baseline",
        description="Set up baseline alerting for critical security events including admin operations, suspicious sign-ins, and data access",
        control_source="Alert Baseline",
        control_reference="Security Alerts",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="LM-004",
        category=RiversideRequirementCategory.LOGGING_MONITORING,
        title="Sentinel log analytics integration",
        description="Integrate unified logs with Microsoft Sentinel for centralized SIEM collection and analysis",
        control_source="Microsoft Sentinel",
        control_reference="SIEM Ingestion",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="LM-005",
        category=RiversideRequirementCategory.LOGGING_MONITORING,
        title="Custom workbooks deployed",
        description="Deploy custom Azure Monitor workbooks for Riverside compliance dashboards and status tracking",
        control_source="Azure Monitor",
        control_reference="Custom Dashboards",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="LM-006",
        category=RiversideRequirementCategory.LOGGING_MONITORING,
        title="Anomaly detection rules",
        description="Configure Sentinel analytics rules for anomaly detection, behavioral baselines, and threat patterns",
        control_source="Analytics Rules",
        control_reference="Anomaly Detection",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="LM-007",
        category=RiversideRequirementCategory.LOGGING_MONITORING,
        title="SIEM centralization",
        description="Achieve centralized SIEM for monitoring across Microsoft 365, endpoints, network, and cloud services",
        control_source="SIEM Centralization",
        control_reference="Log Consolidation",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="LM-008",
        category=RiversideRequirementCategory.LOGGING_MONITORING,
        title="Automated playbooks",
        description="Deploy Azure Logic Apps and Sentinel automation playbooks for standardized incident response workflows",
        control_source="Automation",
        control_reference="Playbooks",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    RiversideRequirement(
        id="LM-009",
        category=RiversideRequirementCategory.LOGGING_MONITORING,
        title="Advanced hunting KQL queries",
        description="Implement advanced hunting KQL query library for proactive threat investigation and incident response",
        control_source="Advanced Hunting",
        control_reference="KQL Library",
        maturity_level=RequirementLevel.LEADING,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    # Incident Response (9)
    RiversideRequirement(
        id="IR-001",
        category=RiversideRequirementCategory.INCIDENT_RESPONSE,
        title="Incident response playbook",
        description="Document comprehensive incident response playbooks for ransomware, phishing, data breach, and insider threats",
        control_source="NIST CSF",
        control_reference="IR-PL001",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="IR-002",
        category=RiversideRequirementCategory.INCIDENT_RESPONSE,
        title="On-call rotation defined",
        description="Establish on-call rotation schedule with designated security responders for 24/7 incident coverage",
        control_source="Duty Roster",
        control_reference="On-call Schedule",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="IR-003",
        category=RiversideRequirementCategory.INCIDENT_RESPONSE,
        title="Escalation matrix defined",
        description="Document escalation matrix defining notification paths, stakeholders, and SLAs for different severity levels",
        control_source="Escalation Policy",
        control_reference="Response Matrix",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="IR-004",
        category=RiversideRequirementCategory.INCIDENT_RESPONSE,
        title="Communication templates",
        description="Create incident communication templates for internal stakeholders, customers, and regulatory notifications",
        control_source="Communication",
        control_reference="Template Library",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_1_Q3_2025,
        target_date=PHASE_1_TARGET_DATE,
    ),
    RiversideRequirement(
        id="IR-005",
        category=RiversideRequirementCategory.INCIDENT_RESPONSE,
        title="Automated containment actions",
        description="Implement automated incident containment including account suspension, device isolation, and conditional access enforcement",
        control_source="Automated Response",
        control_reference="Containment",
        maturity_level=RequirementLevel.EMERGING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="IR-006",
        category=RiversideRequirementCategory.INCIDENT_RESPONSE,
        title="Forensic data preservation",
        description="Establish procedures for forensic data preservation, evidence collection, and chain of custody",
        control_source="Forensics",
        control_reference="Evidence Collection",
        maturity_level=RequirementLevel.DEVELOPING,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="IR-007",
        category=RiversideRequirementCategory.INCIDENT_RESPONSE,
        title="Post-incident reviews",
        description="Conduct structured post-incident reviews with root cause analysis and remediation tracking",
        control_source="PIR Process",
        control_reference="Incident Review",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_2_Q4_2025,
        target_date=PHASE_2_TARGET_DATE,
    ),
    RiversideRequirement(
        id="IR-008",
        category=RiversideRequirementCategory.INCIDENT_RESPONSE,
        title="Root cause analysis automation",
        description="Implement automated root cause analysis correlation and timeline reconstruction for incident investigation",
        control_source="RCA Automation",
        control_reference="Investigation Tools",
        maturity_level=RequirementLevel.MATURE,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
    RiversideRequirement(
        id="IR-009",
        category=RiversideRequirementCategory.INCIDENT_RESPONSE,
        title="Self-healing automated responses",
        description="Deploy self-healing capabilities for automatic risk mitigation and incident remediation across the environment",
        control_source="Self-healing",
        control_reference="Autonomic Security",
        maturity_level=RequirementLevel.LEADING,
        phase=DeadlinePhase.PHASE_3_Q1_2026,
        target_date=PHASE_3_TARGET_DATE,
    ),
]


# Service Tenant configurations
TENANTS: dict[str, str] = {
    "htt": "Health Technology Trust",
    "bcc": "Bio-Care Corporation",
    "fn": "Future Nations",
    "tll": "Tech Lab Logistics",
    "dce": "Digital Cloud Enterprises",
}


class RiversideService:
    """Service for managing Riverside compliance governance across Microsoft 365 tenants."""

    def __init__(self, db: "Session") -> None:
        """Initialize RiversideService with database session."""
        self.db = db
        self._requirement_map: dict[str, RiversideRequirement] = {
            req.id: req for req in REQUIREMENTS
        }

    def get_compliance_summary(self) -> RiversideComplianceSummary:
        """Calculate overall compliance summary across all requirements."""
        total_requirements = len(REQUIREMENTS)
        completed_requirements = sum(
            1
            for req in REQUIREMENTS
            if req.status == RequirementStatus.COMPLETED
        )

        overall_compliance_pct = (
            (completed_requirements / total_requirements) * 100.0
            if total_requirements > 0
            else 0.0
        )
        target_compliance_pct = 75.0  # Target: 75% maturity goal

        return RiversideComplianceSummary(
            overall_compliance_pct=overall_compliance_pct,
            target_compliance_pct=target_compliance_pct,
            completed_requirements_count=completed_requirements,
            total_requirements_count=total_requirements,
        )

    def get_mfa_maturity(self) -> MFAMaturityScore:
        """Calculate MFA maturity score across the environment."""
        # This would integrate with actual MFA data from Graph/Entra ID
        # Default values shown for demonstration
        total_users = 2500  # Total across all tenants
        mfa_enforced_users = 1875
        mfa_available_users = 375
        mfa_pending_users = 150
        mfa_not_configured_users = 100

        enforced_rate_pct = (
            (mfa_enforced_users + mfa_available_users) / total_users * 100.0
            if total_users > 0
            else 0.0
        )

        admin_enforcement_pct = 95.0  # Assumed from requirement MFA-001
        privileged_user_enrollment_pct = 82.5  # Assumed from requirement MFA-002

        # Calculate gaps - count users without MFA protection
        gap_count = mfa_pending_users + mfa_not_configured_users

        overall_maturity = self.calculate_maturity_score(
            {"enrollment_rate_pct": enforced_rate_pct}
        )

        return MFAMaturityScore(
            overall_maturity=overall_maturity,
            enrollment_rate_pct=enforced_rate_pct,
            admin_enforcement_pct=admin_enforcement_pct,
            privileged_user_enrollment_pct=privileged_user_enrollment_pct,
            gap_count=gap_count,
        )

    def get_threat_metrics(self) -> RiversideThreatMetrics:
        """Retrieve threat metrics showing security posture."""
        # This would pull from Microsoft Defender XDR APIs
        # Example values demonstrating the data structure
        return RiversideThreatMetrics(
            phishing_attempts_30d=1247,
            malware_detected_30d=89,
            spam_filtered_30d=156842,
            risk_score=42.5,  # Normalized 0-100 score
            trend_direction="decreasing",  # Risk trend showing improvement
        )

    def get_requirement_details(
        self, requirement_id: str
    ) -> RiversideRequirement | None:
        """Retrieve detailed information for a specific requirement."""
        return self._requirement_map.get(requirement_id)

    def get_tenant_breakdown(self) -> list[TenantRiversideSummary]:
        """Get compliance breakdown by individual tenant."""
        tenant_summaries: list[TenantRiversideSummary] = []

        for tenant_id, tenant_name in TENANTS.items():
            # Calculate per-tenant compliance
            # In production, this query tenant-specific metrics
            overall_compliance_pct = 63.4 + (hash(tenant_id) % 20)  # Staggered for demo
            phase_1_completion_pct = 78.2 + (hash(tenant_id) % 15)
            phase_2_completion_pct = 45.6 + (hash(tenant_id) % 12)
            phase_3_completion_pct = 22.1 + (hash(tenant_id) % 10)

            mfa_maturity = MFAMaturityScore(
                overall_maturity=self.calculate_maturity_score({
                    "enrollment_rate_pct": phase_1_completion_pct
                }),
                enrollment_rate_pct=phase_1_completion_pct,
                admin_enforcement_pct=92.0 + (hash(tenant_id) % 8),
                privileged_user_enrollment_pct=78.5 + (hash(tenant_id) % 10),
                gap_count=25 + (hash(tenant_id) % 15),
            )

            threat_metrics = RiversideThreatMetrics(
                phishing_attempts_30d=150 + (hash(tenant_id) % 50),
                malware_detected_30d=12 + (hash(tenant_id) % 7),
                spam_filtered_30d=25000 + (hash(tenant_id) % 5000),
                risk_score=40.0 + (hash(tenant_id) % 15),
                trend_direction="stable",
            )

            critical_issues_count = 3 + (hash(tenant_id) % 5)

            tenant_summaries.append(
                TenantRiversideSummary(
                    tenant_id=tenant_id,
                    tenant_name=tenant_name,
                    overall_compliance_pct=overall_compliance_pct,
                    phase_1_completion_pct=phase_1_completion_pct,
                    phase_2_completion_pct=phase_2_completion_pct,
                    phase_3_completion_pct=phase_3_completion_pct,
                    mfa_maturity=mfa_maturity,
                    threat_metrics=threat_metrics,
                    critical_issues_count=critical_issues_count,
                )
            )

        return tenant_summaries

    def get_executive_summary(self) -> RiversideExecutiveSummary:
        """Generate executive-level summary across all tenants."""
        compliance = self.get_compliance_summary()
        tenant_breakdown = self.get_tenant_breakdown()
        mfa_maturity = self.get_mfa_maturity()
        gaps = self.identify_gaps()

        # Determine which phases are complete
        phases_complete: list[str] = []
        if tenant_breakdown:
            avg_phase_1 = (
                sum(t.phase_1_completion_pct for t in tenant_breakdown)
                / len(tenant_breakdown)
            )
            avg_phase_2 = (
                sum(t.phase_2_completion_pct for t in tenant_breakdown)
                / len(tenant_breakdown)
            )
            avg_phase_3 = (
                sum(t.phase_3_completion_pct for t in tenant_breakdown)
                / len(tenant_breakdown)
            )
            if avg_phase_1 >= 90:
                phases_complete.append("Phase 1")
            if avg_phase_2 >= 90:
                phases_complete.append("Phase 2")
            if avg_phase_3 >= 90:
                phases_complete.append("Phase 3")

        # Identify critical alerts
        critical_alerts: list[str] = []
        for tenant in tenant_breakdown:
            if tenant.overall_compliance_pct < 50:
                critical_alerts.append(
                    f"CRITICAL: {tenant.tenant_name} compliance at {tenant.overall_compliance_pct:.1f}%"
                )

            if tenant.mfa_maturity.enrollment_rate_pct < 60:
                critical_alerts.append(
                    f"{tenant.tenant_name} MFA enrollment below target ({tenant.mfa_maturity.enrollment_rate_pct:.1f}%)"
                )

        if not critical_alerts:
            critical_alerts = ["No critical security alerts at this time"]

        return RiversideExecutiveSummary(
            overall_compliance_pct=compliance.overall_compliance_pct,
            phases_complete=phases_complete,
            completion_by_tenant=tenant_breakdown,
            mfa_maturity=mfa_maturity,
            key_gaps=gaps,
            critical_alerts=critical_alerts,
            last_updated=datetime.utcnow(),
        )

    def calculate_maturity_score(self, data: dict) -> RequirementLevel:
        """Calculate maturity level based on provided metrics."""
        enrollment_rate_pct = data.get("enrollment_rate_pct", 0.0)

        if enrollment_rate_pct >= MFA_THRESHOLD_PERCENTAGES["Leading"]:
            return RequirementLevel.LEADING
        elif enrollment_rate_pct >= MFA_THRESHOLD_PERCENTAGES["Mature"]:
            return RequirementLevel.MATURE
        elif enrollment_rate_pct >= MFA_THRESHOLD_PERCENTAGES["Developing"]:
            return RequirementLevel.DEVELOPING
        else:
            return RequirementLevel.EMERGING

    def identify_gaps(self) -> list[str]:
        """Identify key compliance gaps across all requirements."""
        gaps: list[str] = []
        now = date.today()

        # Identify Phase 1 gaps approaching or past deadline
        for req in REQUIREMENTS:
            if (
                req.target_date
                and req.target_date < now
                and req.phase == DeadlinePhase.PHASE_1_Q3_2025
                and req.status != RequirementStatus.COMPLETED
            ):
                gaps.append(
                    f"({req.id}) Phase 1 overdue: {req.title} (target: {req.target_date})"
                )

        # Identify Phase 2 overdue requirements
        for req in REQUIREMENTS:
            if (
                req.target_date
                and req.target_date < now
                and req.phase == DeadlinePhase.PHASE_2_Q4_2025
                and req.status != RequirementStatus.COMPLETED
            ):
                gaps.append(
                    f"({req.id}) Phase 2 overdue: {req.title} (target: {req.target_date})"
                )

        # Identify MFA enforcement gaps
        mfa_reqs = [
            req for req in REQUIREMENTS
            if req.category == RiversideRequirementCategory.MFA_ENFORCEMENT
        ]
        mfa_overdue = [
            f"({req.id}) MFA requirement incomplete: {req.title}"
            for req in mfa_reqs
            if req.status != RequirementStatus.COMPLETED and req.target_date and req.target_date < now
        ]
        gaps.extend(mfa_overdue[:5])  # Limit to top 5 MFA gaps

        return gaps

    def get_deadline_watch(self) -> list[tuple[str, date | None, dict[str, RequirementStatus]]]:
        """Get requirements approaching deadlines with status by tenant."""
        deadline_items: list[tuple[str, date | None, dict[str, RequirementStatus]]] = []
        now = date.today()
        window_days = 14  # Alert period in days

        for req in REQUIREMENTS:
            if not req.target_date:
                continue

            # Filter to requirements due within 14 days or past due
            days_until_due = (req.target_date - now).days
            is_due_soon = -7 <= days_until_due <= window_days
            if not is_due_soon:
                continue

            # Get simulated per-tenant status
            per_tenant_status: dict[str, RequirementStatus] = {}
            for tenant_id, tenant_name in TENANTS.items():
                # In production, query actual data
                # Staggered values for demonstration
                if req.phase == DeadlinePhase.PHASE_1_Q3_2025:
                    per_tenant_status[tenant_id] = (
                        RequirementStatus.COMPLETED
                        if hash(tenant_id + req.id) % 2 == 0
                        else RequirementStatus.IN_PROGRESS
                    )
                elif req.phase == DeadlinePhase.PHASE_2_Q4_2025:
                    per_tenant_status[tenant_id] = RequirementStatus.IN_PROGRESS
                else:
                    per_tenant_status[tenant_id] = RequirementStatus.NOT_STARTED

            deadline_items.append((req.id, req.target_date, per_tenant_status))
        return deadline_items

    def update_requirement_status(
        self,
        requirement_id: str,
        status: RequirementStatus,
        evidence_notes: str | None = None,
    ) -> bool:
        """Update the status of a specific requirement."""
        req = self.get_requirement_details(requirement_id)
        if not req:
            return False

        req.status = status
        if status == RequirementStatus.COMPLETED:
            req.evidence_count += 1

        # Log evidence notes (would store in database)
        return True

    def get_requirements_by_category(
        self, category: RiversideRequirementCategory
    ) -> list[RiversideRequirement]:
        """Get all requirements for a specific category."""
        return [req for req in REQUIREMENTS if req.category == category]

    def get_requirements_by_phase(
        self, phase: DeadlinePhase
    ) -> list[RiversideRequirement]:
        """Get all requirements for a specific phase."""
        return [req for req in REQUIREMENTS if req.phase == phase]

    def get_requirements_by_maturity(
        self, maturity: RequirementLevel
    ) -> list[RiversideRequirement]:
        """Get all requirements for a specific maturity level."""
        return [req for req in REQUIREMENTS if req.maturity_level == maturity]

    def get_aggregate_mfa_status(self) -> AggregateMFAStatus:
        """Get aggregate MFA status across all tenants."""
        # Mock data for demonstration
        admin_mfa_status: dict[str, MFAStatus] = dict.fromkeys(TENANTS.keys(), MFAStatus.ENFORCED)

        return AggregateMFAStatus(
            total_users=2500,
            mfa_enforced_users=1875,
            mfa_available_users=375,
            mfa_pending_users=150,
            mfa_not_configured_users=100,
            enforced_rate_pct=90.0,
            admin_mfa_status=admin_mfa_status,
        )
