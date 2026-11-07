# Framework patterns

Quick reference for where things usually live. Always prefer what the project already does over this list.

## Node.js

| Concern | Express | Fastify | NestJS |
|---|---|---|---|
| Route | `router.post(path, ...mw, handler)` | `fastify.post(path, { schema }, handler)` | `@Post()` on a `@Controller()` method |
| Validation | zod, Joi, celebrate | JSON Schema in `schema.body`, or `@fastify/type-provider-typebox` | `class-validator` DTO with `ValidationPipe({ whitelist: true, forbidNonWhitelisted: true })` |
| Auth | middleware (`passport`, custom `requireAuth`) | `onRequest` hook, `@fastify/jwt` | `@UseGuards(AuthGuard)` |
| Tests | `supertest` + Jest or Vitest | `fastify.inject()` | `@nestjs/testing` + `supertest` |
| OpenAPI | hand written or `zod-to-openapi` | `@fastify/swagger` | `@nestjs/swagger` decorators |

Express gotcha: routes match in registration order. Register `/users/me` before `/users/:id`.

## Python

| Concern | FastAPI | Flask | Django REST Framework |
|---|---|---|---|
| Route | `@router.post` on `APIRouter` | `@bp.route(methods=["POST"])` | `ViewSet` + `router.register` |
| Validation | pydantic v2 model | marshmallow, pydantic | `Serializer` with explicit `fields` (never `__all__`) |
| Auth | `Depends(get_current_user)` | `flask-login`, `flask-jwt-extended` | `permission_classes`, `get_queryset` filtered by user |
| Tests | `TestClient` or `httpx.AsyncClient` | `app.test_client()` | `APIClient` |
| OpenAPI | generated at `/openapi.json` | `apispec`, `flask-smorest` | `drf-spectacular` |

DRF gotcha: object-level permissions only run through `get_object()`. Filter `get_queryset()` by owner so list endpoints do not leak.

## JVM

| Concern | Spring Boot |
|---|---|
| Route | `@RestController` + `@PostMapping` |
| Validation | `@Valid` on a record DTO with `@NotBlank`, `@Size(max=...)`, `@Min`, `@Max` |
| Auth | `@PreAuthorize("hasAuthority('SCOPE_orders:write')")`, ownership in service |
| Tests | `@WebMvcTest` + `MockMvc`, or `@SpringBootTest` + `WebTestClient` |
| OpenAPI | `springdoc-openapi` annotations (`@Operation`, `@ApiResponse`) |

Set `spring.jackson.deserialization.fail-on-unknown-properties=true` if the project wants strict bodies.

## Go

| Concern | net/http (1.22+) | chi | Gin |
|---|---|---|---|
| Route | `mux.HandleFunc("POST /orders", h)` | `r.Post("/orders", h)` | `r.POST("/orders", h)` |
| Validation | `go-playground/validator` struct tags | same | `binding:"required,max=120"` tags |
| Decode | `json.NewDecoder(r.Body)` with `DisallowUnknownFields()` and `http.MaxBytesReader` | same | `ShouldBindJSON` |
| Tests | `httptest.NewRecorder()` | same | `httptest` + `gin.SetMode(gin.TestMode)` |
| OpenAPI | hand written, or `swaggo/swag` comments | same | same |

## Status codes

| Case | Code |
|---|---|
| Created | 201 with `Location` header |
| Accepted for async work | 202 |
| No body | 204 |
| Bad input | 400 (or 422 if the project uses it for validation) |
| No or bad credentials | 401 |
| Authenticated but not allowed | 403, or 404 to avoid confirming the object exists |
| Conflict (duplicate, version mismatch) | 409 |
| Rate limited | 429 with `Retry-After` |
