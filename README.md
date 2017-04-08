# IST Tutoring Portal

A web based interface to handle student help requests in the University of Nebraska at Omaha Computer Science Learning Center (UNO CSLC).

## Setup

1. Setup a Google API for the login system.
    1. <https://console.developers.google.com/apis/credentials>
    2. Under credentials, create credentials for an OAuth Client ID
    3. Select Web application
    4. Provide the domain followed by '/oauth-authorized' (eg. 'www.example.com/oauth-authorized') as the authorized redirect URI.
    5. Save the client ID and secret for later.
2. Run the portal in debug mode to create the appropriate database tables.
3. Access the database manually to add configuration information.
    1. In the configuration table the client ID from earlier goes in the setting column of the row with the name 'GOOGLE_CONSUMER_KEY'.
    2. Also in configuration, the client secret goes in the setting column of the row with the name 'GOOGLE_CONSUMER_SECRET'.
    3. In the tutors table create a tutor with an email you can log into Google with. Set the tutor_is_active and tutor_is_superuser columns to true.
4. Restart the application to finish configuration.
5. By logging in as a superuser account other objects can be created.

## Use

### Administrators/Superusers

When logged in as an administrator the administrative tools will be accessible. From the administrative tools page, admins can add and edit the following objects:

* tutors can be added (normal users and superusers)
* messages, which will show up on the status screen and use markdown conversion
* problem types that students can select when creating tickets
* courses for students to select.
* Semesters
* Professors for course sections
* and Course Sections, which must be created after the course, semester, and professor

Admins can also view reports of past tickets. The reports can be filtered by start date, end date, semester, and course. The report can then be downloaded with the current filters applied.

### Tutors

A tutor that is logged in, including both superusers and normal users, can edit their own status including:

* First name
* Last name
* if they are currently in the tutoring center
* the courses they can tutor

Any logged in user can also view the tickets list and claim, close, or reopen tickets.

### Students

Students are any users of the system and do not need to log in. Students can open a ticket or view the status page. The status page shows any current messages and the availability of selected courses (number of tickets vs number of tutors).

If a logged in user views the status page it will show a list of open tickets as well as the normal information.
