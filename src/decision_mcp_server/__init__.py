# Copyright contributors to the IBM ODM MCP Server project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from . import DecisionMCPServer

import sys

def main():
    """Main entry point for the package."""
    # Skip argument parsing when running tests
    if 'pytest' in sys.modules:
        return
    DecisionMCPServer.main()

# Optionally expose other important items at package level
__all__ = ['main', 'DecisionMCPServer', 'DecisionServerManager', 'Credentials', "DecisionServiceDescription"]

if __name__ == "__main__":
    main()