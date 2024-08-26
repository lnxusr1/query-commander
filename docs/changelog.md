# Change Log

All notable changes to this project will be documented in this file.

## [0.7.1] - 2024-08-25

- Enabled environment variable overrides for most common settings
- Documentation updates

## [0.7.0] - 2024-08-24

- Added websockets for long running queries through AWS Lambda
- Added autoconfigure websocket API URL
- Documentation updates and corrections

## [0.6.2] - 2024-08-22

- Bug fix for new script button not firing
- Optimized profile pull to reduce round-trips
- Added configuration option for disabling profiles
- Adjusted HTTP headers for cache breaking
- Documentation cleanup and updates
- Improved logging messages

## [0.6.1] - 2024-08-20

- Added AWS Lambda Layer zip inclusion
- Bug fix for lambda cookies not being set properly
- Bug fix for session update after logout
- Bug fix for PostgreSQL Sequence DDL export
- Bug fix for weirdness in Lambda holding connection names that don't exist
- Bug fix for MySQL "no database selected" error
- Cleaned HTML code for client-side filters
- Added traps in connectors for non-fatal errors to avoid unforced errors
- Added "New SQL Script..." link to context menu for databases
- Updated cache breakers for all API calls
- Improved handling of keyboard shortcuts

## [0.6.0] - 2024-08-19

- **BREAKING**: Library change for PostgreSQL connections
    - Dropped support for psycopg(2/3) due to static linking limitation in lambda
    - Added support for pg8000 and updated docs

- Updated logging for better error trapping in lambda
- Added cache breakers to ajax calls

**NOTICE**: Future releases will call out breaking changes like the library change here explicitly.

## [0.5.4] - 2024-08-18

- Added tab selector for reordering multiple tabs
- Updated tab names to allow for connections to be different than tab name
- Added simple client-side record filtering

## [0.5.3] - 2024-08-17

- Added S3 Profile storage option
- Added "lambda" install subdivision for pip installer
- Updated installation docs for AWS API Gateway/Lambda install
- Logging cleanup

## [0.5.2] - 2024-08-16

- Bug fix in module inheritance from pypi package
- Redesigned page start using start.as_cgi() or start.as_lambda(event, context)
- Added log_level setting
- Centralized version number management
- Improved log divisions

## [0.5.1] - 2024-08-15

- PyPi module launch
- CDN configuration options for overriding default sources
- Additional general documentation cleanup/updates for 5.x version
- Simplified installation process

## [0.5.0] - 2024-08-14

- Major change for configuration (working toward python module install)
- Reworked Apache documentation, testing Lambda configuration

## [0.4.3] - 2024-08-13

- Added active sessions view to sidebar context
- Added active locks view to sidebar context
- Updated output process for AWS Lambda compatibility
- Initial lambda_function.lambda_handler

## [0.4.2] - 2024-08-12

- Migrated Token storage to allow one active login per user
- Migrated rate limits to token from profile
- Added visual confirmation on save
- Bug Fixes:
    - Auto-load results on scroll failing to load next segment

## [0.4.1] - 2024-08-11

- Added feature for records over time limits
- Updated token format for storage
- Bug Fixes:
    - Session time extension not being properly updated on validation
    - API: save-profile trapped errors now return valid error response

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