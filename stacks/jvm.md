# JVM (Java and Kotlin)

## Detect
| Signal | Means |
|---|---|
| `build.gradle.kts`, `build.gradle`, `gradlew` | Gradle: use the wrapper `./gradlew` |
| `pom.xml`, `mvnw` | Maven: use the wrapper `./mvnw` |
| `src/main/kotlin` | Kotlin: detekt and ktlint |
| `src/main/java` | Java: Checkstyle or PMD |
| JUnit 5 in dependencies | `@Tag("integration")` separates the integration tier |

## Commands
| Key | Gradle | Maven |
|---|---|---|
| `commands.test` | `./gradlew test` | `./mvnw test` |
| `commands.offline_args` | `-PexcludeTags=integration` (configure `useJUnitPlatform { excludeTags(...) }`) | `-DexcludedGroups=integration` |
| `commands.integration_args` | `-PincludeTags=integration` | `-Dgroups=integration` |
| `commands.no_coverage_args` | `-x jacocoTestCoverageVerification` | `-Djacoco.skip=true` |
| `commands.lint` | `./gradlew check -x test` | `./mvnw verify -DskipTests` |
| `commands.fix` | `./gradlew spotlessApply` (when Spotless is set) | `./mvnw spotless:apply` |
| `commands.import_check` | `./gradlew compileJava compileKotlin` | `./mvnw compile` |
| `tests.runner` | `./gradlew test {files}` with each file turned into `--tests <ClassName>` by the installer | `./mvnw test -Dtest=<Class1>,<Class2>` |
| `tests.native_related` | empty | empty |
| `tests.failure_regex` | `^(\S+) > \S+ FAILED` | `^\[ERROR\]\s+(\S+)\s+.*<<< FAIL` |

## Structure enforcement
- Java: Checkstyle `MethodLength` (max 80), `FileLength` (max 500), `ClassFanOutComplexity` as a proxy; PMD `ExcessiveClassLength` (300).
- Kotlin: detekt `LongMethod` (threshold 80), `LargeClass` (threshold 300), `LongParameterList`.
- Import direction (AR09) and inheritance (AR04): ArchUnit tests (`layeredArchitecture()`, `noClasses().that()...should().dependOnClassesThat()...`) in the test tier, part of the related tests.
- Baseline: detekt `baseline.xml`, Checkstyle suppressions file; shrink-only.

| Rule | Java | Kotlin |
|---|---|---|
| AR24 complexity | Checkstyle `CyclomaticComplexity` (max 10), `NestedIfDepth` and `NestedForDepth` (max 3 means depth 4), `ParameterNumber` (max 5) | detekt `CyclomaticComplexMethod` (10), `NestedBlockDepth` (4), `LongParameterList` (functionThreshold 5) |
| AR25 dead code | PMD `UnusedPrivateMethod`, `UnusedPrivateField`, `UnusedLocalVariable`; IntelliJ inspections or ErrorProne `UnusedMethod`, `UnusedVariable` for the rest | detekt `UnusedPrivateMember`, `UnusedPrivateClass`; Kotlin compiler warnings with `allWarningsAsErrors` per module; classes reached by Spring, JPA or reflection go to an exclusion list |
| AR26 duplicates | PMD CPD (`cpd --minimum-tokens 100`, Gradle `cpdCheck` plugin: look up) | same, or detekt `DuplicateCaseInWhenExpression` only for the narrow case |
| AR27 typing | not applicable (statically typed); Kotlin and Java nullability: `-Xjsr305=strict`, NullAway or JSpecify annotations are optional | |
| AR22 dispatch | ArchUnit rule forbidding `java.lang.reflect.Method.invoke` and `Class.forName` outside a named package, or Checkstyle `IllegalToken`; Spring conventions go to the TRD | ArchUnit and review |

## Offline guard
Unit tests use fakes; Testcontainers tests carry the integration tag. Under the offline flag, a JUnit extension can fail tests that open sockets.

## CI setup
```yaml
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: <version>
          cache: <gradle|maven>
```

## Ignore
`**/build/**`, `**/target/**`, `**/.gradle/**`.

## Layout
| Layout | Declare |
|---|---|
| Spring by feature (`com.acme.orders`, `com.acme.billing`: controller, service, repository inside each) | `layout: "Spring packages by feature (orders, billing), each with its controller, service and repository"`, `areas: {"orders": ["src/main/java/com/acme/orders/**"]}`, or `feature_root: "src/main/java/com/acme"` when every subpackage is a feature |
| Spring by layer (`controller/`, `service/`, `repository/`, `model/`) | `layout: "Spring packages by technical role (controller, service, repository, model); product areas spread across them"`, `areas` per PRD area by file name (`**/Order*.java`), `map_dirs` the layer packages |
| Gradle or Maven multi-module (`settings.gradle`, `<modules>`) | `layout: "Multi-module build, one module per domain"`, one area per module: `areas: {"<m>": ["<m>/**"]}` |
| Spring Modulith or hexagonal (`domain/`, `application/`, `infrastructure/` per feature) | `layout: "Hexagonal modules, each with domain, application and infrastructure packages"`, one area per module; ArchUnit enforces the direction |
| Android (`app/src/main/java/<pkg>/<feature>`) | `layout: "Android app, one package per feature under the app package"`, `feature_root` the package root |

Source roots are deep (`src/main/java/...`): list them in `source_dirs`.

## Test naming
- `tests.mirror_patterns`: `["{name}Test", "{name}Tests", "{name}IT"]` (add `{name}Spec` for Kotest or Spock); `tests.match_symbol: true` (a test in the same package may name the class without an import).
- The default `test_patterns` include `**/*Test.*`, `**/*Tests.*` and `**/*Spec.*` but not `**/*IT.*`: install adds `**/*IT.*` to `test_patterns` so integration tests count as tests.
- Tests live in the mirrored tree `src/test/java/<same package>/` (AR10); integration tests as `*IT` run by Failsafe, or by a tag.
- `tests.junit_xml`: Gradle writes `build/test-results/test/*.xml` and Maven Surefire `target/surefire-reports/*.xml`; set the flag to the folder glob or the one file the project merges to (look up the aggregation).

## Generated files
`generated_patterns`: `**/build/generated/**`, `**/target/generated-sources/**`, `**/generated/**`, jOOQ, MapStruct, OpenAPI Generator and protobuf output. Markers: `@Generated` annotation, `// Generated by`, protoc `// Generated by the protocol buffer compiler.  DO NOT EDIT!`. These match the ratchet's default marker regex when they sit in the first 5 lines; a generator whose header matches none sets `generated_marker`. Lombok output does not exist in source.

## Framework exemptions
- `unique_name_exempt`: `Application.java`, `package-info.java`, `module-info.java`, `MainActivity.kt` (Android), `build.gradle.kts`; plus any `<Name>Config` or `<Name>Application` the framework fixes (look at the repository).
- AR04: JPA `@MappedSuperclass`, Spring `@Configuration` base classes, abstract test bases, exceptions extending `RuntimeException`, and `Enum` are allowed. DI frameworks inject services: no inheritance is needed.
- AR05: Spring beans with `@Scope("singleton")` holding mutable fields are review; `AtomicReference`, `StateFlow`, `ViewModel` state count as explicit.
- `id_header_lines`: files open with a license, `package` and imports: raise it (for example 30) or put the ID in the class Javadoc and check the first comment block.

## Snapshots
Agents never run the snapshot record or approve mode: Paparazzi `recordPaparazzi`, Roborazzi `recordRoborazzi`, ApprovalTests accepting `.received.*` as `.approved.*`, or the project's own update property (look up). Globs: `**/*.approved.*`, `**/__snapshots__/**`, `src/test/resources/**/expected/**`.

## Contracts
- Spring: springdoc writes `/v3/api-docs` (dump with a test or `./gradlew generateOpenApiDocs`, look up the plugin) into `docs/contracts/openapi.json`.
- Database: Flyway or Liquibase schema from `pg_dump --schema-only`, or the Hibernate `schema-generation` script output.
- Protobuf or Avro schemas: the files themselves.

## Setup
`commands.setup`: `./gradlew assemble -x test` (Gradle) or `./mvnw -DskipTests install` (Maven); for Android also `./gradlew --refresh-dependencies` only when needed.
