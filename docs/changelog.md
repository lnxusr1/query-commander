# Change Log

All notable changes to this project will be documented in this file.

## [0.4.0] - 2024-08-10

- Local User Profile Manager
- DynamoDB User Profile Manager
- Bug fixes in role handling
- Changed connections type option from *local* to *config* to avoid confusion
- Split out connections processing into separate connections module 
- Added valid connections to token processing (now possible with recent role changes) for streamlined operations
- Connections: SecretsManager
    - Optimization to streamline calls to get secrets
    - Added filtering mechanism for AWS-supported [filtering criteria](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager/client/list_secrets.html)
    - Switched to use secret name for connection name

## [0.3.1] - 2024-08-08

- Bug fix for multiple roles
- Removed role chooser

## [0.3.0] - 2024-08-06

**MILESTONE:** All core databases that will be part of v1.0 are now supported!

- AWS Redshift Database Support (and related docs)
- Updated docs for successful Oracle connection

## [0.2.1] - 2024-08-05

- Bug fix for Oracle Partitions and Subpartitions

## [0.2.0] - 2024-08-04

- Oracle Database Support (and related docs)
- New environment variable to move settings.yml to user-specified folder

## [0.1.0] - 2024-08-03

- AWS Secrets Manager Integration for Connections Management
- Updated global settings to support AWS authentication options
- Bug fix for MySQL connector on DML statements not taking to output screen
- Bug fix for MySQL explain plan generation/viewing
- Updated versioning pattern  
  *[Milestone ~ Major Features ~ Bug fixes/Minor Changes/Routine Builds]*

## [0.0.3] - 2024-08-02

- Active Directory Authentication via LDAP/LDAPS
- Redis Session Token Storage (and related docs)
- MySQL/MariaDB Database Support (and related docs)

## [0.0.2] - 2024-08-01

- DynamoDB Session Token Storage (and related docs)

## [0.0.1] - 2024-07-31

- All prior code from all forms for all historic years of experimentation coalesced into single branch
- Includes basic operators rewritten in Python (from C# and PHP)
- Lays out all basic code structure, connector interfaces, and UI/UX
- Added a direct export for result exports through browser (no round-trip required)
- Authentication Types: local, openldap
- Session Management Options: local
- Databases Supported: postgresql