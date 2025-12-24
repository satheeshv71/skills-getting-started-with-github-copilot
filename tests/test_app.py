import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to original state after each test"""
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball": {
            "description": "Learn basketball skills and participate in friendly games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Tennis coaching and competitive matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 8,
            "participants": ["alex@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and mixed media art projects",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["isabella@mergington.edu", "grace@mergington.edu"]
        },
        "Drama Club": {
            "description": "Theater performances and acting workshops",
            "schedule": "Mondays and Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["lucas@mergington.edu"]
        },
        "Debate Team": {
            "description": "Competitive debate and public speaking skills",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["aaron@mergington.edu", "mia@mergington.edu"]
        },
        "Science Olympiad": {
            "description": "STEM competitions and scientific research projects",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": ["ryan@mergington.edu"]
        }
    }
    yield
    # Reset after test
    activities.clear()
    activities.update(original_activities)


class TestActivitiesEndpoint:
    """Tests for /activities GET endpoint"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9
    
    def test_activity_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    """Tests for /activities/{activity_name}/signup POST endpoint"""
    
    def test_signup_for_activity(self, client, reset_activities):
        """Test signing up for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activity = activities_response.json()["Chess Club"]
        assert "newstudent@mergington.edu" in activity["participants"]
    
    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that duplicate signups are prevented"""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_multiple_participants(self, client, reset_activities):
        """Test that multiple different students can sign up"""
        client.post("/activities/Tennis%20Club/signup?email=student1@test.edu")
        client.post("/activities/Tennis%20Club/signup?email=student2@test.edu")
        
        activities_response = client.get("/activities")
        activity = activities_response.json()["Tennis Club"]
        assert "student1@test.edu" in activity["participants"]
        assert "student2@test.edu" in activity["participants"]


class TestUnregisterEndpoint:
    """Tests for /activities/{activity_name}/unregister POST endpoint"""
    
    def test_unregister_from_activity(self, client, reset_activities):
        """Test unregistering from an activity"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activity = activities_response.json()["Chess Club"]
        assert "michael@mergington.edu" not in activity["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregistering from an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_student_not_in_activity(self, client, reset_activities):
        """Test unregistering a student who is not in the activity"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=notinclass@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()


class TestSignupAndUnregisterFlow:
    """Integration tests for signup and unregister workflows"""
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test signing up then unregistering from an activity"""
        email = "testuser@mergington.edu"
        activity_name = "Basketball"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signed up
        get_response = client.get("/activities")
        activity = get_response.json()[activity_name]
        assert email in activity["participants"]
        initial_count = len(activity["participants"])
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        get_response = client.get("/activities")
        activity = get_response.json()[activity_name]
        assert email not in activity["participants"]
        assert len(activity["participants"]) == initial_count - 1
    
    def test_reregister_after_unregister(self, client, reset_activities):
        """Test that a student can re-register after unregistering"""
        email = "testuser@mergington.edu"
        activity_name = "Drama Club"
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Unregister
        client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        # Re-register should work
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify re-registered
        get_response = client.get("/activities")
        activity = get_response.json()[activity_name]
        assert email in activity["participants"]
