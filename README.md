# EdgePulse Documentation

Documentation portfolio project by **Rakesh Pattanaik**, Senior Technical Writer.

EdgePulse is a **fictional** industrial IoT (IIoT) edge monitoring platform. This repository contains its documentation set, a **real, working REST API** that the documentation describes, and the Docs-as-Code tooling that builds and publishes it.

**Live documentation:** <https://rpattanaik04.github.io/edgepulse-docs/>

## Try the API

> **Note:** The hosted demo API runs on Render's free tier. After 15 minutes without traffic the service sleeps, so the first request can take about one minute to respond. Demo data resets each time the service restarts.

**Hosted URL:** to be added after deployment. You can also [run the API locally](api-demo/README.md) in a few minutes.

## What this project demonstrates

- Task-oriented user, administrator and developer documentation
- API documentation backed by a running service and an OpenAPI 3.1 specification
- Docs-as-Code: Markdown, Git, MkDocs and automated publishing
- Structured authoring with a DITA XML sample
- Diagrams as code (Mermaid) and consistent, reviewed screenshots

## Documentation set

| Document | Audience | Status | Last updated |
|---|---|---|---|
| [Product overview](docs/overview/index.md) | Everyone | Published | 2026-11-20 |
| [Quick start](docs/quick-start/index.md) | Developers, evaluators | Published | 2026-11-20 |
| [Installation guide](docs/installation/index.md) | Administrators, developers | Published | 2026-11-20 |
| [Dashboard user guide](docs/user-guide/index.md) | Operators | Published | 2026-11-20 |
| [Administrator guide](docs/admin-guide/index.md) | Administrators | Published | 2026-11-20 |
| [API authentication guide](docs/api/authentication.md) | Developers | Published | 2026-11-20 |
| [API reference](docs/api/reference.md), with tested JSON examples | Developers | Published | 2026-11-20 |
| [Developer guide with tutorials](docs/developer-guide/index.md) | Developers | Published | 2026-11-20 |
| [OpenAPI specification](docs/api/openapi.yaml) | Developers | Published | 2026-11-20 |
| [Documentation style guide](docs/contributing/style-guide.md) | Writers, contributors | Published | 2026-11-19 |
| [MQTT integration guide](docs/integration/mqtt.md), with a tested bridge script | Developers | Published | 2026-11-21 |
| [Troubleshooting guide](docs/troubleshooting/index.md), with a decision tree | Developers, support | Published | 2026-11-21 |
| [FAQ](docs/help-center/faq.md) and [glossary](docs/help-center/glossary.md) | All | Published | 2026-11-21 |
| [Release notes](docs/release-notes/index.md) (fictional history) | All | Published | 2026-11-21 |
| [Upgrade guide, 1.1 to 1.2](docs/migration/upgrade-1.1-to-1.2.md) | Developers | Published | 2026-11-21 |
| [Contribution guide](docs/contributing/index.md) and [Docs-as-Code pipeline](docs/contributing/pipeline.md) | Writers, engineers | Published | 2026-11-21 |
| [DITA XML sample](docs/dita-sample/index.md), with HTML output | Structured authoring reviewers | Published | 2026-11-21 |

## Repository structure

```text
edgepulse-docs/
├── docs/                 Documentation source (Markdown)
│   ├── assets/           Diagrams and screenshots, kept separate from content
│   └── api/              OpenAPI specification
├── api-demo/             Working FastAPI demo, dashboard and tests
├── examples/             Tested Python and JavaScript code samples
├── scripts/              Builds the API reference and screenshots from the running API
├── dita/                 DITA XML sample (map, key map, filter, topics)
├── .github/              CI workflow and Dependabot configuration
├── render.yaml           Render blueprint for the hosted demo API
├── pdf/                  PDF versions of the guides
└── mkdocs.yml            Site configuration
```

## Preview the documentation locally

```bash
pip install -r requirements.txt
mkdocs serve
```

Open <http://127.0.0.1:8000>.

## Run the demo API

See [api-demo/README.md](api-demo/README.md).

## License

Documentation and code are released under the MIT License.
