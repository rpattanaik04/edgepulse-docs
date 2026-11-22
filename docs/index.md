# EdgePulse documentation

Last updated: 2026-11-21

EdgePulse is a fictional platform for monitoring industrial edge devices. This documentation set demonstrates a complete, Docs-as-Code workflow: task-oriented guides, an API reference backed by a real working API, structured authoring, and an automated publishing pipeline.

!!! note "About this project"
    Written and maintained by Rakesh Pattanaik as a technical writing portfolio project. The product is fictional. The API and the tooling are real.

## Start here

| If you want to... | Read |
|---|---|
| Understand what EdgePulse does | [Product overview](overview/index.md) |
| Run EdgePulse and try it in 10 minutes | [Quick start](quick-start/index.md) |
| Install the demo API | [Installation guide](installation/index.md) |
| Monitor devices and respond to alerts | [Dashboard user guide](user-guide/index.md) |
| Configure and secure an installation | [Administrator guide](admin-guide/index.md) |
| Get an access token | [Authentication guide](api/authentication.md) |
| Call the API, with tested JSON examples | [API reference](api/reference.md) |
| Build scripts and applications | [Developer guide](developer-guide/index.md) |
| Inspect the API contract | [OpenAPI specification](api/openapi.yaml) |
| Connect MQTT devices | [MQTT integration guide](integration/mqtt.md) |
| Fix a problem | [Troubleshooting guide](troubleshooting/index.md) |
| Find a quick answer or a term | [FAQ](help-center/faq.md), [Glossary](help-center/glossary.md) |
| See what changed, and upgrade | [Release notes](release-notes/index.md), [Upgrade guide](migration/upgrade-1.1-to-1.2.md) |
| See structured authoring in DITA | [DITA sample](dita-sample/index.md) |
| Learn how the documentation is written and built | [Style guide](contributing/style-guide.md), [Contribution guide](contributing/index.md), [Pipeline](contributing/pipeline.md) |

## How this documentation is built

- **Authoring:** Markdown, with a DITA XML sample for structured authoring.
- **Site generator:** MkDocs with the Material theme.
- **API contract:** OpenAPI 3.1, generated from a working FastAPI service.
- **Publishing:** GitHub Actions deploys the site to GitHub Pages.
- **Diagrams:** Mermaid source files with exported PNG and SVG images.
