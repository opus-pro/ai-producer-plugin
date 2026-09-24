# v1.2.8+reissue.1

The original v1.2.8 GitHub Release was deleted. GitHub does not allow reuse of a tag name after an immutable Release is deleted, so this Release uses a distinct tag pointing to the original [v1.2.8 release commit](https://github.com/opus-pro/ai-producer-plugin/commit/e328a1653f2f1764efcb54a51e7c9c203271959c). The plugin files, declared plugin version (1.2.8), and production MCP endpoint are unchanged. This reissue is not a newer plugin version.

## Changes

### Added

- Adapt plain-text Motion Library requests to the current video and chosen placement. ([#81](https://github.com/opus-pro/ai-producer-plugin/pull/81))
- Send composition text with the workspace commit, reducing upload steps for text-only effects. ([#82](https://github.com/opus-pro/ai-producer-plugin/pull/82))
- Guide conversations without a computer to ChatGPT Work or Codex before attempting an upload. ([#83](https://github.com/opus-pro/ai-producer-plugin/pull/83))
- Place sound effects on the settled cut when sound effects are enabled. ([#85](https://github.com/opus-pro/ai-producer-plugin/pull/85))

### Changed

- Use contrasting caption text on light backgrounds and a bottom-band layout for landscape or square captions. ([#84](https://github.com/opus-pro/ai-producer-plugin/pull/84), [#86](https://github.com/opus-pro/ai-producer-plugin/pull/86))
- Leave framing choices to the brief, preserve complete closing thoughts, and select useful excerpts throughout supplied B-roll. ([#87](https://github.com/opus-pro/ai-producer-plugin/pull/87), [#88](https://github.com/opus-pro/ai-producer-plugin/pull/88))

### Fixed

- Open Codex previews in the embedded project layout and deliver a standard project-page link. ([#89](https://github.com/opus-pro/ai-producer-plugin/pull/89))

## Compatibility

- Direct text commits and sound effects require the corresponding production MCP support. Existing plugin and marketplace identifiers remain unchanged.

**Full Changelog**: [v1.2.7...v1.2.8+reissue.1](https://github.com/opus-pro/ai-producer-plugin/compare/v1.2.7...v1.2.8%2Breissue.1)
