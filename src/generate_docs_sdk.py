#!/usr/bin/env python3
"""
Documentation Generator using GitHub Copilot SDK

This script uses the GitHub Copilot SDK to generate comprehensive documentation
for the MYPPS Portfolio Management System by leveraging specialized agents.

Based on: https://techcommunity.microsoft.com/blog/azuredevcommunityblog/
building-agents-with-github-copilot-sdk-a-practical-guide-to-automated-tech-upda/4488948
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from copilot import CopilotClient
    from copilot.generated.session_events import SessionEventType
except ImportError:
    print("❌ Error: github-copilot-sdk not installed")
    print("Install with: pip install github-copilot-sdk")
    sys.exit(1)


class DocumentationGenerator:
    """Generates documentation using GitHub Copilot SDK with specialized agents."""
    
    # Valid git time specifications pattern
    GIT_TIME_PATTERN = re.compile(r'^\d+\s+(second|minute|hour|day|week|month|year)s?\s+ago$')
    VALID_DOC_TYPES = {'architecture', 'api', 'database', 'workflows'}
    
    # Display limits
    MAX_FILES_TO_DISPLAY = 30
    MAX_COMMIT_MESSAGE_LENGTH = 500
    MAX_DOC_FILES_PREVIEW = 5
    
    # Timeouts
    SESSION_TIMEOUT_SECONDS = 600
    
    # Doc type descriptions
    DOC_TYPE_DESCRIPTIONS = {
        'architecture': 'System architecture, component diagrams, design patterns',
        'api': 'REST API specifications, endpoints, request/response examples',
        'database': 'Database schemas, ER diagrams, relationships, indexes',
        'workflows': 'Business logic flows, data transformations, process diagrams'
    }
    
    def __init__(self, agent_name: str = "doc-architect", doc_types: str = "architecture",
                 mode: str = "incremental", since: str = "1 month ago",
                 model: str = "claude-sonnet-4.5"):
        self.agent_name = agent_name
        self.model = model
        
        # Validate and parse doc_types
        self.doc_types = [dt.strip() for dt in doc_types.split(',') if dt.strip()]
        if not self.doc_types:
            logger.error("No documentation types specified")
            sys.exit(1)
        
        # Warn about unknown doc types
        for dt in self.doc_types:
            if dt not in self.VALID_DOC_TYPES:
                logger.warning(f"Unknown documentation type '{dt}' - will attempt to process anyway")
        
        self.mode = mode  # "full" or "incremental"
        
        # Validate git time specification to prevent command injection
        if not self._validate_git_time(since):
            logger.error(f"Invalid git time specification: '{since}'")
            logger.error("Use format like: '1 month ago', '2 weeks ago', '30 days ago'")
            sys.exit(1)
        self.since = since
        
        self.repository = os.getenv('GITHUB_REPOSITORY', 'mypps/portfolio-system')
        self.work_dir = Path.cwd()
        self.agent_file = self.work_dir / ".github" / "agents" / f"{agent_name}.agent.md"
        self.metadata_file = self.work_dir / "docs" / ".generation-metadata.json"
        
        # Ensure agent file exists
        if not self.agent_file.exists():
            logger.error(f"Agent file not found: {self.agent_file}")
            logger.error("Available agents should be in: .github/agents/")
            sys.exit(1)
    
    def _validate_git_time(self, time_spec: str) -> bool:
        """Validate git time specification to prevent command injection."""
        # Allow common git time formats
        return bool(self.GIT_TIME_PATTERN.match(time_spec.lower()))
    
    def _format_section_header(self, title: str, level: int = 2) -> str:
        """Format a markdown section header."""
        return f"{'#' * level} {title}"
    
    def _format_metadata_list(self, items: Dict[str, str]) -> str:
        """Format a list of metadata items as markdown."""
        return '\n'.join(f"- **{key}**: {value}" for key, value in items.items())
    
    def _build_code_block(self, content: str, max_length: Optional[int] = None) -> str:
        """Format content as a markdown code block with optional truncation."""
        if max_length and len(content) > max_length:
            content = content[:max_length] + '...'
        return f"```\n{content}\n```"
    
    def load_agent_instructions(self) -> str:
        """Load agent instructions from the agent markdown file."""
        try:
            with open(self.agent_file, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            logger.warning(f"Encoding issue with {self.agent_file}, trying latin-1")
            with open(self.agent_file, 'r', encoding='latin-1') as f:
                return f.read()
        except IOError as e:
            logger.error(f"Failed to read agent file: {e}")
            sys.exit(1)
    
    def get_git_changes(self) -> Dict:
        """Get list of changed files and recent commits."""
        try:
            # Get current commit hash
            current_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=self.work_dir,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            # Get changed files since timestamp
            changed_files = subprocess.check_output(
                ["git", "diff", "--name-only", f"@{{{self.since}}}..HEAD"],
                cwd=self.work_dir,
                stderr=subprocess.DEVNULL
            ).decode().splitlines()
            
            # Get recent commits
            recent_commits = subprocess.check_output(
                ["git", "log", f"--since={self.since}", "--oneline", "--no-decorate"],
                cwd=self.work_dir,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            # Get commit count
            commit_count = len(recent_commits.splitlines()) if recent_commits else 0
            
            return {
                "current_commit": current_commit,
                "changed_files": changed_files,
                "recent_commits": recent_commits,
                "commit_count": commit_count,
                "has_changes": len(changed_files) > 0
            }
        except subprocess.CalledProcessError as e:
            # Fallback if git commands fail
            logger.warning(f"Git command failed: {e}")
            logger.warning("Using fallback values - documentation may be incomplete")
            return {
                "current_commit": "unknown",
                "changed_files": [],
                "recent_commits": "",
                "commit_count": 0,
                "has_changes": False
            }
    
    def analyze_existing_docs(self) -> Dict:
        """Analyze existing documentation to understand current state."""
        existing_docs = {}
        
        for doc_type in self.doc_types:
            doc_dir = self.work_dir / "docs" / doc_type
            try:
                if doc_dir.exists():
                    md_files = list(doc_dir.glob("*.md"))
                    existing_docs[doc_type] = {
                        "count": len(md_files),
                        "files": sorted([f.name for f in md_files]),
                        "last_modified": max(
                            (f.stat().st_mtime for f in md_files),
                            default=0
                        )
                    }
                else:
                    existing_docs[doc_type] = {
                        "count": 0,
                        "files": [],
                        "last_modified": 0
                    }
            except OSError as e:
                logger.warning(f"Cannot access {doc_dir}: {e}")
                existing_docs[doc_type] = {
                    "count": 0,
                    "files": [],
                    "last_modified": 0
                }
        
        return existing_docs
    
    def load_last_metadata(self) -> Optional[Dict]:
        """Load metadata from last generation."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load metadata from {self.metadata_file}: {e}")
                return None
        return None
    
    def save_generation_metadata(self, git_changes: Dict):
        """Save metadata about this documentation generation."""
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "agent_name": self.agent_name,
            "doc_types": self.doc_types,
            "mode": self.mode,
            "model": self.model,
            "commit_hash": git_changes["current_commit"],
            "files_analyzed": len(git_changes["changed_files"]),
            "commit_count_since_last": git_changes["commit_count"],
            "repository": self.repository
        }
        
        try:
            # Ensure docs directory exists
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✓ Metadata saved to {self.metadata_file.relative_to(self.work_dir)}")
        except (IOError, OSError) as e:
            logger.warning(f"Failed to save metadata: {e}")
    
    def build_prompt(self) -> str:
        """Build the complete prompt for the Copilot session."""
        agent_instructions = self.load_agent_instructions()
        git_changes = self.get_git_changes()
        existing_docs = self.analyze_existing_docs()
        last_metadata = self.load_last_metadata()
        
        # Determine actual mode based on changes and existing docs
        effective_mode = self._determine_effective_mode(git_changes, existing_docs)
        
        # Build mode-specific context
        if effective_mode == "incremental" and git_changes["has_changes"]:
            update_context = self._build_incremental_context(git_changes, existing_docs, last_metadata)
        else:
            update_context = self._build_full_context(existing_docs)
        
        prompt = f"""{agent_instructions}

## Task Context

**Repository**: {self.repository}
**Documentation Types**: {', '.join(self.doc_types)}
**Working Directory**: {self.work_dir}
**Mode**: {effective_mode.upper()}
**Current Commit**: {git_changes['current_commit'][:8]}

{update_context}

## Documentation Types to Process
{self._format_doc_types()}

## Execution Instructions

1. **Review context above** - Understand what needs to be documented
2. **Analyze relevant code** - Focus on changed files or entire codebase based on mode
3. **{'Update existing' if effective_mode == 'incremental' else 'Generate'} documentation** - Create/modify markdown files
4. **Use Mermaid diagrams** - Include architecture, sequence, ER, and flowcharts
5. **Include code examples** - Reference actual code from the repository
6. **Follow conventions** - Use patterns from `.github/copilot-instructions.md`

## Output Directories
- Architecture docs → `docs/architecture/`
- API docs → `docs/api/`
- Database docs → `docs/database/`
- Workflow docs → `docs/workflows/`

## Quality Standards
- Documentation must be accurate and based on actual code
- Include practical examples and use cases
- Generate proper Mermaid diagrams (architecture, sequence, ER, flowcharts)
- Cross-reference between different documentation sections
- Maintain consistency with existing documentation style
- Add "Last updated: {datetime.now().strftime('%Y-%m-%d')}" to modified sections

## Output Requirements
- Create/update markdown files in the `docs/` directory
- Use clear, professional technical writing
- Include table of contents for long documents
- Ensure all links and references are valid

Execute this task and save all documentation to the appropriate locations.
"""
        return prompt
    
    def _determine_effective_mode(self, git_changes: Dict, existing_docs: Dict) -> str:
        """Determine whether to run in incremental or full mode."""
        # Force full mode if requested
        if self.mode == "full":
            return "full"
        
        # Full mode if no existing docs
        total_docs = sum(info["count"] for info in existing_docs.values())
        if total_docs == 0:
            return "full"
        
        # Incremental if we have docs and changes
        if git_changes["has_changes"]:
            return "incremental"
        
        # Full mode if no changes detected
        return "full"
    
    def _build_strategy_section(self, mode: str, is_initial: bool = False) -> str:
        """Build the strategy section for documentation generation."""
        if mode == "incremental":
            return """### 🎯 INCREMENTAL UPDATE STRATEGY

**IMPORTANT**: This is an incremental update, not a full regeneration.

1. **Read existing documentation first** - Understand the current baseline
2. **Focus on changed files** - Analyze only the files listed above
3. **Update affected sections** - Modify only documentation sections impacted by changes
4. **Preserve valid content** - Keep diagrams, examples, and text that are still accurate
5. **Mark updates** - Add "Last updated: DATE" to modified sections
6. **Maintain consistency** - Match the style and structure of existing docs

**DO NOT** regenerate documentation that is still accurate.
**DO** update cross-references and links to changed code."""
        elif is_initial:
            return """### 🎯 INITIAL GENERATION STRATEGY

1. **Analyze entire codebase** - Understand all system components
2. **Create comprehensive docs** - Cover all aspects thoroughly
3. **Generate diagrams** - Create Mermaid diagrams for all major components
4. **Include examples** - Reference actual code examples
5. **Establish structure** - Create well-organized documentation hierarchy"""
        else:
            return """### 🎯 FULL REGENERATION STRATEGY

This is a complete documentation regeneration from scratch.

1. **Analyze entire codebase** - Understand all system components
2. **Generate comprehensive docs** - Cover all aspects of the system
3. **Create new diagrams** - Generate all Mermaid diagrams fresh
4. **Include all examples** - Reference current code examples
5. **Maintain structure** - Keep similar organization to existing docs if useful

You may replace existing documentation files completely."""
    
    def _build_incremental_context(self, git_changes: Dict, existing_docs: Dict, 
                                   last_metadata: Optional[Dict]) -> str:
        """Build context section for incremental update mode."""
        sections = ["## Update Context (Incremental Mode)", "", "### Recent Changes"]
        
        if git_changes["commit_count"] > 0:
            sections.extend([
                f"**Commits since last update**: {git_changes['commit_count']}",
                f"**Changed files**: {len(git_changes['changed_files'])} files",
                "",
                "**Recent commits**:",
                self._build_code_block(git_changes['recent_commits'], self.MAX_COMMIT_MESSAGE_LENGTH),
            ])
        
        if git_changes["changed_files"]:
            sections.extend([
                "",
                "**Files that changed** (focus your analysis here):",
                self._format_file_list(git_changes['changed_files'])
            ])
        
        sections.extend(["", "### Existing Documentation", self._format_existing_docs(existing_docs)])
        
        if last_metadata:
            sections.extend([
                "",
                "### Last Generation",
                self._format_metadata_list({
                    "Date": last_metadata.get('generated_at', 'unknown'),
                    "Commit": last_metadata.get('commit_hash', 'unknown')[:8],
                    "Agent": last_metadata.get('agent_name', 'unknown')
                })
            ])
        
        sections.extend(["", self._build_strategy_section("incremental")])
        
        return '\n'.join(sections)
    
    def _build_full_context(self, existing_docs: Dict) -> str:
        """Build context section for full generation mode."""
        total_docs = sum(info["count"] for info in existing_docs.values())
        is_initial = total_docs == 0
        
        sections = [
            "## Generation Context (Initial Documentation)" if is_initial else "## Generation Context (Full Regeneration Mode)",
            ""
        ]
        
        if is_initial:
            sections.append("**No existing documentation found** - This is the initial documentation generation.")
        else:
            sections.extend(["### Existing Documentation", self._format_existing_docs(existing_docs)])
        
        sections.extend(["", self._build_strategy_section("full", is_initial=is_initial)])
        
        return '\n'.join(sections)
    
    def _format_file_list(self, files: List[str]) -> str:
        """Format file list for prompt."""
        if not files:
            return "   (no changes)"
        
        display_files = files[:self.MAX_FILES_TO_DISPLAY]
        lines = [f"   - `{f}`" for f in display_files]
        
        if len(files) > self.MAX_FILES_TO_DISPLAY:
            lines.append(f"   ... and {len(files) - self.MAX_FILES_TO_DISPLAY} more files")
        
        return '\n'.join(lines)
    
    def _format_existing_docs(self, docs_info: Dict) -> str:
        """Format existing docs info for prompt."""
        def format_doc_entry(doc_type: str, info: Dict) -> str:
            if info['count'] == 0:
                return f"   - **{doc_type}**: (no existing docs)"
            
            preview_files = info['files'][:self.MAX_DOC_FILES_PREVIEW]
            files_list = ', '.join(f"`{f}`" for f in preview_files)
            
            if len(info['files']) > self.MAX_DOC_FILES_PREVIEW:
                files_list += f" ... and {len(info['files']) - self.MAX_DOC_FILES_PREVIEW} more"
            
            return f"   - **{doc_type}**: {info['count']} files - {files_list}"
        
        return '\n'.join(format_doc_entry(doc_type, info) for doc_type, info in docs_info.items())
    
    def _format_doc_types(self) -> str:
        """Format the documentation types as a bulleted list."""
        lines = [
            f"   - **{doc_type.strip().title()}**: {self.DOC_TYPE_DESCRIPTIONS.get(doc_type.strip(), doc_type)}"
            for doc_type in self.doc_types
        ]
        return '\n'.join(lines)
    
    async def generate(self):
        """Execute the documentation generation process."""
        print("=" * 80)
        print("📚 MYPPS Documentation Generator (Copilot SDK)")
        print("=" * 80)
        print(f"Agent: {self.agent_name}")
        print(f"Doc Types: {', '.join(self.doc_types)}")
        print(f"Repository: {self.repository}")
        print(f"Mode: {self.mode}")
        print(f"Agent File: {self.agent_file.relative_to(self.work_dir)}")
        print("=" * 80)
        print()
        
        # Get git changes for context
        git_changes = self.get_git_changes()
        print("📊 Git Status:")
        print(f"   Commit: {git_changes['current_commit'][:8]}")
        print(f"   Changed files: {len(git_changes['changed_files'])}")
        print(f"   Commits since {self.since}: {git_changes['commit_count']}")
        
        # Analyze existing docs
        existing_docs = self.analyze_existing_docs()
        total_existing = sum(info['count'] for info in existing_docs.values())
        print(f"   Existing docs: {total_existing} files")
        print()
        
        # Initialize Copilot client
        client = CopilotClient()
        await client.start()
        print("✓ Copilot client initialized")
        
        # Ensure output directories exist
        for doc_type in self.doc_types:
            doc_dir = self.work_dir / "docs" / doc_type
            doc_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ Ensured directory exists: {doc_dir.relative_to(self.work_dir)}")
        
        # Create session with specified model
        # Using streaming for real-time feedback
        session = await client.create_session({
            "model": self.model,
            "streaming": True,
            # Note: skill_directories expects SKILL.md files, not agent.md
            # For now, we'll include instructions in the prompt
        })
        
        print(f"✓ Session created (ID: {session.session_id})")
        print()
        print("=" * 80)
        print("🤖 Starting Documentation Generation...")
        print("=" * 80)
        print()
        
        # Listen for response events
        def handle_event(event):
            if event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
                # Print streaming content in real-time
                sys.stdout.write(event.data.delta_content)
                sys.stdout.flush()
            elif event.type == SessionEventType.SESSION_IDLE:
                print("\n")  # New line when done
        
        session.on(handle_event)
        
        # Build and send the prompt
        prompt = self.build_prompt()
        
        # Increase timeout to 10 minutes for comprehensive analysis
        try:
            await session.send_and_wait({"prompt": prompt}, timeout=self.SESSION_TIMEOUT_SECONDS)
        except Exception as e:
            print(f"\n❌ Error during generation: {e}", file=sys.stderr)
            await client.stop()
            sys.exit(1)
        
        print()
        print("=" * 80)
        print("✅ Documentation Generation Complete!")
        print("=" * 80)
        
        # Save generation metadata
        self.save_generation_metadata(git_changes)
        
        # List generated files
        print("\n📄 Documentation files:")
        total_files = 0
        for doc_type in self.doc_types:
            doc_dir = self.work_dir / "docs" / doc_type
            if doc_dir.exists():
                md_files = list(doc_dir.glob("*.md"))
                if md_files:
                    print(f"\n  {doc_type.upper()}:")
                    for md_file in sorted(md_files):
                        size = md_file.stat().st_size
                        print(f"    - {md_file.name} ({size:,} bytes)")
                        total_files += 1
                else:
                    print(f"\n  {doc_type.upper()}: (no files)")
        
        print(f"\n  Total: {total_files} markdown files")
        
        await client.stop()
        print("\n✓ Copilot client stopped")


def main():
    """Main entry point for the documentation generator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate or update documentation using GitHub Copilot SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Incremental update (default)
  python3 script/generate_docs_sdk.py --mode incremental
  
  # Full regeneration
  python3 script/generate_docs_sdk.py --mode full
  
  # Specific doc types
  python3 script/generate_docs_sdk.py --types architecture,api
  
  # Custom time range
  python3 script/generate_docs_sdk.py --since "2 weeks ago"
  
  # Use specific agent
  python3 script/generate_docs_sdk.py --agent doc-api-specialist --types api

Environment Variables:
  AGENT_NAME          Agent to use (default: doc-architect)
  DOC_TYPES           Comma-separated doc types (default: architecture)
  DOC_MODE            Generation mode: full or incremental (default: incremental)
  COPILOT_MODEL       AI model to use (default: claude-sonnet-4.5)
  GITHUB_REPOSITORY   Repository name (default: mypps/portfolio-system)
        """
    )
    
    parser.add_argument(
        '--agent',
        default=os.getenv('AGENT_NAME', 'doc-architect'),
        help='Agent name to use (default: doc-architect)'
    )
    parser.add_argument(
        '--types',
        default=os.getenv('DOC_TYPES', 'architecture'),
        help='Comma-separated doc types (default: architecture)'
    )
    parser.add_argument(
        '--mode',
        choices=['full', 'incremental'],
        default=os.getenv('DOC_MODE', 'incremental'),
        help='Generation mode: full or incremental (default: incremental)'
    )
    parser.add_argument(
        '--since',
        default='1 month ago',
        help='Time range for change detection in git format (default: "1 month ago")'
    )
    parser.add_argument(
        '--model',
        default=os.getenv('COPILOT_MODEL', 'claude-sonnet-4.5'),
        help='AI model to use (default: claude-sonnet-4.5)'
    )
    
    args = parser.parse_args()
    
    # Create and run generator
    generator = DocumentationGenerator(
        agent_name=args.agent,
        doc_types=args.types,
        mode=args.mode,
        since=args.since,
        model=args.model
    )
    
    try:
        asyncio.run(generator.generate())
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
