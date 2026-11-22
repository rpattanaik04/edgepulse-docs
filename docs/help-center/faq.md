# Frequently asked questions

Last updated: 2026-11-21

**Audience:** Evaluators, operators, administrators and developers.

## About the project

### Is EdgePulse a real product?

No. EdgePulse is a fictional product created for a documentation portfolio. The REST API and dashboard are real and runnable, and every example in the guides was tested.

### Can I use the demo API in production?

No. The demo stores data in memory, has one set of credentials and has no rate limits or encryption of its own.

## Using the API

### How do I get an access token?

Send your client ID and secret to `POST /api/v1/auth/token`. The demo credentials are `demo-client` and `demo-secret`. See the [Authentication guide](../api/authentication.md).

### How long does a token last?

3600 seconds (one hour). After that, the API returns `unauthorized`. Request a new token.

### Why did my reading create an alert?

The platform raises a critical alert when a reading has vibration above 5.0 mm/s. You cannot change this limit.

### Can I change the vibration limit?

No. The limit is fixed in the demo.

### Which protocols does a device use?

A device record has one of three protocol values: MQTT, OPCUA or MODBUS. The API accepts readings over REST. To use MQTT, follow the [MQTT integration guide](../integration/mqtt.md).

## Hosting

### Why is the first request slow on the hosted demo?

The free Render instance sleeps after 15 minutes without traffic. It takes about one minute to wake up.

### Why did my data disappear?

The demo keeps data in memory. A restart returns it to the original demo set.

## Documentation

### How are these documents built?

The documents are Markdown files in a Git repository. MkDocs builds the site, and GitHub Actions publishes it. See the [Docs-as-Code pipeline](../contributing/pipeline.md).

### Is there a DITA version?

Yes. See the [DITA sample](../dita-sample/index.md).

## Related information

- [Troubleshooting guide](../troubleshooting/index.md)
- [Glossary](glossary.md)
