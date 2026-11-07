---
name: api-scaffolder
description: Scaffold a new API endpoint (route, handler, input validation, auth check, tests and OpenAPI docs) that follows the project's existing structure and conventions. Use when the user asks to add a REST or HTTP endpoint, create a new route or controller, wire up a CRUD resource, or extend an OpenAPI spec in Express, Fastify, FastAPI, Flask, Django REST Framework, Spring Boot, Go net/http, chi or Gin.
---

# API Scaffolder

## When to use

- The user asks for a new endpoint, route, controller or resource ("add `POST /orders`", "create CRUD for invoices").
- A feature needs a new HTTP handler and the project already has a few to copy from.
- An OpenAPI spec needs a new path that must match a real handler.

Not for: reviewing existing endpoints for OWASP issues (use `security-audit`), writing tests for code that already exists (use `test-generator`), or schema changes behind the endpoint (use `migration-helper`).

## Steps

1. Find the pattern before writing anything. Locate two or three existing endpoints and read them end to end:
   - Router registration (`app.use`, `router.get`, `@app.post`, `urlpatterns`, `@RestController`, `r.Route`).
   - Where validation lives (zod, Joi, pydantic, marshmallow, DRF serializers, `jakarta.validation`, go-playground/validator).
   - Where business logic lives (service layer, use case, repository) and how errors map to HTTP status codes.
   - Test location and naming (`__tests__/`, `tests/api/`, `*_test.go`, `src/test/java`).
   - Whether the OpenAPI spec is hand written (`openapi.yaml`) or generated from code (FastAPI, springdoc, tsoa, swaggo).
2. Confirm the contract with the user in one short block: method, path, request body, response body, status codes, auth requirement. Do not guess the auth model. Ask if it is unclear.
3. Write the input schema first. Reject unknown fields, set max lengths, bound numbers, and use enums for fixed values.
4. Write the handler. Keep it thin: parse, validate, authorize, call the service, map the result. No SQL or external calls inline unless the project already does that.
5. Add the authorization check at the object level, not only the route level. A user who can call `GET /orders/:id` must own order `:id` (or have a role that allows it).
6. Register the route in the same file and order the project uses. Check for path conflicts (`/orders/export` must come before `/orders/:id` in Express).
7. Write tests that cover: happy path, validation failure (400 or 422), unauthenticated (401), wrong owner (403 or 404), not found (404), and one boundary case (empty list, max length).
8. Update the OpenAPI spec or the annotations that generate it. Include every status code the handler can return and an example body.
9. Run the project's lint, type check and test commands. Fix failures before reporting back.
10. Report the files changed and anything you assumed.

## Checklist

Contract and validation
- [ ] Method and path follow existing naming (plural nouns, kebab-case or snake_case to match the codebase).
- [ ] Request schema rejects extra fields (zod `.strict()`, pydantic `model_config = ConfigDict(extra="forbid")`, Joi `.unknown(false)`, DRF serializer with explicit `fields`).
- [ ] Strings have `max_length` / `.max()`. Arrays have a max item count. Numbers have min and max.
- [ ] IDs are validated as UUID or integer before hitting the database.
- [ ] Pagination has a default and a hard cap on `limit` (for example default 20, max 100).

Auth and data exposure
- [ ] Route uses the project's auth middleware or dependency (`requireAuth`, `Depends(get_current_user)`, `@PreAuthorize`, `permission_classes`).
- [ ] Object-level ownership check in the handler or service.
- [ ] Response uses an explicit output schema or DTO. No returning ORM objects directly (avoid leaking `password_hash`, `internal_notes`).
- [ ] Mass assignment blocked: only whitelisted fields are copied from the request into the model.

Errors and behavior
- [ ] Error responses match the project format (RFC 9457 `application/problem+json` if already used).
- [ ] No stack traces or SQL errors in responses.
- [ ] Idempotency key or upsert for `POST` endpoints that create payments, orders or other side effects, if the project has that pattern.
- [ ] Rate limiting applied if other public endpoints have it (`express-rate-limit`, `slowapi`, API gateway config).

Tests and docs
- [ ] Tests use the existing client fixture (`supertest`, `httpx.AsyncClient`, `TestClient`, `MockMvc`, `httptest`).
- [ ] OpenAPI path, parameters, request body, responses and `security` block updated.
- [ ] Spec still validates: `npx @redocly/cli lint openapi.yaml` or `spectral lint openapi.yaml`.

More framework specifics: [references/framework-patterns.md](references/framework-patterns.md).

## Output format

Reply with this structure:

```markdown
### Endpoint
`POST /api/v1/orders` (auth: bearer token, scope `orders:write`)

### Files
| Action | File | Purpose |
|---|---|---|
| added | src/routes/orders.ts | route registration |
| added | src/schemas/order.ts | zod request and response schemas |
| changed | src/services/orderService.ts | createOrder() |
| added | tests/api/orders.test.ts | 6 cases |
| changed | openapi.yaml | /orders POST |

### Checks run
- `npm run lint` passed
- `npm test -- orders` 6/6 passed
- `npx @redocly/cli lint openapi.yaml` passed

### Assumptions
- Orders are scoped to `req.user.tenantId`.
```

## Examples

Bad: no validation, no ownership check, returns the raw model.

```ts
router.patch("/orders/:id", requireAuth, async (req, res) => {
  const order = await Order.findByPk(req.params.id);
  await order.update(req.body); // mass assignment, any field
  res.json(order);              // leaks internal columns
});
```

Good: strict schema, ownership check, explicit output.

```ts
const UpdateOrder = z.object({
  note: z.string().max(500).optional(),
  status: z.enum(["pending", "cancelled"]).optional(),
}).strict();

router.patch("/orders/:id", requireAuth, async (req, res, next) => {
  const id = z.string().uuid().safeParse(req.params.id);
  const body = UpdateOrder.safeParse(req.body);
  if (!id.success || !body.success) return res.status(400).json(problem(400, "Invalid input"));

  const order = await orderService.findForUser(id.data, req.user.id);
  if (!order) return res.status(404).json(problem(404, "Order not found"));

  const updated = await orderService.update(order, body.data);
  res.json(toOrderDto(updated));
});
```

Bad (FastAPI): accepts any dict.

```python
@router.post("/items")
def create_item(payload: dict, db: Session = Depends(get_db)):
    item = Item(**payload)
```

Good (FastAPI): typed model with limits, auth dependency, response model.

```python
class ItemIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(ge=1, le=1000)

@router.post("/items", response_model=ItemOut, status_code=201)
def create_item(payload: ItemIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return item_service.create(db, owner_id=user.id, data=payload)
```
