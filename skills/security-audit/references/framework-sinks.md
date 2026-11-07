# Dangerous sinks and safe replacements by framework

Use these to grep for candidate findings. A hit is a lead, not a finding: trace whether untrusted input reaches it.

## Python (Django, Flask, FastAPI)

| Risk | Grep for | Safe version |
|---|---|---|
| SQLi | `.raw(`, `.extra(`, `cursor.execute(f"`, `execute("..." %`, `text(f"` | `cursor.execute(sql, params)`, ORM filters, `text(":x")` with bind params |
| Command injection | `shell=True`, `os.system`, `os.popen` | `subprocess.run([...], shell=False)` |
| XSS | `mark_safe`, `\|safe`, `Markup(`, `autoescape off` | Default auto-escaping, `bleach` or `nh3` for allowed HTML |
| Deserialization | `pickle.loads`, `yaml.load(`, `marshal.loads`, `jsonpickle` | `json.loads`, `yaml.safe_load` |
| Path traversal | `open(os.path.join(base, user))`, `send_file(user)` | `werkzeug.utils.safe_join`, `realpath` prefix check |
| SSRF | `requests.get(user_url)`, `urllib.request.urlopen` | Allowlist plus resolved-IP check |
| Mass assignment | `Model(**request.json)`, `ModelForm` with `fields = "__all__"` | Explicit field list, Pydantic model |
| XXE | `xml.etree`, `lxml.etree.parse` with defaults | `defusedxml` |

## JavaScript and TypeScript (Express, Next.js, NestJS)

| Risk | Grep for | Safe version |
|---|---|---|
| SQLi | template literals in `query(`, `sequelize.query(`, `knex.raw(`, `$queryRawUnsafe` | Placeholders, `$queryRaw` tagged template |
| NoSQL injection | `find(req.body)`, `$where` | Validate with zod or joi, cast to string, `mongo-sanitize` |
| Command injection | `child_process.exec(`, `execSync(` | `execFile` or `spawn` with arg array |
| XSS | `dangerouslySetInnerHTML`, `innerHTML =`, `v-html`, `document.write` | Text nodes, DOMPurify for allowed HTML |
| Prototype pollution | `merge(`, `extend(`, `lodash.set` with user keys | Block `__proto__`, `constructor`, use `Object.create(null)` |
| Open redirect | `res.redirect(req.query.next)` | Relative paths only, or host allowlist |
| JWT | `jwt.verify(token, key)` with no `algorithms` | `jwt.verify(token, key, { algorithms: ["RS256"], audience, issuer })` |
| Code eval | `eval(`, `new Function(`, `vm.runInNewContext` | Do not evaluate user input |

## Java and Kotlin (Spring)

| Risk | Grep for | Safe version |
|---|---|---|
| SQLi | `createQuery("..." +`, `Statement.execute`, `@Query` with SpEL concatenation | `PreparedStatement`, named params |
| Deserialization | `ObjectInputStream`, `XMLDecoder`, Jackson `enableDefaultTyping` | JSON DTOs, `activateDefaultTyping` with a strict validator |
| SpEL injection | `SpelExpressionParser().parseExpression(user)` | Do not parse user input |
| XXE | `DocumentBuilderFactory` defaults | `setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)` |
| Actuator | `management.endpoints.web.exposure.include=*` | Expose `health` only, protect the rest |

## Go

| Risk | Grep for | Safe version |
|---|---|---|
| SQLi | `fmt.Sprintf` into `db.Query`, `db.Exec` | `db.Query("... WHERE id = $1", id)` |
| Command injection | `exec.Command("sh", "-c", ...)` | `exec.Command(bin, args...)` |
| XSS | `text/template` for HTML, `template.HTML(user)` | `html/template` |
| TLS | `InsecureSkipVerify: true` | Remove, or pin a CA pool |
| Path traversal | `filepath.Join(base, user)` | `filepath.Clean` plus `strings.HasPrefix` on the result, or `os.Root` (Go 1.24+) |

## Ruby on Rails

| Risk | Grep for | Safe version |
|---|---|---|
| SQLi | `where("... #{`, `find_by_sql`, `order(params[` | `where(id: x)`, `where("id = ?", x)`, allowlist sort columns |
| Mass assignment | `permit!`, `params.to_unsafe_h` | `params.require(:x).permit(:a, :b)` |
| XSS | `html_safe`, `raw(` | Default escaping, `sanitize` |
| Command injection | backticks, `system("... #{` | `system(bin, arg1, arg2)` |
| Deserialization | `Marshal.load`, `YAML.load` | `JSON.parse`, `YAML.safe_load` |

## PHP (Laravel)

| Risk | Grep for | Safe version |
|---|---|---|
| SQLi | `DB::raw(`, `whereRaw(` with interpolation | Bindings array |
| XSS | `{!! !!}` | `{{ }}` |
| Deserialization | `unserialize(` | `json_decode` |
| File inclusion | `include $_GET` | Fixed map of allowed files |
