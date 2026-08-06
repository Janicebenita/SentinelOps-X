# Prompt evaluation

Run `python -m pytest backend/tests/test_prompt_catalog.py -q`. The checks load
both YAML catalogs, compile the JSON schema contract, require unique semantic
versions and all CRISPE fields, and prove that approval, gate override, workflow
mutation, and production execution are prohibited. Authenticated managed-model
quality evaluation remains `IMPLEMENTED_REQUIRES_CREDENTIALS`.
