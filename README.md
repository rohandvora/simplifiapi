# simplifiapi

Gets data from Quicken Simplifi account.

## Usage

```python
import simplifiapi

s = simplifiapi.Simplify(username= < email >,
password = < password >,
session_path = < path - to - session - files >,
headless = False)
try:
  s.login()
  accounts = s.get_account_data()
  print(accounts)
except simplifiapi.IncorrectPasswordException:
  print('Password incorrect')

s.close()
```