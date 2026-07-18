# Project Planning

This folder contains project-internal planning and design artifacts.

Use this folder for:

- architecture;
- Architectural Change Documents;
- release definitions and planning-release material;
- implementation planning;
- source notes and discussion notes that are not end-user documentation.

The top-level `docs/` folder is reserved for user documentation. Do not put
architecture, ACDs, specifications, planning notes, or internal design source
notes there.

Architecture documents live under `project/architecture/`. Keep active ACDs
next to the architecture documents they change, using `acd-` filenames and ACD
headers to identify unimplemented transitional decisions. At the end of an
implementation phase, fold accepted ACD decisions into the relevant architecture
documents and retire or close the ACDs.
