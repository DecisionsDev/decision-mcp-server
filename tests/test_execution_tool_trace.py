import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, mock_open, MagicMock
from decision_mcp_server.ExecutionToolTrace import ExecutionToolTrace, DiskTraceStorage


class TestExecutionToolTrace:
    """Test suite for the ExecutionToolTrace class"""

    @pytest.fixture
    def sample_trace(self):
        """Create a sample trace for testing"""
        return ExecutionToolTrace(
            tool_name="test_tool",
            ruleset_path="/test/path",
            inputs={"param1": "value1"},
            results={"result": "success"},
            decision_id="test-123",
            decision_trace={"rule1": "fired"}
        )

    @pytest.fixture
    def sample_trace_dict(self):
        """Create a sample trace dictionary for testing"""
        return {
            "id": "test_tool_12345_test-123",
            "tool_name": "test_tool",
            "ruleset_path": "/test/path",
            "timestamp": "2023-01-01T12:00:00",
            "inputs": {"param1": "value1"},
            "results": {"result": "success"},
            "decision_id": "test-123",
            "decision_trace": {"rule1": "fired"}
        }

    def test_initialization(self, sample_trace):
        """Test that the ExecutionToolTrace initializes correctly"""
        assert sample_trace.tool_name == "test_tool"
        assert sample_trace.ruleset_path == "/test/path"
        assert sample_trace.inputs == {"param1": "value1"}
        assert sample_trace.results == {"result": "success"}
        assert sample_trace.decision_id == "test-123"
        assert sample_trace.decision_trace == {"rule1": "fired"}
        assert sample_trace.timestamp is not None
        assert sample_trace.id is not None
        assert "test_tool" in sample_trace.id
        assert "test-123" in sample_trace.id

    def test_to_dict(self, sample_trace):
        """Test conversion to dictionary"""
        trace_dict = sample_trace.to_dict()
        assert trace_dict["tool_name"] == "test_tool"
        assert trace_dict["ruleset_path"] == "/test/path"
        assert trace_dict["inputs"] == {"param1": "value1"}
        assert trace_dict["results"] == {"result": "success"}
        assert trace_dict["decision_id"] == "test-123"
        assert trace_dict["decision_trace"] == {"rule1": "fired"}
        assert "timestamp" in trace_dict
        assert "id" in trace_dict

    def test_to_json(self, sample_trace):
        """Test conversion to JSON string"""
        json_str = sample_trace.to_json()
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["tool_name"] == "test_tool"
        assert parsed["ruleset_path"] == "/test/path"
        assert parsed["inputs"] == {"param1": "value1"}
        assert parsed["results"] == {"result": "success"}

    def test_from_dict(self, sample_trace_dict):
        """Test creating a trace from a dictionary"""
        trace = ExecutionToolTrace.from_dict(sample_trace_dict)
        assert trace.tool_name == "test_tool"
        assert trace.ruleset_path == "/test/path"
        assert trace.inputs == {"param1": "value1"}
        assert trace.results == {"result": "success"}
        assert trace.decision_id == "test-123"
        assert trace.decision_trace == {"rule1": "fired"}
        assert trace.timestamp == "2023-01-01T12:00:00"
        assert trace.id == "test_tool_12345_test-123"

    def test_from_json(self):
        """Test creating a trace from a JSON string"""
        json_str = json.dumps({
            "id": "test_tool_12345_test-123",
            "tool_name": "test_tool",
            "ruleset_path": "/test/path",
            "timestamp": "2023-01-01T12:00:00",
            "inputs": {"param1": "value1"},
            "results": {"result": "success"},
            "decision_id": "test-123",
            "decision_trace": {"rule1": "fired"}
        })
        
        trace = ExecutionToolTrace.from_json(json_str)
        assert trace.tool_name == "test_tool"
        assert trace.ruleset_path == "/test/path"
        assert trace.inputs == {"param1": "value1"}
        assert trace.results == {"result": "success"}
        assert trace.decision_id == "test-123"
        assert trace.decision_trace == {"rule1": "fired"}
        assert trace.timestamp == "2023-01-01T12:00:00"
        assert trace.id == "test_tool_12345_test-123"


class TestDiskTraceStorage:
    """Test suite for the DiskTraceStorage class"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def storage(self, temp_dir):
        """Create a DiskTraceStorage instance for testing"""
        return DiskTraceStorage(storage_dir=temp_dir, max_traces=3)

    @pytest.fixture
    def sample_trace(self):
        """Create a sample trace for testing"""
        return ExecutionToolTrace(
            tool_name="test_tool",
            ruleset_path="/test/path",
            inputs={"param1": "value1"},
            results={"result": "success"},
            decision_id="test-123",
            decision_trace={"rule1": "fired"}
        )

    def test_initialization(self, storage, temp_dir):
        """Test that the storage initializes correctly"""
        assert storage.storage_dir == temp_dir
        assert storage.max_traces == 3
        assert isinstance(storage.trace_index, dict)
        assert os.path.exists(temp_dir)

    def test_initialization_default_dir(self):
        """Test initialization with default directory"""
        with patch('os.path.expanduser', return_value="/mock/home"):
            with patch('os.makedirs') as mock_makedirs:
                storage = DiskTraceStorage()
                assert storage.storage_dir == "/mock/home/.mcp-server/traces"
                mock_makedirs.assert_called_once_with("/mock/home/.mcp-server/traces", exist_ok=True)

    def test_add_trace(self, storage, sample_trace, temp_dir):
        """Test adding a trace to storage"""
        trace_id = storage.add(sample_trace)
        
        # Verify trace was added to index
        assert trace_id in storage.trace_index
        assert storage.trace_index[trace_id]["tool_name"] == "test_tool"
        
        # Verify file was created
        file_path = os.path.join(temp_dir, f"{trace_id}.json")
        assert os.path.exists(file_path)
        
        # Verify file content
        with open(file_path, 'r') as f:
            content = json.load(f)
            assert content["tool_name"] == "test_tool"
            assert content["ruleset_path"] == "/test/path"

    def test_enforce_max_traces(self, storage, sample_trace, temp_dir):
        """Test that old traces are removed when max is exceeded"""
        # Add 4 traces (max is 3)
        trace_ids = []
        for i in range(4):
            trace = ExecutionToolTrace(
                tool_name=f"tool_{i}",
                ruleset_path="/test/path",
                inputs={},
                results={},
                decision_id=f"id_{i}"
            )
            # Manually set timestamp to ensure predictable ordering
            trace.timestamp = f"2023-01-01T12:00:0{i}"
            trace_id = storage.add(trace)
            trace_ids.append(trace_id)
        
        # Verify oldest trace was removed
        assert trace_ids[0] not in storage.trace_index
        assert not os.path.exists(os.path.join(temp_dir, f"{trace_ids[0]}.json"))
        
        # Verify newer traces remain
        for i in range(1, 4):
            assert trace_ids[i] in storage.trace_index
            assert os.path.exists(os.path.join(temp_dir, f"{trace_ids[i]}.json"))

    def test_get_trace(self, storage, sample_trace):
        """Test retrieving a trace by ID"""
        trace_id = storage.add(sample_trace)
        retrieved_trace = storage.get(trace_id)
        
        assert retrieved_trace is not None
        assert retrieved_trace.tool_name == "test_tool"
        assert retrieved_trace.ruleset_path == "/test/path"
        assert retrieved_trace.inputs == {"param1": "value1"}
        assert retrieved_trace.results == {"result": "success"}

    def test_get_nonexistent_trace(self, storage):
        """Test retrieving a non-existent trace"""
        retrieved_trace = storage.get("nonexistent_id")
        assert retrieved_trace is None

    def test_get_trace_error_handling(self, storage, sample_trace):
        """Test error handling when retrieving a trace"""
        trace_id = storage.add(sample_trace)
        
        # Simulate file read error
        with patch('builtins.open', side_effect=Exception("File read error")):
            retrieved_trace = storage.get(trace_id)
            assert retrieved_trace is None

    def test_get_all_metadata(self, storage):
        """Test retrieving metadata for all traces"""
        # Add some traces
        traces = []
        for i in range(3):
            trace = ExecutionToolTrace(
                tool_name=f"tool_{i}",
                ruleset_path="/test/path",
                inputs={},
                results={},
                decision_id=f"id_{i}"
            )
            trace_id = storage.add(trace)
            traces.append((trace_id, trace))
        
        # Get metadata
        metadata_list = storage.get_all_metadata()
        
        # Verify metadata
        assert len(metadata_list) == 3
        for metadata in metadata_list:
            assert "id" in metadata
            assert "tool_name" in metadata
            assert "timestamp" in metadata
            
            # Find matching trace
            matching_traces = [t for tid, t in traces if tid == metadata["id"]]
            if matching_traces:
                assert metadata["tool_name"] == matching_traces[0].tool_name

    def test_clear(self, storage, temp_dir):
        """Test clearing all traces"""
        # Add some traces
        for i in range(3):
            trace = ExecutionToolTrace(
                tool_name=f"tool_{i}",
                ruleset_path="/test/path",
                inputs={},
                results={},
                decision_id=f"id_{i}"
            )
            storage.add(trace)
        
        # Verify files exist
        assert len(os.listdir(temp_dir)) == 3
        
        # Clear traces
        storage.clear()
        
        # Verify files are gone and index is empty
        assert len(os.listdir(temp_dir)) == 0
        assert len(storage.trace_index) == 0

    def test_clear_error_handling(self, storage):
        """Test error handling when clearing traces"""
        # Add a trace
        trace = ExecutionToolTrace(
            tool_name="test_tool",
            ruleset_path="/test/path",
            inputs={},
            results={},
            decision_id="test_id"
        )
        trace_id = storage.add(trace)
        
        # Simulate file removal error
        with patch('os.remove', side_effect=Exception("File removal error")):
            # This should not raise an exception
            storage.clear()
            # Index should still be cleared
            assert len(storage.trace_index) == 0

    def test_initialize_index_error_handling(self, temp_dir):
        """Test error handling during index initialization"""
        # Create a malformed JSON file
        with open(os.path.join(temp_dir, "malformed.json"), 'w') as f:
            f.write("This is not valid JSON")
        
        # Initialize storage - should not raise exception
        with patch('logging.getLogger') as mock_logger:
            storage = DiskTraceStorage(storage_dir=temp_dir)
            # Verify logger was called for the error
            assert mock_logger.return_value.warning.called

# Made with Bob
