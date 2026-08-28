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

import os
import sys
import tempfile

import pytest

# Add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from decision_mcp_server.utils.ssl_utils import merge_ssl_cert_paths


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_pem(content: str) -> str:
    """Write *content* to a temporary file and return its path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
        f.write(content)
        return f.name


CERT_A = "-----BEGIN CERTIFICATE-----\nMIIAcertA==\n-----END CERTIFICATE-----\n"
CERT_B = "-----BEGIN CERTIFICATE-----\nMIIAcertB==\n-----END CERTIFICATE-----\n"
CERT_C = "-----BEGIN CERTIFICATE-----\nMIIAcertC==\n-----END CERTIFICATE-----\n"


# ---------------------------------------------------------------------------
# Single-path pass-through
# ---------------------------------------------------------------------------

class TestMergeSslCertPathsSinglePath:
    """A single path is returned unchanged — no temp file is created."""

    def test_single_path_returned_as_is(self, tmp_path):
        cert_file = tmp_path / "ca.pem"
        cert_file.write_text(CERT_A)
        path = str(cert_file)

        result = merge_ssl_cert_paths(path)

        assert result == path

    def test_single_path_with_surrounding_whitespace(self, tmp_path):
        """Whitespace around a single entry must still be treated as a single path."""
        cert_file = tmp_path / "ca.pem"
        cert_file.write_text(CERT_A)
        path = str(cert_file)

        result = merge_ssl_cert_paths(f"  {path}  ")

        # The value is returned as-is (including any surrounding spaces) when
        # there is only one token.
        assert result == f"  {path}  "


# ---------------------------------------------------------------------------
# Multi-path concatenation — comma separator
# ---------------------------------------------------------------------------

class TestMergeSslCertPathsComma:

    def test_two_paths_comma_separated(self, tmp_path):
        f_a = tmp_path / "a.pem"
        f_b = tmp_path / "b.pem"
        f_a.write_text(CERT_A)
        f_b.write_text(CERT_B)

        result = merge_ssl_cert_paths(f"{f_a},{f_b}")

        assert result != str(f_a)
        assert os.path.isfile(result)
        content = open(result).read()
        assert CERT_A in content
        assert CERT_B in content
        os.unlink(result)

    def test_three_paths_comma_separated(self, tmp_path):
        f_a = tmp_path / "a.pem"
        f_b = tmp_path / "b.pem"
        f_c = tmp_path / "c.pem"
        f_a.write_text(CERT_A)
        f_b.write_text(CERT_B)
        f_c.write_text(CERT_C)

        result = merge_ssl_cert_paths(f"{f_a},{f_b},{f_c}")

        content = open(result).read()
        assert CERT_A in content
        assert CERT_B in content
        assert CERT_C in content
        os.unlink(result)

    def test_comma_with_spaces_around_paths(self, tmp_path):
        f_a = tmp_path / "a.pem"
        f_b = tmp_path / "b.pem"
        f_a.write_text(CERT_A)
        f_b.write_text(CERT_B)

        result = merge_ssl_cert_paths(f" {f_a} , {f_b} ")

        content = open(result).read()
        assert CERT_A in content
        assert CERT_B in content
        os.unlink(result)


# ---------------------------------------------------------------------------
# Multi-path concatenation — semicolon separator
# ---------------------------------------------------------------------------

class TestMergeSslCertPathsSemicolon:

    def test_two_paths_semicolon_separated(self, tmp_path):
        f_a = tmp_path / "a.pem"
        f_b = tmp_path / "b.pem"
        f_a.write_text(CERT_A)
        f_b.write_text(CERT_B)

        result = merge_ssl_cert_paths(f"{f_a};{f_b}")

        content = open(result).read()
        assert CERT_A in content
        assert CERT_B in content
        os.unlink(result)

    def test_semicolon_with_spaces(self, tmp_path):
        f_a = tmp_path / "a.pem"
        f_b = tmp_path / "b.pem"
        f_a.write_text(CERT_A)
        f_b.write_text(CERT_B)

        result = merge_ssl_cert_paths(f" {f_a} ; {f_b} ")

        content = open(result).read()
        assert CERT_A in content
        assert CERT_B in content
        os.unlink(result)


# ---------------------------------------------------------------------------
# Merged file properties
# ---------------------------------------------------------------------------

class TestMergedFileProperties:

    def test_merged_file_has_pem_suffix(self, tmp_path):
        f_a = tmp_path / "a.pem"
        f_b = tmp_path / "b.pem"
        f_a.write_text(CERT_A)
        f_b.write_text(CERT_B)

        result = merge_ssl_cert_paths(f"{f_a},{f_b}")
        assert result.endswith('.pem')
        os.unlink(result)

    def test_cert_blocks_separated_by_newline(self, tmp_path):
        """No certificate block should bleed into the next without a newline."""
        f_a = tmp_path / "a.pem"
        f_b = tmp_path / "b.pem"
        # Deliberately omit trailing newline in CERT_A content
        f_a.write_text(CERT_A.rstrip('\n'))
        f_b.write_text(CERT_B)

        result = merge_ssl_cert_paths(f"{f_a},{f_b}")
        content = open(result).read()
        # END CERTIFICATE of cert A must not directly touch BEGIN CERTIFICATE of cert B
        assert "-----END CERTIFICATE-----\n-----BEGIN CERTIFICATE-----" in content
        os.unlink(result)

    def test_missing_file_is_skipped(self, tmp_path):
        """A non-existent path in the list is silently skipped."""
        f_a = tmp_path / "a.pem"
        f_a.write_text(CERT_A)
        missing = "/nonexistent/path/ca.pem"

        result = merge_ssl_cert_paths(f"{f_a},{missing}")

        assert os.path.isfile(result)
        content = open(result).read()
        assert CERT_A in content
        os.unlink(result)
