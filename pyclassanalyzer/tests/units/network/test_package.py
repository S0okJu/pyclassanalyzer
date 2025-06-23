import ast
import os
import pytest
import tempfile

from pathlib import Path

from pyclassanalyzer.network.package import (
    Package, PackageNode, PackageTree, split_path,
)

@pytest.fixture 
def packagenode_stub():
    """
    - root
        - test1_depth_1
            - test_depth_2
                - test.py
        - test2_depth_1
            - __init__.py
    """
    return PackageNode(
        value =  Package(
            name = "root",
            type_ = "package"
        ),
        childs = {
            "test1_depth_1": PackageNode(
                value = Package(
                    name = "test1_depth_1",
                    type_ = "package"
                ),
                childs = {
                    "test_depth_2": PackageNode (
                        value = Package(
                            name ="test_depth_2",
                            type_ = "package"
                        ),
                        childs = {}
                    ),
                    "test.py": PackageNode (
                        value = Package(
                            name ="test.py",
                            type_ = "module"
                        ),
                        childs = {} 
                    ),
                }
            ),
            "test2_depth_1": PackageNode(
                value = Package(
                    name = "test2_depth_1",
                    type_ = "package"
                ),
                childs = {
                    "__init__.py": PackageNode (
                        value = Package(
                            name ="__init__.py",
                            type_ = "module"
                        ),
                        childs = {}
                    ),
                }
            )
        }
    )

def test_Packagenode__add_child_package_success(
    packagenode_stub, 
    ):    
    result = Package(name = "test3_depth_1", type_ = "package")
    
    packagenode_stub._add_child(
        name = "test3_depth_1",
        type_ = "package"
    )
    
    assert packagenode_stub.childs['test3_depth_1'] is not None
    assert packagenode_stub.childs['test3_depth_1'].value == result

def test_Packagenode__add_child_module_success(
    packagenode_stub, 
):
    result = Package(name = "helloworld.py", type_ = "module")
    
    packagenode_stub._add_child(
        name = "helloworld.py",
        type_ = "module"
    )
    
    assert packagenode_stub.childs['helloworld.py'] is not None
    assert packagenode_stub.childs['helloworld.py'].value == result

def test_Packagenode__add_child_duplication_failed(
    packagenode_stub,   
):
    with pytest.raises(ValueError) as exec_info:
        packagenode_stub._add_child(
            name = "test1_depth_1",
            type_ = "package"
        )

        assert "Child with name test1_depth_1 already exists" in str(exec_info.value)


def test_Packagenode_get_child_success(
    packagenode_stub,
):
    result = PackageNode(
        value = Package(
            name = "test1_depth_1", 
            type_ = "package"
            ),
        childs = {
            "test_depth_2": PackageNode (
                value = Package(
                    name ="test_depth_2",
                    type_ = "package"
                ),
                childs = {}
            ),
            "test.py": PackageNode (
                value = Package(
                    name ="test.py",
                    type_ = "module"
                ),
                childs = {} 
            ),
        }
    )
    
    child = packagenode_stub.get_child(
        name = "test1_depth_1",
    )
    
    assert child is not None
    assert child.value == result.value
    assert child.childs == result.childs
    
def test_Packagenode_get_child_does_not_exist_failed(
    packagenode_stub,
):
    child = packagenode_stub.get_child(
        name = "test_does_not_exist"
    )
    
    assert child == None

def test_Packagenode_create_child_success(
    packagenode_stub
):
    result = packagenode_stub.create_child(
        name = "test3_depth_1",
        type_ = "package"
    )
    
    assert len(packagenode_stub.childs) == 3
    assert result == packagenode_stub.childs["test3_depth_1"]


def test_Packagenode_create_child_exsit_success(
    packagenode_stub
):
    
    result = packagenode_stub.create_child(
        name = "test2_depth_1",
        type_ = "package"
    )
    
    assert len(packagenode_stub.childs) == 2
    assert result == packagenode_stub.childs["test2_depth_1"]


@pytest.fixture
def path_list():
    return [
        "__init__.py",
        "cli.py",
        "generator/__init__.py",
        "generator/generator.py",
        "generator/Package/Package.py",
        "network/__init__.py",
        "network/Package.py",
    ]

def test_Packagetree_build_success(
    path_list
):
    result = PackageTree(root='pyclassanalyzer')
    
    result.build(paths=path_list, base_path='./pyclassanalyzer')
    
    root = result.root
    assert root.value.name == 'pyclassanalyzer'
    assert 'cli.py' in root.childs
    assert 'generator' in root.childs
    assert 'network' in root.childs

    generator = root.childs['generator']
    assert 'generator.py' in generator.childs
    assert '__init__.py' in generator.childs
    assert 'Package' in generator.childs
    assert 'Package.py' in generator.childs['Package'].childs

    network = root.childs['network']
    assert '__init__.py' in network.childs
    assert 'Package.py' in network.childs

@pytest.fixture
def sample_package_structure():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample directory structure
        root = Path(tmpdir) / "my_package"
        root.mkdir()

        # Create files
        (root / "module1.py").write_text("class A: pass", encoding='utf-8')
        (root / "subpackage").mkdir()
        (root / "subpackage" / "module2.py").write_text("def func(): return 42", encoding='utf-8')

        paths = [
            str(root / "module1.py"),
            str(root / "subpackage" / "module2.py"),
        ]

        yield str(root), paths
   
def test_package_tree_traverse(sample_package_structure):
    base_path, paths = sample_package_structure

    tree = PackageTree(root="my_package")
    tree.build(paths=paths, base_path=base_path)

    results = list(tree.traverse(base_path=base_path))

    assert len(results) == 2
    assert "module1.py" in results[0][0]
    assert "module2.py" in results[1][0]


    

    
    



    
    
    