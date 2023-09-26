import psycopg2
import requests
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from psycopg2 import sql
from dotenv import load_dotenv
import os
from datetime import datetime

users = []


class User:
    def __init__(self, user_id, first_name, last_name, email, scheduled_delete_date, date_deleted, has_been_deleted):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.scheduled_delete_date = scheduled_delete_date
        self.date_deleted = date_deleted
        self.has_been_deleted = has_been_deleted


def connect_to_database():
    load_dotenv()

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_dialect = os.getenv("DB_DIALECT")

    connection = psycopg2.connect(
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name,
        db_dialect=db_dialect
    )
    return connection


# Define a function to check if a timestamp is older than 2 months
def is_old(timestamp):
    current_time = datetime.now()
    last_seen_time = datetime.fromtimestamp(timestamp / 1000)  # Convert milliseconds to seconds
    delta = current_time - last_seen_time
    threshold_str = os.getenv("DELETE_THRESHOLD")

    if threshold_str:
        threshold = int(threshold_str)
        return delta >= timedelta(days=threshold)  # Assuming 30 days is 2 months


def get_future_timestamp():
    delete_date_days_str = os.getenv("DELETE_DATE")
    if delete_date_days_str:
        delete_date_days = int(delete_date_days_str)
        current_date = datetime.now()
        future_date = current_date + timedelta(days=delete_date_days)
        return future_date


def remove_user(user_id, first_name, last_name, email):
    headers = {"Authorization": os.getenv("LAUNCH_DARKLY_KEY")}
    print(f"User {user_id} has name  {first_name}  {last_name} and email: {email} not logged in for 2 months.")
    url = f"https://app.launchdarkly.com/api/v2/members/{user_id}"
    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        print("Success")
    else:
        data = response.json()
        print(data)


def query_launch_darkly():
    url = "https://app.launchdarkly.com/api/v2/members"

    headers = {"Authorization": os.getenv("LAUNCH_DARKLY_KEY")}

    response = requests.get(url, headers=headers)

    data = response.json()

    # Iterate through each user in the response
    for item in data['items']:
        if '_lastSeen' in item:
            user_last_seen = item['_lastSeen']
        else:
            if user_role != 'owner' and user_role != 'admin':
                users.append(User(user_id=item['_id'], first_name=item['firstName'], last_name=item['lastName'],
                                  email=item['email']))

        if '_id' in item:
            user_id = item['_id']
        else:
            print("User id seen attribute not found.")

        if 'role' in item:
            user_role = item['role']
        else:
            print("User role seen attribute not found.")

        if 'firstName' in item:
            first_name = item['firstName']
        else:
            if user_role != 'owner' and user_role != 'admin':
                print("User firstName seen attribute not found.")

        if 'lastName' in item:
            last_name = item['lastName']
        else:
            if user_role != 'owner' and user_role != 'admin':
                print("User lastName seen attribute not found.")

        if 'email' in item:
            email = item['email']
        else:
            print("User email seen attribute not found.")

        if '_pendingInvite' in item:
            pending_invite = item['_pendingInvite']
        else:
            print("User pendingInvite attribute not found.")

        if pending_invite == 'True' and user_role != 'owner' and user_role != 'admin':
            users.append(User(user_id=user_id, first_name=first_name, last_name=last_name, email=email))

        if is_old(user_last_seen) and user_role != 'owner' and user_role != 'admin':
            users.append(User(user_id=user_id, first_name=first_name, last_name=last_name, email=email))


def send_audit_email(pass_in_user):
    # Email configuration
    sender_email = os.getenv("DELETE_THRESHOLD")
    sender_password = os.getenv("DELETE_THRESHOLD")
    recipient_email = pass_in_user.email

    subject = "Action Required: Launch Darkly Account Scheduled For Delete"
    message = (f"Hello {pass_in_user.first_name} {pass_in_user.last_name}, "
               f"This a courtesy email to warn you that your Launch Darkly email"
               f"is scheduled for deletion on {get_future_timestamp()} if you'd like to retain your Launch"
               f"Darkly account please login to the web Launch Darkly portal.")

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    # Establish a secure session with the Gmail SMTP server
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT") | 5349
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()

    # Log in to the server
    server.login(sender_email, sender_password)

    # Send the email
    server.sendmail(sender_email, recipient_email, msg.as_string())

    # Quit the server
    server.quit()

    print("Email sent successfully.")


def insert_employee_record(connection, pass_in_user):
    try:
        query = sql.SQL(
            "INSERT INTO employee (employee_id, first_name, last_name, email, scheduled_delete_date, has_been_deleted) "
            "VALUES (%s, %s, %s, %s)"
        )
        values = (pass_in_user.user_id, pass_in_user.first_name, pass_in_user.last_name, pass_in_user.email, get_future_timestamp(), False)

        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()
        print("Record inserted successfully.")
    except Exception as e:
        print("Error:", e)
        connection.rollback()
    finally:
        cursor.close()


def check_employee_exists(connection, employee_id):
    query = sql.SQL("SELECT EXISTS(SELECT 1 FROM employee WHERE employee_id = %s)")
    values = (employee_id,)

    try:
        cursor = connection.cursor()
        cursor.execute(query, values)
        return cursor.fetchone()[0]
    except Exception as e:
        print("Error:", e)
    finally:
        cursor.close()


def get_user_by_id(connection, user_id):
    query = sql.SQL("SELECT * FROM employee WHERE employee_id = %s")
    values = (user_id,)

    try:
        cursor = connection.cursor()
        cursor.execute(query, values)
        result = cursor.fetchone()

        if result:
            return User(result[0], result[1], result[2], result[3], result[4], result[5], result[6])
        else:
            return None
    except Exception as e:
        print("Error:", e)
    finally:
        cursor.close()


def update_has_been_deleted(connection, user_id):
    query = sql.SQL("UPDATE employee SET has_been_deleted = %s WHERE employee_id = %s")
    values = (True, user_id)

    try:
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()
        print(f"Employee with ID {user_id} has been marked as deleted.")
    except Exception as e:
        print("Error:", e)
        connection.rollback()
    finally:
        cursor.close()


if __name__ == "__main__":
    db_connection = connect_to_database()

    for user in users:
        exists = check_employee_exists(db_connection, user.user_id)
        if exists:
            print(
                f"User with ID {user.user_id} exists in the"
                f" database checking to see if they have not "
                f"been deleted and are scheduled to be deleted.")
            db_user = get_user_by_id(db_connection, user.user_id)

            if db_user.has_been_deleted is False and db_user.scheduled_delete_date == datetime.now().date():
                print(
                    f"User {db_user.user_id} has name {db_user.first_name} "
                    f"{db_user.last_name} and email: {db_user.email} not logged in for 2 months.")
                remove_user(db_user.user_id)
                update_has_been_deleted(db_user.user_id)
        else:
            print(f"User with ID {user.user_id} does not exist in the database.")
            insert_employee_record(user)
            send_audit_email(user)

    db_connection.close()
