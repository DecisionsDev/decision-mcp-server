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

import re
import tempfile

def merge_ssl_cert_paths(ssl_cert_path: str) -> str:
    """Return a path to a single CA-bundle PEM file.

    If *ssl_cert_path* contains multiple file paths separated by ``,`` or
    ``;``, the files are concatenated into a new temporary file and the
    path of that temporary file is returned.  When only a single path is
    given the original value is returned unchanged.

    Non-existent paths are silently skipped with a warning log message.

    Args:
        ssl_cert_path: One or more PEM file paths, separated by ``,`` or ``;``.

    Returns:
        A file path suitable for use as a CA bundle.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Split on commas or semicolons, stripping whitespace around each entry.
    paths = [p.strip() for p in re.split(r'[,;]+', ssl_cert_path) if p.strip()]

    if len(paths) <= 1:
        # Single path — return as-is (no temp file required).
        return ssl_cert_path

    # Multiple paths: concatenate into a NamedTemporaryFile that persists until
    # the process exits (delete=False).
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.pem',
        delete=False,
        prefix='odm_merged_ca_',
    ) as tmp:
        merged = []
        for path in paths:
            try:
                with open(path, 'r') as f:
                    content = f.read()
            except FileNotFoundError:
                logger.warning("ssl-cert-path: file not found, skipping: %s", path)
                continue
            # Ensure each certificate block ends with a newline before the next.
            if not content.endswith('\n'):
                content += '\n'
            tmp.write(content)
            merged.append(path)
        logger.debug(
            "ssl-cert-path: concatenated %s into %s",
            ", ".join(merged),
            tmp.name,
        )
        return tmp.name