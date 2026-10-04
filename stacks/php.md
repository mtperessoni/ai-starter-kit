# PHP

## Detect
| Signal | Means |
|---|---|
| `composer.json`, `composer.lock` | Composer; install `composer install --no-interaction` |
| `phpunit.xml(.dist)` | PHPUnit; test suites defined there |
| `pestphp/pest` | Pest |
| `artisan` | Laravel: source in `app/` |
| `phpstan.neon`, `psalm.xml` | static analysis configured |

## Commands
| Key | Value |
|---|---|
| `commands.test` | `vendor/bin/phpunit` |
| `commands.offline_args` | `--exclude-group integration` |
| `commands.integration_args` | `--group integration` |
| `commands.no_coverage_args` | `--no-coverage` |
| `commands.lint` | `vendor/bin/php-cs-fixer fix --dry-run --diff && vendor/bin/phpstan analyse` |
| `commands.fix` | `vendor/bin/php-cs-fixer fix` |
| `commands.import_check` | `composer dump-autoload --strict-psr` |
| `tests.runner` | `vendor/bin/phpunit {files}` (one file at a time when the version needs it) |
| `tests.native_related` | empty |
| `tests.failure_regex` | `^\d+\) (\S+)` |

## Structure enforcement
- PHPMD `ExcessiveMethodLength` (minimum 80), `ExcessiveClassLength` (300).
- Import direction (AR09): `deptrac` layers, one per feature.
- Baseline: PHPStan baseline file, deptrac `skip_violations`; shrink-only.

## Offline guard
HTTP client fakes (`Http::fake()` in Laravel, mock handlers in Guzzle); integration tests in the `integration` group.

## CI setup
```yaml
      - uses: shivammathur/setup-php@v2
        with:
          php-version: <version>
      - name: Install dependencies (locked)
        run: composer install --no-interaction --prefer-dist
```

## Ignore
`**/vendor/**`, `**/storage/**`, `**/bootstrap/cache/**`.
