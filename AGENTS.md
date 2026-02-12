UP SUPPLY Vendor Management System (VMS)
1. Vision & Context
UP SUPPLY is a specialized PPE and medical supply distributor. This VMS is designed to bridge technology and treatment by ensuring that all third-party vendors meet strict clinical and safety standards. The primary goal of this system is Compliance Automation and Document Integrity.

2. Technical Stack Constraints
Framework: Django 5.x.

Database: PostgreSQL.

Front-end: Tailwind CSS for a modern, clinical look.

Identity: All primary keys for models must use UUIDs for enhanced security and data portability.

3. Core Domain Logic (The PPE Rules)
Jules must implement and enforce the following business rules in the code:

A. Compliance-First Model
Verification Logic: A Vendor status cannot be set to VERIFIED unless there is at least one valid Certification (e.g., ISO, FDA, or CE) uploaded.

Auto-Invalidation: If a vendor's all certifications have passed their expiry_date, the vendor's global status must automatically switch to INACTIVE.

B. Certification Integrity
Model: Certification.

Fields: cert_type (ChoiceField), file (FileField/S3), issue_date, expiry_date, and a boolean is_current.

Validation: Jules must add a custom clean method to ensure expiry_date is always in the future relative to issue_date.

C. Product Linking
Relation: Every Product must be strictly linked to a Vendor via a Foreign Key.

Visibility Rule: Products should only be "Active" in the system if the parent Vendor is currently VERIFIED.

4. UI/UX Requirements (Admin & Portal)
Admin Dashboard: The standard Django admin should be customized to show colored status tags (Green for Verified, Red for Expired/Pending).

Vendor Profile Builder: Jules should create a "restricted" view where a vendor can log in to update only their own contact info and upload new PDFs, without seeing other vendors' data.

5. Security & Safety
Sanitization: All uploaded PDFs must be stored with hashed filenames to prevent IDOR attacks.

Audit Trail: Jules should implement a simple "History" log for the Vendor model to track who changed a status and when.
