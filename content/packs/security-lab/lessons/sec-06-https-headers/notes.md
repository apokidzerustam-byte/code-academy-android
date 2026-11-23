# HTTPS, куки и заголовки безопасности

## HTTPS

HTTPS = HTTP + TLS: **тайна** (посторонний не прочитает), **целостность** (не подменит), **подлинность** (сертификат доказывает, что это именно тот сайт). Замок не означает, что сайт честный.

Смотрите на **имя сайта** (до первой `/`), а не на красивое начало: `bank.example.evil.test` — другой сайт.

## Перенаправление и HSTS

Сервер отвечает на HTTP кодом `301` с адресом по HTTPS и добавляет `Strict-Transport-Security: max-age=31536000; includeSubDomains`.

## Куки

| Флаг | Что делает |
|---|---|
| `Secure` | отправляется только по HTTPS |
| `HttpOnly` | недоступна скриптам страницы |
| `SameSite=Lax/Strict` | не отправляется со сторонних сайтов |
| `Max-Age` | ограничивает срок жизни |

```py
"sid=abc123; Path=/; Max-Age=3600; Secure; HttpOnly; SameSite=Lax"
```

## Заголовки безопасности

| Заголовок | Значение |
|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` или `SAMEORIGIN` |
| `Content-Security-Policy` | например `default-src 'self'` |
| `Referrer-Policy` | например `no-referrer` |

Имена заголовков нечувствительны к регистру. В FastAPI такие заголовки добавляют слоем middleware (урок про middleware).

## Смешанное содержимое

Страница по HTTPS не должна загружать скрипты и картинки по `http://`.
