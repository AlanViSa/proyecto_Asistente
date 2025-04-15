import pytest
from datetime import datetime, time
from app.services.faq_service import FAQService

@pytest.fixture
def faq_service():
    return FAQService()

def test_schedule_initialization(faq_service):
    """Tests the correct initialization of schedules"""
    assert faq_service.opening_time == time(9, 0)
    assert faq_service.closing_time == time(20, 0)

def test_available_services(faq_service):
    """Tests that services are correctly configured"""
    assert "womens_cut" in faq_service.services
    assert "mens_cut" in faq_service.services
    assert "dye" in faq_service.services
    
    service = faq_service.services["womens_cut"]
    assert "name" in service
    assert "duration" in service
    assert "description" in service

def test_get_service_info(faq_service):
    """Tests getting service information"""
    service = faq_service.get_service_info("womens_cut")
    assert service is not None
    assert service["name"] == "Women's Cut"
    assert service["duration"] == 60
    
    # Test non-existent service
    invalid_service = faq_service.get_service_info("non_existent_service")
    assert invalid_service is None

def test_get_service_duration(faq_service):
    """Tests getting service duration"""
    duration = faq_service.get_service_duration("womens_cut")
    assert duration == 60
    
    # Test non-existent service (should return the default value)
    default_duration = faq_service.get_service_duration("non_existent_service")
    assert default_duration == 60

def test_get_faq_response(faq_service):
    """Tests getting answers to frequently asked questions"""
    response = faq_service.get_faq_response("schedule")
    assert response is not None
    assert "business hours" in response.lower()
    
    # Test non-existent question
    invalid_response = faq_service.get_faq_response("non_existent_question")
    assert invalid_response is None

def test_is_time_slot_available(faq_service):
    """Tests the validation of available time slots"""
    # Time slot within the range
    valid_date = datetime(2024, 3, 21, 14, 30)  # 2:30 PM
    assert faq_service.is_time_slot_available(valid_date) is True
    
    # Time slot outside the range
    invalid_date = datetime(2024, 3, 21, 22, 0)  # 10:00 PM
    assert faq_service.is_time_slot_available(invalid_date) is False

def test_get_next_available_time_slot(faq_service):
    """Tests getting the next available time slot"""
    # Time before opening
    early_date = datetime(2024, 3, 21, 7, 0)  # 7:00 AM
    next_slot = faq_service.get_next_available_time_slot(early_date)
    assert next_slot.hour == 9
    assert next_slot.minute == 0
    
    # Time after closing
    late_date = datetime(2024, 3, 21, 21, 0)  # 9:00 PM
    next_slot = faq_service.get_next_available_time_slot(late_date)
    assert next_slot.day == late_date.day + 1
    assert next_slot.hour == 9
    assert next_slot.minute == 0

def test_validate_service(faq_service):
    """Tests service validation"""
    assert faq_service.validate_service("womens_cut") is True
    assert faq_service.validate_service("WOMENS_CUT") is True  # Test case-insensitive
    assert faq_service.validate_service("non_existent_service") is False

def test_generate_services_list(faq_service):
    """Tests the generation of the services list"""
    service_list = faq_service._generate_services_list()
    assert isinstance(service_list, str)
    assert "Women's Cut" in service_list
    assert "min" in service_list
    assert "📌" in service_list  # Checks that it includes emojis