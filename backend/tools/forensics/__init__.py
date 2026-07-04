"""
Forensics & incident-response tool wrappers: memory analysis (Volatility3),
disk/case management (Autopsy REST), PCAP analysis, static file triage,
and YARA-based malware scanning.

All wrappers follow the shared convention in tools/base.py:
  - list-form argv only, never shell=True
  - inputs validated via utils.parser_utils before subprocess use
  - results returned as typed dataclasses for the services layer to persist
"""
