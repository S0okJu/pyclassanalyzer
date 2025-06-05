import os
from collections import defaultdict

class PlantUMLFormatter:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def save_plantuml_diagram(self, filename="class_diagram.puml", include_attributes=True, include_methods=True):
        modules = defaultdict(list)
        for cls, mod in self.analyzer.class_modules.items():
            modules[mod].append(cls)
        tree = {}
        for mod, classes in modules.items():
            if not mod:
                continue
            parts = mod.split('.')
            current_node = tree
            for i in range(len(parts) - 1):
                package_name = parts[i]
                if package_name not in current_node:
                    current_node[package_name] = {}
                current_node = current_node[package_name]
            if '_files' not in current_node:
                current_node['_files'] = []
            current_node['_files'].append(mod)
        def sanitize(name):
            return "".join(c if c.isalnum() else "_" for c in name)
        with open(filename, "w", encoding="utf-8") as f:
            f.write("@startuml\n\n")
            f.write('skinparam class {\n')
            f.write('  BackgroundColor<<External>> LightBlue\n')
            f.write('}\n\n')
            declared_classes = set()
            declared_relationships = set()
            def declare_class(cls_name, external=False):
                cls_id = sanitize(cls_name)
                if cls_id not in declared_classes:
                    declared_classes.add(cls_id)
                    simple_name = cls_name.split(".")[-1]
                    if external:
                        f.write(f'class {cls_id} as "{simple_name}" <<External>>\n')
                    else:
                        f.write(f'class {cls_id} as "{simple_name}"\n')
                return cls_id
            def write_tree(node, indent=0):
                indent_str = "  " * indent
                if '_files' in node:
                    for mod in node['_files']:
                        if mod in self.analyzer.module_to_file:
                            file_name = self.analyzer.module_to_file[mod]
                            file_name_without_ext = os.path.splitext(file_name)[0]
                        else:
                            module_parts = mod.split('.')
                            file_name_without_ext = module_parts[-1]
                        escaped_file_name = f'"{file_name_without_ext}"' if '.' in file_name_without_ext else file_name_without_ext
                        f.write(f'{indent_str}frame {escaped_file_name} {{\n')
                        for cls in modules.get(mod, []):
                            cls_id = sanitize(cls)
                            simple_name = cls.split(".")[-1]
                            f.write(f'{indent_str}  class {cls_id} as "{simple_name}" {{\n')
                            if include_attributes and cls in self.analyzer.class_attributes:
                                attributes = self.analyzer.class_attributes[cls]
                                if attributes:
                                    for attr_name, attr_info in attributes.items():
                                        attr_line = self.analyzer._format_attribute_for_plantuml(attr_name, attr_info)
                                        f.write(f'{indent_str}    {attr_line}\n')
                                    f.write(f'{indent_str}    --\n')
                            if include_methods and cls in self.analyzer.class_methods:
                                methods = self.analyzer.class_methods[cls]
                                for method_info in methods:
                                    method_line = self.analyzer._format_method_for_plantuml(method_info)
                                    if method_line:
                                        f.write(f'{indent_str}    {method_line}\n')
                            f.write(f'{indent_str}  }}\n')
                        f.write(f'{indent_str}}}\n\n')
                for key, subnode in node.items():
                    if key == '_files':
                        continue
                    escaped_package_name = f'"{key}"' if '.' in key else key
                    f.write(f'{indent_str}package {escaped_package_name} <<Folder>> {{\n')
                    write_tree(subnode, indent + 1)
                    f.write(f'{indent_str}}}\n\n')
            write_tree(tree)
            for child, parents in self.analyzer.inheritance.items():
                child_id = sanitize(child)
                for parent in parents:
                    if parent in self.analyzer.external_classes:
                        parent_id = sanitize(parent)
                        if parent_id not in declared_classes:
                            declare_class(parent, external=True)
                    else:
                        parent_id = sanitize(parent)
                    relationship = f"{parent_id} <|-- {child_id}"
                    if relationship not in declared_relationships:
                        declared_relationships.add(relationship)
                        f.write(f"{relationship}\n")
            for cls, members in self.analyzer.composition.items():
                cls_id = sanitize(cls)
                for member in members:
                    if member in self.analyzer.external_classes:
                        member_id = sanitize(member)
                        if member_id not in declared_classes:
                            declare_class(member, external=True)
                    else:
                        member_id = sanitize(member)
                    relationship = f"{cls_id} --> {member_id} : has-a"
                    if relationship not in declared_relationships:
                        declared_relationships.add(relationship)
                        f.write(f"{relationship}\n")
            f.write("\n@enduml\n") 