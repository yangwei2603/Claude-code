# Testing Patterns Reference

Reference file for test-driven-development and code-review-and-quality skills.

## Test Structure by Framework

### JavaScript/TypeScript (Jest / Vitest)

```typescript
describe('TaskList', () => {
  describe('addTask', () => {
    it('appends new task to the list', async () => {
      const tasks = new TaskList();
      await tasks.addTask({ title: 'Write tests' });
      
      expect(tasks.items).toHaveLength(1);
      expect(tasks.items[0].title).toBe('Write tests');
    });

    it('throws if title is empty', async () => {
      const tasks = new TaskList();
      await expect(tasks.addTask({ title: '' }))
        .rejects.toThrow('Title is required');
    });
  });
});
```

### Python (pytest)

```python
import pytest

class TestTaskList:
    async def test_appends_new_task(self):
        tasks = TaskList()
        await tasks.add_task(title="Write tests")
        
        assert len(tasks.items) == 1
        assert tasks.items[0].title == "Write tests"

    async def test_raises_if_title_empty(self):
        tasks = TaskList()
        with pytest.raises(ValueError, match="Title is required"):
            await tasks.add_task(title="")
```

## Testing Anti-Patterns

| Anti-Pattern | Why It's Bad | The Fix |
|---|---|---|
| Testing implementation details | Breaks on refactor even if behavior is correct | Test inputs → outputs |
| No test isolation | Tests pass individually, fail together | Each test sets up its own state |
| Excessive mocking | Tests pass but app breaks in prod | Prefer real impl > fake > stub > mock |
| Snapshot abuse | Large snapshots nobody reviews | Use sparingly, review every diff |
| Test names that don't describe behavior | Can't understand what broke from the name | Name describes expected behavior |
| Asserting on randomness | Flaky tests | Seed random, control timestamps |
| Testing framework internals | Wastes time testing third-party code | Only test your own code |

## Unit vs Integration vs E2E

| Level | What | Example Tool | When |
|---|---|---|---|
| **Unit** | Single function/class in isolation | Jest, pytest | Every behavior of every module |
| **Integration** | Multiple modules working together | Jest, pytest | Database queries, API handlers |
| **E2E** | Complete user flow in real browser | Playwright, Cypress | Critical user journeys only |

**Rule of thumb:** Many unit tests, some integration tests, few E2E tests.

## Mocking Hierarchy

```
1. Real implementation          ← preferred (no mocking)
2. Fake (in-memory DB, etc.)    ← good for slow/non-deterministic
3. Stub (override specific fn)  ← acceptable for boundaries
4. Mock (expect call counts)    ← use sparingly, last resort
```

### Example: Testing a Service That Calls an API

```typescript
// BAD: Mock the HTTP library itself
const mockFetch = jest.fn();
global.fetch = mockFetch;
mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 1 }) });

// GOOD: Mock at the boundary you own
// Create a test double for the external service
const mockUserService = {
  fetchUser: jest.fn().mockResolvedValue({ id: 1, name: 'Alice' }),
};
const service = new TaskService({ userService: mockUserService });

// BEST: Use a fake when possible
const fakeUserService = new FakeUserService({ users: [{ id: 1, name: 'Alice' }] });
const service = new TaskService({ userService: fakeUserService });
```

## Test Naming

Pattern: `describe_[unit]_[scenario]_[expected_behavior]`

```
describe('TaskList', () => {
  describe('addTask', () => {
    it('appends new task to the list')
    it('returns the created task')
    it('trims whitespace from title')
    it('throws ValidationError if title is empty')
    it('throws ValidationError if title exceeds 200 characters')
  });

  describe('completeTask', () => {
    it('marks existing task as done')
    it('throws NotFoundError if task does not exist')
    it('is idempotent (completing twice does not error)')
  });
});
```

## Arrange-Act-Assert (AAA)

```typescript
// Arrange: Set up the state
const taskList = new TaskList();
const task = { title: 'Buy groceries', priority: 'high' };

// Act: Perform the action
const result = await taskList.addTask(task);

// Assert: Verify the outcome
expect(result.title).toBe('Buy groceries');
expect(result.priority).toBe('high');
expect(taskList.items).toHaveLength(1);
```

## Database Testing Patterns

### Use a Real Database (Test Container)

```typescript
// Spin up a real database in Docker for integration tests
const container = await new PostgreSqlContainer().start();
const db = await createDbConnection(container.getConnectionUri());

test('creates and retrieves user', async () => {
  await db.users.create({ email: 'test@example.com' });
  const user = await db.users.findByEmail('test@example.com');
  
  expect(user.email).toBe('test@example.com');
});

afterAll(async () => {
  await container.stop();
});
```

### Use Transactions for Test Isolation

```typescript
beforeEach(async () => {
  await db.beginTransaction();
});

afterEach(async () => {
  await db.rollbackTransaction(); // Never pollute other tests
});
```

## API Testing

### Happy Path

```typescript
test('POST /tasks creates a task and returns 201', async () => {
  const response = await fetch('/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: 'Write tests', priority: 'high' }),
  });

  expect(response.status).toBe(201);
  const task = await response.json();
  expect(task.id).toBeDefined();
  expect(task.title).toBe('Write tests');
  expect(task.priority).toBe('high');
  expect(task.status).toBe('pending');
});
```

### Error Cases

```typescript
test('POST /tasks returns 400 for empty title', async () => {
  const response = await fetch('/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: '' }),
  });

  expect(response.status).toBe(400);
  const error = await response.json();
  expect(error.code).toBe('VALIDATION_ERROR');
  expect(error.fields.title).toBe('Title is required');
});
```

## Frontend Component Testing (React + Testing Library)

```typescript
import { render, screen, userEvent } from '@testing-library/react';

test('TaskItem renders title and responds to click', async () => {
  const task = { id: 1, title: 'Write tests', done: false };
  const onToggle = jest.fn();
  const user = userEvent.setup();

  render(<TaskItem task={task} onToggle={onToggle} />);

  expect(screen.getByText('Write tests')).toBeInTheDocument();
  
  await user.click(screen.getByRole('button', { name: /toggle/i }));
  
  expect(onToggle).toHaveBeenCalledWith(1);
});
```

**Priority (Testing Library hierarchy):**
1. `getByRole` — most inclusive (what screen readers see)
2. `getByLabelText` — for form elements
3. `getByText` — for non-interactive elements
4. `getByTestId` — last resort only

## E2E Testing (Playwright)

```typescript
import { test, expect } from '@playwright/test';

test('user can create and complete a task', async ({ page }) => {
  await page.goto('/tasks');

  // Create task
  await page.getByLabel('Task title').fill('Buy groceries');
  await page.getByRole('button', { name: 'Add task' }).click();
  await expect(page.getByText('Buy groceries')).toBeVisible();

  // Complete task
  await page.getByRole('checkbox', { name: 'Buy groceries' }).check();
  await expect(page.getByText('Buy groceries')).toHaveClass(/completed/);
});
```

## Test-Driven Development (TDD) Cycle

```
1. RED    → Write a failing test (it won't even compile)
2. GREEN  → Write minimal code to pass (no optimization yet)
3. REFACTOR → Improve code while keeping tests green
4. Repeat
```

### Example: TDD for a Validator

```typescript
// Step 1: RED — Write failing test
test('emailValidator rejects invalid email', () => {
  expect(() => validateEmail('not-an-email')).toThrow('Invalid email format');
});

// Step 2: GREEN — Minimal code
function validateEmail(email: string): void {
  if (!email.includes('@')) throw new Error('Invalid email format');
  return;
}

// Step 3: RED — Add failing test for edge case
test('emailValidator rejects empty string', () => {
  expect(() => validateEmail('')).toThrow('Email is required');
});

// Step 3: GREEN — Handle new case
function validateEmail(email: string): void {
  if (!email) throw new Error('Email is required');
  if (!email.includes('@')) throw new Error('Invalid email format');
}

// Step 3: RED → GREEN → REFACTOR — Extract to class, add more cases...
```

## Coverage Targets

| Layer | Target | Why |
|---|---|---|
| Unit tests | 80%+ line coverage | Catch bugs close to source |
| Critical paths | 100% branch coverage | Don't cut corners on money/user data |
| Integration tests | Cover all API endpoints | Ensure modules work together |
| E2E | Cover top 5 user journeys | Expensive, so pick wisely |

**Warning:** Coverage is a means, not an end. 100% coverage with shallow assertions is worse than 70% with meaningful tests.

## CI/CD Test Pipeline

```
push → lint → typecheck → test → build → deploy
         ↓          ↓         ↓
      fail fast  fail fast  fail fast
```

- Lint and typecheck run first (fastest feedback)
- Unit tests run in parallel (fast)
- Integration tests run after unit tests (slower)
- E2E tests run after deployment to staging (slowest)
- Never skip tests to make a deadline — fix the pipeline or parallelize
