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
