# Contract: Submission Export

## Module
`module_1_foundations.export.submission`

### `compile_submission(scenario: Scenario, classifications: list[AgentClassification], interaction_map: str, tradeoff_analysis: str, capability_cycle: str) -> str`

Compiles all 4 deliverables into a single self-contained Markdown document.

**Input**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `scenario` | `Scenario` | The learner's scenario |
| `classifications` | `list[AgentClassification]` | Classification results |
| `interaction_map` | `str` | Mermaid flowchart string |
| `tradeoff_analysis` | `str` | Analysis markdown |
| `capability_cycle` | `str` | Mermaid capability cycle string |

**Output**: Markdown string with sections:
1. Header (course name, module, learner name placeholder, date)
2. Section 1: Agent Classification Table (type + justification per agent)
3. Section 2: Interaction Diagram (Mermaid block)
4. Section 3: Trade-off Analysis (table + qualitative)
5. Section 4: Capability Cycle (Mermaid block)
6. Section 5: Reflection (blank prompt placeholder)

---

### `generate_pdf(markdown_content: str, output_path: str) -> str`

Converts the compiled markdown to PDF using `markdown` (md→HTML) + `pymupdf` (HTML→PDF via `page.insert_htmlbox()`).

**Input**:
- `markdown_content`: The output of `compile_submission()`
- `output_path`: File path for the generated .pdf

**Output**: Path to generated PDF file (same as `output_path`)

**Behavior**:
1. Parse markdown to HTML via `markdown.markdown()` with `extra` extension for tables
2. Wrap HTML in a full HTML document with inline CSS (font-family, spacing, page size)
3. Create a PyMuPDF document: `doc = fitz.Document()`, add page via `doc.new_page()`
4. Render HTML into the page via `page.insert_htmlbox(page.rect, html_content)`
5. Save via `doc.save(output_path)`
