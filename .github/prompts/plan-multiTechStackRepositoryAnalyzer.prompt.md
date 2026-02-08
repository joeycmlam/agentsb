# Plan: Multi-Tech-Stack Repository Analyzer & Testing Agent Framework

**TL;DR:** Transform the repo-app from hardcoded Python/JavaScript detection to a **configuration-driven, language-agnostic analysis platform**. Create standardized JSON exports that testing agents can consume automatically, enabling any team to add their tech stack by editing YAML files instead of code. This unlocks support for Ruby, PHP, C#, Kotlin, Swift, Rust, and any future language through a single `tech-stacks.yaml` configuration file.

**Decision:** Chose **configuration-first MVP over full plugin system** to meet 1-week timeline while maintaining extensibility. Teams edit YAML files to add languages instead of writing Python plugins.

**Steps**

1. **Create Tech Stack Configuration Schema**
   - Add [src/repo-app/config/tech-stacks.yaml](src/repo-app/config/tech-stacks.yaml) defining language detection rules, test frameworks, coverage tools, and test patterns
   - Structure: Each language has `extensions`, `package_files`, `frameworks[]` with `indicators`, `test_patterns`, and `coverage_commands`
   - Seed with 8 languages: Python, JavaScript, TypeScript, Ruby, Java, Go, C#, PHP
   - Add [src/repo-app/config/config_loader.py](src/repo-app/config/config_loader.py) to parse YAML into `TechStackConfig` dataclass

2. **Refactor Detection Logic to Use Configuration**
   - Update [analyzer.py](src/repo-app/analyzer.py) `_detect_languages()` to iterate through config entries instead of hardcoded if/else blocks
   - Update [analyzer.py](src/repo-app/analyzer.py) `_detect_test_frameworks()` to use config's framework indicators
   - Replace hardcoded patterns in [test_analyzer.py](src/repo-app/analyzers/test_analyzer.py) with config-driven `test_patterns` lookup
   - Update [coverage_analyzer.py](src/repo-app/analyzers/coverage_analyzer.py) `_get_coverage_command()` to execute configured commands per framework
   - Migrate all constants from [constants.py](src/repo-app/constants.py) to YAML, keep file for backward compatibility with deprecated warnings

3. **Add Language-Specific Analyzer Strategy Pattern**
   - Create [src/repo-app/analyzers/language_analyzer.py](src/repo-app/analyzers/language_analyzer.py) with `LanguageAnalyzer` abstract base class
   - Implement default `GenericLanguageAnalyzer` that uses config-driven behavior
   - Create specialized implementations: `RubyAnalyzer`, `CSharpAnalyzer`, `SwiftAnalyzer` for language-specific nuances (e.g., Gemfile parsing, .sln detection)
   - Add `LanguageAnalyzerRegistry` in [analyzer.py](src/repo-app/analyzer.py) that selects appropriate analyzer based on detected language
   - Register analyzers: `registry.register('Ruby', RubyAnalyzer)` with fallback to `GenericLanguageAnalyzer`

4. **Create Standardized Analysis Export for Agent Consumption**
   - Add [src/repo-app/exporters/json_exporter.py](src/repo-app/exporters/json_exporter.py) with `export_analysis()` method
   - Export format: `{"repository": {...}, "languages": [...], "frameworks": [...], "test_metrics": {...}, "recommendations": {...}, "agent_context": {...}}`
   - Include `agent_context` with suggested agents (`@test-generator`, `@bdd-automation-engineer`) and tool configurations based on detected stack
   - Add `--export-json` flag to [repo_analyzer.py](src/repo-app/repo_analyzer.py) CLI to output `{repo_name}_analysis.json`
   - Save exports to [src/repo-app/exports/](src/repo-app/exports/) directory

5. **Update Testing Agents for Multi-Stack Support**
   - Modify [.github/agents/test-generator.agent.md](.github/agents/test-generator.agent.md) to accept `--analysis-file` parameter for JSON import
   - Add framework detection logic: if JSON contains `"frameworks": ["RSpec"]` → generate RSpec specs; if `["Jest"]` → generate Jest tests
   - Update [.github/agents/testing-strategy-engineer.agent.md](.github/agents/testing-strategy-engineer.agent.md) orchestration to read `agent_context.suggested_agents` from analysis
   - Add [.github/agents/framework-adapter.agent.md](.github/agents/framework-adapter.agent.md) - new meta-agent that translates generic testing patterns to framework-specific implementations
   - Create language-framework mapping in agent: `{Python: [@bdd-automation-engineer with pytest-bdd], Ruby: [@bdd-automation-engineer with Cucumber], C#: [@bdd-automation-engineer with SpecFlow]}`

6. **Add Quick Start Configuration Template**
   - Create [src/repo-app/config/tech-stacks.template.yaml](src/repo-app/config/tech-stacks.template.yaml) with commented examples for adding new languages
   - Document required fields: `name`, `extensions[]`, `package_files[]`, `frameworks[].name`, `frameworks[].indicators`, `frameworks[].test_patterns[]`, `frameworks[].coverage_command`
   - Add [docs/ADDING_TECH_STACKS.md](docs/ADDING_TECH_STACKS.md) tutorial with step-by-step guide and examples for Kotlin, Swift, Rust
   - Include troubleshooting section for common issues (regex escaping, command shell compatibility)

7. **Integration Testing & Validation**
   - Add [tests/test_config_loader.py](tests/test_config_loader.py) to validate YAML schema parsing
   - Add [tests/test_multi_language_detection.py](tests/test_multi_language_detection.py) with fixture repos for Ruby, C#, PHP
   - Test end-to-end: Analyze multi-language repo → export JSON → invoke `@test-generator --analysis-file=export.json` → verify correct framework tests generated
   - Validate backward compatibility: Existing Python/JavaScript repos produce identical analysis results

8. **Update Documentation & Migration Guide**
   - Update [docs/architecture/diagrams/repo-analyzer-architecture.md](docs/architecture/diagrams/repo-analyzer-architecture.md) to include config loader and analyzer registry
   - Add architecture diagram showing: `tech-stacks.yaml` → `ConfigLoader` → `AnalyzerRegistry` → `LanguageAnalyzer` → `Analysis` → `JSONExporter` → `Agent`
   - Create [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) for teams currently using hardcoded `constants.py` patterns
   - Update [README.md](README.md) with new CLI usage: `python repo_analyzer.py --config=repos.json --export-json`

**Verification**

```bash
# Test multi-language configuration loading
python -m pytest tests/test_config_loader.py -v

# Test polyglot repo analysis (Ruby + JavaScript)
python src/repo-app/repo_analyzer.py --repo=./test-repos/rails-react-app --export-json

# Verify JSON export contains both Ruby (RSpec) and JavaScript (Jest) context
cat src/repo-app/exports/rails-react-app_analysis.json | jq '.frameworks'

# Test agent auto-invocation from analysis
# (Manual step - future CI/CD automation)
cat exports/rails-react-app_analysis.json | jq -r '.agent_context.suggested_agents[]'
# Expected output: @test-generator --framework=RSpec, @test-generator --framework=Jest

# Validate new tech stack addition (add Kotlin example)
# 1. Edit tech-stacks.yaml to add Kotlin entry
# 2. Run: python src/repo-app/repo_analyzer.py --repo=./test-repos/kotlin-spring
# 3. Verify output includes JUnit/Kotest detection
```

**Decisions**

- **Configuration over Plugin API**: YAML files provide 80% of extensibility needs with 20% of implementation complexity; teams can add plugins later if needed
- **Generic Analyzer Fallback**: Most languages follow similar patterns (test files in `test/` or `spec/` directories); specialized analyzers only for exceptions (e.g., Swift's Xcode project parsing)
- **JSON as Integration Protocol**: Standardized format enables any agent/tool to consume analysis; future webhook support can POST this JSON to external systems
- **Phased Language Rollout**: Seed config with 8 languages in week 1; document self-service process so teams add others incrementally
- **Agent Polymorphism via Context Injection**: Rather than creating 5 variants of each agent (pytest version, RSpec version, etc.), agents read `framework` from context and adapt behavior

---

**This plan transforms repo-app into a platform that supports heterogeneous tech stacks through configuration rather than code changes, while enabling agent automation via standardized JSON exports.**
