#!/usr/bin/env python3
"""
GitHub Repository List Retriever
Fetches repository information using GitHub REST API v3

Usage:
    python get-github-repos.py <username>
    python get-github-repos.py <username> --token <github_token>
    python get-github-repos.py <org_name> --org --token <github_token>

Examples:
    python get-github-repos.py octocat
    python get-github-repos.py myorg --org --token ghp_xxxxx
"""

import argparse
import json
import os
import ssl
import sys
from typing import List, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class GitHubRepoFetcher:
    """Fetches repository information from GitHub API"""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None, verify_ssl: bool = True):
        """
        Initialize the fetcher with optional authentication token

        Args:
            token: GitHub personal access token for authentication
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Repo-Fetcher'
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
        
        # Create SSL context
        if verify_ssl:
            # Try to use system certificates
            try:
                import certifi
                self.ssl_context = ssl.create_default_context(cafile=certifi.where())
            except ImportError:
                # Fallback to default context
                self.ssl_context = ssl.create_default_context()
        else:
            # Disable SSL verification (not recommended for production)
            self.ssl_context = ssl._create_unverified_context()

    def _make_request(self, url: str) -> List[Dict]:
        """
        Make HTTP request to GitHub API with pagination support

        Args:
            url: API endpoint URL

        Returns:
            List of repository dictionaries
        """
        all_results = []
        page = 1
        per_page = 100  # Maximum allowed by GitHub API

        while True:
            paginated_url = f"{url}?page={page}&per_page={per_page}"

            try:
                request = Request(paginated_url, headers=self.headers)
                with urlopen(request, timeout=30, context=self.ssl_context) as response:
                    data = json.loads(response.read().decode('utf-8'))

                    if not data:  # No more results
                        break

                    all_results.extend(data)

                    # Check if there are more pages
                    if len(data) < per_page:
                        break

                    page += 1

            except HTTPError as e:
                error_body = e.read().decode('utf-8')
                print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
                print(f"Response: {error_body}", file=sys.stderr)

                if e.code == 401:
                    print("Authentication failed. Check your token.", file=sys.stderr)
                elif e.code == 403:
                    print("Rate limit exceeded or access forbidden.", file=sys.stderr)
                elif e.code == 404:
                    print("User/organization not found.", file=sys.stderr)

                sys.exit(1)

            except URLError as e:
                print(f"Network Error: {e.reason}", file=sys.stderr)
                sys.exit(1)

            except Exception as e:
                print(f"Unexpected error: {str(e)}", file=sys.stderr)
                sys.exit(1)

        return all_results

    def get_user_repos(self, username: str) -> List[Dict]:
        """
        Get all repositories for a user

        Args:
            username: GitHub username

        Returns:
            List of repository information dictionaries
        """
        url = f"{self.BASE_URL}/users/{username}/repos"
        return self._make_request(url)

    def get_org_repos(self, org_name: str) -> List[Dict]:
        """
        Get all repositories for an organization

        Args:
            org_name: GitHub organization name

        Returns:
            List of repository information dictionaries
        """
        url = f"{self.BASE_URL}/orgs/{org_name}/repos"
        return self._make_request(url)

    def get_authenticated_user_repos(self) -> List[Dict]:
        """
        Get all repositories for the authenticated user (requires token)

        Returns:
            List of repository information dictionaries
        """
        if not self.token:
            print("Error: Token required for authenticated user repos", file=sys.stderr)
            sys.exit(1)

        url = f"{self.BASE_URL}/user/repos"
        return self._make_request(url)


def format_repo_info(repos: List[Dict], output_format: str = 'table') -> None:
    """
    Format and display repository information

    Args:
        repos: List of repository dictionaries
        output_format: Output format ('table', 'json', 'simple')
    """
    if not repos:
        print("No repositories found.")
        return

    if output_format == 'json':
        print(json.dumps(repos, indent=2))
        return

    if output_format == 'simple':
        for repo in repos:
            print(f"{repo['full_name']}: {repo['html_url']}")
        return

    # Table format (default)
    print(f"\nFound {len(repos)} repositories:\n")
    print(f"{'Repository':<40} {'Private':<8} {'Stars':<8} {'Language':<15}")
    print("-" * 80)

    for repo in repos:
        name = repo['full_name'][:39]
        private = 'Yes' if repo['private'] else 'No'
        stars = repo['stargazers_count']
        language = repo['language'] or 'N/A'

        print(f"{name:<40} {private:<8} {stars:<8} {language:<15}")

    print(f"\nTotal: {len(repos)} repositories")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Fetch GitHub repositories using GitHub API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get public repos for a user
  python get-github-repos.py octocat

  # Get repos for an organization with authentication
  python get-github-repos.py microsoft --org --token ghp_xxxxx

  # Get repos for authenticated user
  python get-github-repos.py --me --token ghp_xxxxx

  # Output as JSON
  python get-github-repos.py octocat --format json
  
  # Disable SSL verification (if encountering certificate errors)
  python get-github-repos.py --me --no-verify-ssl

Environment Variables:
  GITHUB_TOKEN: GitHub personal access token (alternative to --token)

Note:
  If you encounter SSL certificate errors on macOS, you can:
  1. Install certifi: pip install certifi
  2. Run the Install Certificates command from Python folder in Applications
  3. Use --no-verify-ssl flag (not recommended for production)
        """
    )

    parser.add_argument(
        'name',
        nargs='?',
        help='GitHub username or organization name'
    )
    parser.add_argument(
        '--token',
        help='GitHub personal access token for authentication'
    )
    parser.add_argument(
        '--org',
        action='store_true',
        help='Fetch organization repositories instead of user repositories'
    )
    parser.add_argument(
        '--me',
        action='store_true',
        help='Fetch repositories for the authenticated user (requires token)'
    )
    parser.add_argument(
        '--format',
        choices=['table', 'json', 'simple'],
        default='table',
        help='Output format (default: table)'
    )
    parser.add_argument(
        '--no-verify-ssl',
        action='store_true',
        help='Disable SSL certificate verification (not recommended for production)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.me:
        if not args.token and not os.environ.get('GITHUB_TOKEN'):
            parser.error("--me requires --token or GITHUB_TOKEN environment variable")
    elif not args.name:
        parser.error("name is required unless using --me")

    # Create fetcher instance
    fetcher = GitHubRepoFetcher(token=args.token, verify_ssl=not args.no_verify_ssl)

    # Fetch repositories
    try:
        # Use stderr for progress messages when outputting JSON
        output_stream = sys.stderr if args.format == 'json' else sys.stdout
        
        if args.me:
            print("Fetching repositories for authenticated user...", file=output_stream)
            repos = fetcher.get_authenticated_user_repos()
        elif args.org:
            print(f"Fetching repositories for organization: {args.name}", file=output_stream)
            repos = fetcher.get_org_repos(args.name)
        else:
            print(f"Fetching repositories for user: {args.name}", file=output_stream)
            repos = fetcher.get_user_repos(args.name)

        # Display results
        format_repo_info(repos, args.format)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
