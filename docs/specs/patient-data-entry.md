# Spec: Patient Data Entry Form — basic clinic intake app

### FEATURE SUMMARY
A basic, single-page web app that lets clinic/reception staff record a new patient through one data-entry form: patient demographics and contact details are typed in, validated in the browser and on the server, saved to a shared server-side store, and shown in a "recently entered patients" list on the same page. It is deliberately minimal — a working intake screen, not an EMR. Closest existing pattern: the factory's employee-onboarding-form build (small backend server + JSON file store + static single-page frontend, one `GET`/`POST` API resource, no build tooling). The same architecture applies here because entered patients must persist beyond a single browser session.

### USER STORIES
1. As a receptionist, I want to enter a new patient's details in one form so that their record is captured at intake.
2. As a receptionist, I want required fields clearly enforced so that I cannot save an incomplete patient record by mistake.
3. As a receptionist, I want immediate validation feedback (e.g. bad date, bad email) so that I can fix errors before submitting.
4. As a receptionist, I want a clear confirmation when a patient is saved so that I know the entry succeeded.
5. As a receptionist, I want to see a list of recently entered patients on the same page so that I can confirm what has been recorded without leaving the screen.
6. As a receptionist, I want saved patients to still be there after I reload the page so that entries are not lost.
7. As a staff member, I want the form to work on a tablet or phone so that I can register patients away from the front desk.
8. As a staff member, I want the app to run with a single command and no sign-up so that it is trivial to start using.

### ACCEPTANCE CRITERIA
1. The single page shows a patient entry form with these fields: first name (required), last name (required), date of birth (required, date input), gender (required, select with at least Female / Male / Other / Prefer not to say), phone (required), email (optional), street address, city, state/region, ZIP/postal code, emergency contact name, emergency contact phone, and a free-text notes field (optional).
2. Submitting with any required field empty blocks the save and marks the missing fields inline; nothing is sent to the server.
3. Validation enforced both client- and server-side: date of birth must be a valid date not in the future; email, when provided, must match a standard email format; phone fields accept a reasonable phone pattern (digits, spaces, `+`, `-`, parentheses, minimum 7 digits).
4. A valid submission sends `POST /api/patients` (or the repo's chosen API route), receives a 201-style success, and stores the full submitted record plus a generated id and a created-at timestamp.
5. On success the page shows a visible confirmation (e.g. "Patient saved") and the form resets to empty, ready for the next patient.
6. The page displays a "Recent patients" list served by `GET /api/patients`, newest first, each row showing at least full name, date of birth, gender, and phone; the list updates immediately after a save without manual refresh.
7. Patient records persist server-side (e.g. a JSON file on disk): restarting the page and reloading still shows previously entered patients.
8. A server-side validation failure returns a 400-style error and the page displays the error without saving anything.
9. The layout is a single responsive page usable on a phone-width screen, and the repo's README documents how to start the app with one command.
10. No login, sign-up, or password appears anywhere in the app.

### SCOPE
IN:
- One patient entry form (demographics, contact details, emergency contact, notes) with client- and server-side validation.
- Save via a small backend API with server-side persistence (JSON file or equivalent simple store).
- Newest-first list of entered patients on the same page.
- Responsive single-page UI; single-command local run documented in README.
- One shared patient list per deployment; no user identity.

OUT:
- Accounts, login, roles, or any authentication/authorization.
- Editing, deleting, or searching/filtering patients (entry + list only).
- Appointments, visits, insurance/billing workflows, medical history beyond a free-text notes field.
- File/photo uploads, document attachments.
- HIPAA or other compliance features: audit logging, encryption at rest, access controls, consent management. This is a demo intake form, not for real PHI.
- Multi-clinic support, patient matching/deduplication, imports/exports (CSV, HL7, FHIR).
- Production hosting/deployment.

### OPEN QUESTIONS
1. Stack choice: implementation stack is left to the DEV agent — mirror the factory's established pattern (small server + JSON store + static SPA, e.g. `server.py` or `server.js` + `public/`). Default assumption: whichever the sibling onboarding app used is preferred for consistency.
2. Patient list detail: the list shows name/DOB/gender/phone only. If the user wants edit/delete or search later, that is a follow-up feature, not this one.
3. Data sensitivity: real patient data would trigger privacy/compliance requirements; default assumption is demo/fake data only, so no compliance features are built.

### SPEC IN GIT
- `BRANCH: devin/1791790390-factory-patient-entry`
- `FILE: docs/specs/patient-data-entry.md`
- `COMMIT: see branch HEAD (recorded after commit)`

### STATUS
`STATUS: COMPLETE`
