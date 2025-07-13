## Setup

### configuration

#### exclude

It is configurations for exclusion settings

|     Key     |        Description         | Supported values |
| :---------: | :------------------------: | ---------------- |
| directories | directory name to exclude  | tests            |
|    types    | class type name to exclude | exception        |
|   methods   |   method name to exclude   | magic            |

#### exception

It is configurations for exception-related settings

| Key  |               Description                |
| :--: | :--------------------------------------: |
| name | pattern to specify exception class names |

### Example

```toml
[exclude]
directories = ["tests"]
types = ["exception"]
methods = ["magic"] # __init__(), __str__()

[exception]
name = "*Exception" # ex LevelOneException
```
