# DITA structured authoring sample

Last updated: 2026-11-21

## Overview

This sample shows the same product content written in DITA 1.3, an XML standard for structured, reusable technical documentation. It covers alerts in EdgePulse: one concept, one reference and two task topics.

**Audience:** Technical writers and documentation leads who review structured authoring skills.

## What the sample demonstrates

- **Topic types.** Concept, task and reference topics, each with the correct DITA structure.
- **Keys (`keydef`, `keyref`).** The product name, version and vibration limit are defined once in `keys.ditamap`.
- **Content reuse (`conref`).** Two notes are written once in `reusable-content.dita` and reused in other topics.
- **Relationship table (`reltable`).** The map generates "Related" links by topic type.
- **Conditional filtering.** Content marked `audience="administrator"` is removed in the operator edition.
- **Metadata.** Each topic has `author` and `critdates` in its prolog.
- **Accessibility.** The image has alt text.

## View the published output

- [Full edition](output/full/index.html)
- [Operator edition](output/operator/index.html) (administrator-only content removed)

## Source files

All files are in the `dita/` folder of the repository.

| File | Purpose |
|---|---|
| `edgepulse.ditamap` | Map that sets the structure, the reltable and the key map reference |
| `keys.ditamap` | Key definitions |
| `operator.ditaval` | Filter that excludes administrator content |
| `topics/alerts-concept.dita` | Concept: what alerts are |
| `topics/alert-severity-reference.dita` | Reference: severity levels and the automatic rule |
| `topics/acknowledge-alert-task.dita` | Task: acknowledge an alert |
| `topics/register-device-task.dita` | Task: register a device |
| `topics/reusable-content.dita` | Reusable notes (not published on its own) |

## Prerequisites

- Java 17 or later. DITA-OT 4.4 was tested with Java 21.
- DITA Open Toolkit (DITA-OT) 4.x, free and open source.

## Run the sample

You do not need a paid tool. Choose one option.

### Option 1: Build HTML with DITA-OT

1. Download DITA-OT from the [DITA-OT releases page](https://github.com/dita-ot/dita-ot/releases) and unzip it.
2. Open a terminal in the `dita/` folder of this repository.
3. Run the build:

    ```bash
    /path/to/dita-ot-4.4.2/bin/dita -i edgepulse.ditamap -f html5 -o out --processing-mode=strict
    ```

4. Open `out/index.html` in a browser.

To build the operator edition, add `--filter=operator.ditaval` and use a different output folder.

!!! note "Windows"
    Use `bin\dita.bat` instead of `bin/dita`.

### Option 2: Open the files in a free XML editor

Any editor that reads XML opens the `.dita` files. Visual Studio Code with a free XML extension validates the files and shows errors as you type.

### Option 3: Validate from the command line

`xmllint` checks that the files follow the DITA rules. Point it to the catalog that ships with DITA-OT:

```bash
XML_CATALOG_FILES=/path/to/dita-ot-4.4.2/catalog-dita.xml \
  xmllint --noout --valid --nonet topics/alerts-concept.dita
```

No output means the file is valid.

## Expected results

- The validation command prints nothing for all files.
- The strict build completes without errors or warnings.
- The full edition has four topics and generated "Related" links.
- The operator edition omits the administrator tip and the post-requisite in the acknowledge task.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `DOTJ013E` or `validity error` | An element is in the wrong place. | Compare the element with the DITA 1.3 DTD. Run the `xmllint` command to find the line. |
| `Unable to find a Java runtime` | Java is not installed. | Install Java 17 or later. |
| Keys show as empty text | The map does not reference `keys.ditamap`. | Add the `mapref` element to the map. |

!!! note "Known limitation"
    The `audience` value in a topic `prolog` is metadata. It does not filter content. Filtering uses the `audience` attribute on an element, as the sample does for the tip and the post-requisite.

## Related information

- [Dashboard user guide](../user-guide/index.md)
- [Style guide](../contributing/style-guide.md)
