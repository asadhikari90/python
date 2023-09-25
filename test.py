import unittest
from unittest.mock import MagicMock, patch
from main import User, connect_to_database, is_old, remove_user, insert_employee_record, check_employee_exists, \
    get_user_by_id, update_has_been_deleted, send_audit_email, query_launch_darkly


class TestScript(unittest.TestCase):

    @patch('main.os.getenv')
    def test_connect_to_database(self, mock_getenv):
        # Mock the environment variables
        mock_getenv.side_effect = lambda key: {
            "DB_USER": "your_db_user",
            "DB_PASSWORD": "your_db_password",
            "DB_HOST": "your_db_host",
            "DB_PORT": "your_db_port",
            "DB_NAME": "your_db_name",
            "DB_DIALECT": "your_db_dialect"
        }.get(key)

        # Test the connect_to_database function
        conn = connect_to_database()
        self.assertIsNotNone(conn)
        conn.close()  # Close the connection

    def test_is_old(self):
        # Test the is_old function with a timestamp (modify as needed)
        timestamp = 1632384000000  # Replace with a timestamp from your test data
        result = is_old(timestamp)
        self.assertTrue(result)  # Modify the assertion as needed

    @patch('main.requests.delete')
    def test_remove_user(self, mock_delete):
        # Mock the requests.delete method
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        # Test the remove_user function
        user_id = "test_user_id"
        first_name = "John"
        last_name = "Doe"
        email = "johndoe@example.com"
        remove_user(user_id, first_name, last_name, email)

        # Assert that requests.delete was called with the correct URL and headers
        mock_delete.assert_called_once_with(
            f"https://app.launchdarkly.com/api/v2/members/{user_id}",
            headers={"Authorization": "your_launchdarkly_key"}
        )

    @patch('main.requests.get')
    def test_query_launch_darkly(self, mock_get):
        # Mock the requests.get method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {
                    '_id': 'user1',
                    'firstName': 'John',
                    'lastName': 'Doe',
                    'email': 'johndoe@example.com',
                    '_lastSeen': 1632384000000,
                    'role': 'user',
                    '_pendingInvite': 'True'
                },
                # Add more test data as needed
            ]
        }
        mock_get.return_value = mock_response

        # Test the query_launch_darkly function
        query_launch_darkly()

        # Assert that requests.get was called with the correct URL and headers
        mock_get.assert_called_once_with(
            "https://app.launchdarkly.com/api/v2/members",
            headers={"Authorization": "your_launchdarkly_key"}
        )

    @patch('main.smtplib.SMTP')
    def test_send_audit_email(self, mock_smtp):
        # Mock the smtplib.SMTP class
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        # Test the send_audit_email function
        user = User("test_user_id", "John", "Doe", "johndoe@example.com", None, None, None)
        send_audit_email(user)

        # Assert that the SMTP server was used to send the email
        mock_smtp.assert_called_once_with("your_smtp_server", 5349)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("your_delete_threshold", "your_delete_threshold")
        mock_server.sendmail.assert_called_once()

    @patch('main.psycopg2.connect')
    def test_insert_employee_record(self, mock_connect):
        # Mock the database connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Mock the cursor.execute method
        mock_cursor.execute.return_value = None

        # Create a User object for testing
        user = User("test_user_id", "John", "Doe", "johndoe@example.com", None, None, None)

        # Test the insert_employee_record function
        insert_employee_record(mock_connection, user)

        # Assert that the cursor.execute and connection.commit methods were called
        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
    @patch('main.psycopg2.connect')
    def test_check_employee_exists(self, mock_connect):
        # Mock the database connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Mock the cursor.fetchone method
        mock_cursor.fetchone.return_value = (True,)  # Employee exists in the database

        # Test the check_employee_exists function
        employee_id = "test_employee_id"
        result = check_employee_exists(mock_connection, employee_id)
        self.assertTrue(result)  # Modify the assertion as needed

    @patch('main.psycopg2.connect')
    def test_get_user_by_id(self, mock_connect):
        # Mock the database connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Mock the cursor.fetchone method
        mock_cursor.fetchone.return_value = (1, "John", "Doe", "johndoe@example.com", None, None, False)

        # Test the get_user_by_id function
        user_id = "test_user_id"
        result = get_user_by_id(mock_connection, user_id)
        self.assertIsNotNone(result)
        self.assertEqual(result.user_id, 1)
        self.assertEqual(result.first_name, "John")
        self.assertEqual(result.last_name, "Doe")
        self.assertEqual(result.email, "johndoe@example.com")
        self.assertIsNone(result.scheduled_delete_date)
        self.assertIsNone(result.date_deleted)
        self.assertFalse(result.has_been_deleted)

    @patch('main.psycopg2.connect')
    def test_update_has_been_deleted(self, mock_connect):
        # Mock the database connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Test the update_has_been_deleted function
        user_id = "test_user_id"
        update_has_been_deleted(mock_connection, user_id)

        # Assert that the cursor.execute and connection.commit methods were called
        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
