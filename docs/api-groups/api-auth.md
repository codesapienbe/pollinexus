# User Authentication & Accounts API

Note: Authentication is not enforced in development; use in production deployments.

## Endpoints

- `POST /api/v1/user/register` — Register new user (OTP sent)
- `POST /api/v1/user/send-verification` — Resend verification code
- `POST /api/v1/user/verify-registration` — Verify registration OTP (returns JWT)
- `POST /api/v1/user/login` — Request login OTP
- `POST /api/v1/user/verify-login` — Verify login OTP (returns JWT)
- `GET /api/v1/user/me` — Get current user info

## Flow

Register → Verify → Login → Verify OTP → Use JWT.

## Presentation Notes
>>
>> Explain OTP-first design: fast onboarding with strong verification; JWT issued post-verify for stateless auth.
>> Emphasize secure handling: rate limiting, code expiry, hashed tokens, and no PII in logs.
>> Demo path: register → verify → login → verify-login → hit protected `user/me` with Authorization header.
