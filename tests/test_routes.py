"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...

    def test_read_account(self):
        """It should Read a single account using the Location header"""
        created = self.client.post(BASE_URL, json=AccountFactory().serialize())
        response = self.client.get(created.headers['Location'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), created.get_json())

    def test_read_missing_account(self):
        """It should return 404 when reading a missing account"""
        self.assertEqual(self.client.get('/accounts/99999').status_code, 404)

    def test_list_accounts(self):
        """It should List all accounts and return an empty list when none exist"""
        self.assertEqual(self.client.get(BASE_URL).get_json(), [])
        accounts = self._create_accounts(3)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual({a['id'] for a in response.get_json()}, {a.id for a in accounts})

    def test_filter_accounts(self):
        """It should filter accounts by name"""
        account = self._create_accounts(1)[0]
        self.assertEqual(len(self.client.get(BASE_URL, query_string={'name': account.name}).get_json()), 1)

    def test_update_account(self):
        """It should Update an account and persist the changed fields"""
        account = self._create_accounts(1)[0]
        data = account.serialize()
        data['name'] = 'Jane Doe'
        data['id'] = 99999
        url = f'{BASE_URL}/{account.id}'
        response = self.client.put(url, json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['id'], account.id)
        self.assertEqual(self.client.get(url).get_json()['name'], 'Jane Doe')

    def test_update_missing_account(self):
        """It should return 404 when updating a missing account"""
        response = self.client.put('/accounts/99999', json=AccountFactory().serialize())
        self.assertEqual(response.status_code, 404)

    def test_update_invalid_body(self):
        """It should reject incomplete update data"""
        account = self._create_accounts(1)[0]
        self.assertEqual(self.client.put(f'{BASE_URL}/{account.id}', json={}).status_code, 400)

    def test_update_wrong_media_type(self):
        """It should reject an update with an unsupported media type"""
        self.assertEqual(self.client.put('/accounts/1', data='no JSON', content_type='text/plain').status_code, 415)

    def test_delete_account(self):
        """It should Delete an account and return an empty response"""
        account = self._create_accounts(1)[0]
        url = f'{BASE_URL}/{account.id}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_security_headers(self):
        """It should set security headers using Talisman"""
        response = self.client.get('/')
        self.assertEqual(response.headers['X-Frame-Options'], 'SAMEORIGIN')
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertIn("default-src 'self'", response.headers['Content-Security-Policy'])
        self.assertIn('Strict-Transport-Security', self.client.get('/', base_url='https://localhost').headers)

    def test_cors(self):
        """It should allow CORS and answer a preflight request"""
        origin = 'https://example.com'
        response = self.client.get(BASE_URL, headers={'Origin': origin})
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], origin)
        preflight = self.client.options(BASE_URL, headers={
            'Origin': origin, 'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'})
        self.assertEqual(preflight.status_code, 200)
        self.assertIn('POST', preflight.headers['Access-Control-Allow-Methods'])

    def test_method_not_allowed(self):
        """It should reject unsupported methods with a JSON error"""
        self.assertEqual(self.client.patch('/accounts/1').status_code, 405)

    def test_bad_date(self):
        """It should reject invalid account dates"""
        data = AccountFactory().serialize()
        data['date_joined'] = 'invalid-date'
        self.assertEqual(self.client.post(BASE_URL, json=data).status_code, 400)

    def test_bad_json(self):
        """It should reject malformed JSON"""
        self.assertEqual(self.client.post(BASE_URL, data='{', content_type='application/json').status_code, 400)

    def test_optional_fields(self):
        """It should default omitted date and phone fields"""
        from datetime import date
        data = {'name': 'Test', 'email': 'test@example.com', 'address': 'Example'}
        response = self.client.post(BASE_URL, json=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()['date_joined'], date.today().isoformat())
        self.assertIsNone(response.get_json()['phone_number'])

    def test_internal_error_handler(self):
        """It should produce a JSON 500 error response"""
        from service.common.error_handlers import internal_server_error
        with app.test_request_context():
            response, code = internal_server_error('test error')
        self.assertEqual(code, 500)
        self.assertEqual(response.get_json()['status'], 500)
