# IST Tutoring Portal

A web based interface to handle student help requests in the University of Nebraska at Omaha Computer Science Learning Center (UNO CSLC).

## Setup

1. Setup a Google API for the login system
    1. <https://console.developers.google.com/apis/credentials>
    2. Under credentials, create credentials for an OAuth Client ID
    3. Select Web application
    4. Provide the domain followed by `/oauth-authorized` (eg. `www.example.com/oauth-authorized`) as the authorized redirect URI
    5. Save the client ID and secret for later
2. Setup a Google reCAPTCHA key/secret
    1. <https://www.google.com/recaptcha/admin>
    2. Select "invisible reCAPTCHA"
    3. Provide the domain (no subpage this time)
    4. Save the site key and secret key for later
3. Run the portal in debug mode to create the appropriate database tables
4. Access the database manually to add configuration information
    1. In the configuration table the Google API client ID from earlier goes in the setting column of the row with the name `GOOGLE_CONSUMER_KEY`
    2. Also in configuration, the Google API client secret goes in the setting column of the row with the name `GOOGLE_CONSUMER_SECRET`
    3. Add the reCAPTCHA site key to the configuration in the `GOOGLE_CAPTCHA_KEY` row
    4. Add the reCAPTCHA secret key to the configuration in the `GOOGLE_CAPTCHA_SECRET` row
    5. In the tutors table create a tutor with an email you can log into Google with. Set the `tutor_is_active` and `tutor_is_superuser` columns to true
5. Restart the application to finish configuration
6. By logging in as a superuser account other objects can be created

## Use

### Students

Students do not need to log in to the system. While not logged in, two features are accessible, opening tickets and the status page.

#### Open Ticket

A ticket can be opened by clicking the `Open Ticket` button on the home page. This opens the Open Ticket form.

On the form, a student must enter their Email, First Name, Last Name, Course and Section, Assignment Name, Specific Question, and Problem Type.

The Email, First Name, and Last Name are the personal contact information for the student requesting the session. If a group is requesting tutoring only the contact information for the group leader should be entered.

The Course selection filters the Section options based on the course selected.

The Section selection is the course section the student is requesting tutoring for.

The Assignment Name is the name of the assignment the student is requesting help with. This is usually similar to "Assignment 1" or "Project 1".

The Specific Question is the question the student is asking or a topic they need to know more about. Students should be instructed to be as specific as possible.

The Problem Type is a selection of the categories of problems that students may encouter. This helps determine the stage of problem solving they are at.

Once all of the fields are filled out, the ticket is submitted with the `Submit` button. The page is protected by a CAPTCHA so students may be asked to respond to the CAPTCHA before the ticket is submitted.

#### Status

The status screen gives an overview of the situation in the tutoring center. It can be accessed by clicking the `Status` button in the toolbar. The status screen has three sections.

The `Messages` section displays any current messages entered by an administrator.

The `Course Availability` section gives the current number of tickets and tutors in the tutoring center for courses selected by an administrator. This shows how busy the tutoring center is and whether there are tutors available to students planning on getting help.

The last section, `Open Tickets` only displays for logged in users. It shows the current list of open tickets.

### Logging In

To perform any tutor or administrator actions the tutor or administrator must be logged in. To log in, click the `Tutor Login` button in the toolbar. This will redirect to a Google login page. Log in using the email for your account (usually an `@unomaha.edu` accout). If this is the account's first time logging in access must be granted for the application to view the account's email address. The tutor will then be logged in if the account they used to log in is a valid, active tutor account or rejected otherwise. Either way, they will be redirected back to the application's home page.

To log out, a tutor can click the `logout` button in the toolbar. They will be logged out and redirected to the home page.

### Tutors

#### Edit User

Tutors can edit a subset of the information about themself by clicking `Tutor` in the toolbar, then `Edit User`. Administrators will be redirected to the Edit Tutor page for themself, while normal tutors will be shown a subset of the fields accessible to administrators.

Tutors can edit their First Name, Last Name, Currently Working status, and Can Tutor course proficiencies. For detailed instructions see the Tutors page description below.

#### View Tickets

Tutors can. The tickets list can be accessed by clicking `Tutor` in the toolbar, then `Tickets` or by clicking `View Tickets` on the homepage.

The view tickets page has three sections. `Open` is for tickets not yet claimed by a tutor. `Claimed` is for tickets that have been claimed, but the session is not yet finished. `Closed` is for tickets for which the session has been finished.

##### Claim/Close Ticket

Tickets in the `Open` section have a `Claim` button and tickets in the `Claimed` section have a `Close` button. Both of these lead to the Claim/Close page for the selected ticket.

On the Claim/Close page tutors can edit the ticket's course and section, assignment name, question, problem type, claiming tutor, assisting tutor, and whether the session was successful. The Claiming Tutor is the tutor that helped the student during the session. The Assisting Tutor is for if another tutor provided input during the session. Was Successful indicates if the original question for the session was resolved. The purposes of the rest of the fields are described in the Open Ticket page description above. All of these fields are requred except the assisting tutor.

Once the neccessary fields are filled out the ticket can be assigned to the `Claimed` section by clicking the `Claim` button or the `Closed` section by clicking the `Close` button.

##### Reopen Ticket

Tickets in the `Closed` section have a `Reopen` button. Clicking this moves the ticket from the `Closed` section back to the `Claimed` section, altering its status accordingly. The rest of the tickets details remain the same.

### Administrators Only

#### Administration Console

The administration console is where the administrator can set up tutor accounts, messages, problem types, and all of the information necessary for course sections.

The Administration Console can be accessed when logged in as an administrator by clicking `Admin` in the toolbar, followed by `Admin Console`. If the `Admin` option does not exist you are not logged in as an administrator.

On the Administration Console page there are links to menus for Messages, Courses, Course Sections, Semesters, Professors, Problem Types, and Tutors. By clicking each link, menus can be accessed that allow editing and viewing of objects of each type. Before adding a Course Section, the corresponding Course, Semester, and Professor must be added.

Each menus is the same, with a `+ New` button to create a new object and `Edit` buttons to change the details of an existing object. The screen for editing is the same as for creating an object, but the existing details are already filled in.

##### Messages

...

##### Courses

...

##### Course Sections

...

##### Semesters

...

##### Professors

...

##### Problem Types

...

##### Tutors

...

#### Reports

The reports page contains a summary of all of the tickets in the system. The reports can be accessed when logged in as an administrator by clicking `Admin` in the toolbar, followed by `Reports`. If the `Admin` option does not exist you are not logged in as an administrator.

Various filters can be applied to the list. By entering a start date only tickets opened on or after the date will be displayed. By entering an end date only tickets opened on or before the date will be displayed. By selecting a semester only tickets that belong to that semester will be displayed. By selecting a course only tickets that belong to that course will be displayed. Once he desired filters are entered clicking the `Filter` button will apply them to the list.

The current report can be downloaded in a CSV format (openable in Microsoft Excel) by clicking the `Download Report` button. The current list of tickets will be downloaded with the same filters applied. Filters are only applied to the download if they have been applied to the list using the `Filter` button.

More information about a given ticket can be viewed by clicking the `Details` button on the ticket's row.
