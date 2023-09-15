## 2.1.1
### 2023-09-15

- Specify version of validators package as 0.20.0, because 0.21.0 upwards won't allow localhost in URL.

## 2.1.0
### 2023-08-09 

- Add parameter `verify_peer` to CoreConnect class, to make it possible to use self-signed TLS certificates.
- Add parameter `return_object` to CoreConnect class, to make it possible to return `requests.Response` object instead of deserialized JSON.
- Add partly support for multidimensional Query parameters.
- Fix importing and dependency bugs.
- Unify error handling.
- Other improvements and bug fixes.
