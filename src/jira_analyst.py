#!/usr/bin/env python3
"""
JIRA Project Analyst Bot
Reads JIRA projects and provides comprehensive analysis
"""

import os
import sys
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from jira import JIRA
import json


class JiraAnalyst:
    """JIRA Project Analysis Bot"""
    
    def __init__(self, server=None, user=None, token=None):
        """Initialize JIRA connection"""
        self.server = server or os.getenv('JIRA_URL', 'https://joeycmlam-1762529818344.atlassian.net')
        self.user = user or os.getenv('JIRA_USER')
        self.token = token or os.getenv('JIRA_API_TOKEN')
        
        if not self.user or not self.token:
            raise ValueError("JIRA credentials not provided. Set JIRA_USER and JIRA_API_TOKEN environment variables.")
        
        # Use JIRA API v3 for Atlassian Cloud
        options = {'server': self.server, 'rest_api_version': '3'}
        self.jira = JIRA(options=options, basic_auth=(self.user, self.token))
        print(f"✓ Connected to JIRA: {self.server}")
    
    def analyze_project(self, project_key, max_results=1000):
        """Analyze a JIRA project and return comprehensive insights"""
        print(f"\n🔍 Analyzing project: {project_key}")
        
        try:
            # Fetch all issues
            jql = f'project={project_key} ORDER BY created DESC'
            issues = self.jira.search_issues(jql, maxResults=max_results)
            
            if not issues:
                return f"⚠️  No issues found in project {project_key}"
            
            print(f"✓ Found {len(issues)} issues")
            
            # Perform analysis
            analysis = {
                'project_key': project_key,
                'analysis_date': datetime.now().isoformat(),
                'total_tickets': len(issues),
                'overview': self._analyze_overview(issues),
                'distribution': self._analyze_distribution(issues),
                'quality': self._analyze_quality(issues),
                'risks': self._analyze_risks(issues),
                'team': self._analyze_team(issues),
                'trends': self._analyze_trends(issues),
            }
            
            # Generate report
            report = self._generate_report(analysis)
            
            return report
            
        except Exception as e:
            return f"❌ Error analyzing project: {str(e)}"
    
    def _analyze_overview(self, issues):
        """Generate overview metrics"""
        statuses = Counter(issue.fields.status.name for issue in issues)
        types = Counter(issue.fields.issuetype.name for issue in issues)
        priorities = Counter(issue.fields.priority.name if issue.fields.priority else 'None' for issue in issues)
        
        total = len(issues)
        done_count = sum(count for status, count in statuses.items() if 'done' in status.lower() or 'closed' in status.lower())
        
        return {
            'total': total,
            'done': done_count,
            'done_percentage': round((done_count / total * 100), 1) if total > 0 else 0,
            'in_progress': statuses.get('In Progress', 0),
            'to_do': statuses.get('To Do', 0) + statuses.get('Open', 0),
            'statuses': dict(statuses),
            'types': dict(types),
            'priorities': dict(priorities),
        }
    
    def _analyze_distribution(self, issues):
        """Analyze ticket distribution"""
        by_status = defaultdict(list)
        by_priority = defaultdict(list)
        by_type = defaultdict(list)
        
        for issue in issues:
            by_status[issue.fields.status.name].append(issue.key)
            by_type[issue.fields.issuetype.name].append(issue.key)
            priority = issue.fields.priority.name if issue.fields.priority else 'None'
            by_priority[priority].append(issue.key)
        
        return {
            'by_status': {k: len(v) for k, v in by_status.items()},
            'by_type': {k: len(v) for k, v in by_type.items()},
            'by_priority': {k: len(v) for k, v in by_priority.items()},
        }
    
    def _analyze_quality(self, issues):
        """Analyze ticket quality"""
        missing_description = []
        missing_acceptance = []
        well_defined = []
        
        for issue in issues:
            # Check description quality
            desc = issue.fields.description or ""
            # Handle both string and rich text format
            desc_text = str(desc) if desc else ""
            if len(desc_text.strip()) < 50:
                missing_description.append(issue.key)
            
            # Check acceptance criteria (look in description or custom field)
            if 'acceptance' not in desc_text.lower() and 'criteria' not in desc_text.lower():
                missing_acceptance.append(issue.key)
            else:
                well_defined.append(issue.key)
        
        return {
            'well_defined': len(well_defined),
            'missing_description': len(missing_description),
            'missing_acceptance_criteria': len(missing_acceptance),
            'quality_score': round((len(well_defined) / len(issues) * 10), 1) if issues else 0,
            'needs_improvement': missing_description[:5],  # First 5 examples
        }
    
    def _analyze_risks(self, issues):
        """Identify risks and blockers"""
        overdue = []
        blockers = []
        high_priority_open = []
        stale_tickets = []
        
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        for issue in issues:
            # Check overdue
            if issue.fields.duedate:
                try:
                    due = datetime.strptime(issue.fields.duedate, '%Y-%m-%d')
                    if due < now and issue.fields.status.name.lower() not in ['done', 'closed']:
                        overdue.append({
                            'key': issue.key,
                            'summary': issue.fields.summary,
                            'due_date': issue.fields.duedate
                        })
                except:
                    pass
            
            # Check for blocker priority
            if issue.fields.priority and issue.fields.priority.name in ['Blocker', 'Highest']:
                if issue.fields.status.name.lower() not in ['done', 'closed']:
                    blockers.append({
                        'key': issue.key,
                        'summary': issue.fields.summary,
                        'status': issue.fields.status.name
                    })
            
            # Check high priority open items
            if issue.fields.priority and issue.fields.priority.name in ['High', 'Critical']:
                if issue.fields.status.name.lower() not in ['done', 'closed', 'in progress']:
                    high_priority_open.append(issue.key)
            
            # Check stale tickets (not updated in 30 days)
            if issue.fields.updated:
                try:
                    updated = datetime.strptime(issue.fields.updated[:10], '%Y-%m-%d')
                    if updated < thirty_days_ago and issue.fields.status.name.lower() not in ['done', 'closed']:
                        stale_tickets.append({
                            'key': issue.key,
                            'last_updated': issue.fields.updated[:10]
                        })
                except:
                    pass
        
        return {
            'overdue_count': len(overdue),
            'overdue_tickets': overdue[:5],  # First 5
            'blocker_count': len(blockers),
            'blockers': blockers[:5],  # First 5
            'high_priority_open': len(high_priority_open),
            'stale_count': len(stale_tickets),
            'stale_tickets': stale_tickets[:5],  # First 5
        }
    
    def _analyze_team(self, issues):
        """Analyze team workload and contribution"""
        assignee_workload = defaultdict(lambda: {'total': 0, 'open': 0, 'in_progress': 0, 'done': 0})
        reporters = Counter()
        
        for issue in issues:
            assignee = issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'
            reporter = issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown'
            
            assignee_workload[assignee]['total'] += 1
            
            status = issue.fields.status.name.lower()
            if 'done' in status or 'closed' in status:
                assignee_workload[assignee]['done'] += 1
            elif 'progress' in status:
                assignee_workload[assignee]['in_progress'] += 1
            else:
                assignee_workload[assignee]['open'] += 1
            
            reporters[reporter] += 1
        
        # Sort by total workload
        sorted_workload = sorted(assignee_workload.items(), key=lambda x: x[1]['total'], reverse=True)
        
        return {
            'team_members': len([a for a in assignee_workload.keys() if a != 'Unassigned']),
            'unassigned': assignee_workload.get('Unassigned', {}).get('total', 0),
            'workload': dict(sorted_workload[:10]),  # Top 10
            'top_reporters': dict(reporters.most_common(5)),
        }
    
    def _analyze_trends(self, issues):
        """Analyze trends and patterns"""
        # Group by creation month
        by_month = defaultdict(int)
        bug_count = 0
        story_count = 0
        
        for issue in issues:
            if issue.fields.created:
                month = issue.fields.created[:7]  # YYYY-MM
                by_month[month] += 1
            
            issue_type = issue.fields.issuetype.name.lower()
            if 'bug' in issue_type:
                bug_count += 1
            elif 'story' in issue_type:
                story_count += 1
        
        bug_ratio = round((bug_count / len(issues) * 100), 1) if issues else 0
        
        return {
            'creation_by_month': dict(sorted(by_month.items())),
            'bug_count': bug_count,
            'story_count': story_count,
            'bug_ratio_percentage': bug_ratio,
            'health_indicator': 'Good' if bug_ratio < 30 else 'Needs Attention' if bug_ratio < 50 else 'Critical'
        }
    
    def _generate_report(self, analysis):
        """Generate markdown report"""
        overview = analysis['overview']
        distribution = analysis['distribution']
        quality = analysis['quality']
        risks = analysis['risks']
        team = analysis['team']
        trends = analysis['trends']
        
        report = f"""
# JIRA Project Analysis: {analysis['project_key']}

**Analysis Date:** {analysis['analysis_date'][:10]}  
**Total Tickets:** {analysis['total_tickets']}

---

## 📊 Executive Summary

### Health Score: {quality['quality_score']}/10

### Key Metrics
- **Total Tickets:** {overview['total']}
- **Completed:** {overview['done']} ({overview['done_percentage']}%)
- **In Progress:** {overview['in_progress']}
- **To Do:** {overview['to_do']}
- **Bug Ratio:** {trends['bug_ratio_percentage']}%
- **Health Status:** {trends['health_indicator']}

---

## 📈 Ticket Distribution

### By Status
"""
        for status, count in distribution['by_status'].items():
            percentage = round((count / analysis['total_tickets'] * 100), 1)
            report += f"- **{status}:** {count} ({percentage}%)\n"
        
        report += "\n### By Type\n"
        for type_name, count in distribution['by_type'].items():
            report += f"- **{type_name}:** {count}\n"
        
        report += "\n### By Priority\n"
        for priority, count in distribution['by_priority'].items():
            report += f"- **{priority}:** {count}\n"
        
        report += f"""

---

## ⚠️  Risks & Issues

### Critical Items
"""
        if risks['blocker_count'] > 0:
            report += f"- **{risks['blocker_count']} Blocker/Highest Priority** tickets found:\n"
            for blocker in risks['blockers']:
                report += f"  - [{blocker['key']}] {blocker['summary']} (Status: {blocker['status']})\n"
        else:
            report += "- ✅ No blockers found\n"
        
        if risks['overdue_count'] > 0:
            report += f"\n- **{risks['overdue_count']} Overdue** tickets:\n"
            for ticket in risks['overdue_tickets']:
                report += f"  - [{ticket['key']}] {ticket['summary']} (Due: {ticket['due_date']})\n"
        else:
            report += "\n- ✅ No overdue tickets\n"
        
        if risks['stale_count'] > 0:
            report += f"\n- **{risks['stale_count']} Stale** tickets (not updated in 30+ days):\n"
            for ticket in risks['stale_tickets'][:3]:
                report += f"  - [{ticket['key']}] Last updated: {ticket['last_updated']}\n"
        
        report += f"""

---

## 💎 Quality Assessment

- **Well-Defined Tickets:** {quality['well_defined']}
- **Missing Description:** {quality['missing_description']}
- **Missing Acceptance Criteria:** {quality['missing_acceptance_criteria']}
- **Quality Score:** {quality['quality_score']}/10

"""
        if quality['needs_improvement']:
            report += "### Tickets Needing Improvement\n"
            for key in quality['needs_improvement']:
                report += f"- {key}: Add detailed description\n"
        
        report += f"""

---

## 👥 Team Insights

- **Team Members:** {team['team_members']}
- **Unassigned Tickets:** {team['unassigned']}

### Top Contributors (by ticket count)
"""
        for assignee, workload in list(team['workload'].items())[:5]:
            report += f"- **{assignee}:** {workload['total']} tickets "
            report += f"({workload['done']} done, {workload['in_progress']} in progress, {workload['open']} open)\n"
        
        report += "\n### Top Reporters\n"
        for reporter, count in team['top_reporters'].items():
            report += f"- **{reporter}:** {count} tickets\n"
        
        report += f"""

---

## 📉 Trends

### Bug vs Story Ratio
- **Bugs:** {trends['bug_count']}
- **Stories:** {trends['story_count']}
- **Bug Ratio:** {trends['bug_ratio_percentage']}%

### Ticket Creation Trend
"""
        for month, count in list(trends['creation_by_month'].items())[-6:]:  # Last 6 months
            report += f"- **{month}:** {count} tickets created\n"
        
        report += """

---

## 🎯 Recommendations

### Immediate Actions
"""
        recommendations = []
        
        if risks['blocker_count'] > 0:
            recommendations.append(f"1. **Address {risks['blocker_count']} blocker tickets** immediately")
        
        if risks['overdue_count'] > 0:
            recommendations.append(f"2. **Review {risks['overdue_count']} overdue tickets** and update timelines")
        
        if quality['missing_acceptance_criteria'] > 10:
            recommendations.append(f"3. **Add acceptance criteria** to {quality['missing_acceptance_criteria']} tickets")
        
        if team['unassigned'] > 5:
            recommendations.append(f"4. **Assign {team['unassigned']} unassigned tickets** to team members")
        
        if trends['bug_ratio_percentage'] > 40:
            recommendations.append("5. **Investigate high bug ratio** - consider technical debt sprint")
        
        if risks['stale_count'] > 10:
            recommendations.append(f"6. **Close or update {risks['stale_count']} stale tickets** not touched in 30+ days")
        
        if not recommendations:
            recommendations.append("1. ✅ Project is in good health - maintain current practices")
        
        for rec in recommendations:
            report += f"{rec}\n"
        
        report += """

### Process Improvements
1. Ensure all tickets have clear acceptance criteria before development
2. Regular grooming sessions to prevent ticket staleness
3. Balance workload across team members
4. Monitor bug trends and allocate time for quality improvements

---

**Generated by JIRA Analyst Bot**
"""
        
        return report


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python jira_analyst.py <PROJECT_KEY> [output_file]")
        print("Example: python jira_analyst.py PROJ analysis-report.md")
        sys.exit(1)
    
    project_key = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        analyst = JiraAnalyst()
        report = analyst.analyze_project(project_key)
        
        print("\n" + "="*80)
        print(report)
        print("="*80)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"\n✅ Report saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
