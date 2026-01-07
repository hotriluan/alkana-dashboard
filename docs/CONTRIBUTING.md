# Contributing Guide

Thank you for contributing to the Alkana Dashboard! This guide will help you get started.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)

---

## Code of Conduct

### Our Standards

**Be Respectful:**
- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the community

**Collaboration:**
- Help other contributors
- Share knowledge freely
- Credit others for their work

**Quality:**
- Write clean, maintainable code
- Test your changes thoroughly
- Document your code

---

## Getting Started

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/alkana-dashboard.git
   cd alkana-dashboard
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/original-org/alkana-dashboard.git
   ```

### Set Up Development Environment

**Backend:**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development tools

# Set up pre-commit hooks
pre-commit install
```

**Frontend:**
```bash
cd web
npm install
```

**Database:**
```bash
# Create development database
createdb alkana_dev

# Configure .env
cp .env.example .env
# Edit DATABASE_URL to point to alkana_dev

# Initialize schema
python -m src.main init
```

### Verify Setup

```bash
# Backend tests
pytest

# Frontend tests
cd web && npm test

# Start development servers
# Terminal 1: Backend
uvicorn src.api.main:app --reload

# Terminal 2: Frontend
cd web && npm run dev
```

---

## Development Workflow

### Branch Strategy

```
main (production-ready)
  ↑
develop (integration branch)
  ↑
feature/*, bugfix/*, hotfix/* (your work)
```

### Creating a Feature Branch

```bash
# Update develop
git checkout develop
git pull upstream develop

# Create feature branch
git checkout -b feature/add-new-dashboard
# Or: bugfix/fix-inventory-calculation
# Or: hotfix/critical-security-fix
```

**Branch Naming:**
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical production fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Adding tests

### Making Changes

1. **Write code following [code standards](#code-standards)**

2. **Commit frequently with clear messages:**
   ```bash
   git add .
   git commit -m "feat: add inventory slow-moving filter"
   ```

   **Commit Message Format:**
   ```
   <type>: <subject>

   <body>

   <footer>
   ```

   **Types:**
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation only
   - `style`: Formatting, missing semicolons, etc.
   - `refactor`: Code change that neither fixes a bug nor adds a feature
   - `test`: Adding tests
   - `chore`: Updating build tasks, package manager configs, etc.

   **Examples:**
   ```
   feat: add P02-P01 yield tracking dashboard

   - Implement genealogy tree visualization
   - Add batch linking algorithm
   - Create new API endpoint for yield data

   Closes #123
   ```

   ```
   fix: correct inventory netting for MVT 122

   Movement type 122 was not properly handled in reversal logic.
   Updated netting.py to recognize MVT 122 as return to vendor.

   Fixes #456
   ```

3. **Test your changes:**
   ```bash
   # Run tests
   pytest
   cd web && npm test

   # Check code quality
   black src/  # Auto-format Python
   flake8 src/  # Linting
   mypy src/   # Type checking
   ```

4. **Update documentation:**
   - Update README if adding features
   - Add docstrings to new functions
   - Update API_REFERENCE.md for new endpoints
   - Add USER_GUIDE.md sections for UI changes

### Keeping Your Branch Updated

```bash
# Fetch latest changes
git fetch upstream

# Rebase on develop
git checkout feature/your-feature
git rebase upstream/develop

# If conflicts, resolve them and continue
git add .
git rebase --continue
```

---

## Code Standards

See [code-standards.md](./code-standards.md) for comprehensive guide.

### Python Code Standards

**Formatting:**
- Use **Black** for formatting (line length: 100)
- Use **flake8** for linting
- Use **mypy** for type checking

**Example:**
```python
from typing import List, Optional
from datetime import datetime

def calculate_yield(
    planned_qty: float, 
    actual_qty: float, 
    material_code: Optional[str] = None
) -> float:
    """
    Calculate production yield percentage.
    
    Args:
        planned_qty: Target production quantity
        actual_qty: Actual output quantity
        material_code: Optional material identifier for logging
        
    Returns:
        Yield percentage (0-100)
        
    Raises:
        ValueError: If planned_qty is zero or negative
        
    Example:
        >>> calculate_yield(100, 95)
        95.0
    """
    if planned_qty <= 0:
        raise ValueError("Planned quantity must be positive")
    
    yield_pct = (actual_qty / planned_qty) * 100
    
    if material_code:
        logger.info(f"Yield for {material_code}: {yield_pct:.2f}%")
    
    return round(yield_pct, 2)
```

**Key Points:**
- Type hints for all function parameters and returns
- Docstrings with Args, Returns, Raises, Example
- Descriptive variable names
- Error handling with specific exceptions
- Logging for important operations

### TypeScript Code Standards

**Formatting:**
- Use **Prettier** for formatting
- Use **ESLint** for linting

**Example:**
```typescript
import { FC, useState, useEffect } from 'react';
import { getInventoryCurrent } from '../services/api';

interface InventoryItem {
  materialCode: string;
  description: string;
  quantity: number;
  unit: string;
}

interface InventoryTableProps {
  plantFilter?: string;
  onItemClick?: (item: InventoryItem) => void;
}

export const InventoryTable: FC<InventoryTableProps> = ({ 
  plantFilter, 
  onItemClick 
}) => {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInventory = async () => {
      try {
        setLoading(true);
        const data = await getInventoryCurrent({ plant: plantFilter });
        setInventory(data);
      } catch (err) {
        setError('Failed to load inventory data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchInventory();
  }, [plantFilter]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <table>
      <thead>
        <tr>
          <th>Material</th>
          <th>Description</th>
          <th>Quantity</th>
        </tr>
      </thead>
      <tbody>
        {inventory.map((item) => (
          <tr key={item.materialCode} onClick={() => onItemClick?.(item)}>
            <td>{item.materialCode}</td>
            <td>{item.description}</td>
            <td>{item.quantity} {item.unit}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

**Key Points:**
- Use functional components with TypeScript
- Define interfaces for props and data
- Use hooks (useState, useEffect) appropriately
- Error handling for async operations
- Proper typing for all variables

### SQL Standards

```sql
-- Use uppercase for keywords
-- Descriptive table/column names
-- Comments for complex queries

-- Get inventory with low stock alert
SELECT 
    m.material_code,
    m.description,
    i.quantity,
    i.storage_location,
    i.last_movement_date
FROM fact_inventory i
INNER JOIN dim_material m 
    ON i.material_code = m.material_code
WHERE i.quantity < m.min_stock_level
    AND i.plant = '1000'
ORDER BY i.quantity ASC
LIMIT 50;
```

---

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up-to-date with develop
- [ ] No merge conflicts

### Creating Pull Request

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature
   ```

2. **Open PR on GitHub:**
   - Base: `develop` (not `main`)
   - Compare: `your-feature-branch`
   - Fill out PR template

**PR Title Format:**
```
[TYPE] Brief description

Examples:
[FEATURE] Add P02-P01 yield tracking dashboard
[BUGFIX] Fix inventory netting for MVT 122
[DOCS] Update API reference for new endpoints
```

**PR Description Template:**
```markdown
## Description
Brief summary of changes

## Related Issues
Closes #123
Fixes #456

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- Added new yield tracking algorithm
- Updated API endpoint `/api/yield/genealogy`
- Added unit tests for genealogy logic
- Updated USER_GUIDE.md with new dashboard instructions

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if UI changes)
[Add screenshots here]

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added and passing
```

### Code Review Process

**Review Timeline:**
- Small PRs (<200 lines): 1-2 days
- Medium PRs (200-500 lines): 2-3 days
- Large PRs (>500 lines): 3-5 days

**Reviewer Responsibilities:**
- Check code quality and style
- Verify tests are adequate
- Test functionality locally
- Provide constructive feedback

**Author Responsibilities:**
- Respond to feedback promptly
- Make requested changes
- Re-request review after updates
- Keep PR scope focused

**Approval:**
- Requires 1 approving review minimum
- All CI checks must pass
- No unresolved conversations

### Merging

**Merge Strategy:**
- Use "Squash and Merge" for feature branches
- Use "Rebase and Merge" for hotfixes
- Delete branch after merge

**After Merge:**
```bash
# Update your local develop
git checkout develop
git pull upstream develop

# Delete feature branch
git branch -d feature/your-feature
```

---

## Issue Guidelines

### Reporting Bugs

**Template:**
```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll to '...'
4. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Screenshots
If applicable

## Environment
- OS: [e.g., Windows 10, Ubuntu 20.04]
- Browser: [e.g., Chrome 120, Firefox 121]
- Python Version: [e.g., 3.11.5]
- Database Version: [e.g., PostgreSQL 15.3]

## Additional Context
Any other relevant information
```

### Requesting Features

**Template:**
```markdown
## Feature Description
Clear description of the feature

## Use Case
Why is this feature needed? Who will use it?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Mockups, examples, references
```

### Issue Labels

- `bug` - Something isn't working
- `feature` - New functionality
- `enhancement` - Improve existing feature
- `documentation` - Documentation improvement
- `good first issue` - Good for newcomers
- `help wanted` - Community assistance needed
- `priority: high` - Urgent
- `priority: low` - Nice to have
- `blocked` - Cannot proceed yet

---

## Testing Requirements

### For New Features

- **Unit Tests:** Required for all business logic
- **Integration Tests:** Required for API endpoints
- **Frontend Tests:** Required for new components

**Coverage Target:** >80%

```bash
# Check coverage before submitting PR
pytest --cov=src --cov-report=term
cd web && npm test -- --coverage
```

### For Bug Fixes

- **Regression Test:** Add test that reproduces the bug
- Verify fix resolves the bug
- Ensure no other tests break

See [TESTING.md](./TESTING.md) for detailed guide.

---

## Documentation

### Code Documentation

**Python Docstrings:**
```python
def complex_function(param1: str, param2: int) -> dict:
    """
    Brief one-line description.
    
    Longer description if needed, explaining what the function does,
    any important details, algorithms used, etc.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When invalid input provided
        
    Example:
        >>> result = complex_function("test", 42)
        >>> result['status']
        'success'
    """
```

**TypeScript JSDoc:**
```typescript
/**
 * Calculate total revenue for a customer
 * 
 * @param customerId - Unique customer identifier
 * @param startDate - Period start date (ISO format)
 * @param endDate - Period end date (ISO format)
 * @returns Total revenue amount
 * 
 * @example
 * ```typescript
 * const revenue = calculateRevenue("CUST001", "2025-01-01", "2025-12-31");
 * ```
 */
function calculateRevenue(
  customerId: string,
  startDate: string,
  endDate: string
): number {
  // Implementation
}
```

### User-Facing Documentation

Update when:
- Adding new dashboard or feature
- Changing UI significantly
- Adding/changing API endpoints
- Modifying deployment process

**Files to Update:**
- [USER_GUIDE.md](./USER_GUIDE.md) - End-user instructions
- [API_REFERENCE.md](./API_REFERENCE.md) - API documentation
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment changes
- [README.md](../README.md) - Project overview

---

## Development Tools

### Pre-commit Hooks

Automatically format and check code before commit:

```bash
# Install
pre-commit install

# Run manually
pre-commit run --all-files
```

**Hooks configured:**
- Black (Python formatting)
- Flake8 (Python linting)
- Prettier (JS/TS formatting)
- ESLint (JS/TS linting)
- Trailing whitespace removal
- YAML syntax check

### VS Code Extensions (Recommended)

- **Python:** ms-python.python
- **Pylance:** ms-python.vscode-pylance
- **Black Formatter:** ms-python.black-formatter
- **ESLint:** dbaeumer.vscode-eslint
- **Prettier:** esbenp.prettier-vscode
- **GitLens:** eamodio.gitlens

**.vscode/settings.json:**
```json
{
  "python.formatting.provider": "black",
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

---

## Getting Help

**Questions?**
- Check existing issues
- Read documentation
- Ask in discussions
- Email: dev-team@yourcompany.com

**Stuck?**
- Comment on the issue
- Request review from maintainers
- Join team chat (if available)

---

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Project README

Thank you for contributing! 🎉
