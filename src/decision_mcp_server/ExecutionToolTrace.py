from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import os
import glob
import logging
import time

class ExecutionToolTrace:
    """
    Class to store details about a decision service execution.
    Captures all relevant information for tracing and debugging purposes.
    """
    
    def __init__(
        self, 
        tool_name: str, 
        ruleset_path: str, 
        inputs: Dict[str, Any],
        results: Any,
        decision_id: Optional[str] = None,
        decision_trace: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new ExecutionToolTrace.
        
        Args:
            tool_name: The name of the tool that was executed
            ruleset_path: The path to the ruleset that was used
            inputs: The input parameters provided to the decision service
            results: The results returned by the decision service
            decision_id: The unique ID for this decision (if provided by ODM)
            decision_trace: The trace information provided by ODM (if available)
        """
        self.tool_name = tool_name
        self.ruleset_path = ruleset_path
        self.inputs = inputs
        self.results = results
        self.decision_id = decision_id
        self.decision_trace = decision_trace
        self.timestamp = datetime.now().isoformat()
        self.id = f"{tool_name}_{int(time.time())}_{decision_id or ''}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the trace to a dictionary for storage or serialization."""
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "ruleset_path": self.ruleset_path,
            "timestamp": self.timestamp,
            "inputs": self.inputs,
            "results": self.results,
            "decision_id": self.decision_id,
            "decision_trace": self.decision_trace
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert the trace to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionToolTrace':
        """Create an ExecutionToolTrace instance from a dictionary."""
        trace = cls(
            tool_name=data["tool_name"],
            ruleset_path=data["ruleset_path"],
            inputs=data["inputs"],
            results=data["results"],
            decision_id=data.get("decision_id"),
            decision_trace=data.get("decision_trace")
        )
        trace.timestamp = data["timestamp"]
        trace.id = data["id"]
        return trace
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ExecutionToolTrace':
        """Create an ExecutionToolTrace instance from a JSON string."""
        return cls.from_dict(json.loads(json_str))


class DiskTraceStorage:
    """
    A storage mechanism for ExecutionToolTrace objects that saves them to disk.
    Maintains a limited number of traces by removing the oldest ones when limit is reached.
    """
    
    def __init__(self, storage_dir: Optional[str] = None, max_traces: int = 50):
        """
        Initialize the disk-based trace storage.
        
        Args:
            storage_dir: Directory to store traces (defaults to ~/.mcp-server/traces)
            max_traces: Maximum number of traces to keep (defaults to 50)
        """
        if storage_dir is None:
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".mcp-server", "traces")
        
        self.storage_dir = storage_dir
        self.max_traces = max_traces
        self.logger = logging.getLogger(__name__)
        
        # Create the storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Initialize index for faster access
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize an in-memory index of available traces."""
        self.trace_index = {}
        trace_files = glob.glob(os.path.join(self.storage_dir, "*.json"))
        
        # Read basic metadata from each file to build the index
        for file_path in trace_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Store minimal info in the index
                    trace_id = os.path.basename(file_path).replace(".json", "")
                    self.trace_index[trace_id] = {
                        "timestamp": data.get("timestamp"),
                        "tool_name": data.get("tool_name"),
                        "file_path": file_path
                    }
            except Exception as e:
                self.logger.warning(f"Error reading trace file {file_path}: {e}")
    
    def add(self, trace: ExecutionToolTrace) -> str:
        """
        Add a trace to storage.
        If the number of traces exceeds max_traces, the oldest traces will be removed.
        
        Args:
            trace: The ExecutionToolTrace to add
            
        Returns:
            str: The ID of the added trace
        """
        # Ensure a valid filename by removing any characters that could cause issues
        safe_id = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in trace.id)
        file_path = os.path.join(self.storage_dir, f"{safe_id}.json")
        
        # Save the trace to disk
        with open(file_path, 'w') as f:
            f.write(trace.to_json())
        
        # Add to index
        self.trace_index[safe_id] = {
            "timestamp": trace.timestamp,
            "tool_name": trace.tool_name,
            "file_path": file_path
        }
        
        # Enforce the maximum number of traces
        self._enforce_max_traces()
        
        return safe_id
    
    def _enforce_max_traces(self):
        """Remove oldest traces if the number exceeds max_traces."""
        if len(self.trace_index) <= self.max_traces:
            return
        
        # Sort traces by timestamp (oldest first)
        sorted_traces = sorted(
            self.trace_index.items(), 
            key=lambda x: x[1]["timestamp"]
        )
        
        # Remove oldest traces until we're under the limit
        traces_to_remove = len(sorted_traces) - self.max_traces
        for i in range(traces_to_remove):
            trace_id, trace_info = sorted_traces[i]
            try:
                # Remove from disk
                os.remove(trace_info["file_path"])
                # Remove from index
                del self.trace_index[trace_id]
            except Exception as e:
                self.logger.warning(f"Error removing trace {trace_id}: {e}")
    
    def get(self, trace_id: str) -> Optional[ExecutionToolTrace]:
        """
        Get a trace by ID.
        
        Args:
            trace_id: The ID of the trace to get
            
        Returns:
            ExecutionToolTrace or None: The trace if found, None otherwise
        """
        if trace_id not in self.trace_index:
            return None
        
        try:
            file_path = self.trace_index[trace_id]["file_path"]
            with open(file_path, 'r') as f:
                trace_data = json.load(f)
                return ExecutionToolTrace.from_dict(trace_data)
        except Exception as e:
            self.logger.error(f"Error reading trace {trace_id}: {e}")
            return None
    
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """
        Get metadata for all traces without loading full content.
        
        Returns:
            List[Dict]: List of trace metadata including id, tool_name, and timestamp
        """
        return [
            {
                "id": trace_id,
                "tool_name": info["tool_name"],
                "timestamp": info["timestamp"]
            }
            for trace_id, info in self.trace_index.items()
        ]
    
    def clear(self) -> None:
        """Delete all trace files and clear the index."""
        for trace_id, info in self.trace_index.items():
            try:
                os.remove(info["file_path"])
            except Exception as e:
                self.logger.warning(f"Error removing trace {trace_id}: {e}")
        
        self.trace_index = {}