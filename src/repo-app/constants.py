"""
Constants for repository analysis.

Author: Automated Software Engineering Team
Date: February 2026
"""

# Test file patterns
TEST_PATTERNS = [
    "test_*.py", "*_test.py", "test*.py",  # Python
    "*.test.ts", "*.test.js", "*.spec.ts", "*.spec.js",  # JavaScript/TypeScript
    "*Test.java",  # Java
    "*_test.go",  # Go
]

FEATURE_FILE_PATTERN = "*.feature"

# Language detection patterns
LANGUAGE_PATTERNS = {
    "Python": "*.py",
    "JavaScript": ["*.js", "*.jsx"],
    "TypeScript": ["*.ts", "*.tsx"],
    "Java": "*.java",
    "Go": "*.go",
}

# Test framework indicators
FRAMEWORK_INDICATORS = {
    "requirements.txt": {
        "pytest": "pytest",
        "unittest": "unittest",
        "pytest-bdd": "pytest-bdd",
    },
    "package.json": {
        "jest": "Jest",
        "vitest": "Vitest",
        "playwright": "Playwright",
        "cypress": "Cypress",
    }
}

# Test classification keywords
TEST_KEYWORDS = {
    "e2e": ["e2e", "end_to_end", "playwright", "cypress"],
    "performance": ["performance", "perf", "benchmark", "load_test"],
    "smoke": ["smoke"],
    "integration": ["integration"],
}

# Coverage file locations
COVERAGE_FILES = {
    "python": "coverage.xml",
    "javascript": "coverage/coverage-summary.json",
}

# CI/CD platform indicators
CICD_PLATFORMS = {
    "GitHub Actions": ".github/workflows",
    "GitLab CI": ".gitlab-ci.yml",
    "Jenkins": "Jenkinsfile",
    "CircleCI": ".circleci/config.yml",
    "Travis CI": ".travis.yml",
    "Azure Pipelines": "azure-pipelines.yml",
}

# CI/CD capability keywords
CICD_KEYWORDS = {
    "testing": ["test", "pytest", "jest", "npm test", "npm run test", "mvn test", "go test"],
    "security": [
        "codeql", "snyk", "trivy", "security", "vulnerability", "scan",
        "dependabot", "npm audit", "safety check", "bandit", "sast",
        "dependency_scanning", "container_scanning", "sonar", "owasp"
    ],
    "deployment": [
        "deploy", "deployment", "publish", "release", "docker push",
        "kubectl apply", "terraform apply", "aws deploy", "azure deploy",
        "gcloud deploy", "heroku", "vercel", "netlify", "production", "staging"
    ],
}

# Git analysis timeframes (in days)
GIT_TIMEFRAMES = {
    "month": 30,
    "quarter": 90,
    "year": 365,
}

# Performance constants
COPILOT_BATCH_SIZE = 10
COPILOT_TIMEOUT = 30.0
GIT_COMMAND_TIMEOUT = 30
CLONE_TIMEOUT = 300
FILE_PREVIEW_LENGTH = 500

# API constants
GITHUB_API_BASE = "https://api.github.com"
GITHUB_API_PER_PAGE = 100
