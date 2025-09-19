# Fix Flaky Authentication Test

## Type
bug

## Description
The test `test_user_authentication` in `tests/auth/test_login.py` is failing intermittently. It appears to be a timing issue with the session token validation.

## Expected Behavior
The test should consistently pass and properly validate user sessions.

## Current Behavior
Test fails approximately 30% of the time with timeout errors.

## Success Criteria
1. Fix the timing issue in the authentication flow
2. All tests pass consistently
3. Test coverage remains above 85%
4. No regression in other auth tests

## Notes
This requires running the full test suite to validate the fix doesn't break other authentication flows.