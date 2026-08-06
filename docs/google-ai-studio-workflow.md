# Google AI Studio prompt lifecycle

Status: `IMPLEMENTED_REQUIRES_CREDENTIALS`

Google AI Studio is the prompt prototyping and evaluation environment, while
the managed Google runtime is the inference target. The repository lifecycle
is: prototype → evaluation cases → version-controlled CRISPE assets → managed
runtime invocation → strict schema validation → non-secret audit metadata.

Thirteen task-level Gemini and Gemma prompts live under `prompts/`; automated
tests verify their structure, uniqueness, refusals, prohibited actions, and
permanent safety boundary. No AI Studio session is claimed because no exported
session evidence was available in this environment.
