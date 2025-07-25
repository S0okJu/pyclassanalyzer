# pyclassanalyzer

**pyclassanalyzer** automatically analyzes the class structure of a Python project and exports the results as a diagram.

> [!IMPORTANT]  
> We did not using the `dataclass` element supported by PlantUML.
> Using the dataclass(@dataclass) may cause errors when working with older versions(prior to [v1.2025.4](https://github.com/plantuml/plantuml/releases/tag/v1.2025.4)) of the PlantUML. Therefore, we will create our own custom elements until the updated version of PlnatUML is widely adopted.

## Features

- **Automatic Analysis:** Parses your Python codebase to extract class information (attributes, methods) and relationships (inheritance, composition, usage).
- **PlantUML Output:** Generates class diagrams compatible with PlantUML.
- **Customization:** An configuration file is available that allow you to generate the graph you want.

## Prerequisites

To use PlantUML output, you need to have **Java** and **Graphviz** installed.

## How to Use

#### 1. Set up a configuration file(`config.toml`)

> [!NOTE]  
> For more information, please read [configuration file guide](./docs/config.md)

```toml
[exclude]
directories = ["tests"]
types = ["exception"]
methods = ["magic"]

[exception]
name = "*Exception"
```

#### 2. Execute pyclassanalyzer

```bash
python3 -m pyclassanalyzer.cli [path] [options]
```

### Options

| Option                | Description                                                                 | Default                           |
| --------------------- | --------------------------------------------------------------------------- | --------------------------------- |
| `path`                | Path to the Python file or directory to analyze                             |                                   |
| `--output`, `-o` NAME | Specify the output PlantUML file name                                       | `{project_name}_{timestamp}.puml` |
| `--summary`           | Print a summary of the analysis results                                     |                                   |
| `--title`, `-t` TITLE | Set the diagram title (auto-generated based on the project name by default) |                                   |

##### Example

![result](./imgs/v1.0.4.png)
