# Cost and Licensing Check

**Research Date:** March 6, 2026  
**Researcher:** Web-Puppy  
**Purpose:** Quick licensing verification for 9 specific tools to determine compatibility with MIT-licensed open source CLI tool.

---

## Summary Table

| Tool | Cost | License | MIT-Compatible | Hidden Costs | Notes |
|------|------|---------|--------------|--------------|-------|
| Pa11y 9.1.1 | Free | LGPL-3.0-only | ⚠️ Complex | None | Copyleft - linking restrictions apply |
| axe-core 4.11.1 | Free | MPL-2.0 | ✅ Yes | None | File-level copyleft, compatible with MIT |
| Spectral CLI | Free | Apache-2.0 | ✅ Yes | None | Permissive, fully compatible |
| MADR 4.0 | Free | MIT OR CC0-1.0 | ✅ Yes | None | Dual-licensed, very permissive |
| STRIDE | Free* | Proprietary | ⚠️ N/A | None | Microsoft methodology, free tool available |
| GPC | Free | W3C License | ✅ Yes | None | Permissive for software |
| IBM Carbon DS | Free | Apache-2.0 | ✅ Yes | None | Permissive, fully compatible |
| Decision Guardian | Unknown | Unknown | ❓ Unknown | Unknown | No prominent OSS found |
| ATAM-lite | Free* | N/A (method) | ✅ N/A | None | Architecture methodology, not a tool |

---

## Detailed Analysis

### 1. Pa11y 9.1.1
**Cost:** Free/Open Source  
**License:** LGPL-3.0-only  
**Can be embedded in MIT CLI:** ⚠️ Complex

**Analysis:**
- LGPL is a copyleft license that requires modifications to be shared
- As a library, it can be linked to MIT code BUT with important caveats:
  - If Pa11y is modified, changes must be LGPL-licensed
  - Dynamic linking is generally acceptable, static linking may create derivative work concerns
  - Must provide source code and license notices

**Recommendation:** Can use as external dependency (npm install), but embedding/modifying requires LGPL compliance.

**Hidden Costs:** None

---

### 2. axe-core 4.11.1
**Cost:** Free/Open Source  
**License:** Mozilla Public License 2.0 (MPL-2.0)  
**Can be embedded in MIT CLI:** ✅ Yes

**Analysis:**
- MPL-2.0 is a weak copyleft license (file-level)
- Files from axe-core remain under MPL, but your MIT code stays MIT
- Can combine with MIT code in same project
- Must include MPL license notice for axe-core files

**Recommendation:** Safe to use. axe-core files stay MPL, your code stays MIT.

**Hidden Costs:** None

---

### 3. Spectral CLI (Stoplight)
**Cost:** Free/Open Source  
**License:** Apache License 2.0  
**Can be embedded in MIT CLI:** ✅ Yes

**Analysis:**
- Apache-2.0 is a permissive license
- Fully compatible with MIT
- Requires attribution and license preservation
- Patent grant included

**Recommendation:** Safe to use. Include Apache-2.0 notice for Spectral components.

**Hidden Costs:** None

---

### 4. MADR 4.0 (Markdown ADR)
**Cost:** Free/Open Source  
**License:** MIT OR CC0-1.0 (dual licensed)  
**Can be embedded in MIT CLI:** ✅ Yes

**Analysis:**
- Dual licensed - can choose either MIT or CC0
- CC0 is public domain dedication (most permissive)
- MIT is standard permissive license
- No attribution required if using CC0

**Recommendation:** Safe to use. Choose MIT for consistency or CC0 for maximum freedom.

**Hidden Costs:** None

---

### 5. STRIDE (Microsoft Threat Modeling)
**Cost:** Free*  
**License:** Proprietary (methodology)

**Analysis:**
- STRIDE is a Microsoft security methodology, not open source software
- Microsoft provides a free Threat Modeling Tool (Windows desktop app)
- The tool itself is free but proprietary
- Cannot embed in an open source CLI tool

**Recommendation:** Cannot embed STRIDE itself. Can document using STRIDE methodology. For CLI integration, consider alternatives or wrapping the free tool (if platform permits).

**Hidden Costs:** None for the tool, but it's Windows-only desktop software

---

### 6. GPC (Global Privacy Control)
**Cost:** Free/Standard  
**License:** W3C Software and Document License  
**Can be embedded in MIT CLI:** ✅ Yes

**Analysis:**
- W3C license is permissive for software
- Allows modification and distribution
- Requires attribution

**Recommendation:** Safe to use for implementing GPC signal support.

**Hidden Costs:** None

---

### 7. IBM Carbon Design System
**Cost:** Free/Open Source  
**License:** Apache License 2.0  
**Can be embedded in MIT CLI:** ✅ Yes

**Analysis:**
- Apache-2.0 permissive license
- Full compatibility with MIT
- Requires license preservation and attribution

**Recommendation:** Safe to use.

**Hidden Costs:** None

---

### 8. Decision Guardian
**Cost:** Unknown  
**License:** Unknown

**Analysis:**
- No prominent open source project found by this exact name
- May refer to:
  - A proprietary commercial product
  - An internal tool
  - A lesser-known project
  - A methodology rather than software

**Recommendation:** Need clarification on which "Decision Guardian" is intended. Not a standard open source tool.

**Hidden Costs:** Unknown

---

### 9. ATAM-lite (Architecture Tradeoff Analysis Method)
**Cost:** Free*  
**License:** N/A (methodology)

**Analysis:**
- ATAM is a software architecture evaluation methodology from SEI/Carnegie Mellon
- "ATAM-lite" appears to be a simplified version of the methodology
- Not a specific software tool - it's an analysis approach
- Can use the methodology freely

**Recommendation:** Can implement ATAM-lite process/documentation. No license restrictions on using the methodology.

**Hidden Costs:** None

---

## License Compatibility Quick Reference

### Safe for MIT CLI Integration (No Special Requirements)
- ✅ axe-core (MPL-2.0)
- ✅ Spectral CLI (Apache-2.0)
- ✅ MADR (MIT/CC0)
- ✅ GPC (W3C)
- ✅ IBM Carbon (Apache-2.0)

### Requires Careful Integration
- ⚠️ Pa11y (LGPL-3.0) - Use as external dependency, don't modify/embed without LGPL compliance

### Not Applicable/Not Software
- ℹ️ STRIDE - Methodology, free tool available but proprietary
- ℹ️ ATAM-lite - Methodology, not software
- ❓ Decision Guardian - Cannot locate specific open source project

---

## Source Verification

| Tool | Source | Verification Date |
|------|--------|-------------------|
| Pa11y | https://github.com/pa11y/pa11y | March 6, 2026 |
| axe-core | https://raw.githubusercontent.com/dequelabs/axe-core/develop/LICENSE | March 6, 2026 |
| Spectral | https://raw.githubusercontent.com/stoplightio/spectral/develop/LICENSE | March 6, 2026 |
| MADR | https://raw.githubusercontent.com/adr/madr/main/LICENSE | March 6, 2026 |
| STRIDE | https://www.microsoft.com/securityengineering/sdl/threatmodeling | March 6, 2026 |
| GPC | https://raw.githubusercontent.com/w3c/gpc/main/LICENSE.md | March 6, 2026 |
| IBM Carbon | https://raw.githubusercontent.com/carbon-design-system/carbon/main/LICENSE | March 6, 2026 |

---

## Recommendations

1. **Immediate Use (No Issues):** axe-core, Spectral CLI, MADR, GPC, IBM Carbon
2. **Use as Dependency:** Pa11y (via npm, don't bundle/modify)
3. **Need Clarification:** Decision Guardian - identify specific project
4. **Documentation Only:** STRIDE, ATAM-lite (use as methodologies, not embeddable code)

---

*Research conducted using official GitHub repositories and direct license file inspection.*
