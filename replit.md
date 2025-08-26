# Overview

This is an HR Management System ("Système RH") for Ceramica, a French-language web application built with Flask that manages employee information, attendance tracking, payroll processing, and organizational structure. The system provides comprehensive human resources functionality including employee management, time tracking, salary calculations, and reporting capabilities.

# User Preferences

Preferred communication style: Simple, everyday language.
Design preferences: Modern, tablet-friendly design with blue color scheme (#003E9C), touch-optimized interface.

# System Architecture

## Backend Architecture

**Framework**: Flask web framework with SQLAlchemy ORM for database operations
**Database**: PostgreSQL with SQLAlchemy models defining the core entities (User, Branch, Department, Designation, Employee)
**Form Handling**: Flask-WTF for form validation and CSRF protection
**Session Management**: Flask sessions with configurable secret key

## Frontend Architecture

**Template Engine**: Jinja2 templating with a base template system
**CSS Framework**: Bootstrap 5 with dark theme and Font Awesome icons
**JavaScript**: Vanilla JavaScript for interactive features (tooltips, form validation, real-time updates)
**Responsive Design**: Mobile-first approach using Bootstrap grid system

## Data Model Design

**Hierarchical Structure**: Organizations → Branches → Departments → Designations → Employees
**Audit Trail**: Created_by, created_at, updated_at fields on all entities
**Employee Data**: Comprehensive employee information including personal details, banking info, and salary configuration

## Security & Configuration

**Environment Variables**: Database URL, session secrets, and configuration via environment variables
**Database Connection**: Connection pooling with health checks and retry logic
**Proxy Support**: ProxyFix middleware for deployment behind reverse proxies

## Application Structure

**Modular Design**: Separated concerns with dedicated files for models, forms, routes, and static assets
**Template Organization**: Structured template hierarchy with feature-specific directories
**Static Assets**: Custom CSS and JavaScript with CDN dependencies for Bootstrap and Font Awesome

# Recent Changes

## Migration Completed (26/08/2025)
- **Project Migration**: Successfully migrated from Replit Agent to Replit environment
- **Package Installation**: Installed all required Python dependencies (Flask, SQLAlchemy, gunicorn, etc.)
- **JavaScript Fix**: Fixed setupTouchSearchHandlers error in main.js
- **Bulk Operations**: Added bulk import/export functionality for employees section
  - CSV export of all employee data
  - CSV import with validation and error handling
  - Import template download feature
  - Enhanced UI with Actions dropdown menu

## Employee Management Enhancements
- **Import Features**: CSV import with comprehensive validation
- **Export Features**: Full employee data export to CSV format
- **Template System**: Downloadable CSV template with example data
- **Error Handling**: Detailed error reporting for import operations
- **User Interface**: Added Actions dropdown with import/export options

## Moroccan Payroll System Implementation (26/08/2025)
- **Comprehensive Payroll Calculator**: Implemented full Moroccan labor law compliance
  - Base salary calculations with attendance-based adjustments
  - Overtime payments (25%, 50%, 100% rates for different scenarios)
  - Paid leave and holiday payment calculations
  - Automatic seniority bonus (5-25% based on years of service)
  - Social security contributions (CNSS, AMO, CIMR) with proper ceilings
  - Professional expenses deduction (35%/25% based on salary level)
  - Progressive income tax (IR) calculation with family allowances
  - Automatic retirement event creation for eligible employees
- **Enhanced Database Models**: Extended PaySlip model with detailed calculation fields
- **Calculation Features**: 
  - Handles complex overtime scenarios (regular, weekend, holiday)
  - Family allowances that reduce income tax burden
  - CNSS contribution ceiling of 6,000 MAD enforcement
  - Automatic advance payment and loan deduction handling
- **Batch Processing**: Added batch payroll calculation for all employees
- **Compliance Features**: Full adherence to Moroccan tax brackets and social security rates

# External Dependencies

## Core Dependencies
- **Flask**: Web framework and core application structure
- **SQLAlchemy**: Database ORM and model definitions
- **Flask-WTF**: Form handling and CSRF protection
- **WTForms**: Form field validation and rendering
- **Werkzeug**: WSGI utilities and proxy middleware

## Frontend Dependencies
- **Bootstrap 5**: CSS framework with dark theme support
- **Font Awesome 6**: Icon library for UI elements
- **Bootstrap JavaScript**: Interactive components and validation

## Database
- **PostgreSQL**: Primary database system (configurable via DATABASE_URL)
- **Connection pooling**: Managed through SQLAlchemy engine options

## Deployment Infrastructure
- **WSGI**: Standard Python web application interface
- **Proxy support**: Configured for deployment behind reverse proxies
- **Environment configuration**: Flexible configuration through environment variables