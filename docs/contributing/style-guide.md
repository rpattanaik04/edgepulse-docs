# Documentation style guide

- **Audience:** Writers, reviewers and engineers who contribute to EdgePulse documentation.
- **Purpose:** Keep every document consistent, accurate and easy to use.
- **Last updated:** 2026-11-19

## Principles

- Write for the reader's task, not for the product's internal design.
- State what a feature does before explaining how it works.
- Use only the detail the reader needs.
- Verify every procedure and every code sample against the running product.

## Language and tone

- Use US English.
- Use a formal, direct tone. Avoid slang, humor and marketing language.
- Write in active voice. Write "Select **Save**", not "The Save button should be selected".
- Use present tense. Write "The API returns a list", not "The API will return a list".
- Address the reader as "you".
- Keep sentences short. Aim for 25 words or fewer.
- Define a term the first time it appears. Add it to the glossary.
- Use "must" for requirements, "can" for options and avoid "should" when the action is mandatory.

## Document structure

Each task-oriented document uses this order. Omit a section only when it does not apply.

1. Overview
2. Purpose
3. Prerequisites
4. Key concepts
5. Procedure
6. Expected results
7. Troubleshooting
8. Best practices
9. Related information

Every document begins with a short header list. It states the audience, the document type, the version it applies to and the date of the last update.

```markdown
- **Audience:** Administrators who install EdgePulse.
- **Document type:** Installation guide
- **Applies to:** EdgePulse 1.2
- **Last updated:** 2026-11-19
```

## Headings

- Use sentence case: "Create an access token", not "Create An Access Token".
- Use one level-1 heading per page.
- Do not skip heading levels.
- Start task headings with a verb. Start concept headings with a noun.

## Procedures

- Use a numbered list. Give one action per step.
- Start each step with a verb.
- State the expected result after the step when it is not obvious.
- Use no more than 10 steps. Split longer tasks into separate procedures.
- Put a precondition before the first step, not inside it.

**Example**

1. Send a `POST` request to `/api/v1/auth/token` with your client credentials.
2. Copy the `access_token` value from the response.

   The response status is `200 OK`.

## Formatting conventions

| Element | Convention | Example |
|---|---|---|
| UI labels | Bold | Select **Acknowledge**. |
| Code, endpoints, field names, values | Monospace | `GET /api/v1/devices` |
| File names and paths | Monospace | `docs/index.md` |
| Placeholders | Monospace, angle brackets | `<access_token>` |
| Emphasis | Italic, used sparingly | The token is *short-lived*. |
| Keyboard keys | Plain text, capitalized | Press Ctrl+C. |

## Notes, warnings and tips

Use admonitions for information that stands apart from the procedure.

| Type | Use when |
|---|---|
| `note` | The reader benefits from extra context. |
| `tip` | A faster or better way exists. |
| `warning` | The reader could lose data or cause an outage. |

Keep each admonition to three sentences or fewer.

## API documentation

- Describe every endpoint with: purpose, method and path, authentication, parameters, request body, response, status codes and an example.
- Use JSON examples taken from real responses of the running API. Do not hand-write response bodies.
- Format JSON with a four-space indent and keep field order the same as the API.
- Show timestamps in ISO 8601 format, in UTC. Example: `2026-11-18T07:54:32Z`.
- Use `<access_token>` as the placeholder for a token. Never publish a real token or secret.
- Document the standard error structure once, then link to it:

```json
{
    "error": {
        "code": "device_not_found",
        "message": "No device exists with the given ID."
    }
}
```

## Images and diagrams

- Store images under `docs/assets/`: diagrams in `docs/assets/diagrams/` and screenshots in `docs/assets/screenshots/`.
- Keep diagram source files, such as Mermaid `.mmd`, in `docs/assets/diagrams/source/` and exported images in `docs/assets/diagrams/exports/`.
- Name files in lowercase with hyphens, for example `token-flow.png`.
- Give every image alt text that describes what it shows.
- Add a numbered caption below each figure: *Figure 1. Caption text.*
- Do not rely on color alone to carry meaning.
- Crop screenshots to the relevant area. Remove personal or sensitive data.

## Terminology

| Use | Do not use |
|---|---|
| device | node, endpoint (for hardware) |
| alert | alarm, notification |
| acknowledge | ack, dismiss |
| access token | auth key, session key |
| sign in | log in, login (as a verb) |
| select | click on, hit |
| enter | type in, put in |
| REST API | rest service, web service |

## Versioning and dates

- State the product version at the top of each document.
- Record the date of the last update in each document header, in the format `Last updated: 2026-11-19`. Change it whenever the content changes.
- Use `MAJOR.MINOR.PATCH` for versions.
- Write dates as `18 November 2026` in prose and `2026-11-18` in tables and data.

## Review checklist

- [ ] The audience, version and last updated date are stated.
- [ ] Every procedure was run from start to finish.
- [ ] Every code sample and JSON example comes from the running API.
- [ ] Terminology matches this guide and the glossary.
- [ ] Every image has alt text and a caption.
- [ ] All links work.
- [ ] Spelling and grammar are checked.
