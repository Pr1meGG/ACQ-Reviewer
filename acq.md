# 🚀 Automated Code Quality Reviewer Backend

Based on the latest 2024 tools and best practices, here's a comprehensive backend architecture for your automated code quality reviewer project. This is perfect for 7th semester CS majors as it combines modern web development, DevOps, and software engineering principles.

## 🏗️ Architecture Overview

```python
# Project Structure
code-quality-backend/
├── app/
│   ├── main.py                 # FastAPI app factory
│   ├── api/
│   │   └── v1/
│   │       ├── routers/        # API endpoints
│   │       ├── schemas/        # Pydantic models
│   │       └── deps.py         # Dependencies
│   ├── core/                   # Config, logging, security
│   ├── services/               # Business logic
│   ├── workers/               # Async task handlers
│   ├── integrations/          # GitHub/GitLab integrations
│   ├── db/                    # Database models & migrations
│   └── utils/                 # Helper functions
├── tests/                     # Comprehensive test suite
├── containers/               # Docker configurations
└── deploy/                   # Kubernetes/Helm charts
```

## 🛠️ Core Tech Stack (2024 Modern Stack)

```python
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
alembic==1.12.1
python-jose==3.3.0
aioredis==2.0.1
aiobotocore==2.11.0
ruff==0.1.9              # Ultra-fast Python linter
semgrep==1.48.0          # Security-focused static analysis
biome==1.9.0             # JavaScript/TypeScript all-in-one
docker==6.1.3            # For containerized tool execution
gitpython==3.1.40        # Git repository handling
```

## 🎯 Key Features

1. **Multi-language Support** (Python, JavaScript/TypeScript, Java, Go)
2. **Real-time PR Analysis** with GitHub/GitLab integration
3. **Custom Rule Engine** for project-specific standards
4. **Security Scanning** with Semgrep and Bandit
5. **Performance Metrics** and trend analysis
6. **Sandboxed Execution** for security

## 📋 Database Schema

```python
# Core Entities
class Scan(Base):
    __tablename__ = "scans"
    
    id = Column(UUID, primary_key=True)
    org_id = Column(UUID, ForeignKey("organizations.id"))
    repo_id = Column(UUID, ForeignKey("repositories.id"))
    commit_sha = Column(String(40))
    branch = Column(String(255))
    status = Column(Enum("queued", "running", "completed", "failed"))
    metrics = Column(JSON)  # {total_issues: 15, critical: 2, ...}
    created_at = Column(DateTime, default=datetime.utcnow)

class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(UUID, primary_key=True)
    scan_id = Column(UUID, ForeignKey("scans.id"))
    tool = Column(String(50))  # ruff, semgrep, biome, etc.
    rule_id = Column(String(100))
    file_path = Column(String(500))
    line = Column(Integer)
    severity = Column(Enum("info", "warning", "error", "critical"))
    message = Column(Text)
    fingerprint = Column(String(64))  # For deduplication
```

## 🚀 API Endpoints

```python
# app/api/v1/routers/scans.py
from fastapi import APIRouter, Depends, HTTPException
from app.api.v1.schemas.scans import ScanCreate, ScanOut
from app.services.scans import scan_service

router = APIRouter(prefix="/scans", tags=["scans"])

@router.post("", response_model=ScanOut, status_code=202)
async def create_scan(
    payload: ScanCreate,
    current_user: User = Depends(get_current_user)
):
    """Enqueue a new code quality scan"""
    return await scan_service.enqueue_scan(
        org_id=current_user.org_id,
        repo_id=payload.repo_id,
        commit_sha=payload.commit_sha,
        branch=payload.branch
    )

@router.get("/{scan_id}", response_model=ScanOut)
async def get_scan(scan_id: UUID):
    """Get scan status and results"""
    return await scan_service.get_scan(scan_id)

@router.get("/{scan_id}/findings")
async def get_findings(
    scan_id: UUID,
    severity: Optional[str] = None,
    file_path: Optional[str] = None
):
    """Get paginated findings with filters"""
    return await scan_service.get_findings(
        scan_id, severity, file_path
    )
```

## 🔧 Worker Implementation

```python
# app/workers/tool_runners/python_runner.py
import subprocess
import json
from pathlib import Path

class PythonCodeAnalyzer:
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        
    async def run_ruff(self) -> List[Dict]:
        """Run Ruff linter and return normalized results"""
        cmd = [
            "ruff", "check", ".",
            "--format", "json",
            "--exit-zero"  # Don't fail on findings
        ]
        
        result = subprocess.run(
            cmd,
            cwd=self.work_dir,
            capture_output=True,
            text=True
        )
        
        return self._parse_ruff_output(result.stdout)
    
    async def run_bandit(self) -> List[Dict]:
        """Run Bandit security scanner"""
        cmd = [
            "bandit", "-r", ".",
            "-f", "json",
            "--exit-zero"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=self.work_dir,
            capture_output=True,
            text=True
        )
        
        return self._parse_bandit_output(result.stdout)
    
    def _parse_ruff_output(self, output: str) -> List[Dict]:
        findings = []
        try:
            data = json.loads(output)
            for violation in data.get("violations", []):
                findings.append({
                    "tool": "ruff",
                    "rule_id": violation.get("code"),
                    "file_path": violation.get("filename"),
                    "line": violation.get("location", {}).get("row"),
                    "severity": self._map_severity(violation.get("code")),
                    "message": violation.get("message"),
                    "fingerprint": self._generate_fingerprint(violation)
                })
        except json.JSONDecodeError:
            pass
        return findings
```

## 🎨 GitHub Integration

```python
# app/integrations/github/webhook_handler.py
from github import GithubIntegration
import hmac
import hashlib

class GitHubWebhookHandler:
    def __init__(self, webhook_secret: str):
        self.webhook_secret = webhook_secret
        
    async def handle_pr_event(self, payload: Dict, signature: str):
        """Handle GitHub pull request webhook"""
        if not self._verify_signature(payload, signature):
            raise HTTPException(401, "Invalid signature")
            
        if payload.get("action") in ["opened", "synchronize"]:
            pr_data = payload["pull_request"]
            await self._analyze_pr(
                pr_data["head"]["repo"]["clone_url"],
                pr_data["head"]["sha"],
                pr_data["number"]
            )
    
    async def _analyze_pr(self, repo_url: str, commit_sha: str, pr_number: int):
        """Analyze PR and post results as comments"""
        scan_result = await scan_service.analyze_commit(repo_url, commit_sha)
        
        # Post results as PR comments
        comments = self._format_pr_comments(scan_result)
        await self._post_pr_comments(pr_number, comments)
        
        # Update PR status
        await self._update_pr_status(pr_number, scan_result.metrics)

    def _format_pr_comments(self, scan_result) -> List[str]:
        """Format findings as GitHub review comments"""
        comments = []
        for finding in scan_result.findings[:10]:  # Limit to 10 comments
            if finding.severity in ["error", "critical"]:
                comments.append(f"""
**{finding.severity.upper()}**: {finding.message}
File: `{finding.file_path}:{finding.line}`
Rule: `{finding.rule_id}`
                """)
        return comments
```

## 🐳 Docker Configuration

```dockerfile
# containers/worker.Dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install analysis tools
RUN pip install ruff==0.1.9 semgrep==1.48.0 bandit==1.7.5

# Create non-root user
RUN useradd --create-home --shell /bin/bash worker
USER worker

WORKDIR /app
COPY --chown=worker:worker requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=worker:worker app/ ./app/
COPY --chown=worker:worker workers/ ./workers/

CMD ["python", "-m", "workers.main"]
```

## 📊 Metrics and Analytics

```python
# app/services/metrics_service.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

class MetricsService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_org_metrics(self, org_id: UUID) -> Dict:
        """Get organization-level code quality metrics"""
        # Total scans
        total_scans = await self.db.execute(
            select(func.count(Scan.id))
            .where(Scan.org_id == org_id)
        )
        
        # Issue trends
        severity_counts = await self.db.execute(
            select(
                Finding.severity,
                func.count(Finding.id)
            )
            .join(Scan)
            .where(Scan.org_id == org_id)
            .group_by(Finding.severity)
        )
        
        # Most common issues
        common_issues = await self.db.execute(
            select(
                Finding.rule_id,
                func.count(Finding.id)
            )
            .join(Scan)
            .where(Scan.org_id == org_id)
            .group_by(Finding.rule_id)
            .order_by(func.count(Finding.id).desc())
            .limit(10)
        )
        
        return {
            "total_scans": total_scans.scalar(),
            "severity_distribution": dict(severity_counts.all()),
            "top_issues": dict(common_issues.all()),
            "improvement_trend": await self._calculate_trend(org_id)
        }
```

## 🧪 Testing Strategy

```python
# tests/test_scan_service.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.scan_service import ScanService

@pytest.mark.asyncio
async def test_enqueue_scan_success():
    """Test successful scan enqueue"""
    mock_db = AsyncMock()
    mock_queue = AsyncMock()
    
    service = ScanService(db=mock_db, queue=mock_queue)
    
    result = await service.enqueue_scan(
        org_id="test-org",
        repo_id="test-repo",
        commit_sha="abc123"
    )
    
    assert result.status == "queued"
    mock_queue.enqueue.assert_called_once()

@pytest.mark.asyncio
async def test_scan_deduplication():
    """Test that duplicate scans are prevented"""
    mock_db = AsyncMock()
    mock_cache = AsyncMock()
    mock_cache.exists.return_value = True
    
    service = ScanService(db=mock_db, cache=mock_cache)
    
    result = await service.enqueue_scan(
        org_id="test-org",
        repo_id="test-repo", 
        commit_sha="abc123"
    )
    
    # Should return existing scan instead of creating new one
    assert result is not None
```

## 🚀 Deployment & CI/CD

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - name: Run tests
      run: |
        pytest -v --cov=app --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 🎓 Why This is Perfect for 7th Sem CS Majors

1. **Modern Tech Stack**: FastAPI, AsyncIO, Pydantic v2, SQLAlchemy 2.0
2. **Real-world Concepts**: Microservices, message queues, containerization
3. **DevOps Integration**: CI/CD, Docker, Kubernetes readiness
4. **Security Focus**: Sandboxed execution, webhook verification
5. **Scalability**: Designed for horizontal scaling
6. **Industry Relevance**: Uses tools like Ruff, Semgrep that are industry standards

This architecture gives you exposure to full-stack development, cloud-native patterns, and modern software engineering practices that are highly valued in the industry!
