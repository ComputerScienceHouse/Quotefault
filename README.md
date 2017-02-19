# quotefault
quote-submission system for CSH Segfault editors as well as CSH InfoSys

Intial (Hackathon 1/14/17) goals:
Allow users to access the QuoteFault Main page and submit a quote and name to the system; Have flask/mySQL utilities collect the two pieces of user input, as well as a datetime stamp and store them; Display the data collected on a seperate, password-protected page in date-submitted order for Segfault editors to view

Long-term goals:
Allow InfoSys to access the database and take one quote a day and display it in the user-center once per hour; Allow Segfault editors to delete old/used quotes from the database at any time; Appearance improvements

(2/12/17):
Submission now updates a MySQL server hosted by CSH, grabbing csh username, quote and name form strings, and datetime as it goes.  Second /get page is coded to retrieve rows from the MySQL server, and will eventually display them for general user consumption (upon discussion with members of floor, I think I'll have this page be open to everyone in a non-editable state, and just use the CSH MySQL viewer to allow Quotefault editors to remove quotes from the db).  Next step is to learn the nencesary Jinja to implement this properly, and create a button that'll redirect to it from the main page.

Opcommathon (2/19/17):
Site functions locally.  Submission now catches repeat quotes before throwing a 500 error.  CSS updated to make both templates more visually appealing, a blend of CSH bootstrap and personal work.  Links inserted to both templates so users can easily jump between the two pages.
