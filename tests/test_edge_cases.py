import pytest
import os
import yaml
from pipeline.edge_cases import EdgeCaseManager
from unittest.mock import patch, mock_open

@pytest.fixture
def mock_config():
    return {
        "pipeline": {
            "group_proximity_pixels": 150,
            "child_height_ratio": 0.6
        }
    }

def test_staff_identification(mock_config):
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config))):
        manager = EdgeCaseManager("dummy_path")
        
        # Track 1 enters normal zone
        assert manager.identify_staff(1, "makeup") is False
        
        # Track 1 enters staff zone
        assert manager.identify_staff(1, "backroom") is True
        
        # Track 1 is now marked as staff everywhere
        assert manager.identify_staff(1, "makeup") is True

def test_group_detection(mock_config):
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config))):
        manager = EdgeCaseManager("dummy_path")
        
        # Track 1 at (100, 100)
        group1 = manager.update_positions_and_groups(1, 100, 100)
        assert group1 is None
        
        # Track 2 at (150, 150) -> dist = 70.7 < 150 -> should join group
        group2 = manager.update_positions_and_groups(2, 150, 150)
        assert group2 is not None
        assert manager.track_groups[1] == group2
        
        # Track 3 at (500, 500) -> too far
        group3 = manager.update_positions_and_groups(3, 500, 500)
        assert group3 is None

def test_child_heuristic(mock_config):
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config))):
        manager = EdgeCaseManager("dummy_path")
        
        # Adult bbox (height = 600)
        adult_bbox = [0, 0, 100, 600]
        assert manager.check_child(adult_bbox, average_height=600.0) is False
        
        # Child bbox (height = 300)
        child_bbox = [0, 0, 100, 300]
        assert manager.check_child(child_bbox, average_height=600.0) is True
