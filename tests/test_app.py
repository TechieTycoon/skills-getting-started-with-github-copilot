"""
Test suite for the High School Management System API using AAA pattern.

The AAA (Arrange-Act-Assert) pattern structures each test with three clear sections:
- Arrange: Set up test data and conditions
- Act: Execute the code being tested
- Assert: Verify the results

Best Practices Applied:
- Constants for test data to avoid magic strings
- Comprehensive fixtures for test setup
- Parameterized tests for testing multiple scenarios
- Descriptive assertion messages
- Clear test isolation and independence
- Focused, single-responsibility tests
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

# ========== Test Constants ==========
# HTTP Status Codes
STATUS_OK = 200
STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND = 404
STATUS_REDIRECT = 307

# Test Activities (matching the application data)
ACTIVITY_CHESS = "Chess Club"
ACTIVITY_PROGRAMMING = "Programming Class"
ACTIVITY_DRAMA = "Drama Club"
ACTIVITY_NONEXISTENT = "Underwater Basket Weaving"

# Test Email Addresses
EMAIL_EXISTING_STUDENT = "michael@mergington.edu"
EMAIL_NEW_STUDENT = "newstudent@mergington.edu"
EMAIL_DRAMA_STUDENT = "newdramaactor@mergington.edu"
EMAIL_TEST_STUDENT = "student@mergington.edu"

# Expected Response Fields
REQUIRED_ACTIVITY_FIELDS = {"description", "schedule", "max_participants", "participants"}


# ========== Fixtures ==========
@pytest.fixture
def client():
    """Fixture to provide a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def activities_list(client):
    """Fixture to retrieve all activities from the endpoint."""
    response = client.get("/activities")
    return response.json()


@pytest.fixture
def valid_activities():
    """Fixture providing valid activity names for testing."""
    return [ACTIVITY_CHESS, ACTIVITY_PROGRAMMING, ACTIVITY_DRAMA]


@pytest.fixture
def test_emails():
    """Fixture providing test email addresses."""
    return {
        "existing": EMAIL_EXISTING_STUDENT,
        "new": EMAIL_NEW_STUDENT,
        "drama": EMAIL_DRAMA_STUDENT,
        "generic": EMAIL_TEST_STUDENT,
    }



class TestGetActivities:
    """Test suite for the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities."""
        # Arrange: Test is ready with client fixture

        # Act: Send GET request to /activities endpoint
        response = client.get("/activities")

        # Assert: Verify response status and content
        assert response.status_code == STATUS_OK, "Expected 200 OK status"
        activities = response.json()
        assert isinstance(activities, dict), "Response should be a dictionary"
        assert len(activities) > 0, "Should return at least one activity"
        assert ACTIVITY_CHESS in activities, f"Should contain {ACTIVITY_CHESS}"
        assert ACTIVITY_PROGRAMMING in activities, f"Should contain {ACTIVITY_PROGRAMMING}"

    @pytest.mark.parametrize("activity_name", [ACTIVITY_CHESS, ACTIVITY_PROGRAMMING, ACTIVITY_DRAMA])
    def test_get_activities_all_contain_required_fields(self, client, activity_name):
        """Test that all activities contain required fields."""
        # Arrange: Expected fields are defined in constants

        # Act: Fetch activities from the endpoint
        response = client.get("/activities")
        activities = response.json()

        # Assert: Verify activity exists and has all required fields
        assert activity_name in activities, f"Activity {activity_name} should exist"
        activity_data = activities[activity_name]
        
        assert isinstance(activity_data, dict), f"{activity_name} data should be a dictionary"
        assert REQUIRED_ACTIVITY_FIELDS.issubset(
            activity_data.keys()
        ), f"{activity_name} missing required fields"
        assert isinstance(
            activity_data["participants"], list
        ), f"{activity_name} participants should be a list"
        assert isinstance(
            activity_data["max_participants"], int
        ), f"{activity_name} max_participants should be an integer"
        assert activity_data["max_participants"] > 0, f"{activity_name} max_participants should be positive"

    def test_get_activities_contains_chess_club_with_correct_details(self, client):
        """Test that Chess Club activity exists with correct details."""
        # Arrange: Define expected Chess Club data
        expected_description = "Learn strategies and compete in chess tournaments"
        expected_schedule_keyword = "Fridays"

        # Act: Retrieve activities
        response = client.get("/activities")
        activities = response.json()

        # Assert: Verify Chess Club exists and has correct details
        assert ACTIVITY_CHESS in activities, f"Should contain {ACTIVITY_CHESS} activity"
        chess_data = activities[ACTIVITY_CHESS]
        
        assert (
            chess_data["description"] == expected_description
        ), f"Chess Club description mismatch"
        assert (
            expected_schedule_keyword in chess_data["schedule"]
        ), f"Chess Club schedule should contain {expected_schedule_keyword}"

    def test_get_activities_response_structure(self, activities_list):
        """Test that activities response has valid structure."""
        # Arrange: Expected response structure

        # Act: Activity list already fetched via fixture

        # Assert: Validate structure
        for activity_name, activity_data in activities_list.items():
            assert isinstance(activity_name, str), f"Activity name should be string"
            assert isinstance(activity_data, dict), f"Activity data should be dictionary"
            assert len(activity_name) > 0, f"Activity name should not be empty"



class TestSignupForActivity:
    """Test suite for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_student_succeeds(self, client):
        """Test that a new student can successfully sign up for an activity."""
        # Arrange: Prepare signup data for a new student
        activity_name = ACTIVITY_CHESS
        new_email = EMAIL_NEW_STUDENT

        # Act: Send POST request to signup endpoint
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert: Verify successful signup
        assert response.status_code == STATUS_OK, "Signup should return 200 OK"
        response_data = response.json()
        assert "message" in response_data, "Response should contain 'message' field"
        assert "Signed up" in response_data["message"], "Message should contain 'Signed up'"
        assert new_email in response_data["message"], "Message should contain the student email"

    @pytest.mark.parametrize("activity_name", [ACTIVITY_CHESS, ACTIVITY_PROGRAMMING, ACTIVITY_DRAMA])
    def test_signup_new_student_to_multiple_activities(self, client, activity_name):
        """Test that a new student can sign up for different activities."""
        # Arrange: Create unique email for this test
        test_email = f"multi_activity_{activity_name.lower()}@mergington.edu"

        # Act: Sign up for the activity
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )

        # Assert: Verify successful signup to the activity
        assert response.status_code == STATUS_OK, f"Should be able to sign up for {activity_name}"
        assert activity_name in response.json()["message"], f"Message should mention {activity_name}"

    def test_signup_already_registered_student_fails(self, client):
        """Test that a student cannot sign up twice for the same activity."""
        # Arrange: Prepare data for a student already registered
        activity_name = ACTIVITY_CHESS
        existing_email = EMAIL_EXISTING_STUDENT

        # Act: Attempt to sign up with an already registered email
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )

        # Assert: Verify signup fails with appropriate error
        assert response.status_code == STATUS_BAD_REQUEST, "Should return 400 Bad Request"
        response_data = response.json()
        assert "detail" in response_data, "Response should contain 'detail' field"
        assert "Already registered" in response_data["detail"], "Should indicate already registered"

    def test_signup_for_nonexistent_activity_fails(self, client):
        """Test that signup for a non-existent activity returns 404."""
        # Arrange: Prepare data for a non-existent activity
        nonexistent_activity = ACTIVITY_NONEXISTENT
        student_email = EMAIL_TEST_STUDENT

        # Act: Attempt to sign up for activity that doesn't exist
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": student_email}
        )

        # Assert: Verify 404 error is returned
        assert response.status_code == STATUS_NOT_FOUND, "Should return 404 Not Found"
        response_data = response.json()
        assert "detail" in response_data, "Response should contain 'detail' field"
        assert "Activity not found" in response_data["detail"], "Should indicate activity not found"

    def test_signup_response_contains_confirmation_message(self, client):
        """Test that signup response contains a proper confirmation message."""
        # Arrange: Set up signup parameters
        activity_name = ACTIVITY_DRAMA
        test_email = EMAIL_DRAMA_STUDENT

        # Act: Submit signup request
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )

        # Assert: Verify response structure and message content
        assert response.status_code == STATUS_OK, "Signup should succeed"
        json_response = response.json()
        
        assert "message" in json_response, "Response should have 'message' field"
        assert activity_name in json_response["message"], f"Message should contain activity name: {activity_name}"
        assert test_email in json_response["message"], f"Message should contain email: {test_email}"

    def test_signup_with_empty_email(self, client):
        """Test that signup with an empty email is accepted (no validation)."""
        # Arrange: Prepare request with empty email

        # Act: Submit signup with empty email
        response = client.post(
            f"/activities/{ACTIVITY_CHESS}/signup",
            params={"email": ""}
        )

        # Assert: Verify API accepts it (no email validation)
        # Note: The API does not validate email format
        assert response.status_code == STATUS_OK, "API accepts empty email (no validation)"
        assert "message" in response.json(), "Should still return a response"



class TestRootEndpoint:
    """Test suite for the root endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static index.html."""
        # Arrange: Prepare test client with follow_redirects disabled
        
        # Act: Send GET request to root endpoint
        response = client.get("/", follow_redirects=False)

        # Assert: Verify redirect status code and location
        assert response.status_code == STATUS_REDIRECT, "Should return 307 Temporary Redirect"
        assert "location" in response.headers, "Should contain 'location' header"
        assert "/static/index.html" in response.headers["location"], "Should redirect to static/index.html"

    def test_root_endpoint_with_follow_redirects(self, client):
        """Test that following redirects from root leads to static index.html."""
        # Arrange: Prepare to follow redirects

        # Act: Send GET request with redirects enabled
        response = client.get("/", follow_redirects=True)

        # Assert: Verify that we reach the static file
        assert response.status_code == STATUS_OK, "Should eventually return 200 OK"
        # The response should be HTML content (not a redirect response)
        assert response.headers.get("content-type", "").startswith(
            "text/html"
        ), "Should return HTML content"


# ========== Test Execution Notes ==========
"""
Running the tests:
  pytest tests/test_app.py                 # Run all tests
  pytest tests/test_app.py -v              # Verbose output
  pytest tests/test_app.py -k "signup"     # Run tests matching "signup"
  pytest tests/test_app.py --tb=short      # Short traceback format
  
Best practices implemented in this test suite:
1. ✅ AAA Pattern: Clear Arrange-Act-Assert structure
2. ✅ Constants: All magic strings defined as module constants
3. ✅ Fixtures: Reusable test setup and data
4. ✅ Parameterization: Test multiple scenarios with @pytest.mark.parametrize
5. ✅ Assertion Messages: Descriptive messages for failed assertions
6. ✅ Test Isolation: Each test is independent and self-contained
7. ✅ Naming Conventions: Clear, descriptive test names
8. ✅ Documentation: Comprehensive docstrings and comments
9. ✅ DRY Principle: No test data duplication
10. ✅ Edge Cases: Tests for error conditions and invalid inputs
"""
