"""
Configuration loader for tech stack definitions.

This module provides data structures and loading logic for the tech-stacks.yaml
configuration file, enabling language-agnostic repository analysis.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any
import yaml


@dataclass
class FrameworkIndicator:
    """Represents how to detect a test framework in a repository."""
    
    file: str  # File path pattern (e.g., "requirements.txt", "*.csproj")
    pattern: str  # Content pattern to search for (regex or plain text)
    
    def __repr__(self) -> str:
        return f"FrameworkIndicator(file='{self.file}', pattern='{self.pattern}')"


@dataclass
class FrameworkConfig:
    """Configuration for a test framework."""
    
    name: str
    indicators: List[FrameworkIndicator]
    test_patterns: List[str]  # Glob patterns for test files
    coverage_command: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FrameworkConfig":
        """Create FrameworkConfig from dictionary."""
        indicators = [
            FrameworkIndicator(**indicator) 
            for indicator in data.get("indicators", [])
        ]
        return cls(
            name=data["name"],
            indicators=indicators,
            test_patterns=data.get("test_patterns", []),
            coverage_command=data.get("coverage_command", ""),
        )
    
    def __repr__(self) -> str:
        return f"FrameworkConfig(name='{self.name}', indicators={len(self.indicators)}, patterns={len(self.test_patterns)})"


@dataclass
class LanguageConfig:
    """Configuration for a programming language."""
    
    name: str
    extensions: List[str]
    package_files: List[str]
    frameworks: List[FrameworkConfig]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LanguageConfig":
        """Create LanguageConfig from dictionary."""
        frameworks = [
            FrameworkConfig.from_dict(fw) 
            for fw in data.get("frameworks", [])
        ]
        return cls(
            name=data["name"],
            extensions=data.get("extensions", []),
            package_files=data.get("package_files", []),
            frameworks=frameworks,
        )
    
    def get_framework(self, name: str) -> Optional[FrameworkConfig]:
        """Get framework configuration by name."""
        for framework in self.frameworks:
            if framework.name.lower() == name.lower():
                return framework
        return None
    
    def __repr__(self) -> str:
        return f"LanguageConfig(name='{self.name}', extensions={len(self.extensions)}, frameworks={len(self.frameworks)})"


@dataclass
class CICDPlatformConfig:
    """Configuration for CI/CD platform detection."""
    
    name: str
    indicators: List[FrameworkIndicator]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CICDPlatformConfig":
        """Create CICDPlatformConfig from dictionary."""
        indicators = [
            FrameworkIndicator(**indicator) 
            for indicator in data.get("indicators", [])
        ]
        return cls(
            name=data["name"],
            indicators=indicators,
        )


@dataclass
class TestClassificationConfig:
    """Configuration for test type classification."""
    
    patterns: List[str]
    paths: List[str]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestClassificationConfig":
        """Create TestClassificationConfig from dictionary."""
        return cls(
            patterns=data.get("patterns", []),
            paths=data.get("paths", []),
        )


@dataclass
class TechStackConfig:
    """Complete tech stack configuration."""
    
    languages: List[LanguageConfig]
    cicd_platforms: List[CICDPlatformConfig] = field(default_factory=list)
    test_classifications: Dict[str, TestClassificationConfig] = field(default_factory=dict)
    maturity_weights: Dict[str, float] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TechStackConfig":
        """Create TechStackConfig from dictionary."""
        languages = [
            LanguageConfig.from_dict(lang) 
            for lang in data.get("languages", [])
        ]
        
        cicd_platforms = [
            CICDPlatformConfig.from_dict(platform)
            for platform in data.get("cicd_platforms", [])
        ]
        
        test_classifications = {
            name: TestClassificationConfig.from_dict(config)
            for name, config in data.get("test_classifications", {}).items()
        }
        
        maturity_weights = data.get("maturity_weights", {})
        
        return cls(
            languages=languages,
            cicd_platforms=cicd_platforms,
            test_classifications=test_classifications,
            maturity_weights=maturity_weights,
        )
    
    def get_language(self, name: str) -> Optional[LanguageConfig]:
        """Get language configuration by name."""
        for language in self.languages:
            if language.name.lower() == name.lower():
                return language
        return None
    
    def get_language_by_extension(self, extension: str) -> Optional[LanguageConfig]:
        """Get language configuration by file extension."""
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        for language in self.languages:
            if extension in language.extensions:
                return language
        return None
    
    def get_all_test_patterns(self) -> List[str]:
        """Get all test file patterns from all languages."""
        patterns = []
        for language in self.languages:
            for framework in language.frameworks:
                patterns.extend(framework.test_patterns)
        return list(set(patterns))  # Remove duplicates
    
    def __repr__(self) -> str:
        return f"TechStackConfig(languages={len(self.languages)}, cicd_platforms={len(self.cicd_platforms)})"


class ConfigLoader:
    """Loader for tech stack configuration files."""
    
    _instance: Optional["ConfigLoader"] = None
    _config: Optional[TechStackConfig] = None
    _config_path: Optional[Path] = None
    
    def __new__(cls):
        """Singleton pattern to cache configuration."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load(self, config_path: Optional[Path] = None) -> TechStackConfig:
        """
        Load tech stack configuration from YAML file.
        
        Args:
            config_path: Path to config file. If None, uses default location.
        
        Returns:
            TechStackConfig object with loaded configuration.
        
        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file has invalid YAML.
        """
        # Use cached config if same path
        if self._config is not None and self._config_path == config_path:
            return self._config
        
        # Determine config file path
        if config_path is None:
            # Default to config/tech-stacks.yaml relative to this file
            current_dir = Path(__file__).parent
            config_path = current_dir / "tech-stacks.yaml"
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Tech stack configuration file not found: {config_path}\n"
                f"Please ensure tech-stacks.yaml exists in {config_path.parent}"
            )
        
        # Load YAML
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f"Invalid YAML in tech stack configuration: {config_path}\n"
                f"Error: {e}"
            )
        
        # Parse into dataclasses
        self._config = TechStackConfig.from_dict(yaml_data)
        self._config_path = config_path
        
        return self._config
    
    def reload(self, config_path: Optional[Path] = None) -> TechStackConfig:
        """Force reload configuration, bypassing cache."""
        self._config = None
        self._config_path = None
        return self.load(config_path)
    
    @property
    def config(self) -> Optional[TechStackConfig]:
        """Get cached configuration (None if not loaded)."""
        return self._config


# Convenience function for quick access
def load_tech_stacks(config_path: Optional[Path] = None) -> TechStackConfig:
    """
    Load tech stack configuration.
    
    Args:
        config_path: Optional path to configuration file.
    
    Returns:
        TechStackConfig object.
    
    Example:
        >>> config = load_tech_stacks()
        >>> python_lang = config.get_language("Python")
        >>> print(python_lang.frameworks[0].name)
        pytest
    """
    loader = ConfigLoader()
    return loader.load(config_path)


# Module-level convenience functions
def get_language_config(language_name: str, config_path: Optional[Path] = None) -> Optional[LanguageConfig]:
    """Get language configuration by name."""
    config = load_tech_stacks(config_path)
    return config.get_language(language_name)


def get_framework_config(
    language_name: str, 
    framework_name: str, 
    config_path: Optional[Path] = None
) -> Optional[FrameworkConfig]:
    """Get framework configuration for a specific language."""
    lang_config = get_language_config(language_name, config_path)
    if lang_config:
        return lang_config.get_framework(framework_name)
    return None


if __name__ == "__main__":
    # Example usage and validation
    import sys
    
    try:
        config = load_tech_stacks()
        print(f"✅ Configuration loaded successfully!")
        print(f"   Languages: {len(config.languages)}")
        print(f"   CI/CD Platforms: {len(config.cicd_platforms)}")
        print()
        
        print("Supported Languages:")
        for lang in config.languages:
            framework_names = [f.name for f in lang.frameworks]
            print(f"  - {lang.name}: {', '.join(framework_names)}")
        
        print()
        print("Supported CI/CD Platforms:")
        for platform in config.cicd_platforms:
            print(f"  - {platform.name}")
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)
