# MongoDB-Gym-Membership-Management-System

# 🧠 1. Core Technologies Used
Flask: Web framework to handle routing and views.

MongoDB (via PyMongo): Backend database to store member, subscription, and admin data.

Jinja2: Templating engine (used in HTML templates).

Werkzeug Security: Used for password hashing.

Bootstrap-like CSS + Font Awesome: For modern UI styling (written manually in templates).

# 🏗 2. Application Structure
# A. MongoDB Collections

members: Stores member personal info and subscription.

subscriptions: Stores plan options (Basic, Standard, Premium).

admin: Stores admin credentials and metadata.

# B. Routes (Flask App Endpoints)

/login	-> Admin login page
/	 -> Dashboard (view all members + expired)
/add_member  ->	Add a new gym member
/update_subscription/<member_id>	-> Update an existing subscription
/delete_member/<member_id> -> Delete a member
/delete_expired  -> Remove all expired memberships
/members_by_plan/<plan_id>	-> View members filtered by plan
/view_member/<member_id>	-> View a single member’s full info
/logout	 -> Admin logout
/print_member/<member_id> -> Generates a printable version (intended PDF)

# 🧾 3. Functions and Features Explained
# 🔒 login_required
A decorator used to restrict access to pages unless the admin is logged in.

Checks for 'admin_logged_in' in Flask session.

# 🔑 login()
Handles admin login (POST) and renders login form (GET).

Uses check_password_hash() to securely authenticate.

# 📋 initialize_sample_data()
Initializes:

Indexes for faster MongoDB queries.

Sample subscriptions: Basic, Standard, Premium.

Default admin account (admin/admin123).

# 📁 create_templates()
Programmatically creates 4 HTML templates:

login.html – login page

index.html – dashboard

members_by_plan.html – filter view

view_member.html – single member info

# ➕ add_member()
Reads form inputs and inserts a new member to MongoDB.

Validates:

Age as integer

Start date must be before expiry

Saves plan_id, payment method, start/expiry date in the subscription info.

# 🔁 update_subscription(member_id)
Allows updating an existing member’s subscription details.

Validates start/expiry dates and updates the member in the DB.

# ❌ delete_member(member_id)
Deletes a specific member from the DB using _id.

# ❌ delete_expired()
Deletes all members whose subscription.expiry_date < current_date.

# 🔍 members_by_plan(plan_id)
Retrieves all members with a specific plan (e.g., Premium).

Dynamically fills plan badge UI using Jinja2 logic.

# 👁 view_member(member_id)
Shows a full profile of the member.

Includes:

Personal details (age, contact, email, etc.)

Subscription (plan, start/expiry, payment)

Remaining days and status (Active/Expired)

UI-styled printable view.

# 🖨 print_member(member_id)
Renders the view_member.html template with Content-Type: application/pdf.

Intended for printing or saving membership card.

Note: Not an actual PDF unless integrated with tools like WeasyPrint or wkhtmltopdf.

# 🚪 logout()
Clears session and redirects to login.

# 💡 Extra Details
# ✅ Security
Passwords are hashed using generate_password_hash.

Session secret key is generated using os.urandom(24) (should be constant in production).

# 🖼 UI
Inline styles using style tags in HTML.

Utilizes responsive design and attractive animated CSS components.

# Summary
This is a complete end-to-end Gym Management web app using Flask + MongoDB. It supports:

Admin login

CRUD operations on members

View/filter by plans

Expiry tracking

Basic analytics (status badges, days remaining)

Auto-generated HTML templates

# Command Required for this project 

1.pip install flask pymongo

2.Get-Service | Where-Object { $_.Name -like "*MongoDB*"}

3.python
