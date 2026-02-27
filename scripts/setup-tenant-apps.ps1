#requires -Version 7.0
#requires -Modules Microsoft.Graph.Applications, Microsoft.Graph.Authentication, Az.KeyVault

<#
.SYNOPSIS
    Riverside Governance Platform - Multi-Tenant App Registration Setup

.DESCRIPTION
    Automates the creation of app registrations across 4 Riverside tenants:
    - HTT (Huntington Technology)
    - BCC (Beach Cities Consulting)
    - FN (Fulton & Nieman)
    - TLL (Tower Legal)

    Creates app registration with Graph API permissions, generates client secrets,
    stores in Key Vault, grants admin consent, and exports configuration.

.PARAMETER ResumeFrom
    Resume from a specific tenant name (HTT, BCC, FN, or TLL)

.PARAMETER SkipConsent
    Skip the admin consent step (useful if you don't have global admin)

.PARAMETER SecretExpiryYears
    Number of years until client secret expires (default: 1)

.PARAMETER KeyVaultName
    Azure Key Vault name for storing secrets (optional)

.PARAMETER OutputPath
    Path for .env output file (default: ./riverside-config.env)

.EXAMPLE
    # Interactive setup for all tenants
    .\setup-tenant-apps.ps1

.EXAMPLE
    # Resume from BCC tenant with 2-year secret expiry
    .\setup-tenant-apps.ps1 -ResumeFrom "BCC" -SecretExpiryYears 2

.EXAMPLE
    # Skip consent and use custom Key Vault
    .\setup-tenant-apps.ps1 -SkipConsent -KeyVaultName "my-keyvault"

.NOTES
    Author: Riverside DevOps
    Version: 1.0
    Requires: 
      - PowerShell 7+
      - Microsoft.Graph.Applications module
      - Microsoft.Graph.Authentication module
      - Az.KeyVault module (optional, for Key Vault storage)
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter()]
    [ValidateSet("HTT", "BCC", "FN", "TLL")]
    [string]$ResumeFrom,

    [Parameter()]
    [switch]$SkipConsent,

    [Parameter()]
    [ValidateRange(1, 2)]
    [int]$SecretExpiryYears = 1,

    [Parameter()]
    [string]$KeyVaultName = "riverside-kv-governance",

    [Parameter()]
    [string]$OutputPath = "./riverside-config.env",

    [Parameter()]
    [string]$ProgressFile = "./.setup-progress.json"
)

#region Configuration

$script:Tenants = @(
    @{
        Name       = "HTT"
        TenantId   = "0c0e35dc-188a-4eb3-b8ba-61752154b407"
        Description = "Huntington Technology"
    }
    @{
        Name       = "BCC"
        TenantId   = "b5380912-79ec-452d-a6ca-6d897b19b294"
        Description = "Beach Cities Consulting"
    }
    @{
        Name       = "FN"
        TenantId   = "98723287-044b-4bbb-9294-19857d4128a0"
        Description = "Fulton & Nieman"
    }
    @{
        Name       = "TLL"
        TenantId   = "3c7d2bf3-b597-4766-b5cb-2b489c2904d6"
        Description = "Tower Legal"
    }
)

$script:AppName = "Riverside-Governance-Platform"
$script:RequiredPermissions = @(
    # Microsoft Graph API Permissions
    @{Resource = "Microsoft Graph"; Id = "b357db82-186d-4c42-9d72-3029f97259bf"; Type = "Role"; Name = "Reports.Read.All" },         # Application: Read all reports
    @{Resource = "Microsoft Graph"; Id = "95138ef0-6e1d-4674-af51-60b6c63015a5"; Type = "Role"; Name = "SecurityEvents.Read.All" }, # Application: Read security events
    @{Resource = "Microsoft Graph"; Id = "dbb74f18-5761-4a50-999b-3ef16dcebd12"; Type = "Role"; Name = "Domain.Read.All" },         # Application: Read domains
    @{Resource = "Microsoft Graph"; Id = "7ab1d382-f21e-4acd-a64e-f761e3816c87"; Type = "Role"; Name = "Directory.Read.All" }       # Application: Read directory
)

#endregion

#region Utility Functions

function Write-ProgressHeader {
    param([string]$Title)
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan -BackgroundColor Black
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

function Write-Status {
    param(
        [string]$Message,
        [ValidateSet("Info", "Success", "Warning", "Error", "Step")]
        [string]$Type = "Info"
    )

    $prefix = switch ($Type) {
        "Success" { "[✓]"; $color = "Green" }
        "Warning" { "[!]"; $color = "Yellow" }
        "Error" { "[✗]"; $color = "Red" }
        "Step" { "[→]"; $color = "Magenta" }
        default { "[i]"; $color = "Blue" }
    }

    Write-Host "  $prefix " -NoNewline -ForegroundColor $color
    Write-Host $Message
}

function Test-Prerequisites {
    Write-ProgressHeader "Checking Prerequisites"

    # Check PowerShell version
    if ($PSVersionTable.PSVersion.Major -lt 7) {
        throw "PowerShell 7+ required. Current version: $($PSVersionTable.PSVersion)"
    }
    Write-Status "PowerShell version: $($PSVersionTable.PSVersion)" "Success"

    # Check required modules
    $requiredModules = @("Microsoft.Graph.Authentication", "Microsoft.Graph.Applications")
    foreach ($module in $requiredModules) {
        if (-not (Get-Module -ListAvailable -Name $module)) {
            Write-Status "Module '$module' not found. Installing..." "Warning"
            try {
                Install-Module -Name $module -Force -Scope CurrentUser -AllowClobber
                Write-Status "Installed $module" "Success"
            }
            catch {
                throw "Failed to install $module. Run: Install-Module $module -Scope CurrentUser"
            }
        }
        else {
            Write-Status "Module '$module' found" "Success"
        }
    }

    Write-Status "All prerequisites satisfied!" "Success"
}

function Get-Progress {
    if (Test-Path $ProgressFile) {
        return Get-Content $ProgressFile | ConvertFrom-Json
    }
    return @{ CompletedTenants = @(); CurrentTenant = $null; Step = $null }
}

function Save-Progress {
    param(
        [string]$TenantName = $null,
        [string]$Step = $null,
        [switch]$MarkComplete
    )

    $progress = Get-Progress

    if ($MarkComplete -and $TenantName -and $progress.CompletedTenants -notcontains $TenantName) {
        $progress.CompletedTenants += $TenantName
        $progress.CurrentTenant = $null
        $progress.Step = $null
    }
    else {
        $progress.CurrentTenant = $TenantName
        $progress.Step = $Step
    }

    $progress | ConvertTo-Json -Depth 3 | Set-Content $ProgressFile
}

function Clear-Progress {
    if (Test-Path $ProgressFile) {
        Remove-Item $ProgressFile -Force
        Write-Status "Cleared progress file" "Info"
    }
}

#endregion

#region Tenant Setup Functions

function Connect-Tenant {
    param([hashtable]$Tenant)

    Write-ProgressHeader "Connecting to $($Tenant.Name) - $($Tenant.Description)"
    Write-Status "Tenant ID: $($Tenant.TenantId)" "Info"

    $scopes = @(
        "Application.ReadWrite.All",
        "Directory.ReadWrite.All",
        "AppRoleAssignment.ReadWrite.All"
    )

    if (-not $SkipConsent) {
        $scopes += "DelegatedPermissionGrant.ReadWrite.All"
    }

    Write-Status "Opening browser for authentication..." "Step"
    Write-Host "  Please sign in with Global Admin credentials for $($Tenant.Name)" -ForegroundColor Yellow

    try {
        Connect-MgGraph -TenantId $Tenant.TenantId -Scopes $scopes -NoWelcome
        $context = Get-MgContext
        Write-Status "Connected as: $($context.Account)" "Success"
        return $true
    }
    catch {
        Write-Status "Failed to connect: $_" "Error"
        return $false
    }
}

function New-AppRegistration {
    param([hashtable]$Tenant)

    Write-ProgressHeader "Creating App Registration for $($Tenant.Name)"
    Save-Progress -TenantName $Tenant.Name -Step "CreatingApp"

    # Check if app already exists
    $existingApp = Get-MgApplication -Filter "displayName eq '$script:AppName'" -ErrorAction SilentlyContinue
    if ($existingApp) {
        Write-Status "App '$script:AppName' already exists" "Warning"
        $confirmation = Read-Host "  Delete existing app and recreate? (y/n)"
        if ($confirmation -eq 'y') {
            Remove-MgApplication -ApplicationId $existingApp.Id
            Write-Status "Deleted existing app" "Success"
        }
        else {
            Write-Status "Using existing app" "Info"
            return $existingApp
        }
    }

    try {
        # Create app registration
        $appParams = @{
            DisplayName            = $script:AppName
            SignInAudience         = "AzureADMyOrg"
            RequiredResourceAccess = @(
                @{
                    ResourceAppId  = "00000003-0000-0000-c000-000000000000" # Microsoft Graph
                    ResourceAccess = $script:RequiredPermissions | ForEach-Object {
                        @{Id = $_.Id; Type = $_.Type }
                    }
                }
            )
        }

        $app = New-MgApplication @appParams
        Write-Status "Created app registration: $($app.AppId)" "Success"

        # Create service principal for admin consent
        $sp = New-MgServicePrincipal -AppId $app.AppId
        Write-Status "Created service principal: $($sp.Id)" "Success"

        return $app
    }
    catch {
        Write-Status "Failed to create app: $_" "Error"
        throw
    }
}

function New-ClientSecret {
    param(
        [hashtable]$Tenant,
        [string]$AppId
    )

    Write-ProgressHeader "Creating Client Secret for $($Tenant.Name)"
    Save-Progress -TenantName $Tenant.Name -Step "CreatingSecret"

    try {
        $endDate = (Get-Date).AddYears($SecretExpiryYears)
        $displayName = "Riverside-Governance-Secret-$(Get-Date -Format 'yyyyMMdd')"

        $secret = Add-MgApplicationPassword -ApplicationId $AppId -PasswordCredential @{
            DisplayName = $displayName
            EndDateTime = $endDate
        }

        Write-Status "Created client secret (expires: $($endDate.ToString('yyyy-MM-dd')))" "Success"
        Write-Status "IMPORTANT: Secret will only be shown once!" "Warning"

        return $secret.SecretText
    }
    catch {
        Write-Status "Failed to create client secret: $_" "Error"
        throw
    }
}

function Grant-AdminConsent {
    param(
        [hashtable]$Tenant,
        [string]$AppId
    )

    if ($SkipConsent) {
        Write-Status "Skipping admin consent (SkipConsent flag set)" "Warning"
        return
    }

    Write-ProgressHeader "Granting Admin Consent for $($Tenant.Name)"
    Save-Progress -TenantName $Tenant.Name -Step "GrantingConsent"

    try {
        $sp = Get-MgServicePrincipal -Filter "appId eq '$AppId'"
        $graphSp = Get-MgServicePrincipal -Filter "appId eq '00000003-0000-0000-c000-000000000000'"

        foreach ($permission in $script:RequiredPermissions) {
            $appRole = $graphSp.AppRoles | Where-Object { $_.Value -eq $permission.Name }

            if ($appRole) {
                $assignment = @{
                    PrincipalId = $sp.Id
                    ResourceId  = $graphSp.Id
                    AppRoleId   = $appRole.Id
                }

                New-MgServicePrincipalAppRoleAssignment `
                    -ServicePrincipalId $sp.Id `
                    -BodyParameter $assignment | Out-Null

                Write-Status "Granted: $($permission.Name)" "Success"
            }
        }

        Write-Status "Admin consent granted successfully!" "Success"
    }
    catch {
        Write-Status "Failed to grant admin consent: $_" "Error"
        Write-Status "You may need to grant consent manually in Azure Portal" "Warning"
    }
}

function Test-GraphConnection {
    param(
        [hashtable]$Tenant,
        [string]$AppId,
        [string]$ClientSecret
    )

    Write-ProgressHeader "Verifying Graph API Connection for $($Tenant.Name)"

    try {
        # Disconnect current session and test with app credentials
        Disconnect-MgGraph | Out-Null

        $tokenUrl = "https://login.microsoftonline.com/$($Tenant.TenantId)/oauth2/v2.0/token"
        $body = @{
            grant_type    = "client_credentials"
            client_id     = $AppId
            client_secret = $ClientSecret
            scope         = "https://graph.microsoft.com/.default"
        }

        $tokenResponse = Invoke-RestMethod -Uri $tokenUrl -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"

        if ($tokenResponse.access_token) {
            Write-Status "Successfully obtained access token" "Success"

            # Test API call
            $headers = @{ Authorization = "Bearer $($tokenResponse.access_token)" }
            $testResponse = Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/organization" -Headers $headers

            if ($testResponse.value) {
                $org = $testResponse.value[0]
                Write-Status "Connected to organization: $($org.displayName)" "Success"
                return $true
            }
        }
    }
    catch {
        Write-Status "Graph API test failed: $_" "Error"
        return $false
    }

    return $false
}

function Store-SecretInKeyVault {
    param(
        [hashtable]$Tenant,
        [string]$SecretValue
    )

    if ([string]::IsNullOrEmpty($KeyVaultName)) {
        Write-Status "No Key Vault specified, skipping secret storage" "Info"
        return $null
    }

    Write-ProgressHeader "Storing Secret in Key Vault"

    try {
        # Ensure Az.KeyVault module
        if (-not (Get-Module -ListAvailable Az.KeyVault)) {
            Write-Status "Installing Az.KeyVault module..." "Info"
            Install-Module Az.KeyVault -Force -Scope CurrentUser
        }

        Import-Module Az.KeyVault -Force

        # Check if connected to Azure
        $azContext = Get-AzContext -ErrorAction SilentlyContinue
        if (-not $azContext) {
            Write-Status "Connecting to Azure..." "Step"
            Connect-AzAccount | Out-Null
        }

        $secretName = "riverside-$($Tenant.Name.ToLower())-client-secret"

        $secureSecret = ConvertTo-SecureString -String $SecretValue -AsPlainText -Force
        Set-AzKeyVaultSecret `
            -VaultName $KeyVaultName `
            -Name $secretName `
            -SecretValue $secureSecret `
            -ContentType "text/plain" | Out-Null

        Write-Status "Secret stored in Key Vault: $secretName" "Success"
        return $secretName
    }
    catch {
        Write-Status "Failed to store secret in Key Vault: $_" "Error"
        Write-Status "Secret will be in output file - SECURE IT IMMEDIATELY!" "Warning"
        return $null
    }
}

#endregion

#region Main Execution

function Invoke-TenantSetup {
    param([hashtable]$Tenant)

    $config = @{}

    # Step 1: Connect
    if (-not (Connect-Tenant $Tenant)) {
        throw "Failed to connect to tenant $($Tenant.Name)"
    }

    # Step 2: Create App Registration
    $app = New-AppRegistration -Tenant $Tenant
    $config.AppId = $app.AppId
    $config.ObjectId = $app.Id

    # Step 3: Create Client Secret
    $secret = New-ClientSecret -Tenant $Tenant -AppId $app.AppId
    $config.ClientSecret = $secret

    # Step 4: Grant Admin Consent
    Grant-AdminConsent -Tenant $Tenant -AppId $app.AppId

    # Step 5: Store in Key Vault (optional)
    $config.KeyVaultSecretName = Store-SecretInKeyVault -Tenant $Tenant -SecretValue $secret

    # Step 6: Verify
    if (Test-GraphConnection -Tenant $Tenant -AppId $app.AppId -ClientSecret $secret) {
        Write-Status "Verification PASSED!" "Success"
    }
    else {
        Write-Status "Verification FAILED - check permissions" "Error"
    }

    return $config
}

function Export-Configuration {
    param(
        [hashtable]$Results
    )

    Write-ProgressHeader "Exporting Configuration"

    $envContent = @(
        "# Riverside Governance Platform Configuration"
        "# Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        "# DO NOT COMMIT THIS FILE TO VERSION CONTROL!"
        ""
    )

    foreach ($tenant in $script:Tenants) {
        $result = $Results[$tenant.Name]

        $envContent += "# $($tenant.Name) - $($tenant.Description)"
        $envContent += "RIVERSIDE_$($tenant.Name)_TENANT_ID=$($tenant.TenantId)"

        if ($result) {
            $envContent += "RIVERSIDE_$($tenant.Name)_CLIENT_ID=$($result.AppId)"

            if ($result.KeyVaultSecretName) {
                $envContent += "RIVERSIDE_$($tenant.Name)_KEY_VAULT_SECRET_NAME=$($result.KeyVaultSecretName)"
                $envContent += "# Client secret stored in Key Vault: $KeyVaultName"
            }
            else {
                $envContent += "RIVERSIDE_$($tenant.Name)_CLIENT_SECRET=$($result.ClientSecret)"
            }

            $envContent += "RIVERSIDE_$($tenant.Name)_OBJECT_ID=$($result.ObjectId)"
        }
        else {
            $envContent += "# FAILED - run again to complete"
        }

        $envContent += ""
    }

    # Add Key Vault reference
    if (-not [string]::IsNullOrEmpty($KeyVaultName)) {
        $envContent += "# Azure Key Vault Configuration"
        $envContent += "AZURE_KEY_VAULT_NAME=$KeyVaultName"
        $envContent += ""
    }

    # Add notes
    $envContent += "# Notes:"
    $envContent += "# - Client secrets expire after $SecretExpiryYears year(s)"
    $envContent += "# - Keep this file secure and do not commit to git"
    $envContent += "# - For Key Vault access, ensure Managed Identity is configured"
    $envContent += ""

    $envContent -join "`n" | Set-Content $OutputPath -Force
    Write-Status "Configuration exported to: $OutputPath" "Success"

    # Also create a secure JSON version
    $jsonPath = $OutputPath -replace '\.env$', '.json'
    $Results | ConvertTo-Json -Depth 3 | Set-Content $jsonPath
    Write-Status "Full configuration saved to: $jsonPath" "Success"
    Write-Status "(JSON contains secrets - secure it!)" "Warning"
}

function Show-Summary {
    param([hashtable]$Results)

    Write-ProgressHeader "Setup Complete"

    Write-Host "`n  Tenant Setup Summary:" -ForegroundColor White
    Write-Host "  " + ("-" * 50) -ForegroundColor Gray

    foreach ($tenant in $script:Tenants) {
        $result = $Results[$tenant.Name]
        $status = if ($result) { "✓ COMPLETE" } else { "✗ FAILED" }
        $color = if ($result) { "Green" } else { "Red" }

        Write-Host "  $($tenant.Name.PadRight(5)) | $($tenant.Description.PadRight(25)) | " -NoNewline
        Write-Host $status -ForegroundColor $color
    }

    Write-Host "`n  Output Files:" -ForegroundColor White
    Write-Host "  - Environment: $OutputPath" -ForegroundColor Cyan
    Write-Host "  - JSON Config: $($OutputPath -replace '\.env$', '.json')" -ForegroundColor Cyan

    Write-Host "`n  Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Secure the output files immediately" -ForegroundColor White
    Write-Host "  2. Store client secrets in your secure credential store" -ForegroundColor White
    Write-Host "  3. Update your application to read from .env file" -ForegroundColor White
    Write-Host "  4. Set up Key Vault access for your application" -ForegroundColor White
    Write-Host "  5. Delete progress file: $ProgressFile" -ForegroundColor White
}

#endregion

#region Script Entry Point

function Main {
    $results = @{}

    try {
        # Check prerequisites
        Test-Prerequisites

        # Load progress
        $progress = Get-Progress
        if ($progress.CompletedTenants.Count -gt 0) {
            Write-Status "Resuming from previous session" "Info"
            Write-Status "Completed: $($progress.CompletedTenants -join ', ')" "Info"
        }

        # Determine which tenants to process
        $tenantsToProcess = $script:Tenants

        if ($ResumeFrom) {
            $found = $false
            $tenantsToProcess = $script:Tenants | Where-Object {
                if ($_.Name -eq $ResumeFrom) { $found = $true }
                return $found
            }
        }

        # Filter out already completed
        $tenantsToProcess = $tenantsToProcess | Where-Object { $progress.CompletedTenants -notcontains $_.Name }

        if ($tenantsToProcess.Count -eq 0) {
            Write-Status "All tenants already processed!" "Success"
            Clear-Progress
            return
        }

        # Confirm with user
        Write-ProgressHeader "Setup Plan"
        Write-Host "  Tenants to configure:" -ForegroundColor White
        foreach ($tenant in $tenantsToProcess) {
            Write-Host "    - $($tenant.Name): $($tenant.Description)" -ForegroundColor Gray
        }
        Write-Host ""

        $confirm = Read-Host "  Proceed with setup? (yes/no)"
        if ($confirm -ne 'yes') {
            Write-Status "Setup cancelled by user" "Warning"
            return
        }

        # Process each tenant
        foreach ($tenant in $tenantsToProcess) {
            try {
                Write-ProgressHeader "Processing $($tenant.Name)"
                $config = Invoke-TenantSetup -Tenant $tenant
                $results[$tenant.Name] = $config
                Save-Progress -TenantName $tenant.Name -MarkComplete
            }
            catch {
                Write-Status "Failed to setup $($tenant.Name): $_" "Error"
                $results[$tenant.Name] = $null

                $continue = Read-Host "  Continue with next tenant? (y/n)"
                if ($continue -ne 'y') {
                    break
                }
            }
            finally {
                Disconnect-MgGraph -ErrorAction SilentlyContinue | Out-Null
            }
        }

        # Export results
        Export-Configuration -Results $results

        # Show summary
        Show-Summary -Results $results

        # Clean up progress if all successful
        $allSuccessful = $results.Values | Where-Object { $_ -eq $null } | Measure-Object
        if ($allSuccessful.Count -eq 0) {
            Clear-Progress
        }
    }
    catch {
        Write-Status "FATAL ERROR: $_" "Error"
        Write-Status "Stack Trace: $($_.ScriptStackTrace)" "Error"
        exit 1
    }
}

# Run main function
Main

#endregion
